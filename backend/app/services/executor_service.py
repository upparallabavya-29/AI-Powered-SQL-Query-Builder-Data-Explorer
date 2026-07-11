import os
import time
import sqlite3
import logging
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from backend.app.models.models import UploadedSchema
from backend.app.repositories.query_repository import SchemaRepository, ExecutionLogRepository
from backend.app.security.validator import validate_sql_query
from backend.app.security.sqlite_authorizer import apply_sqlite_security

logger = logging.getLogger(__name__)

class QueryExecutorService:
    @staticmethod
    def execute_query(
        db: Session,
        schema_id: str,
        sql: str,
        limit: int = 100,
        offset: int = 0,
        query_history_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes an approved read-only SELECT query against the dynamic database.
        Enforces execution constraints:
          1. AST security checks
          2. sqlite3 set_authorizer write prevention
          3. 10-second execution timeout via progress handler aborts
          4. Pagination capping (maximum 1000 rows returned)
        """
        # 1. Fetch schema information
        schema = SchemaRepository.get(db, schema_id)
        if not schema:
            error_msg = f"Schema with ID {schema_id} not found."
            ExecutionLogRepository.create(db, query_history_id, False, error_msg, 0, 0)
            raise ValueError(error_msg)

        if not schema.db_path or not os.path.exists(schema.db_path):
            error_msg = "Database file is missing or has not been initialized for this schema."
            ExecutionLogRepository.create(db, query_history_id, False, error_msg, 0, 0)
            raise FileNotFoundError(error_msg)

        # 2. Run AST validation
        is_valid, clean_sql, validation_errors = validate_sql_query(sql, dialect="sqlite")
        if not is_valid:
            error_msg = f"SQL Security Validation failed: {', '.join(validation_errors)}"
            ExecutionLogRepository.create(db, query_history_id, False, error_msg, 0, 0)
            return {
                "success": False,
                "columns": [],
                "rows": [],
                "execution_time_ms": 0,
                "total_rows": 0,
                "has_more": False,
                "errors": validation_errors
            }

        # 3. Apply pagination wrapping
        # Enforce server-side pagination limit (max 1000)
        final_limit = min(max(1, limit), 1000)
        # Wrap query to fetch rows for current page + 1 (to check for has_more)
        paginated_sql = f"SELECT * FROM ({clean_sql}) LIMIT {final_limit + 1} OFFSET {offset}"

        columns = []
        rows = []
        execution_time_ms = 0
        success = False
        error_msg = None

        start_time = time.time()
        conn = None
        try:
            # 4. Open isolated connection
            conn = sqlite3.connect(schema.db_path)
            conn.row_factory = sqlite3.Row  # Returns rows as dictionary-like objects
            
            # Apply connection-level write blocking
            apply_sqlite_security(conn)

            # 5. Set progress handler for 10-second timeout
            # Every 50 SQLite VM instructions, check if time limit has passed.
            def timeout_check():
                if time.time() - start_time > 10.0:
                    return 1  # Abort query
                return 0
            
            conn.set_progress_handler(timeout_check, 50)

            # 6. Execute SQL
            cursor = conn.cursor()
            cursor.execute(paginated_sql)
            
            # Fetch results
            db_rows = cursor.fetchall()
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Extract column names
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
            
            # Format row data as dictionaries
            rows = [dict(row) for row in db_rows]
            
            # Calculate pagination details
            has_more = len(rows) > final_limit
            if has_more:
                rows = rows[:final_limit]  # Discard the extra row used for has_more check
            
            success = True
            
        except sqlite3.DatabaseError as de:
            execution_time_ms = int((time.time() - start_time) * 1000)
            err_str = str(de)
            if "authorizer" in err_str or "not authorized" in err_str:
                error_msg = "Security constraint violation: The query attempted an unauthorized write or schema modification operation."
            elif "interrupted" in err_str or "query aborted" in err_str:
                error_msg = "Query execution timeout: The query exceeded the maximum allowed limit of 10 seconds."
            else:
                error_msg = f"Database execution error: {err_str}"
            logger.error(f"SQL execution error on schema {schema_id}: {err_str}")
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Execution failed: {str(e)}"
            logger.error(f"Execution failed on schema {schema_id}: {str(e)}")
            
        finally:
            if conn:
                conn.close()

        # 7. Write to Execution Log
        ExecutionLogRepository.create(
            db=db,
            query_history_id=query_history_id,
            success=success,
            error_message=error_msg,
            rows_returned=len(rows) if success else 0,
            execution_time_ms=execution_time_ms
        )

        if not success:
            return {
                "success": False,
                "columns": [],
                "rows": [],
                "execution_time_ms": execution_time_ms,
                "total_rows": 0,
                "has_more": False,
                "errors": [error_msg]
            }

        return {
            "success": True,
            "columns": columns,
            "rows": rows,
            "execution_time_ms": execution_time_ms,
            "total_rows": len(rows),
            "has_more": has_more,
            "errors": []
        }

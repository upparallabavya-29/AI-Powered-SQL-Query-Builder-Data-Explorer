import os
import json
import sqlite3
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
import sqlglot
from sqlglot import expressions as exp
from sqlalchemy.orm import Session
from backend.app.models.models import UploadedSchema
from backend.app.repositories.query_repository import SchemaRepository
from backend.app.utils.seeder import seed_sample_database

logger = logging.getLogger(__name__)

if (
    os.getenv("VERCEL")
    or os.getenv("VERCEL_ENV")
    or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
    or os.getenv("LAMBDA_TASK_ROOT")
):
    DB_FILES_DIR = "/tmp/db_files"
else:
    DB_FILES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "db_files"))

try:
    os.makedirs(DB_FILES_DIR, exist_ok=True)
except Exception as e:
    logging.getLogger(__name__).warning(f"Could not create DB_FILES_DIR {DB_FILES_DIR} at startup: {e}")

class SchemaService:
    @staticmethod
    def parse_sql_ddl(ddl: str) -> Dict[str, Any]:
        """
        Parses raw SQL DDL using sqlglot and returns a structured representation:
        { "table_name": [{"name": "col_name", "type": "col_type"}, ...] }
        """
        parsed_structure = {}
        try:
            expressions = sqlglot.parse(ddl)
            for expr in expressions:
                if isinstance(expr, exp.Create) and expr.args.get("kind") == "TABLE":
                    table_node = expr.find(exp.Table)
                    if not table_node:
                        continue
                    table_name = table_node.name.lower()
                    
                    columns = []
                    for col_def in expr.find_all(exp.ColumnDef):
                        col_name = col_def.name.lower()
                        col_type_node = col_def.args.get("kind")
                        col_type = str(col_type_node) if col_type_node else "TEXT"
                        columns.append({"name": col_name, "type": col_type})
                    
                    if table_name and columns:
                        parsed_structure[table_name] = columns
        except Exception as e:
            logger.error(f"Error parsing DDL SQL: {str(e)}")
            raise ValueError(f"Failed to parse DDL SQL schema: {str(e)}")
        
        if not parsed_structure:
            raise ValueError("No valid CREATE TABLE statements found in the uploaded SQL DDL.")
            
        return parsed_structure

    @staticmethod
    def parse_json_schema(json_str: str) -> Dict[str, Any]:
        """
        Parses JSON schemas of the format:
        { "tables": { "table_name": { "column_name": "data_type", ... } } }
        Or:
        { "table_name": [{"name": "column_name", "type": "data_type"}, ...] }
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as jde:
            raise ValueError(f"Invalid JSON format: {str(jde)}")

        parsed_structure = {}
        
        # Check format 1: { "tables": { "table_name": { "col": "type" } } }
        if "tables" in data and isinstance(data["tables"], dict):
            tables = data["tables"]
            for t_name, cols in tables.items():
                if isinstance(cols, dict):
                    parsed_structure[t_name.lower()] = [
                        {"name": col_name.lower(), "type": str(col_type).upper()}
                        for col_name, col_type in cols.items()
                    ]
        # Check format 2: { "table_name": [{"name": "col", "type": "type"}] }
        elif isinstance(data, dict):
            for t_name, cols in data.items():
                if isinstance(cols, list):
                    columns = []
                    for col in cols:
                        if isinstance(col, dict) and "name" in col and "type" in col:
                            columns.append({"name": str(col["name"]).lower(), "type": str(col["type"]).upper()})
                    if columns:
                        parsed_structure[t_name.lower()] = columns
                elif isinstance(cols, dict):
                    parsed_structure[t_name.lower()] = [
                        {"name": col_name.lower(), "type": str(col_type).upper()}
                        for col_name, col_type in cols.items()
                    ]
        
        if not parsed_structure:
            raise ValueError("No valid table structures could be extracted from JSON.")
            
        return parsed_structure

    @classmethod
    def generate_ddl_from_parsed(cls, parsed_tables: Dict[str, Any]) -> str:
        """Converts structured table details back to a standard SQLite DDL string."""
        ddl_parts = []
        for table_name, columns in parsed_tables.items():
            col_definitions = []
            for col in columns:
                col_definitions.append(f"{col['name']} {col['type']}")
            col_str = ", ".join(col_definitions)
            ddl_parts.append(f"CREATE TABLE {table_name} (\n  {col_str}\n);")
        return "\n\n".join(ddl_parts)

    @classmethod
    def upload_schema(cls, db: Session, name: str, schema_type: str, raw_content: str) -> UploadedSchema:
        """Processes a schema upload, creates a corresponding sqlite database, and seeds it."""
        # 1. Parse content based on type
        if schema_type == "sql":
            parsed_tables = cls.parse_sql_ddl(raw_content)
            ddl_sql = raw_content
        elif schema_type == "json":
            parsed_tables = cls.parse_json_schema(raw_content)
            ddl_sql = cls.generate_ddl_from_parsed(parsed_tables)
        else:
            raise ValueError("Invalid schema type. Supported types are 'sql' or 'json'.")

        # Create schema record (temporary DB path to generate UUID first)
        schema_record = SchemaRepository.create(
            db=db,
            name=name,
            schema_type=schema_type,
            raw_content=raw_content,
            parsed_tables=parsed_tables
        )

        # Update db_path using the schema record ID
        db_filename = f"schema_{schema_record.id}.db"
        db_path = os.path.join(DB_FILES_DIR, db_filename)
        
        schema_record.db_path = db_path
        db.commit()
        db.refresh(schema_record)

        # 2. Build and seed the database
        try:
            cls.initialize_sqlite_database(db_path, ddl_sql, parsed_tables)
        except Exception as e:
            # Cleanup DB file if initialization failed
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except Exception:
                    pass
            SchemaRepository.delete(db, schema_record.id)
            raise RuntimeError(f"Database initialization failed: {str(e)}")

        return schema_record

    @classmethod
    def initialize_sqlite_database(cls, db_path: str, ddl_sql: str, parsed_tables: Dict[str, Any]):
        """Executes the DDL statements on the SQLite file and seeds it with mock data."""
        # Check if the schema matches our high-fidelity sample analytics database
        required_sample_tables = {"customers", "orders", "products", "employees", "sales"}
        uploaded_tables = set(parsed_tables.keys())
        
        if required_sample_tables.issubset(uploaded_tables):
            # Seed our rich pre-populated analytics dataset
            seed_sample_database(db_path)
            return

        # Otherwise, dynamically create the tables and seed generic mock data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Execute the DDL queries to create the tables
        # SQLite's executescript parses and runs multiple SQL commands
        cursor.executescript(ddl_sql)
        
        # Generate and insert mock data (5-10 rows per table)
        for table_name, columns in parsed_tables.items():
            cls.seed_generic_mock_data(cursor, table_name, columns)
            
        conn.commit()
        conn.close()

    @classmethod
    def seed_generic_mock_data(cls, cursor: sqlite3.Cursor, table_name: str, columns: list):
        """Generates and inserts generic mock rows into a table depending on column data types."""
        # Simple data generation depending on type name matching
        col_names = [col["name"] for col in columns]
        
        # We don't want to insert primary keys if they are AUTOINCREMENT or generated,
        # but for simple seeding, let's identify column definitions
        # Let's generate 8 records
        for i in range(1, 9):
            vals = []
            for col in columns:
                c_name = col["name"].lower()
                c_type = col["type"].upper()
                
                # Check for ID columns
                if "id" in c_name and ("key" in c_type or "int" in c_type):
                    # If it's the primary key of this table (usually named id or table_id),
                    # let's just use the index 'i' unless it's a foreign key.
                    if c_name == "id" or c_name == f"{table_name}_id":
                        vals.append(i)
                    else:
                        # Probably a foreign key to another table, reference index (random 1 to 5)
                        vals.append(random.randint(1, 5))
                elif "INT" in c_type or "NUM" in c_type or "DEC" in c_type or "DOUBLE" in c_type or "FLOAT" in c_type:
                    if "price" in c_name or "amount" in c_name or "total" in c_name or "salary" in c_name:
                        vals.append(round(random.uniform(10.0, 500.0), 2))
                    elif "qty" in c_name or "quantity" in c_name or "stock" in c_name or "age" in c_name:
                        vals.append(random.randint(1, 100))
                    else:
                        vals.append(random.randint(1000, 9999))
                elif "DATE" in c_type or "TIME" in c_type:
                    # Random date within last year
                    days_ago = random.randint(1, 365)
                    random_date = (datetime.utcnow() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
                    vals.append(random_date)
                elif "BOOL" in c_type:
                    vals.append(random.choice([0, 1]))
                else:
                    # String column
                    if "email" in c_name:
                        vals.append(f"user{i}@{table_name}.com")
                    elif "name" in c_name:
                        vals.append(f"Mock {table_name.capitalize()} Name {i}")
                    elif "desc" in c_name:
                        vals.append(f"This is a mock description number {i} for table {table_name}.")
                    elif "country" in c_name or "city" in c_name:
                        vals.append(random.choice(["USA", "Canada", "Germany", "Japan", "UK"]))
                    else:
                        vals.append(f"MockData_{i}")

            # Construct INSERT statement
            placeholders = ", ".join(["?"] * len(col_names))
            query = f"INSERT OR IGNORE INTO {table_name} ({', '.join(col_names)}) VALUES ({placeholders})"
            try:
                cursor.execute(query, vals)
            except Exception as e:
                logger.warning(f"Failed to seed generic row {i} for {table_name}: {str(e)}")

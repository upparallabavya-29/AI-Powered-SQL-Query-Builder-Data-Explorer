from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.schemas import (
    ApiResponse,
    SchemaUploadRequest,
    SchemaResponse,
    GenerateSqlRequest,
    GenerateSqlResponse,
    ValidateSqlRequest,
    ValidateSqlResponse,
    ExecuteSqlRequest,
    ExecuteSqlResponse,
    SaveQueryRequest,
    SavedQueryResponse,
    FavoriteToggleRequest,
    HistoryResponse
)
from backend.app.repositories.query_repository import (
    SchemaRepository,
    HistoryRepository,
    SavedQueryRepository,
    FavoriteRepository
)
from backend.app.services.schema_service import SchemaService
from backend.app.services.executor_service import QueryExecutorService
from backend.app.llm.llm_client import LlmClient
from backend.app.security.validator import validate_sql_query

router = APIRouter()

# --- SCHEMA ENDPOINTS ---

@router.post("/schemas", response_model=ApiResponse)
def upload_schema(payload: SchemaUploadRequest, db: Session = Depends(get_db)):
    """Uploads a schema (SQL DDL or JSON), provisions a SQLite database, and seeds mock data."""
    try:
        schema = SchemaService.upload_schema(
            db=db,
            name=payload.name,
            schema_type=payload.schema_type,
            raw_content=payload.raw_content
        )
        return ApiResponse(
            success=True,
            data=SchemaResponse.model_validate(schema),
            message="Schema uploaded and database sandbox created successfully."
        )
    except ValueError as ve:
        return ApiResponse(success=False, message=str(ve), errors=[str(ve)])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema upload failed: {str(e)}"
        )


@router.get("/schemas", response_model=ApiResponse)
def list_schemas(db: Session = Depends(get_db)):
    """Lists all uploaded schemas and their details."""
    schemas = SchemaRepository.list_all(db)
    return ApiResponse(
        success=True,
        data=[SchemaResponse.model_validate(s) for s in schemas]
    )


@router.get("/schemas/{schema_id}", response_model=ApiResponse)
def get_schema(schema_id: str, db: Session = Depends(get_db)):
    """Fetches a specific schema definition."""
    schema = SchemaRepository.get(db, schema_id)
    if not schema:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schema not found")
    return ApiResponse(
        success=True,
        data=SchemaResponse.model_validate(schema)
    )


# --- SQL GENERATION AND VALIDATION ENDPOINTS ---

@router.post("/queries/generate", response_model=ApiResponse)
def generate_sql(payload: GenerateSqlRequest, db: Session = Depends(get_db)):
    """Translates a natural language question into valid SQLite SQL using LLM."""
    schema = SchemaRepository.get(db, payload.schema_id)
    if not schema:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schema not found")

    try:
        # Generate the SQL string
        sql = LlmClient.generate_sql(
            schema_name=schema.name,
            parsed_tables=schema.parsed_tables,
            prompt=payload.prompt
        )

        # Automatically log the query in history (without execution logs yet)
        history_item = HistoryRepository.create(
            db=db,
            schema_id=payload.schema_id,
            prompt=payload.prompt,
            generated_sql=sql
        )

        # Prepare response including generated query and the history item ID
        res_data = {
            "query_history_id": history_item.id,
            "generated_sql": sql
        }
        return ApiResponse(
            success=True,
            data=res_data,
            message="SQL query generated and logged to history."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SQL generation failed: {str(e)}"
        )


@router.post("/queries/validate", response_model=ApiResponse)
def validate_sql(payload: ValidateSqlRequest):
    """Checks query safety (read-only, single-statement) before execution."""
    is_valid, clean_sql, errors = validate_sql_query(payload.sql, dialect="sqlite")
    data = ValidateSqlResponse(valid=is_valid, message="SQL is valid." if is_valid else "SQL failed validation checks.", errors=errors)
    return ApiResponse(success=is_valid, data=data, message=data.message, errors=errors)


@router.post("/queries/execute", response_model=ApiResponse)
def execute_sql(payload: ExecuteSqlRequest, db: Session = Depends(get_db)):
    """Executes a user-approved read-only SQL query on the target database sandbox."""
    try:
        result = QueryExecutorService.execute_query(
            db=db,
            schema_id=payload.schema_id,
            sql=payload.sql,
            limit=payload.limit,
            offset=payload.offset,
            query_history_id=payload.query_history_id
        )
        
        # If execution succeeded, return result, else wrap errors
        if result["success"]:
            # Update history execution time if query_history_id is supplied
            if payload.query_history_id:
                history_item = HistoryRepository.get(db, payload.query_history_id)
                if history_item:
                    history_item.execution_time_ms = result["execution_time_ms"]
                    db.commit()
            
            data = ExecuteSqlResponse(
                columns=result["columns"],
                rows=result["rows"],
                execution_time_ms=result["execution_time_ms"],
                total_rows=result["total_rows"],
                has_more=result["has_more"]
            )
            return ApiResponse(success=True, data=data, message="Query executed successfully.")
        else:
            return ApiResponse(
                success=False,
                message="Query execution failed.",
                errors=result["errors"]
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution service failure: {str(e)}"
        )


# --- HISTORY & FAVORITES ENDPOINTS ---

@router.get("/queries/history/{schema_id}", response_model=ApiResponse)
def get_query_history(schema_id: str, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """Fetches the past query history logs for a schema."""
    history_items = HistoryRepository.list_by_schema(db, schema_id, limit, offset)
    
    # Map models to response and check favorite flags
    response_items = []
    for item in history_items:
        is_fav = FavoriteRepository.is_favorite(db, item.id)
        response_items.append(
            HistoryResponse(
                id=item.id,
                schema_id=item.schema_id,
                prompt=item.prompt,
                generated_sql=item.generated_sql,
                execution_time_ms=item.execution_time_ms,
                created_at=item.created_at,
                is_favorite=is_fav
            )
        )
    return ApiResponse(success=True, data=response_items)


@router.delete("/queries/history/{schema_id}", response_model=ApiResponse)
def clear_query_history(schema_id: str, db: Session = Depends(get_db)):
    """Deletes all query history items for a schema."""
    HistoryRepository.delete_all_by_schema(db, schema_id)
    return ApiResponse(success=True, message="Query history cleared successfully.")


@router.delete("/queries/history-item/{history_id}", response_model=ApiResponse)
def delete_history_item(history_id: str, db: Session = Depends(get_db)):
    """Deletes a single history item."""
    success = HistoryRepository.delete_by_id(db, history_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History item not found")
    return ApiResponse(success=True, message="History item deleted successfully.")


@router.post("/queries/favorites", response_model=ApiResponse)
def toggle_favorite(payload: FavoriteToggleRequest, db: Session = Depends(get_db)):
    """Toggles the favorite flag on a history item."""
    is_fav = FavoriteRepository.is_favorite(db, payload.query_history_id)
    if is_fav:
        FavoriteRepository.remove(db, payload.query_history_id)
        is_now_fav = False
        msg = "Removed from favorites."
    else:
        FavoriteRepository.add(db, payload.query_history_id)
        is_now_fav = True
        msg = "Added to favorites."
        
    return ApiResponse(success=True, data={"is_favorite": is_now_fav}, message=msg)


@router.get("/queries/favorites/{schema_id}", response_model=ApiResponse)
def list_favorites(schema_id: str, db: Session = Depends(get_db)):
    """Lists all favorited queries for a schema."""
    items = FavoriteRepository.list_by_schema(db, schema_id)
    response_items = [
        HistoryResponse(
            id=item.id,
            schema_id=item.schema_id,
            prompt=item.prompt,
            generated_sql=item.generated_sql,
            execution_time_ms=item.execution_time_ms,
            created_at=item.created_at,
            is_favorite=True
        )
        for item in items
    ]
    return ApiResponse(success=True, data=response_items)


# --- SAVED QUERIES ---

@router.post("/queries/saved", response_model=ApiResponse)
def save_query(payload: SaveQueryRequest, db: Session = Depends(get_db)):
    """Saves a SQL query with a name for future reuse."""
    try:
        saved = SavedQueryRepository.create(
            db=db,
            schema_id=payload.schema_id,
            name=payload.name,
            prompt=payload.prompt,
            sql_query=payload.sql_query
        )
        return ApiResponse(
            success=True,
            data=SavedQueryResponse.model_validate(saved),
            message="Query saved successfully."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save query: {str(e)}"
        )


@router.get("/queries/saved/{schema_id}", response_model=ApiResponse)
def list_saved_queries(schema_id: str, db: Session = Depends(get_db)):
    """Lists all saved queries for a schema."""
    queries = SavedQueryRepository.list_by_schema(db, schema_id)
    return ApiResponse(
        success=True,
        data=[SavedQueryResponse.model_validate(q) for q in queries]
    )


@router.delete("/queries/saved/{query_id}", response_model=ApiResponse)
def delete_saved_query(query_id: str, db: Session = Depends(get_db)):
    """Deletes a saved query."""
    success = SavedQueryRepository.delete(db, query_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved query not found")
    return ApiResponse(success=True, message="Saved query deleted successfully.")

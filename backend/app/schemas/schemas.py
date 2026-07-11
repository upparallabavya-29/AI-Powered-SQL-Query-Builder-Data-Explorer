from typing import Any, List, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

# Standard API response envelope
class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = ""
    errors: Optional[List[str]] = Field(default_factory=list)


# Schema upload models
class SchemaUploadRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    schema_type: str = Field(..., pattern="^(sql|json)$")
    raw_content: str = Field(..., min_length=1)


class SchemaResponse(BaseModel):
    id: str
    name: str
    schema_type: str
    parsed_tables: dict
    created_at: datetime

    class Config:
        from_attributes = True


# SQL generation models
class GenerateSqlRequest(BaseModel):
    schema_id: str
    prompt: str = Field(..., min_length=1)


class GenerateSqlResponse(BaseModel):
    generated_sql: str


# SQL validation models
class ValidateSqlRequest(BaseModel):
    sql: str = Field(..., min_length=1)


class ValidateSqlResponse(BaseModel):
    valid: bool
    message: str
    errors: List[str] = []


# SQL execution models
class ExecuteSqlRequest(BaseModel):
    schema_id: str
    sql: str = Field(..., min_length=1)
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)
    query_history_id: Optional[str] = None


class ExecuteSqlResponse(BaseModel):
    columns: List[str]
    rows: List[dict]
    execution_time_ms: int
    total_rows: int
    has_more: bool


# Saved query models
class SaveQueryRequest(BaseModel):
    schema_id: str
    name: str = Field(..., min_length=1, max_length=255)
    prompt: Optional[str] = None
    sql_query: str = Field(..., min_length=1)


class SavedQueryResponse(BaseModel):
    id: str
    schema_id: str
    name: str
    prompt: Optional[str] = None
    sql_query: str
    created_at: datetime

    class Config:
        from_attributes = True


# Favorite models
class FavoriteToggleRequest(BaseModel):
    query_history_id: str


# History models
class HistoryResponse(BaseModel):
    id: str
    schema_id: str
    prompt: str
    generated_sql: str
    execution_time_ms: Optional[int] = None
    created_at: datetime
    is_favorite: bool = False

    class Config:
        from_attributes = True

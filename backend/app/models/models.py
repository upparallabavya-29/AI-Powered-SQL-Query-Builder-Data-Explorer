import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class UploadedSchema(Base):
    __tablename__ = "uploaded_schemas"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    schema_type = Column(String(50), nullable=False)  # "sql" or "json"
    raw_content = Column(Text, nullable=False)
    parsed_tables = Column(JSON, nullable=False)      # JSON tree of table schemas
    db_path = Column(String(512), nullable=True)       # Path to dynamic SQLite db file
    created_at = Column(DateTime, default=datetime.utcnow)

    queries = relationship("QueryHistory", back_populates="schema", cascade="all, delete-orphan")
    saved_queries = relationship("SavedQuery", back_populates="schema", cascade="all, delete-orphan")


class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    schema_id = Column(String(36), ForeignKey("uploaded_schemas.id", ondelete="CASCADE"), nullable=False)
    prompt = Column(Text, nullable=False)
    generated_sql = Column(Text, nullable=False)
    execution_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    schema = relationship("UploadedSchema", back_populates="queries")
    favorites = relationship("Favorite", back_populates="query_history", cascade="all, delete-orphan")
    execution_logs = relationship("ExecutionLog", back_populates="query_history", cascade="all, delete-orphan")


class SavedQuery(Base):
    __tablename__ = "saved_queries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    schema_id = Column(String(36), ForeignKey("uploaded_schemas.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    prompt = Column(Text, nullable=True)
    sql_query = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    schema = relationship("UploadedSchema", back_populates="saved_queries")


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    query_history_id = Column(String(36), ForeignKey("query_history.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    query_history = relationship("QueryHistory", back_populates="favorites")


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    query_history_id = Column(String(36), ForeignKey("query_history.id", ondelete="CASCADE"), nullable=True)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    rows_returned = Column(Integer, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)

    query_history = relationship("QueryHistory", back_populates="execution_logs")

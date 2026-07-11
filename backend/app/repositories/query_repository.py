from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.models import UploadedSchema, QueryHistory, SavedQuery, Favorite, ExecutionLog

class SchemaRepository:
    @staticmethod
    def create(db: Session, name: str, schema_type: str, raw_content: str, parsed_tables: dict, db_path: Optional[str] = None) -> UploadedSchema:
        db_schema = UploadedSchema(
            name=name,
            schema_type=schema_type,
            raw_content=raw_content,
            parsed_tables=parsed_tables,
            db_path=db_path
        )
        db.add(db_schema)
        db.commit()
        db.refresh(db_schema)
        return db_schema

    @staticmethod
    def get(db: Session, schema_id: str) -> Optional[UploadedSchema]:
        return db.query(UploadedSchema).filter(UploadedSchema.id == schema_id).first()

    @staticmethod
    def list_all(db: Session) -> List[UploadedSchema]:
        return db.query(UploadedSchema).order_by(UploadedSchema.created_at.desc()).all()

    @staticmethod
    def delete(db: Session, schema_id: str) -> bool:
        db_schema = db.query(UploadedSchema).filter(UploadedSchema.id == schema_id).first()
        if db_schema:
            db.delete(db_schema)
            db.commit()
            return True
        return False


class HistoryRepository:
    @staticmethod
    def create(db: Session, schema_id: str, prompt: str, generated_sql: str, execution_time_ms: Optional[int] = None) -> QueryHistory:
        history = QueryHistory(
            schema_id=schema_id,
            prompt=prompt,
            generated_sql=generated_sql,
            execution_time_ms=execution_time_ms
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        return history

    @staticmethod
    def get(db: Session, history_id: str) -> Optional[QueryHistory]:
        return db.query(QueryHistory).filter(QueryHistory.id == history_id).first()

    @staticmethod
    def list_by_schema(db: Session, schema_id: str, limit: int = 50, offset: int = 0) -> List[QueryHistory]:
        return (
            db.query(QueryHistory)
            .filter(QueryHistory.schema_id == schema_id)
            .order_by(QueryHistory.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def delete_all_by_schema(db: Session, schema_id: str) -> bool:
        db.query(QueryHistory).filter(QueryHistory.schema_id == schema_id).delete(synchronize_session=False)
        db.commit()
        return True

    @staticmethod
    def delete_by_id(db: Session, history_id: str) -> bool:
        history = db.query(QueryHistory).filter(QueryHistory.id == history_id).first()
        if history:
            db.delete(history)
            db.commit()
            return True
        return False


class SavedQueryRepository:
    @staticmethod
    def create(db: Session, schema_id: str, name: str, prompt: Optional[str], sql_query: str) -> SavedQuery:
        saved = SavedQuery(
            schema_id=schema_id,
            name=name,
            prompt=prompt,
            sql_query=sql_query
        )
        db.add(saved)
        db.commit()
        db.refresh(saved)
        return saved

    @staticmethod
    def get(db: Session, query_id: str) -> Optional[SavedQuery]:
        return db.query(SavedQuery).filter(SavedQuery.id == query_id).first()

    @staticmethod
    def list_by_schema(db: Session, schema_id: str) -> List[SavedQuery]:
        return (
            db.query(SavedQuery)
            .filter(SavedQuery.schema_id == schema_id)
            .order_by(SavedQuery.created_at.desc())
            .all()
        )

    @staticmethod
    def delete(db: Session, query_id: str) -> bool:
        saved = db.query(SavedQuery).filter(SavedQuery.id == query_id).first()
        if saved:
            db.delete(saved)
            db.commit()
            return True
        return False


class FavoriteRepository:
    @staticmethod
    def add(db: Session, query_history_id: str) -> Favorite:
        # Check if already favorited
        existing = db.query(Favorite).filter(Favorite.query_history_id == query_history_id).first()
        if existing:
            return existing
        favorite = Favorite(query_history_id=query_history_id)
        db.add(favorite)
        db.commit()
        db.refresh(favorite)
        return favorite

    @staticmethod
    def remove(db: Session, query_history_id: str) -> bool:
        favorite = db.query(Favorite).filter(Favorite.query_history_id == query_history_id).first()
        if favorite:
            db.delete(favorite)
            db.commit()
            return True
        return False

    @staticmethod
    def is_favorite(db: Session, query_history_id: str) -> bool:
        return db.query(Favorite).filter(Favorite.query_history_id == query_history_id).count() > 0

    @staticmethod
    def list_by_schema(db: Session, schema_id: str) -> List[QueryHistory]:
        return (
            db.query(QueryHistory)
            .join(Favorite, QueryHistory.id == Favorite.query_history_id)
            .filter(QueryHistory.schema_id == schema_id)
            .order_by(Favorite.created_at.desc())
            .all()
        )


class ExecutionLogRepository:
    @staticmethod
    def create(db: Session, query_history_id: Optional[str], success: bool, error_message: Optional[str], rows_returned: Optional[int], execution_time_ms: Optional[int]) -> ExecutionLog:
        log = ExecutionLog(
            query_history_id=query_history_id,
            success=success,
            error_message=error_message,
            rows_returned=rows_returned,
            execution_time_ms=execution_time_ms
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

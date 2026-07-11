import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Ensure backend root is in PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.database.session import Base, get_db
from backend.app.main import app
from backend.app.models.models import UploadedSchema

# Use a separate SQLite database for testing purposes
TEST_DATABASE_URL = "sqlite:///./test_app.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Create test database schemas
    Base.metadata.create_all(bind=engine)
    yield
    # Drop schemas after tests finish
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_app.db"):
        try:
            os.remove("./test_app.db")
        except Exception:
            pass

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def mock_schema(db_session):
    """Inserts a mock schema representation into the test database."""
    parsed = {
        "customers": [
            {"name": "id", "type": "INTEGER PRIMARY KEY"},
            {"name": "name", "type": "VARCHAR(100)"}
        ],
        "orders": [
            {"name": "id", "type": "INTEGER PRIMARY KEY"},
            {"name": "customer_id", "type": "INTEGER"},
            {"name": "total", "type": "DECIMAL(10,2)"}
        ]
    }
    
    # We create a temporary DB file representing the schema
    db_path = os.path.abspath("./test_mock_schema.db")
    
    # Create schema record
    schema = UploadedSchema(
        name="Test Retail Database",
        schema_type="json",
        raw_content="{}",
        parsed_tables=parsed,
        db_path=db_path
    )
    db_session.add(schema)
    db_session.commit()
    db_session.refresh(schema)
    
    # Initialize the actual tables in that db
    import sqlite3
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY, name VARCHAR(100))")
    c.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, total DECIMAL(10,2))")
    # Insert mock records
    c.execute("INSERT INTO customers VALUES (1, 'Alice')")
    c.execute("INSERT INTO customers VALUES (2, 'Bob')")
    c.execute("INSERT INTO orders VALUES (10, 1, 150.00)")
    c.execute("INSERT INTO orders VALUES (20, 2, 80.00)")
    conn.commit()
    conn.close()
    
    yield schema
    
    # Cleanup schema database file after test
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.database.session import engine, Base
from backend.app.api.endpoints import router as api_router
from backend.app.schemas.schemas import ApiResponse

# Configure Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize database schemas
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
    
    # Auto-seed a default sandbox database schema on startup if none exist
    import sys
    if "pytest" not in sys.modules:
        from backend.app.database.session import get_db_context
        from backend.app.repositories.query_repository import SchemaRepository
        from backend.app.services.schema_service import SchemaService

        with get_db_context() as db:
            existing_schemas = SchemaRepository.list_all(db)
            if not existing_schemas:
                logger.info("No database schemas found. Seeding default 'Retail Analytics' sandbox...")
                default_ddl = """
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    country VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL
);

CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    department VARCHAR(50) NOT NULL,
    salary DECIMAL(10, 2) NOT NULL,
    hire_date DATE NOT NULL
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INT NOT NULL,
    employee_id INT,
    order_date TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    discount DECIMAL(5, 2) DEFAULT 0.00,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);
                """.strip()
                try:
                    SchemaService.upload_schema(
                        db=db,
                        name="Retail Analytics",
                        schema_type="sql",
                        raw_content=default_ddl
                    )
                    logger.info("Default 'Retail Analytics' sandbox seeded successfully.")
                except Exception as e:
                    logger.error(f"Failed to seed default database schema: {str(e)}")
except Exception as e:
    logger.critical(f"Failed to initialize database tables: {str(e)}")

# Initialize FastAPI App
app = FastAPI(
    title="AI-Powered SQL Query Builder & Data Explorer API",
    description="Backend service for generating, validating, and executing safe SQL queries.",
    version="1.0.0"
)

# CORS Configuration for Frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production: e.g. ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(api_router, prefix="/api")

# Global Exception Handler to maintain consistent JSON response formats
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception caught on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiResponse(
            success=False,
            message="An unexpected server error occurred.",
            errors=[str(exc)]
        ).model_dump()
    )

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "sql-builder-backend"}

import pytest
from backend.app.schemas.schemas import ApiResponse

def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_schema_upload_sql(client):
    # Upload SQL DDL schema
    payload = {
        "name": "ECommerce Sales",
        "schema_type": "sql",
        "raw_content": (
            "CREATE TABLE customers (id INT PRIMARY KEY, name TEXT);\n"
            "CREATE TABLE orders (id INT PRIMARY KEY, amount REAL);"
        )
    }
    
    response = client.post("/api/schemas", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "ECommerce Sales"
    assert "customers" in data["data"]["parsed_tables"]
    assert "orders" in data["data"]["parsed_tables"]


def test_schema_upload_json(client):
    # Upload JSON schema
    payload = {
        "name": "Inventory DB",
        "schema_type": "json",
        "raw_content": (
            '{\n  "tables": {\n    "products": {\n      "id": "INTEGER PRIMARY KEY",\n      "title": "TEXT",\n      "price": "REAL"\n    }\n  }\n}'
        )
    }
    
    response = client.post("/api/schemas", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "products" in data["data"]["parsed_tables"]


def test_generate_sql_endpoint(client, mock_schema):
    # Tests calling the LLM SQL generator
    payload = {
        "schema_id": mock_schema.id,
        "prompt": "Show all customers in the database"
    }
    
    response = client.post("/api/queries/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "generated_sql" in data["data"]
    assert "query_history_id" in data["data"]
    assert "SELECT" in data["data"]["generated_sql"]


def test_validate_sql_endpoint(client):
    # Valid query
    response = client.post("/api/queries/validate", json={"sql": "SELECT * FROM customers"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["valid"] is True

    # Invalid query
    response = client.post("/api/queries/validate", json={"sql": "UPDATE customers SET name = 'X'"})
    assert response.status_code == 200
    assert response.json()["success"] is False
    assert response.json()["data"]["valid"] is False


def test_execute_sql_endpoint(client, mock_schema):
    # 1. Execute a safe query returning results
    payload = {
        "schema_id": mock_schema.id,
        "sql": "SELECT * FROM customers ORDER BY id ASC",
        "limit": 10
    }
    response = client.post("/api/queries/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["columns"] == ["id", "name"]
    assert len(data["data"]["rows"]) == 2
    assert data["data"]["rows"][0]["name"] == "Alice"
    assert data["data"]["rows"][1]["name"] == "Bob"

    # 2. Execute an unsafe query (blocked by authorizer or validator)
    payload_unsafe = {
        "schema_id": mock_schema.id,
        "sql": "DROP TABLE orders;"
    }
    response = client.post("/api/queries/execute", json=payload_unsafe)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert len(data["errors"]) > 0


def test_history_and_favorites(client, mock_schema):
    # Generate query to create history log
    client.post(
        "/api/queries/generate",
        json={"schema_id": mock_schema.id, "prompt": "Show orders total"}
    )
    
    # List history
    history_res = client.get(f"/api/queries/history/{mock_schema.id}")
    assert history_res.status_code == 200
    history_data = history_res.json()["data"]
    assert len(history_data) >= 1
    
    history_item_id = history_data[0]["id"]
    assert history_data[0]["is_favorite"] is False

    # Toggle favorite
    fav_res = client.post("/api/queries/favorites", json={"query_history_id": history_item_id})
    assert fav_res.status_code == 200
    assert fav_res.json()["data"]["is_favorite"] is True

    # Check history contains favorite flag now
    history_res2 = client.get(f"/api/queries/history/{mock_schema.id}")
    assert history_res2.json()["data"][0]["is_favorite"] is True


def test_save_query_endpoints(client, mock_schema):
    payload = {
        "schema_id": mock_schema.id,
        "name": "Customer Orders Report",
        "prompt": "Find all customer orders",
        "sql_query": "SELECT * FROM orders JOIN customers ON orders.customer_id = customers.id"
    }
    
    # Save
    save_res = client.post("/api/queries/saved", json=payload)
    assert save_res.status_code == 200
    assert save_res.json()["success"] is True
    
    # List
    list_res = client.get(f"/api/queries/saved/{mock_schema.id}")
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) == 1
    assert list_res.json()["data"][0]["name"] == "Customer Orders Report"

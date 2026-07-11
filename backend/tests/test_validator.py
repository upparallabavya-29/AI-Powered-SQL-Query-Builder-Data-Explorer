import pytest
from backend.app.security.validator import validate_sql_query

def test_valid_select_queries():
    # Simple query
    is_valid, clean_sql, errors = validate_sql_query("SELECT * FROM customers")
    assert is_valid
    assert not errors
    assert "SELECT" in clean_sql

    # Query with filter and order
    is_valid, _, errors = validate_sql_query(
        "SELECT name, email FROM customers WHERE country = 'USA' ORDER BY created_at DESC"
    )
    assert is_valid
    assert not errors

    # Join query
    is_valid, _, errors = validate_sql_query(
        "SELECT c.name, o.total_amount FROM customers c JOIN orders o ON c.id = o.customer_id"
    )
    assert is_valid
    assert not errors

    # Aggregations
    is_valid, _, errors = validate_sql_query(
        "SELECT category, AVG(price), COUNT(*) FROM products GROUP BY category HAVING COUNT(*) > 5"
    )
    assert is_valid
    assert not errors


def test_rejected_write_operations():
    write_queries = [
        "INSERT INTO customers (name, email) VALUES ('Malicious', 'm@m.com')",
        "UPDATE customers SET name = 'Hacked' WHERE id = 1",
        "DELETE FROM orders WHERE id = 1",
        "DROP TABLE customers",
        "ALTER TABLE customers ADD COLUMN balance DECIMAL",
        "TRUNCATE TABLE sales",
        "CREATE TABLE backdoor (id INT)",
        "MERGE INTO customers USING temp ON (id) WHEN MATCHED THEN UPDATE SET name = 'x'"
    ]
    
    for query in write_queries:
        is_valid, _, errors = validate_sql_query(query)
        assert not is_valid, f"Query '{query}' should have been rejected."
        assert len(errors) > 0
        assert any("Forbidden" in err or "Query type" in err for err in errors)


def test_rejected_multi_statements():
    multi_queries = [
        "SELECT * FROM customers; DROP TABLE orders;",
        "SELECT * FROM customers; SELECT * FROM orders;",
        "SELECT * FROM customers;\nDELETE FROM products;"
    ]
    
    for query in multi_queries:
        is_valid, _, errors = validate_sql_query(query)
        assert not is_valid, f"Multi-statement query '{query}' should have been rejected."
        assert any("Multiple statements" in err for err in errors)


def test_comment_removal_and_bypass():
    # Comments inside queries should be cleanly removed during validation
    comment_queries = [
        "SELECT * FROM customers -- Fetching all customers",
        "SELECT name /* comment here */ FROM customers",
        "SELECT * FROM customers; -- SELECT * FROM orders"
    ]
    
    for query in comment_queries:
        is_valid, clean_sql, errors = validate_sql_query(query)
        assert is_valid
        assert "--" not in clean_sql
        assert "/*" not in clean_sql
        assert not errors


def test_invalid_syntax():
    invalid_queries = [
        "SELECT * FROM",
        "INSERT customers",
        "SELECT * FORM customers"
    ]
    
    for query in invalid_queries:
        is_valid, _, errors = validate_sql_query(query)
        assert not is_valid
        assert any("syntax error" in err or "pre-validation failed" in err or "Query type" in err for err in errors)

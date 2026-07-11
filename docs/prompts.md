# LLM Prompt Engineering & Mappings

This document details the system instructions, prompt templates, and dialect management rules used by the LLM client to translate natural language into valid database queries.

## 1. Prompt Structure & Context Injection

The LLM is prompted using a **system context** containing the available schema definition. This ensures that the generated SQL is accurate and avoids column hallucinations.

### Prompt Template

```text
System Instruction:
You are a Senior Data Engineer. Your task is to write a single, clean, valid SQLite SQL query to answer the user's question based ONLY on the database schema provided.

Strict Constraints:
1. ONLY use the tables and columns defined in the schema. DO NOT hallucinate tables or columns.
2. Return ONLY the raw SQL query. Do NOT wrap the code in markdown blocks (e.g. do not write ```sql ... ```).
3. Do NOT include any explanations, introduction, or text outside of the SQL statement.
4. Only write SELECT statements. Multiple statements separated by semicolons are strictly forbidden.
5. Ensure SQL joins use correct matching foreign keys.

Database Schema:
Table: customers
Columns: id (INTEGER PRIMARY KEY), name (VARCHAR(100)), email (VARCHAR(100) UNIQUE), country (VARCHAR(50)), created_at (TIMESTAMP)

Table: orders
Columns: id (INTEGER PRIMARY KEY), customer_id (INTEGER), order_date (TIMESTAMP), total_amount (DECIMAL(10,2))

Question:
Show total spending for customers in USA.

SQLite SQL Query:
```

### Prompt Parameters
- **Temperature**: `0.0` (Ensures deterministic, high-fidelity queries).
- **Max Tokens**: `500` (Restricts long-winded answers or conversational drift).
- **Model**: `gpt-4o-mini` (Fast, cost-effective, and highly capable in code-generation tasks).

---

## 2. Dialect Controls & Cleaning

To guarantee the query executes cleanly in the Sandbox environment, we request SQLite format:
1. **No Markdown Wrapper**: Prompt instructs the LLM to output only raw SQL. If the LLM still returns a markdown block (e.g. ` ```sql ... ``` `), the backend client has regex cleansers to strip it.
2. **Deterministic Dialect**: By specifying SQLite in system instructions, the LLM avoids Postgres-specific keywords (like `ILIKE`, `LIMIT ALL`, or `NOW()`) and uses SQLite compatible equivalents (like `LIKE`, `LIMIT`, or `datetime('now')`).

---

## 3. Local Mock Heuristics Fallback

If `OPENAI_API_KEY` is not provided in environment variables, the system executes an offline mock SQL builder:
- **Heuristic Pattern Matching**:
  - Scans prompt keywords.
  - If "count" is detected: `SELECT COUNT(*) AS total_count FROM table;`
  - If "revenue", "salary", or "total" is matched: `SELECT SUM(column) AS total_value FROM table;`
  - If multiple tables are detected in the prompt, it automatically searches for foreign key mappings (columns ending with `_id`) and constructs a `JOIN` statement.
  - Otherwise, defaults to a `SELECT * FROM table LIMIT 50;` query.
- **Benefit**: Ensures the developer workspace or tests run successfully without requiring internet access or billing configurations.

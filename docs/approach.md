# Implementation Approach

This document outlines the engineering approaches, security strategies, and execution mechanisms deployed to build the **AI-Powered SQL Query Builder & Data Explorer**.

## 1. Sandbox Isolation Strategy

Executing user-submitted SQL is inherently risky. To prevent cross-contamination or unauthorized access:
- **Dynamic Database Provisioning**: Every uploaded schema (JSON or SQL DDL) creates a separate, dedicated SQLite database file named `schema_{uuid}.db` inside the `backend/db_files` directory.
- **Independent Schema Context**: Tables and rows are confined entirely inside this dynamic database. There are no linkages between different schemas or with the main app database (`sql_builder.db`), isolating customer sandboxes completely.
- **Smart Data Seeding**: If the uploaded schema matches a standard analytical layout, a rich dataset is seeded; otherwise, column-type scanners generate matching mock datasets so the workspace is immediately queryable.

## 2. Dual-Layer SQL Security

To guarantee that the backend NEVER runs modifying SQL, we implement a defensive-in-depth model:

### Layer 1: AST (Abstract Syntax Tree) Verification
Before submitting queries to the database driver, they are parsed using `sqlglot`:
1. **Comment Stripping**: The query is transpiled to strip comments, defeating SQL injection bypasses that hide commands in comments.
2. **Single Statement Check**: Any semicolon-separated queries or multiple parsed AST nodes are rejected outright.
3. **AST Walking**: The parsed tree is searched recursively. If any node inherits from forbidden keywords (e.g., `exp.Insert`, `exp.Update`, `exp.Delete`, `exp.Drop`, `exp.AlterTable`, `exp.Merge`, `exp.Command`), execution is blocked.

### Layer 2: Driver-Level Callback Authorizers
Even if a query bypasses AST checks, the SQLite driver enforces read-only states:
- A connection callback (`connection.set_authorizer`) is registered.
- Any action that attempts writing, schema alterations, or database attachment (`SQLITE_INSERT`, `SQLITE_UPDATE`, `SQLITE_DELETE`, `SQLITE_CREATE_TABLE`, `SQLITE_ATTACH`, etc.) returns `SQLITE_DENY` and raises a database exception.

## 3. Query Timeouts and Cancellation

To prevent infinite loops or heavy resource utilization (e.g., joining columns without indexes):
- **SQLite Progress Handler**: The connection registers `conn.set_progress_handler`.
- **Instruction-Based Callback**: Every 50 virtual machine operations, the database driver invokes a Python check:
  ```python
  def timeout_check():
      if time.time() - start_time > 10.0:
          return 1  # Returns non-zero to immediately abort execution
      return 0
  ```
- **Abort & Interrupt**: If execution exceeds 10 seconds, the progress handler aborts the transaction, cancels execution, and raises an `sqlite3.DatabaseError` that is translated to a user-friendly error message.
- **Pagination Capping**: The query is wrapped inside a subquery `SELECT * FROM ( {clean_sql} ) LIMIT 101 OFFSET {offset}`. This ensures that no more than 100 records are fetched per page, protecting memory footprints.

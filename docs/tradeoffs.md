# Architecture Tradeoffs

This document outlines the key technical tradeoffs considered during the design and implementation of the **AI-Powered SQL Query Builder & Data Explorer**.

---

## 1. Database Sandbox: SQLite-per-Schema vs Central PostgreSQL

### SQLite-per-Schema (Chosen)
- **Pros**:
  - **Perfect Isolation**: Every database schema has its own file, completely avoiding cross-schema data leaks.
  - **Zero Maintenance Overhead**: Dynamically creating a new SQLite file is extremely lightweight, requires no database user management, and consumes no idle connections.
  - **Easy Cleanups**: Deleting a schema is as simple as deleting a file (`os.remove`).
- **Cons**:
  - Lacks advanced PostgreSQL features (like Window functions or schemas), though SQLite covers 95%+ of analytical SQL commands.

### Central PostgreSQL (Alternative)
- **Pros**:
  - Supports full PostgreSQL-specific SQL dialect, JSON operators, and concurrent scaling.
- **Cons**:
  - Requires managing Postgres users, schemas, or prefixing tables to prevent collision, which is complex and error-prone.
  - Resource-intensive for lightweight user test beds.

*Decision*: We defaulted sandbox environments to SQLite for isolation and lightweight provisioning, while allowing the core application storage to connect to PostgreSQL if the `DATABASE_URL` is updated.

---

## 2. SQL Parser: `sqlglot` vs `sqlparse`

### `sqlglot` (Chosen)
- **Pros**:
  - **AST Parsing**: Parses SQL into a structural Abstract Syntax Tree (AST), enabling us to check expression nodes reliably (e.g. distinguishing a CTE from a CREATE TABLE).
  - **Comment Elimination**: Strips comments during AST transpilation reliably.
  - **Dialect Transpilation**: Easily converts or validates SQL queries against SQLite, Postgres, DuckDB, etc.
- **Cons**:
  - Slightly larger library footprint.

### `sqlparse` (Alternative)
- **Pros**:
  - Extremely lightweight, token-based parser.
- **Cons**:
  - Standard token-based parsing makes it difficult to detect nested write expressions (like a subquery or a CTE) without complex recursive parsing logic.
  - Prone to SQL Injection bypasses when tokens are manipulated.

*Decision*: Selected `sqlglot` to implement a secure, production-grade AST validator.

---

## 3. SQL Timeout: progress_handler vs threading/signals

### Progress Handler (Chosen)
- **Pros**:
  - **Windows & Unix Compatible**: Multi-threading or signals (`signal.alarm`) are notoriously unreliable or unavailable on Windows platforms. The SQLite progress handler is cross-platform.
  - **Zero OS Overhead**: Works entirely inside the SQLite virtual machine execution loop, preventing OS-level context switching.
- **Cons**:
  - Requires tuning instructions frequency (e.g. checking every 50 instructions).

*Decision*: Adopted connection-level `progress_handler` timeout callbacks for reliability and OS cross-compatibility.

---

## 4. UI State: Zustand + Axios vs React Query Cache Only

### Zustand + Axios (Chosen)
- **Pros**:
  - **Centralized Editing State**: Managing the Monaco editor text buffer, validation errors state, and results grid pagination variables in Zustand is cleaner than storing them in React Query's cache.
  - **Unified Operations**: Zustand coordinates generating, validating, and executing actions in a single file (`useAppStore.ts`).
- **Cons**:
  - Does not provide automatic cache validation or query de-duplication like React Query.

*Decision*: Managed transient editing and active results states in Zustand, and supplemented it with React Query client caching for static/stable resources if necessary.

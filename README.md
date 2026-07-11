# Athena: AI-Powered SQL Query Builder & Data Explorer

Athena is a modern web application designed for non-technical users to explore database sandboxes using natural language. It generates secure SQLite-compliant SQL queries using LLMs, validates the queries against AST rules, and executes read-only SELECT queries with connection-level guards.

---

## Technical Stack

* **Backend**: Python FastAPI, SQLAlchemy, SQLite (default, with PG support), Pydantic, sqlglot, OpenAI SDK.
* **Frontend**: React, TypeScript, Vite, Material UI (Dark Theme), Zustand state store, Monaco SQL Editor, TanStack Table.
* **Orchestration**: Docker, Docker Compose.
* **Tests**: Pytest (mock schema databases, AST security, and API endpoints validation).

---

## Features

1. **Schema Uploads**: Upload standard SQL DDL files (e.g. `CREATE TABLE`) or JSON files outlining tables and columns.
2. **Dynamic Database Sandboxing**: Creates an isolated SQLite database file per schema, completely eliminating database cross-talk.
3. **Analytics-Friendly Mock Seeding**: Automatically detects schema layouts; if matching our pre-defined sales schemas, it populates a rich sample dataset, otherwise it generates type-matching mock data.
4. **Natural Language Translation**: Generates SQL SELECT statements on the fly. Falls back to a local heuristic query generator if offline or no LLM key is configured.
5. **AST Security Validator**: Rejects multiple statements (semicolon chains), strips comments, and walks AST nodes to block any writing or schema modifications.
6. **Connection-level Authorizer Callback**: SQLite connection restrictions block `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`, `ATTACH`, and `DETACH` operations directly in the database driver.
7. **Execution Time Limits**: Terminate queries running longer than 10 seconds via SQLite progress handler vm interruption.
8. **Results Explorer**: Paginated data grid with column sorting, resizing, metadata metrics, and CSV exports.
9. **History & Bookmarks**: Save favorite SQL queries, explore history log lists, clear histories, or re-run queries with a single click.

---

## Quick Start (Docker Compose)

The easiest way to run the entire stack is using Docker Compose:

1. Clone or copy the workspace files.
2. Create a `.env` file in the root based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Provide your `OPENAI_API_KEY` (or leave blank to use the offline mock generator).
3. Start the containers:
   ```bash
   docker-compose up --build
   ```
4. Access the applications:
   * **Frontend**: `http://localhost:3000`
   * **Backend API Docs**: `http://localhost:8000/docs`

---

## Local Development (Manual Run)

If you prefer to run services individually:

### 1. Backend Setup
1. Move to the backend folder:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Unix:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### 2. Frontend Setup
1. Move to the frontend folder:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
4. Open the application in your browser at the displayed URL (usually `http://localhost:5173`).

---

## Running the Test Suite

We have written detailed unit and integration tests covering SQL AST validators, SQLite isolation authorizers, and REST API controllers.

To run the backend test suite:
1. Ensure the backend virtual environment is active.
2. From the project root, run:
   ```bash
   python -m pytest backend/tests -v
   ```

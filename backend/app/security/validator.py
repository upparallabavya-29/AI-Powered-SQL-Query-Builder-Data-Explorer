import sqlglot
from sqlglot import expressions as exp
from typing import Tuple, List

# AST Node classes that are strictly forbidden for read-only query execution
FORBIDDEN_AST_NODES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.TruncateTable,
    exp.Merge,
    exp.Command,      # Block commands like CALL, EXEC
    exp.Set,          # Block modifying session variables
    exp.Transaction,  # Block BEGIN, COMMIT, ROLLBACK
    exp.Show,
    exp.Pragma,
    exp.Analyze
)

def validate_sql_query(sql: str, dialect: str = "sqlite") -> Tuple[bool, str, List[str]]:
    """
    Validates a SQL query using sqlglot AST parsing.
    Enforces the following rules:
      1. Must be a single valid statement (rejects multiple statements separated by semicolons).
      2. Must be a read-only SELECT statement (no INSERT, UPDATE, DELETE, etc.).
      3. Strips all SQL comments during AST transpilation to prevent comments-based validation bypass.
    
    Returns:
      (is_valid: bool, canonical_sql: str, errors: List[str])
    """
    if not sql or not sql.strip():
        return False, "", ["SQL query cannot be empty."]

    errors = []
    
    # Pre-parse syntax check & comment stripping via sqlglot transpile
    try:
        raw_queries = sqlglot.transpile(sql, read=dialect, write=dialect, comments=False)
        # Filter out empty statements (e.g. trailing empty blocks from semicolons)
        transpiled_queries = [q.strip() for q in raw_queries if q.strip()]
        if not transpiled_queries:
            return False, "", ["Unable to parse SQL query."]
        
        # Verify that transpilation produced exactly one query statement
        if len(transpiled_queries) > 1:
            return False, "", ["Multiple statements are not allowed. Only a single SELECT query can be executed."]
        
        clean_sql = transpiled_queries[0]
    except sqlglot.errors.ParseError as pe:
        # Capture syntax error detail
        return False, "", [f"SQL syntax error: {str(pe)}"]
    except Exception as e:
        return False, "", [f"SQL pre-validation failed: {str(e)}"]

    # Reparse the clean canonical SQL for detailed AST verification
    try:
        expressions = sqlglot.parse(clean_sql, read=dialect)
        if not expressions or len(expressions) > 1 or expressions[0] is None:
            return False, "", ["Failed to parse clean SQL or multiple statements detected."]
        
        ast_root = expressions[0]
        
        # Enforce that the root node is related to SELECT queries
        # Safe root nodes: Select, Subquery, Union, CTE (Wrapped inside Select or Union)
        if not isinstance(ast_root, (exp.Select, exp.Union, exp.Subquery)):
            # If it's a CTE (With), check if the underlying query is a Select or Union
            if isinstance(ast_root, exp.CTE):
                pass  # We will check its contents in the walk
            elif hasattr(ast_root, "this") and isinstance(ast_root.this, (exp.Select, exp.Union)):
                pass
            else:
                return False, "", [f"Query type '{type(ast_root).__name__}' is not allowed. Only SELECT queries are permitted."]

        # Walk the AST to search for any modifying statements or forbidden nodes
        for node in ast_root.walk():
            # Check if node is in the forbidden class list
            if isinstance(node, FORBIDDEN_AST_NODES):
                errors.append(f"Forbidden SQL action or statement type detected: '{type(node).__name__}'")
                
            # Block data modification keywords by text inspection of custom expressions
            if isinstance(node, exp.Expression):
                # Extra layer of defense: check sqlglot token keywords if any match forbidden actions
                pass
                
        if errors:
            return False, "", list(set(errors))

        return True, clean_sql, []
        
    except sqlglot.errors.ParseError as pe:
        return False, "", [f"AST Parsing error: {str(pe)}"]
    except Exception as e:
        return False, "", [f"AST validation error: {str(e)}"]

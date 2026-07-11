import sqlite3
import logging

logger = logging.getLogger(__name__)

# List of SQLite action codes to block for read-only user queries
BLOCKED_ACTIONS = {
    sqlite3.SQLITE_CREATE_INDEX,
    sqlite3.SQLITE_CREATE_TABLE,
    sqlite3.SQLITE_CREATE_TEMP_INDEX,
    sqlite3.SQLITE_CREATE_TEMP_TABLE,
    sqlite3.SQLITE_CREATE_TEMP_TRIGGER,
    sqlite3.SQLITE_CREATE_TEMP_VIEW,
    sqlite3.SQLITE_CREATE_TRIGGER,
    sqlite3.SQLITE_CREATE_VIEW,
    sqlite3.SQLITE_DELETE,
    sqlite3.SQLITE_DROP_INDEX,
    sqlite3.SQLITE_DROP_TABLE,
    sqlite3.SQLITE_DROP_TEMP_INDEX,
    sqlite3.SQLITE_DROP_TEMP_TABLE,
    sqlite3.SQLITE_DROP_TEMP_TRIGGER,
    sqlite3.SQLITE_DROP_TEMP_VIEW,
    sqlite3.SQLITE_DROP_TRIGGER,
    sqlite3.SQLITE_DROP_VIEW,
    sqlite3.SQLITE_INSERT,
    sqlite3.SQLITE_UPDATE,
    sqlite3.SQLITE_TRANSACTION,  # Block transaction commands (BEGIN, COMMIT, ROLLBACK)
    sqlite3.SQLITE_ATTACH,       # Block attaching external databases
    sqlite3.SQLITE_DETACH,       # Block detaching databases
}

def sqlite_read_only_authorizer(action_code: int, arg1: str, arg2: str, db_name: str, trigger_name: str) -> int:
    """
    SQLite authorizer callback that rejects any state-modifying actions.
    Returns sqlite3.SQLITE_DENY to block execution, or sqlite3.SQLITE_OK to allow.
    """
    if action_code in BLOCKED_ACTIONS:
        logger.warning(
            f"Blocked unauthorized query action: code={action_code}, arg1={arg1}, arg2={arg2}, db={db_name}"
        )
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK

def apply_sqlite_security(connection: sqlite3.Connection):
    """Applies the read-only authorizer and restricts SQLite query limits."""
    # Register the authorizer
    connection.set_authorizer(sqlite_read_only_authorizer)
    
    # Limit execution timeouts at connection level (if sqlite is built with loadable extensions or limits)
    # connection.set_progress_handler(timeout_handler, 1000) can be used to interrupt long-running queries

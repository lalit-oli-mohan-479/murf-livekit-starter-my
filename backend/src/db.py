import sqlite3
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger("agent.db")

# Place database file in backend src directory
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.db")

def init_db():
    logger.info(f"Initializing database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS callers (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT,
            last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outbound_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT,
            customer_name TEXT,
            scheme_name TEXT,
            outcome TEXT,
            duration_seconds REAL,
            retry_recommended BOOLEAN,
            called_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

import re

def lookup_caller(user_id: str) -> dict | None:
    logger.info(f"Looking up caller: {user_id}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, name, language_preference, facts, last_interaction FROM callers WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            try:
                facts = json.loads(row[3]) if row[3] else {}
            except Exception as e:
                logger.error(f"Error parsing facts JSON: {e}")
                facts = {}
                
            formatted_time = row[4]
            if row[4]:
                try:
                    dt = datetime.fromisoformat(row[4])
                    formatted_time = dt.strftime("%B %d at %I:%M %p")
                except Exception:
                    pass
                    
            return {
                "user_id": row[0],
                "name": row[1],
                "language_preference": row[2],
                "facts": facts,
                "last_interaction": formatted_time
            }
    except Exception as e:
        logger.error(f"Error checking caller {user_id}: {e}")
    return None

def save_caller(user_id: str, name: str, language_preference: str, facts: dict) -> None:
    logger.info(f"Saving caller info for {user_id}: name={name}, lang={language_preference}")
    try:
        # Strict filter: strip any sequences of 4+ digits from facts to guard account/ID numbers
        clean_facts = {}
        for k, v in facts.items():
            if isinstance(v, str):
                clean_facts[k] = re.sub(r'\b\d{4,}\b', '[REDACTED]', v)
            elif isinstance(v, list):
                clean_facts[k] = [re.sub(r'\b\d{4,}\b', '[REDACTED]', item) if isinstance(item, str) else item for item in v]
            else:
                clean_facts[k] = v

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        facts_str = json.dumps(clean_facts)
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO callers (user_id, name, language_preference, facts, last_interaction)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                language_preference = excluded.language_preference,
                facts = excluded.facts,
                last_interaction = excluded.last_interaction
        """, (user_id, name, language_preference, facts_str, now))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error saving caller {user_id}: {e}")

def delete_caller(user_id: str) -> bool:
    logger.info(f"Deleting caller profile: {user_id}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM callers WHERE user_id = ?", (user_id,))
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_affected > 0
    except Exception as e:
        logger.error(f"Error deleting caller {user_id}: {e}")
        return False

def log_outbound_call(phone_number: str, customer_name: str, scheme_name: str, outcome: str, duration_seconds: float, retry_recommended: bool) -> None:
    """Save outbound call logs (who was called, duration, outcome, retry) into SQLite."""
    logger.info(f"Logging outbound call in SQLite: {customer_name} ({phone_number}) | {outcome} | {duration_seconds:.1f}s")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO outbound_calls (phone_number, customer_name, scheme_name, outcome, duration_seconds, retry_recommended, called_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (phone_number, customer_name, scheme_name, outcome, round(duration_seconds, 1), retry_recommended, now))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error logging outbound call to SQLite: {e}")


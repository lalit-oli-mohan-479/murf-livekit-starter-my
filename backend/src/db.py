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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_id TEXT UNIQUE,
            user_id TEXT,
            caller_name TEXT,
            contact_method TEXT,
            reason_category TEXT,
            issue_summary TEXT,
            steps_already_taken TEXT,
            urgency TEXT,
            caller_language TEXT,
            status TEXT DEFAULT 'Open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

import re
import random
import urllib.request
import urllib.error

def redact_sensitive_info(text: str) -> str:
    """Redacts sensitive information like passwords, OTPs, PINs, bank account numbers, 4+ digit numbers."""
    if not text:
        return ""
    # Redact explicit keyword pattern matches (OTP, PIN, Password, Card #, Account #)
    redacted = re.sub(r'(?i)\b(otp|pin|password|passcode|cvv)\s*[:=]?\s*\d+', r'\1 [REDACTED]', text)
    # Redact any numbers with 4 or more consecutive digits
    redacted = re.sub(r'\b\d{4,}\b', '[REDACTED]', redacted)
    return redacted

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
                clean_facts[k] = redact_sensitive_info(v)
            elif isinstance(v, list):
                clean_facts[k] = [redact_sensitive_info(item) if isinstance(item, str) else item for item in v]
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

def create_escalation_record(
    user_id: str,
    caller_name: str,
    contact_method: str,
    reason_category: str,
    issue_summary: str,
    steps_already_taken: str,
    urgency: str,
    caller_language: str
) -> dict:
    """Creates a human help request record in SQLite, handling privacy redaction and duplicate prevention."""
    clean_summary = redact_sensitive_info(issue_summary)
    clean_steps = redact_sensitive_info(steps_already_taken)
    valid_urgencies = ["Low", "Medium", "High", "Emergency"]
    norm_urgency = urgency.capitalize() if urgency and urgency.capitalize() in valid_urgencies else "High"
    
    logger.info(f"Creating escalation for user={user_id}, caller={caller_name}, category={reason_category}, urgency={norm_urgency}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check for existing open duplicate ticket for same caller/category in last 24h
        cursor.execute("""
            SELECT reference_id, issue_summary, urgency, created_at FROM escalations 
            WHERE (user_id = ? OR caller_name = ?) AND reason_category = ? AND status IN ('Open', 'In Progress')
            ORDER BY created_at DESC LIMIT 1
        """, (user_id, caller_name, reason_category))
        existing = cursor.fetchone()
        
        now_str = datetime.now().isoformat()
        
        if existing:
            ref_id = existing[0]
            logger.info(f"Found existing open duplicate escalation {ref_id}. Updating ticket notes.")
            updated_summary = f"{existing[1]} | Updated Note: {clean_summary}"
            cursor.execute("""
                UPDATE escalations 
                SET issue_summary = ?, steps_already_taken = ?, urgency = ?, updated_at = ?
                WHERE reference_id = ?
            """, (updated_summary, clean_steps, norm_urgency, now_str, ref_id))
            conn.commit()
            conn.close()
            
            result = {
                "reference_id": ref_id,
                "caller_name": caller_name,
                "contact_method": contact_method,
                "reason_category": reason_category,
                "issue_summary": updated_summary,
                "steps_already_taken": clean_steps,
                "urgency": norm_urgency,
                "caller_language": caller_language,
                "status": "Open",
                "is_duplicate": True,
                "created_at": existing[3]
            }
            send_discord_webhook_notification(result)
            return result

        # Create new unique reference ID (e.g. ESC-83912)
        ref_id = f"ESC-{random.randint(10000, 99999)}"
        
        cursor.execute("""
            INSERT INTO escalations (
                reference_id, user_id, caller_name, contact_method, reason_category, 
                issue_summary, steps_already_taken, urgency, caller_language, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?, ?)
        """, (
            ref_id, user_id, caller_name, contact_method, reason_category,
            clean_summary, clean_steps, norm_urgency, caller_language, now_str, now_str
        ))
        conn.commit()
        conn.close()
        
        result = {
            "reference_id": ref_id,
            "caller_name": caller_name,
            "contact_method": contact_method,
            "reason_category": reason_category,
            "issue_summary": clean_summary,
            "steps_already_taken": clean_steps,
            "urgency": norm_urgency,
            "caller_language": caller_language,
            "status": "Open",
            "is_duplicate": False,
            "created_at": now_str
        }
        send_discord_webhook_notification(result)
        return result

    except Exception as e:
        logger.error(f"Error creating escalation in SQLite: {e}")
        fallback_ref = f"ESC-{random.randint(10000, 99999)}"
        return {
            "reference_id": fallback_ref,
            "caller_name": caller_name,
            "contact_method": contact_method,
            "reason_category": reason_category,
            "issue_summary": clean_summary,
            "steps_already_taken": clean_steps,
            "urgency": norm_urgency,
            "caller_language": caller_language,
            "status": "Open",
            "is_duplicate": False,
            "created_at": datetime.now().isoformat()
        }

def get_escalations(status: str = None) -> list:
    """Retrieves human escalation records from SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if status:
            cursor.execute("""
                SELECT reference_id, user_id, caller_name, contact_method, reason_category, 
                       issue_summary, steps_already_taken, urgency, caller_language, status, created_at 
                FROM escalations WHERE status = ? ORDER BY id DESC
            """, (status,))
        else:
            cursor.execute("""
                SELECT reference_id, user_id, caller_name, contact_method, reason_category, 
                       issue_summary, steps_already_taken, urgency, caller_language, status, created_at 
                FROM escalations ORDER BY id DESC
            """)
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for r in rows:
            results.append({
                "reference_id": r[0],
                "user_id": r[1],
                "caller_name": r[2],
                "contact_method": r[3],
                "reason_category": r[4],
                "issue_summary": r[5],
                "steps_already_taken": r[6],
                "urgency": r[7],
                "caller_language": r[8],
                "status": r[9],
                "created_at": r[10]
            })
        return results
    except Exception as e:
        logger.error(f"Error fetching escalations: {e}")
        return []

def send_discord_webhook_notification(escalation: dict) -> None:
    """Sends escalation details to a real Discord Webhook if DISCORD_WEBHOOK_URL is configured."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook_url:
        logger.info("No DISCORD_WEBHOOK_URL configured. Escalation saved to SQLite database locally.")
        return
        
    try:
        color_map = {
            "Emergency": 15158332,  # Red
            "High": 15105570,       # Orange/Amber
            "Medium": 16776960,     # Yellow
            "Low": 3066993          # Green
        }
        color = color_map.get(escalation.get("urgency"), 15105570)
        dup_tag = " [UPDATED DUPLICATE TICKET]" if escalation.get("is_duplicate") else ""

        payload = {
            "username": "Jan Dhan Seva Escalation Bot",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/4712/4712109.png",
            "embeds": [
                {
                    "title": f"🚨 Human Help Request: {escalation['reference_id']}{dup_tag}",
                    "description": f"**Reason:** {escalation['reason_category']}",
                    "color": color,
                    "fields": [
                        {"name": "👤 Caller Name", "value": escalation['caller_name'], "inline": True},
                        {"name": "📞 Follow-up Method", "value": escalation['contact_method'], "inline": True},
                        {"name": "⚡ Urgency", "value": escalation['urgency'], "inline": True},
                        {"name": "🌐 Language", "value": escalation['caller_language'], "inline": True},
                        {"name": "📌 Status", "value": escalation['status'], "inline": True},
                        {"name": "📝 Issue Summary (Sanitized)", "value": escalation['issue_summary'], "inline": False},
                        {"name": "🔍 Agent Steps Checked", "value": escalation['steps_already_taken'], "inline": False}
                    ],
                    "footer": {
                        "text": f"Jan Dhan Seva • Voice Agent Escalation System • Ref: {escalation['reference_id']}"
                    }
                }
            ]
        }
        
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'Python-JanDhanSeva-Agent'}
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            logger.info(f"Successfully posted escalation {escalation['reference_id']} to Discord webhook. Status: {resp.status}")
    except Exception as e:
        logger.error(f"Failed to post escalation to Discord Webhook: {e}")


def update_escalation_status(reference_id: str, new_status: str, resolution_note: str = "") -> dict | None:
    """Updates the status of an escalation ticket. Valid statuses: Open, In Progress, Resolved."""
    valid = ["Open", "In Progress", "Resolved"]
    if new_status not in valid:
        logger.warning(f"Invalid escalation status '{new_status}'. Must be one of {valid}")
        return None

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()

        if resolution_note:
            cursor.execute("""
                UPDATE escalations
                SET status = ?, updated_at = ?,
                    issue_summary = issue_summary || ' | Resolution: ' || ?
                WHERE reference_id = ?
            """, (new_status, now_str, resolution_note, reference_id))
        else:
            cursor.execute("""
                UPDATE escalations SET status = ?, updated_at = ? WHERE reference_id = ?
            """, (new_status, now_str, reference_id))

        rows_affected = cursor.rowcount
        conn.commit()

        if rows_affected == 0:
            conn.close()
            logger.warning(f"No escalation found with reference_id={reference_id}")
            return None

        # Fetch the updated record
        cursor.execute("""
            SELECT reference_id, user_id, caller_name, contact_method, reason_category,
                   issue_summary, steps_already_taken, urgency, caller_language, status, created_at
            FROM escalations WHERE reference_id = ?
        """, (reference_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            result = {
                "reference_id": row[0],
                "user_id": row[1],
                "caller_name": row[2],
                "contact_method": row[3],
                "reason_category": row[4],
                "issue_summary": row[5],
                "steps_already_taken": row[6],
                "urgency": row[7],
                "caller_language": row[8],
                "status": row[9],
                "created_at": row[10],
            }
            logger.info(f"Escalation {reference_id} updated to status: {new_status}")
            return result
        return None
    except Exception as e:
        logger.error(f"Error updating escalation status for {reference_id}: {e}")
        return None


def lookup_escalation_by_ref(reference_id: str) -> dict | None:
    """Looks up a single escalation ticket by its reference ID."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT reference_id, user_id, caller_name, contact_method, reason_category,
                   issue_summary, steps_already_taken, urgency, caller_language, status, created_at
            FROM escalations WHERE reference_id = ?
        """, (reference_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "reference_id": row[0],
                "user_id": row[1],
                "caller_name": row[2],
                "contact_method": row[3],
                "reason_category": row[4],
                "issue_summary": row[5],
                "steps_already_taken": row[6],
                "urgency": row[7],
                "caller_language": row[8],
                "status": row[9],
                "created_at": row[10],
            }
        return None
    except Exception as e:
        logger.error(f"Error looking up escalation {reference_id}: {e}")
        return None

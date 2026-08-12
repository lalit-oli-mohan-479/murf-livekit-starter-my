import sqlite3
import json
import os
import sys

# Reconfigure stdout to support Devanagari/UTF-8 printing on Windows command line
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.db")

def print_db():
    if not os.path.exists(DB_PATH):
        print(f"Database file does not exist at {DB_PATH} yet.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id, name, language_preference, facts, last_interaction FROM callers")
        rows = cursor.fetchall()
        if not rows:
            print("No callers saved yet.")
        else:
            print("\n" + "=" * 60)
            print("          SAVED CALLERS IN SQLITE DATABASE          ")
            print("=" * 60)
            for row in rows:
                print(f"User ID:          {row[0]}")
                print(f"Name:             {row[1]}")
                print(f"Language Pref:    {row[2]}")
                try:
                    facts = json.loads(row[3])
                    print(f"Facts:            {json.dumps(facts, ensure_ascii=False)}")
                except Exception:
                    print(f"Facts (raw):      {row[3]}")
                print(f"Last Interaction: {row[4]}")
                print("-" * 60)

        # Print Escalations
        try:
            cursor.execute("SELECT reference_id, caller_name, contact_method, reason_category, issue_summary, steps_already_taken, urgency, caller_language, status, created_at FROM escalations ORDER BY id DESC")
            esc_rows = cursor.fetchall()
            print("\n" + "=" * 60)
            print("       HUMAN HELP ESCALATIONS (HUMAN SUPPORT TICKETS)       ")
            print("=" * 60)
            if not esc_rows:
                print("No human help escalations created yet.")
            else:
                for esc in esc_rows:
                    print(f"Ref ID:         {esc[0]}")
                    print(f"Caller Name:    {esc[1]}")
                    print(f"Follow-up:      {esc[2]}")
                    print(f"Category:       {esc[3]}")
                    print(f"Urgency:        {esc[6]} | Status: {esc[8]}")
                    print(f"Language:       {esc[7]}")
                    print(f"Summary:        {esc[4]}")
                    print(f"Agent Steps:    {esc[5]}")
                    print(f"Created At:     {esc[9]}")
                    print("-" * 60)
        except Exception as err:
            print(f"No escalations table or error: {err}")

    except Exception as e:
        print(f"Error reading database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print_db()


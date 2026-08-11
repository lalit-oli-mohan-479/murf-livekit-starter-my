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
            print("Database is empty. No callers saved yet.")
            return
        
        print("\n" + "=" * 50)
        print("          SAVED CALLERS IN SQLITE DATABASE          ")
        print("=" * 50)
        for row in rows:
            print(f"User ID:          {row[0]}")
            print(f"Name:             {row[1]}")
            print(f"Language Pref:    {row[2]}")
            try:
                facts = json.loads(row[3])
                print(f"Facts:            {json.dumps(facts)}")
            except Exception:
                print(f"Facts (raw):      {row[3]}")
            print(f"Last Interaction: {row[4]}")
            print("-" * 50)
    except Exception as e:
        print(f"Error reading database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print_db()

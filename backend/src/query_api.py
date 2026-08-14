import argparse
import sys
import json
from pathlib import Path

# Enforce UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))

import db


def main():
    parser = argparse.ArgumentParser(description="Query escalations for API")
    parser.add_argument("--ref", default="", help="Reference ID to query")
    parser.add_argument("--status", default="", help="Status filter")
    args = parser.parse_args()

    db.init_db()

    ref_id = args.ref.strip().upper()
    status_val = args.status.strip()

    if ref_id:
        res = db.lookup_escalation_by_ref(ref_id)
        print(json.dumps(res if res else None, ensure_ascii=False))
    else:
        s_filter = status_val if status_val else None
        res = db.get_escalations(status=s_filter)
        print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()

import argparse
import sys
import json
import random
import time
from pathlib import Path

# Enforce UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))

import db

def main():
    parser = argparse.ArgumentParser(description="Query or log call analytics for API")
    parser.add_argument("--channel", default="All", help="Channel filter: Browser, SIP, All")
    parser.add_argument("--outcome", default="All", help="Outcome filter: success, failed, All")
    parser.add_argument("--log_test", action="store_true", help="Flag to insert a test call record")
    parser.add_argument("--test_type", default="success", help="Test type: success or failed")
    parser.add_argument("--test_channel", default="Browser", help="Test channel: Browser or SIP")
    parser.add_argument("--test_reason", default="None", help="Test failure reason")
    args = parser.parse_args()

    db.init_db()

    if args.log_test:
        ts = int(time.time())
        sess_id = f"test_{args.test_type}_{ts}_{random.randint(1000, 9999)}"
        is_succ = args.test_type.lower() == "success"
        
        tools = ["lookup_govt_scheme", "check_scheme_eligibility"] if is_succ else []
        reason = "None" if is_succ else (args.test_reason if args.test_reason != "None" else "Incomplete Task / Early Hangup")
        dur = random.uniform(25.0, 90.0) if is_succ else random.uniform(4.0, 12.0)
        user_name = f"Test User {random.randint(100, 999)}"

        res = db.log_call_session(
            session_id=sess_id,
            user_id=f"test_id_{ts}",
            caller_name=user_name,
            channel=args.test_channel,
            outcome="success" if is_succ else "failed",
            failure_reason=reason,
            duration_seconds=dur,
            tools_used=tools
        )
        # Return updated analytics
    
    data = db.get_call_analytics(
        channel_filter=args.channel if args.channel != "All" else None,
        outcome_filter=args.outcome if args.outcome != "All" else None
    )
    print(json.dumps(data, ensure_ascii=False))

if __name__ == "__main__":
    main()

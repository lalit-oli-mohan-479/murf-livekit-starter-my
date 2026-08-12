"""Resolve an escalation ticket and manage human help requests.

Usage:
    # Mark ticket as Resolved:
    uv run python src/resolve_escalation.py --ref ESC-23835 --note "Issue resolved by branch manager"

    # Mark as In Progress:
    uv run python src/resolve_escalation.py --ref ESC-23835 --status "In Progress"

    # List all escalations:
    uv run python src/resolve_escalation.py --list

    # List by status:
    uv run python src/resolve_escalation.py --list --status Open
"""

import argparse
import sys
from pathlib import Path

# Reconfigure stdout to support Devanagari/UTF-8 printing on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(".env.local")

import db


def list_escalations(status_filter: str = None):
    """Print all escalation tickets, optionally filtered by status."""
    tickets = db.get_escalations(status=status_filter)
    if not tickets:
        print(f"\nNo escalation tickets found{' with status: ' + status_filter if status_filter else ''}.")
        return

    print(f"\n{'=' * 70}")
    print(f"  ESCALATION TICKETS{' (Status: ' + status_filter + ')' if status_filter else ' (All)'}")
    print(f"{'=' * 70}")

    for t in tickets:
        urgency_icon = {"Emergency": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(t["urgency"], "⚪")
        status_icon = {"Open": "📬", "In Progress": "🔧", "Resolved": "✅"}.get(t["status"], "❓")

        print(f"\n  {status_icon} {t['reference_id']}  |  {urgency_icon} {t['urgency']}  |  {t['status']}")
        print(f"     Caller:     {t['caller_name']}")
        print(f"     Category:   {t['reason_category']}")
        print(f"     Follow-up:  {t['contact_method']}  |  Language: {t['caller_language']}")
        print(f"     Summary:    {t['issue_summary'][:120]}...")
        print(f"     Created:    {t['created_at']}")
        print(f"  {'─' * 66}")

    print(f"\n  Total: {len(tickets)} ticket(s)\n")


def main():
    parser = argparse.ArgumentParser(
        description="Manage human help escalation tickets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--ref", help="Escalation reference ID (e.g. ESC-23835)")
    parser.add_argument("--status", default="Resolved", help="New status: 'Open', 'In Progress', or 'Resolved' (default: Resolved)")
    parser.add_argument("--note", default="", help="Resolution note to append to the ticket")
    parser.add_argument("--list", action="store_true", dest="list_tickets", help="List all escalation tickets")

    args = parser.parse_args()

    db.init_db()

    if args.list_tickets:
        status_filter = args.status if args.status != "Resolved" else None
        list_escalations(status_filter)
        return

    if not args.ref:
        parser.error("--ref is required to update a ticket. Use --list to see all tickets.")

    # Look up ticket first
    ticket = db.lookup_escalation_by_ref(args.ref.strip().upper())
    if not ticket:
        print(f"\n❌  No escalation ticket found with reference ID: {args.ref}")
        return

    print(f"\n📋  Current ticket:")
    print(f"    Ref:       {ticket['reference_id']}")
    print(f"    Caller:    {ticket['caller_name']}")
    print(f"    Category:  {ticket['reason_category']}")
    print(f"    Status:    {ticket['status']} → {args.status}")

    # Update status
    updated = db.update_escalation_status(args.ref.strip().upper(), args.status, args.note)
    if not updated:
        print(f"\n❌  Failed to update ticket {args.ref}")
        return

    print(f"\n✅  Ticket {args.ref} updated to: {args.status}")
    if args.note:
        print(f"    Note: {args.note}")


if __name__ == "__main__":
    main()

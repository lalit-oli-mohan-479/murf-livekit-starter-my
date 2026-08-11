"""Trigger an outbound call with scheme reminder metadata from CLI or CSV file.

Examples:

1. Direct CLI flags:
    uv run python src/telephony/outbound/dial.py --to lalitomohan --name "Ramesh Kumar" --scheme "Atal Pension Yojana" --deadline "31 August 2026"

2. Using CSV file:
    uv run python src/telephony/outbound/dial.py --csv src/telephony/outbound/customers.csv --row 1
"""

import argparse
import asyncio
import csv
import json
import os
import uuid

from dotenv import load_dotenv
from livekit import api

load_dotenv(".env.local")

AGENT_NAME = "outbound-agent"


async def dial(phone_number: str, room_name: str, metadata: dict) -> None:
    """Create the room and dispatch the outbound agent into it."""
    lk = api.LiveKitAPI()
    try:
        await lk.room.create_room(api.CreateRoomRequest(name=room_name))

        # The agent reads this metadata to know who to call and what to say.
        await lk.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=AGENT_NAME,
                room=room_name,
                metadata=json.dumps(metadata),
            )
        )
    finally:
        await lk.aclose()


def load_from_csv(csv_path: str, row_index: int = 1) -> dict:
    """Read customer details from a CSV file."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise ValueError(f"CSV file '{csv_path}' is empty!")

    if row_index < 1 or row_index > len(rows):
        raise IndexError(
            f"Row index {row_index} out of bounds. CSV contains {len(rows)} rows."
        )

    selected = rows[row_index - 1]
    return {
        "phone_number": selected.get("phone_number", "").strip(),
        "customer_name": selected.get("customer_name", "").strip(),
        "scheme_name": selected.get("scheme_name", "").strip(),
        "deadline": selected.get("deadline", "").strip(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Place an outbound scheme reminder call (via CLI or CSV).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--to",
        help="Number/SIP user to call (e.g. +919876543210 or linphone-username)",
    )
    parser.add_argument(
        "--name",
        default="",
        help="Name of the person being called",
    )
    parser.add_argument(
        "--scheme",
        default="Atal Pension Yojana",
        help="Scheme to remind about",
    )
    parser.add_argument(
        "--deadline",
        default="31 August 2026",
        help="Application deadline",
    )
    parser.add_argument(
        "--csv",
        help="Path to CSV file containing customer list (e.g. src/telephony/outbound/customers.csv)",
    )
    parser.add_argument(
        "--row",
        type=int,
        default=1,
        help="1-indexed row number from CSV file to dial (default: 1)",
    )
    parser.add_argument(
        "--room",
        default=None,
        help="Room name to use.",
    )
    args = parser.parse_args()

    if args.csv:
        print(f"📄 Loading customer details from CSV: {args.csv} (Row {args.row})")
        metadata = load_from_csv(args.csv, args.row)
    elif args.to:
        metadata = {
            "phone_number": args.to.strip(),
            "customer_name": args.name.strip(),
            "scheme_name": args.scheme.strip(),
            "deadline": args.deadline.strip(),
        }
    else:
        parser.error("Either --to or --csv must be specified!")

    room_name = args.room or f"outbound-{uuid.uuid4().hex[:8]}"

    asyncio.run(dial(metadata["phone_number"], room_name, metadata))

    print(f"\n{'='*60}")
    print(f"  OUTBOUND CALL DISPATCHED FROM CSV / CLI")
    print(f"{'='*60}")
    print(f"  Agent:    {AGENT_NAME}")
    print(f"  Room:     {room_name}")
    print(f"  Calling:  {metadata['phone_number']}")
    print(f"  Name:     {metadata['customer_name']}")
    print(f"  Scheme:   {metadata['scheme_name']}")
    print(f"  Deadline: {metadata['deadline']}")
    print(f"{'='*60}")
    print(f"\nWatch the worker terminal for call progress.")


if __name__ == "__main__":
    main()

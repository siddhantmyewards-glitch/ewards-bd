#!/usr/bin/env python3
"""
Google Sheets Pusher for eWards Lead Generation
Takes merged lead data and pushes it to a Google Sheet as a single new tab.

Each run creates one tab with combined company + people data:
  Company Name | Vertical / Nature | Website URL | Company LinkedIn | Person Name | Designation | Person LinkedIn

The tab label defaults to "{company_focus}_{date}" from metadata, or can be overridden with --label.

Requirements:
    pip install gspread google-auth

Usage:
    python push_to_gsheet.py --input merged_leads.json --sheet-id YOUR_GOOGLE_SHEET_ID
    python push_to_gsheet.py --input merged_leads.json --sheet-id YOUR_GOOGLE_SHEET_ID --label "Smartping_Apr13"
    python push_to_gsheet.py --input merged_leads.json --sheet-id YOUR_GOOGLE_SHEET_ID --cred path/to/creds.json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("ERROR: Required packages not installed. Run:")
    print("  pip install gspread google-auth")
    sys.exit(1)


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Default credential file locations (checked in order)
DEFAULT_CRED_PATHS = [
    Path("gsheets_cred.json"),
    Path.home() / ".config" / "gsheets_cred.json",
    Path(__file__).parent.parent.parent.parent / "gsheets_cred.json",  # project root
]


def find_credentials(explicit_path=None):
    """Find the Google service account credentials JSON file."""
    if explicit_path:
        p = Path(explicit_path)
        if p.exists():
            return p
        print(f"ERROR: Credential file not found: {explicit_path}")
        sys.exit(1)

    for p in DEFAULT_CRED_PATHS:
        if p.exists():
            print(f"Using credentials: {p}")
            return p

    print("ERROR: No Google credentials file found.")
    print("Expected in one of:")
    for p in DEFAULT_CRED_PATHS:
        print(f"  - {p}")
    print("\nSee README.md for setup instructions.")
    sys.exit(1)


def authenticate(cred_path):
    """Authenticate with Google Sheets API using service account."""
    creds = Credentials.from_service_account_file(str(cred_path), scopes=SCOPES)
    client = gspread.authorize(creds)
    return client


def push_to_sheet(client, sheet_id, data, label):
    """Push combined company + people data as a single new tab."""

    companies = data.get("companies", [])
    people = data.get("people", [])

    # Build a lookup from company name to company details
    company_lookup = {}
    for c in companies:
        company_lookup[c.get("name", "")] = c

    spreadsheet = client.open_by_key(sheet_id)

    tab_name = label[:100]  # Google Sheets tab name limit

    header = [
        "Company Name", "Vertical / Nature", "Website URL", "Company LinkedIn",
        "Person Name", "Designation", "Person LinkedIn",
    ]

    rows = []
    for p in people:
        company_name = p.get("company", "")
        c = company_lookup.get(company_name, {})
        rows.append([
            company_name,
            c.get("vertical", ""),
            c.get("website", ""),
            c.get("linkedin_url", ""),
            p.get("name", ""),
            p.get("designation", ""),
            p.get("linkedin_url", ""),
        ])

    ws = spreadsheet.add_worksheet(
        title=tab_name,
        rows=max(len(rows) + 1, 2),
        cols=len(header),
    )
    ws.update([header] + rows, value_input_option="RAW")

    # Style header row — dark background, white bold text, frozen
    ws.format("1:1", {
        "backgroundColor": {"red": 0.1, "green": 0.1, "blue": 0.1},
        "textFormat": {"bold": True, "foregroundColorStyle": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}},
    })
    ws.freeze(rows=1)

    # Set column widths
    col_widths = [220, 180, 280, 350, 200, 300, 350]
    requests = [
        {"updateDimensionProperties": {
            "range": {"sheetId": ws.id, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
            "properties": {"pixelSize": w},
            "fields": "pixelSize",
        }}
        for i, w in enumerate(col_widths)
    ]
    spreadsheet.batch_update({"requests": requests})

    print(f"  Tab '{tab_name}': {len(rows)} rows")

    return f"https://docs.google.com/spreadsheets/d/{sheet_id}"


def main():
    parser = argparse.ArgumentParser(description="Push leads to Google Sheets")
    parser.add_argument("--input", required=True, help="Merged JSON file")
    parser.add_argument("--sheet-id", required=True, help="Google Sheet ID (from the URL)")
    parser.add_argument("--label", default=None, help="Tab label prefix (default: auto from metadata)")
    parser.add_argument("--cred", default=None, help="Path to Google service account JSON key")
    args = parser.parse_args()

    # Load data
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: {args.input} not found")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Auto-generate label if not provided
    if not args.label:
        meta = data.get("metadata", {})
        focus = meta.get("company_focus", meta.get("type", "leads"))
        city = meta.get("city", "")
        date_str = datetime.now().strftime("%b%d")
        parts = [p for p in [focus, city, date_str] if p]
        args.label = "_".join(parts).replace(" ", "_")

    # Authenticate and push
    cred_path = find_credentials(args.cred)
    client = authenticate(cred_path)

    print(f"Pushing to Google Sheet...")
    sheet_url = push_to_sheet(client, args.sheet_id, data, args.label)

    people_count = len(data.get("people", []))
    companies_count = len(data.get("companies", []))
    print(f"\nDone! {companies_count} companies + {people_count} people pushed to one tab.")
    print(f"Sheet: {sheet_url}")


if __name__ == "__main__":
    main()

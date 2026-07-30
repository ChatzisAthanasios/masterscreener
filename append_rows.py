"""Append a day's screener results to data/<screener-id>.csv.

Usage:
    python append_rows.py <screener-id> < rows.json

stdin is a JSON object:
    {"date": "2026-07-30", "rows": [
        {"ticker": "NCRA", "company": "Nocera Inc", "price": 3.12,
         "change_pct": 118.18, "volume": 127673091, "notes": ""}
    ]}

Rows whose (date, ticker) pair is already present are skipped, so re-running
the same day is safe and will not duplicate history.
"""

import csv
import json
import os
import sys

FIELDS = ["date", "ticker", "company", "price", "change_pct", "volume", "notes"]
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def existing_keys(path):
    if not os.path.exists(path):
        return set()
    with open(path, newline="", encoding="utf-8") as fh:
        return {(r["date"], r["ticker"]) for r in csv.DictReader(fh)}


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python append_rows.py <screener-id> < rows.json")

    screener_id = sys.argv[1]
    payload = json.load(sys.stdin)
    date = payload["date"]
    rows = payload["rows"]

    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, screener_id + ".csv")
    seen = existing_keys(path)
    is_new = not os.path.exists(path)

    written = skipped = 0
    with open(path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        if is_new:
            writer.writeheader()
        for row in rows:
            key = (date, row["ticker"])
            if key in seen:
                skipped += 1
                continue
            seen.add(key)
            writer.writerow({
                "date": date,
                "ticker": row["ticker"],
                "company": row.get("company", ""),
                "price": row.get("price", ""),
                "change_pct": row.get("change_pct", ""),
                "volume": row.get("volume", ""),
                "notes": row.get("notes", ""),
            })
            written += 1

    print("{}: {} appended, {} already present -> {}".format(
        screener_id, written, skipped, path))


if __name__ == "__main__":
    main()

"""Append a day's screener results to data/<screener-id>.csv.

This file is the APPEARANCE log: which tickers a screener surfaced on each date and
at what price. It is NOT the performance record.

`change_pct_at_entry` is the stock's move on the day at the moment it was screened.
For the momentum screens it is the very move that caused the stock to be selected,
so it must never be read as a return. Profitability lives in perf/ (written by
score_day.py), which measures entry price against the closing price.


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

FIELDS = ["date", "ticker", "company", "entry_price", "change_pct_at_entry",
          "volume", "notes"]
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
                "entry_price": row.get("price", ""),
                "change_pct_at_entry": row.get("change_pct", ""),
                "volume": row.get("volume", ""),
                "notes": row.get("notes", ""),
            })
            written += 1

    print("{}: {} appended, {} already present -> {}".format(
        screener_id, written, skipped, path))


if __name__ == "__main__":
    main()

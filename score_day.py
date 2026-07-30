"""Score one screener for one day: entry snapshot vs exit snapshot.

Usage:
    python score_day.py <screener-id> --date 2026-07-30 \
        --entry entry.json --exit exit.json

Both snapshot files are JSON:
    {"time": "09:45 ET", "rows": [{"ticker": "NCRA", "company": "Nocera Inc",
                                   "price": 3.12, "volume": 127673091}]}

The exit file only needs "ticker" and "price".

Writes two things:
  perf/<screener-id>.csv  one row per pick per day, with its return
  perf/summary.csv        one row per screener per day, with the day's stats

A ticker present at entry but missing at exit (halted, delisted, or dropped
from Finviz) is written with a blank exit price and excluded from the day's
statistics. It is counted in `n_unscored` so the gap is visible rather than
silently improving the win rate.

Re-running the same screener and date replaces that day's rows instead of
duplicating them.
"""

import argparse
import csv
import json
import os
import statistics

BASE = os.path.dirname(os.path.abspath(__file__))
PERF_DIR = os.path.join(BASE, "perf")

PICK_FIELDS = [
    "date", "screener_id", "ticker", "company",
    "entry_time", "entry_price", "exit_time", "exit_price",
    "return_pct", "outcome",
]
SUMMARY_FIELDS = [
    "date", "screener_id", "n_picks", "n_scored", "n_unscored",
    "n_wins", "n_losses", "win_rate_pct", "avg_return_pct",
    "median_return_pct", "best_ticker", "best_return_pct",
    "worst_ticker", "worst_return_pct",
]


def load_rows(path, existing=None):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("screener_id")
    ap.add_argument("--date", required=True)
    ap.add_argument("--entry", required=True)
    ap.add_argument("--exit", dest="exit_path", required=True)
    args = ap.parse_args()

    sid, date = args.screener_id, args.date
    entry = load_rows(args.entry)
    exit_ = load_rows(args.exit_path)
    exit_prices = {r["ticker"]: r["price"] for r in exit_["rows"]}

    picks, returns = [], []
    for row in entry["rows"]:
        ticker = row["ticker"]
        entry_price = float(row["price"])
        exit_price = exit_prices.get(ticker)

        if exit_price is None or entry_price <= 0:
            picks.append({
                "date": date, "screener_id": sid, "ticker": ticker,
                "company": row.get("company", ""),
                "entry_time": entry["time"], "entry_price": entry_price,
                "exit_time": exit_["time"], "exit_price": "",
                "return_pct": "", "outcome": "unscored",
            })
            continue

        exit_price = float(exit_price)
        ret = (exit_price - entry_price) / entry_price * 100.0
        returns.append((ticker, ret))
        picks.append({
            "date": date, "screener_id": sid, "ticker": ticker,
            "company": row.get("company", ""),
            "entry_time": entry["time"], "entry_price": entry_price,
            "exit_time": exit_["time"], "exit_price": exit_price,
            "return_pct": round(ret, 2),
            "outcome": "win" if ret > 0 else "loss" if ret < 0 else "flat",
        })

    # Replace any prior scoring of this same date.
    pick_path = os.path.join(PERF_DIR, sid + ".csv")
    os.makedirs(PERF_DIR, exist_ok=True)
    kept = [r for r in read_csv(pick_path) if r["date"] != date]
    write_csv(pick_path, PICK_FIELDS, kept + picks)

    vals = [r for _, r in returns]
    wins = sum(1 for v in vals if v > 0)
    losses = sum(1 for v in vals if v < 0)
    best = max(returns, key=lambda x: x[1]) if returns else ("", "")
    worst = min(returns, key=lambda x: x[1]) if returns else ("", "")

    summary = {
        "date": date,
        "screener_id": sid,
        "n_picks": len(entry["rows"]),
        "n_scored": len(vals),
        "n_unscored": len(entry["rows"]) - len(vals),
        "n_wins": wins,
        "n_losses": losses,
        "win_rate_pct": round(wins / len(vals) * 100, 1) if vals else "",
        "avg_return_pct": round(statistics.fmean(vals), 2) if vals else "",
        "median_return_pct": round(statistics.median(vals), 2) if vals else "",
        "best_ticker": best[0],
        "best_return_pct": round(best[1], 2) if vals else "",
        "worst_ticker": worst[0],
        "worst_return_pct": round(worst[1], 2) if vals else "",
    }

    sum_path = os.path.join(PERF_DIR, "summary.csv")
    kept = [r for r in read_csv(sum_path)
            if not (r["date"] == date and r["screener_id"] == sid)]
    write_csv(sum_path, SUMMARY_FIELDS, kept + [summary])

    print("{} {}: {} scored, {} unscored, win rate {}%, avg {}%".format(
        date, sid, summary["n_scored"], summary["n_unscored"],
        summary["win_rate_pct"], summary["avg_return_pct"]))


if __name__ == "__main__":
    main()

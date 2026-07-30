"""Roll perf/summary.csv up into a per-screener leaderboard.

Usage:
    python report.py [--days N]

--days limits the report to the N most recent tracked dates.

Each screener's daily average return is treated as one observation, i.e. the
result of equal-weighting that day's picks. "cum_return_pct" compounds those
daily averages; it is a comparison figure between screeners, not a claim about
what an account would have made (it ignores costs, slippage, and the fact that
you cannot buy every pick).
"""

import argparse
import csv
import json
import os
import statistics

BASE = os.path.dirname(os.path.abspath(__file__))
SUMMARY = os.path.join(BASE, "perf", "summary.csv")
REGISTRY = os.path.join(BASE, "screeners.json")


def categories():
    """Map screener id -> category, so the report can group comparable screens."""
    try:
        with open(REGISTRY, encoding="utf-8") as fh:
            return {s["id"]: s["category"] for s in json.load(fh)["screeners"]}
    except (OSError, KeyError, ValueError):
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=0)
    args = ap.parse_args()

    if not os.path.exists(SUMMARY):
        print("No perf/summary.csv yet — score a day first.")
        return

    with open(SUMMARY, newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["avg_return_pct"] != ""]

    if not rows:
        print("perf/summary.csv has no scored days yet.")
        return

    if args.days:
        keep = sorted({r["date"] for r in rows})[-args.days:]
        rows = [r for r in rows if r["date"] in keep]

    by_screener = {}
    for r in rows:
        by_screener.setdefault(r["screener_id"], []).append(r)

    cats = categories()
    table = []
    for sid, days in by_screener.items():
        daily = [float(d["avg_return_pct"]) for d in days]
        picks = sum(int(d["n_scored"]) for d in days)
        wins = sum(int(d["n_wins"]) for d in days)

        cum = 1.0
        for v in daily:
            cum *= (1 + v / 100.0)

        table.append({
            "screener": sid,
            "category": cats.get(sid, "?"),
            "days": len(daily),
            "picks": picks,
            "win_rate": round(wins / picks * 100, 1) if picks else 0.0,
            "avg_day": round(statistics.fmean(daily), 2),
            "best_day": round(max(daily), 2),
            "worst_day": round(min(daily), 2),
            "cum_return": round((cum - 1) * 100, 2),
        })

    dates = sorted({r["date"] for r in rows})
    print("Screener performance | {} screeners | {} sessions | {} to {}\n".format(
        len(table), len(dates), dates[0], dates[-1]))

    hdr = "{:<28}{:>6}{:>7}{:>9}{:>10}{:>9}{:>9}{:>10}"
    order = ["DayTrading", "SwingTrading", "Growth", "Value", "Income"]
    groups = sorted(
        {r["category"] for r in table},
        key=lambda c: order.index(c) if c in order else len(order),
    )

    for cat in groups:
        rows_in = sorted([r for r in table if r["category"] == cat],
                         key=lambda r: r["cum_return"], reverse=True)
        print("== {} ({}) ==".format(cat, len(rows_in)))
        print(hdr.format("SCREENER", "DAYS", "PICKS", "WIN%",
                         "AVG/DAY", "BEST", "WORST", "CUM%"))
        print("-" * 88)
        for r in rows_in:
            print(hdr.format(
                r["screener"][:27], r["days"], r["picks"], r["win_rate"],
                r["avg_day"], r["best_day"], r["worst_day"], r["cum_return"]))
        print()

    print("Ranked within category. Cross-category comparison is misleading: the momentum")
    print("screens re-select their picks daily, the fundamental screens return nearly the")
    print("same names each day, so their return series are not equivalent observations.")

    if len(dates) < 20:
        print("\nNote: {} sessions tracked. Treat rankings as provisional - "
              "day-to-day variance dominates small samples.".format(len(dates)))


if __name__ == "__main__":
    main()

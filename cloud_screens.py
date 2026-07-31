"""Cloud-native screen evaluation (v2 pipeline).

Finviz screener pages cannot be fetched from Anthropic's cloud (robots.txt),
so the cloud runs rebuild the DayTrading screens from accessible sources:

  candidates  : finviz.com homepage signal tables (allowed by robots) plus
                stockanalysis.com /markets/ gainers-losers-active lists
  stats       : stockanalysis.com /stocks/<t>/statistics/ per candidate
                (float, short % of float, RSI, MA50, MA200, 20-day avg volume)

Each screen below re-implements its Finviz filter definition from
screeners.json on those fields. Deviations from the original Finviz filters
are recorded in APPROXIMATIONS and must be copied into the daily log.

Usage:
    python3 cloud_screens.py candidates.json <date> "<HH:MM ET>"

candidates.json: [{"ticker","company","price","change_pct","volume",
                   "market_cap_m","float_m","short_pct_float","rsi",
                   "ma50","ma200","avgvol20","sources":[...]}]
  Numeric fields may be null when a stat was unreadable; a screen that
  needs a null field simply does not match that candidate (logged).

Writes snapshots/<date>-<id>-entry.json and pipes rows to append_rows.py
format on stdout-free files: tmp_rows_<id>.json (caller runs append_rows).
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

APPROXIMATIONS = {
    "gap-up-momentum": "ta_gap_u4 approximated by change_pct >= 4 at capture "
                       "time (open gap not separately observable).",
    "unusual-volume": "ta_sma20_pa approximated by price > MA50 (MA20 not "
                      "available from the cloud source).",
    "top-losers": "RSI is daily RSI as of the prior close, not intraday.",
    "most-volatile": "ta_volatility_wo5 approximated by |change_pct| >= 5; "
                     "sh_opt_option (optionable) not verifiable in cloud.",
    "short-squeeze": "Short % of float is exchange-reported (bi-weekly lag), "
                     "same limitation as Finviz's own field.",
}

def n(x):
    return x is not None

def relvol(c):
    if n(c.get("avgvol20")) and c["avgvol20"] and n(c.get("volume")):
        return c["volume"] / c["avgvol20"]
    return None


def evaluate(c):
    """Return list of screen ids candidate c matches."""
    hits = []
    p = c.get("price")
    ch = c.get("change_pct")
    v = c.get("volume")
    rv = relvol(c)
    fl = c.get("float_m")
    sh = c.get("short_pct_float")
    rsi = c.get("rsi")

    if all(map(n, (p, ch, v))) and rv is not None and n(fl):
        if v > 50_000 and fl < 50 and p > 5 and rv > 2 and ch >= 4:
            hits.append("gap-up-momentum")
    if all(map(n, (p, v))) and v > 500_000 and p > 2 and n(ch) and ch > 0:
        hits.append("top-gainers")  # ranked later, top 25 by change
    if rv is not None and rv > 3 and n(ch) and ch > 0 \
            and n(p) and n(c.get("ma50")) and p > c["ma50"]:
        hits.append("unusual-volume")
    if all(map(n, (p, v))) and rv is not None \
            and v > 1_000_000 and p < 5 and rv > 3:
        hits.append("penny-stock-momentum")
    if n(fl) and rv is not None and fl < 20 and rv > 3 and n(ch) and ch > 0:
        hits.append("low-float")
    if n(sh) and rv is not None and sh > 20 and rv > 2 and n(ch) and ch > 0:
        hits.append("short-squeeze")
    if all(map(n, (v, ch, rsi))) and v > 1_000_000 and ch < 0 and rsi < 20:
        hits.append("top-losers")
    if all(map(n, (v, ch))) and v > 1_000_000 and abs(ch) >= 5:
        hits.append("most-volatile")
    return hits


def main():
    cand_path, date, etime = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(cand_path, encoding="utf-8") as fh:
        cands = json.load(fh)

    screens = {sid: [] for sid in (
        "gap-up-momentum", "top-gainers", "unusual-volume",
        "penny-stock-momentum", "low-float", "short-squeeze",
        "top-losers", "most-volatile")}

    for c in cands:
        for sid in evaluate(c):
            screens[sid].append(c)

    # top-gainers: keep top 25 by change like Finviz's o=-change ordering
    screens["top-gainers"].sort(key=lambda c: -(c.get("change_pct") or 0))
    for sid in screens:
        screens[sid] = screens[sid][:25]

    os.makedirs(os.path.join(BASE, "snapshots"), exist_ok=True)
    report = {}
    for sid, rows in screens.items():
        snap = {"time": etime, "rows": [
            {"ticker": c["ticker"], "company": c.get("company", ""),
             "price": c["price"]} for c in rows]}
        with open(os.path.join(BASE, "snapshots",
                               f"{date}-{sid}-entry.json"),
                  "w", encoding="utf-8") as fh:
            json.dump(snap, fh, indent=1)
        append_payload = {"date": date, "rows": [
            {"ticker": c["ticker"], "company": c.get("company", ""),
             "price": c["price"], "change_pct": c.get("change_pct", ""),
             "volume": c.get("volume", ""),
             "notes": ("ETF" if c.get("etf") else "")} for c in rows]}
        with open(os.path.join(BASE, f"tmp_rows_{sid}.json"),
                  "w", encoding="utf-8") as fh:
            json.dump(append_payload, fh, indent=1)
        report[sid] = [c["ticker"] for c in rows]

    print(json.dumps(report, indent=1))
    print("\nAPPROXIMATIONS to copy into the log:", file=sys.stderr)
    for k, v in APPROXIMATIONS.items():
        print(f"  {k}: {v}", file=sys.stderr)


if __name__ == "__main__":
    main()

"""Detect Finviz filter codes that have stopped working.

Finviz silently IGNORES filter codes it does not recognise instead of returning
an error. A screener with a dud code therefore looks healthy while actually
running without that constraint — it quietly screens a far wider universe than
its name claims, and its performance numbers become incomparable to the others.

This script catches that by comparing result counts against the unfiltered
universe:

    python3 validate_filters.py            # check all 40 screener URLs (41 requests)
    python3 validate_filters.py --codes    # also check each filter code alone

A screener whose count equals the unfiltered baseline has had ALL its filters
dropped. A screener above --wide-pct of the universe is flagged WIDE for a human
to look at: legitimate for a loose screen, suspicious for a restrictive one.

Exit code is 1 if anything is UNFILTERED or errored, so a caller can detect
trouble without parsing the output.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(BASE, "screeners.json")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126 Safari/537.36")
COUNT_RE = re.compile(r"#1\s*/\s*([\d,]+)")
TICKER_RE = re.compile(r"quote\.ashx\?t=([A-Z.\-]{1,6})&")


def fetch_count(url, timeout=30):
    """Return (count, error). count is None when the page had no results table."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", "replace")
    except Exception as exc:                      # network, TLS, HTTP error
        return None, "{}: {}".format(type(exc).__name__, exc)

    m = COUNT_RE.search(html)
    if m:
        return int(m.group(1).replace(",", "")), None
    # No pagination counter. Genuinely empty if there are no ticker links.
    if not TICKER_RE.search(html):
        return 0, None
    return None, "results present but no count found (Finviz layout change?)"


def screener_url(filters):
    return "https://finviz.com/screener.ashx?v=111&f=" + filters


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codes", action="store_true",
                    help="also test every filter code in isolation (slower)")
    ap.add_argument("--wide-pct", type=float, default=40.0,
                    help="flag screeners matching more than this %% of the universe")
    ap.add_argument("--delay", type=float, default=0.4,
                    help="seconds between requests")
    args = ap.parse_args()

    with open(REGISTRY, encoding="utf-8") as fh:
        registry = json.load(fh)
    screeners = registry["screeners"]

    baseline, err = fetch_count("https://finviz.com/screener.ashx?v=111")
    if err or not baseline:
        print("FATAL: could not read the unfiltered baseline count:", err)
        return 2
    print("Unfiltered universe: {}\n".format(baseline))

    problems = []

    print("{:<28}{:>8}{:>8}  {}".format("SCREENER", "COUNT", "%UNIV", "STATUS"))
    print("-" * 60)
    for s in screeners:
        if not s.get("enabled"):
            continue
        count, err = fetch_count(s["url"])
        if err:
            status, shown, pct = "ERROR", "-", 0.0
            problems.append("{}: {}".format(s["id"], err))
        else:
            pct = count / baseline * 100.0
            shown = count
            if count == baseline:
                status = "UNFILTERED"
                problems.append("{}: all filters ignored by Finviz".format(s["id"]))
            elif count == 0:
                status = "empty"
            elif pct > args.wide_pct:
                status = "WIDE"
            else:
                status = "ok"
        print("{:<28}{:>8}{:>7.1f}%  {}".format(s["id"][:27], shown, pct, status))
        time.sleep(args.delay)

    if args.codes:
        codes = set()
        for s in screeners:
            q = urllib.parse.parse_qs(urllib.parse.urlparse(s["url"]).query)
            codes.update(c for c in q.get("f", [""])[0].split(",") if c)
        print("\n{:<28}{:>8}  {}".format("FILTER CODE", "COUNT", "STATUS"))
        print("-" * 52)
        for code in sorted(codes):
            count, err = fetch_count(screener_url(code))
            if err:
                status, shown = "ERROR", "-"
                problems.append("code {}: {}".format(code, err))
            elif count == baseline:
                status, shown = "IGNORED", count
                problems.append("code {}: ignored by Finviz (invalid)".format(code))
            else:
                status, shown = "ok", count
            print("{:<28}{:>8}  {}".format(code, shown, status))
            time.sleep(args.delay)

    print()
    if problems:
        print("PROBLEMS FOUND ({}):".format(len(problems)))
        for p in problems:
            print("  -", p)
        print("\nA screener flagged UNFILTERED or a code flagged IGNORED is not")
        print("measuring what its name says. Fix the code before trusting its numbers.")
        print("See FILTER-FIXES.md for how the current codes were derived.")
        return 1

    print("All enabled screeners are applying their filters. No dud codes found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

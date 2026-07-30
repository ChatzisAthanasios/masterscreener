# Finviz Screener Performance Tracker — Runbook

Persistent workspace that records what each of the 40 screeners surfaced, and how those picks
performed intraday. Every screener is measured on the same day-trading horizon — entry shortly
after the open, exit at the close — so their results are directly comparable regardless of the
category the screener belongs to.

## Layout

| Path | Purpose |
|---|---|
| `screeners.json` | All 40 screeners, all enabled. Set `enabled: false` to drop one. |
| `validate_filters.py` | Detects Finviz filter codes that have stopped working. |
| `FILTER-FIXES.md` | Why the current filter codes are what they are; 12 were corrected. |
| `append_rows.py` | Appends a day's appearances to `data/<id>.csv`, deduped by (date, ticker). |
| `score_day.py` | Scores one screener-day: entry snapshot vs exit snapshot. |
| `report.py` | Per-screener leaderboard across all tracked sessions. |
| `data/<id>.csv` | What the screener surfaced: date, ticker, company, price, change_pct, volume, notes. |
| `perf/<id>.csv` | One row per pick per day, with its intraday return and win/loss/flat. |
| `perf/summary.csv` | One row per screener per day: win rate, avg return, best, worst. |
| `logs/<date>.md` | Human-readable daily summary. |

Source of the URLs: `C:/Users/user/strategymasterscreeners/finviz-screeners.txt`

## Which file answers "is this screener profitable?"

Three files, three different questions. Reading the wrong one gives a badly wrong answer.

**`data/<id>.csv` — what the screener surfaced. NOT performance.**

```
date, ticker, company, entry_price, change_pct_at_entry, volume, notes
```

One row per ticker per date, accumulating forever. `change_pct_at_entry` is the stock's move
**on that day at the moment it was screened** — for the momentum screens it is the very move
that caused the stock to be selected. It is selection context, never a return. A `top-gainers`
row showing +116% means the stock was already up 116% when it appeared, not that the screener
made 116%.

**`perf/<id>.csv` — what each pick did afterwards.**

```
date, screener_id, ticker, company, entry_time, entry_price, exit_time,
exit_price, return_pct, outcome
```

One row per pick per date. `return_pct` is entry price to closing price — the actual result.
`outcome` is win / loss / flat, or `unscored` when the ticker could not be re-quoted.

**`perf/summary.csv` — one row per screener per date. This is the profitability record.**

```
date, screener_id, n_picks, n_scored, n_unscored, n_wins, n_losses,
win_rate_pct, avg_return_pct, median_return_pct,
best_ticker, best_return_pct, worst_ticker, worst_return_pct
```

Every scored session appends a row and none are ever removed, so this file is the full history.
Re-scoring a date replaces that date's row rather than duplicating it.

Read it with:

```bash
python3 report.py              # leaderboard across all dates, grouped by category
python3 report.py --by-date    # every screener's session-by-session series and running total
python3 report.py --days 20    # last 20 sessions only
```

`--by-date` is the one that answers "which screeners are actually profitable" honestly: it
shows whether a screener is consistently positive or whether one outlier session is carrying
its average.

## Where this runs

Both runs execute as **cloud routines** in Anthropic's cloud, not on a local machine. Each run
is a fully isolated session that clones this repository fresh, so:

- **Nothing persists unless it is committed and pushed.** Every run must `git add`, `git commit`
  and `git push` its output before finishing. A run that does the work but does not push has
  accomplished nothing.
- **`snapshots/` must be committed, not ignored.** It is the only channel through which the
  morning ENTRY run passes its picks and entry prices to the evening EXIT run. If the entry
  snapshot is not pushed, the exit run has nothing to score.
- Every run should `git pull` first, in case the other run of the day pushed since the clone.

## Why there are two runs per day

Day-trading performance is an *intraday* measurement: it needs a price at the moment the
screener flagged the stock, and a price at the end of the session.

A single post-close run cannot produce this. After the close, the `change_pct` Finviz reports
is the full session's move — and the momentum screens select on that move (`ta_perf_dup`,
`o=-change`, gap and relative-volume filters). Scoring those on the move that caused the stock
to appear would measure nothing but the selection rule itself, and would look spectacularly
profitable while being unactionable. The fundamental screens (Value, Income, Growth) are not
distorted the same way, but they use the same two-run structure so that every screener is
measured identically and the leaderboard compares like with like. So:

- **ENTRY run — shortly after the open.** Fetch each enabled screener, record the picks and
  their prices. This is the shortlist as a trader would have seen it that morning.
- **EXIT run — at/after the close.** Re-quote *the same tickers* and compute the return from
  entry to close.

## ENTRY run

For each enabled screener in `screeners.json`:

1. WebFetch the screener `url`, requesting ticker, company, price, change %, volume.
2. Keep at most `max_rows_per_screener` rows (default 25) from page 1. Do not paginate.
3. Append appearances: `python append_rows.py <id> < rows.json`
4. Save the entry snapshot to `snapshots/<date>-<id>-entry.json`:
   `{"time": "09:45 ET", "rows": [{"ticker": ..., "company": ..., "price": ...}]}`

## EXIT run

For each enabled screener that has an entry snapshot for today:

1. Read the ticker list from that snapshot.
2. Re-quote all of them in **one** fetch using Finviz's ticker filter:
   `https://finviz.com/screener.ashx?v=111&t=TICKER1,TICKER2,...`
   (verified: this returns exactly the requested tickers, one row each)
3. Save as `snapshots/<date>-<id>-exit.json` with the same shape.
4. Score it:

   ```bash
   python score_day.py <id> --date <YYYY-MM-DD> --entry snapshots/<date>-<id>-entry.json --exit snapshots/<date>-<id>-exit.json
   ```

5. Write `logs/<date>.md` with each screener's win rate, average return, best and worst pick.
6. Run `python report.py` and include the leaderboard in the log.

## Filter health

Finviz silently ignores filter codes it does not recognise instead of erroring, so a broken
screener looks identical to a working one — it just quietly matches a much wider universe.
Twelve dud codes were found and fixed on 2026-07-30; see `FILTER-FIXES.md`.

The Monday ENTRY run re-checks this automatically with `python3 validate_filters.py`. If any
screener is reported `UNFILTERED`, its numbers are not comparable to the others and the code
needs fixing before its history is trusted.

## Rules

- Run only on US trading days. Finviz serves the last session's data on weekends and
  holidays, which would be logged again under a new date as if it were fresh.
- `date` is the US market date, not the local run date.
- A ticker present at entry but missing at exit (halted, delisted) is written with a blank
  exit price and counted in `n_unscored`. Never substitute a guessed price — that would
  quietly bias the win rate.
- If a fetch fails, record `FETCH FAILED` for that screener in the daily log and continue.
  Never write a partial or invented row.
- Re-running `score_day.py` for the same screener and date replaces that day's rows rather
  than duplicating them, so a retry is safe.

## What these numbers are and are not

- Prices come from Finviz's free web data, which is delayed. Entry and exit prices are
  therefore approximate, and the entry price is *not* a fill price.
- Returns assume equal weight across every pick, no costs, no slippage, no position sizing,
  and no intraday stop or target. Real results would differ.
- `cum_return_pct` in `report.py` compounds daily average returns. It is a way to compare
  screeners against each other, not a projection of account performance.
- The screener universe is re-selected every morning, so this measures the *screen*, not a
  held portfolio.
- The 40 screeners are not comparable in the way the leaderboard's single ranking implies.
  The momentum and day-trading screens turn over almost completely each morning, so their
  daily return reflects a genuinely new set of picks. The fundamental screens (Value, Income,
  Growth) return nearly the same names every day, so their daily return is close to a static
  basket's — lower variance, and the day-to-day figures are highly correlated rather than
  independent observations. Judging the two groups against each other on `cum_return_pct`
  compares different things.
- This workspace records and summarizes data. It does not recommend trades.

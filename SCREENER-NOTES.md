# Screener Notes — what each screen hunts, how it's tracked, what the data says

Living document. Updated 2026-07-31 after the first scored session (2026-07-30) and the
first cloud-native entry run (2026-07-31). Everything here is measurement commentary, not
trade advice. One scored session means every ranking below is provisional — day-to-day
variance dominates until ~15-20 sessions accumulate.

## How to read performance claims

`perf/summary.csv` is the profitability record (win rate, avg return per screener per day).
`data/<id>.csv` is only what was surfaced. A +116% `change_pct_at_entry` is selection
context, never a return. All returns: entry (~09:45-10:50 ET) to same-day close, equal
weight, delayed quotes, no costs/slippage.

---

## DayTrading screens (8) — all tracked daily by the cloud v2 pipeline

### gap-up-momentum — "Gap Up Morning Gappers"
Filters: gap up ≥4%, price >$5, float <50M, rel-vol >2, volume >50K.
The classic small-float gap-and-go setup: enough price to matter, small enough float to move.
- 2026-07-30: 20 picks, 65% win, +4.07% avg — the steadiest momentum screen of the day.
- 2026-07-31: only FCUV qualified (float 0.58M, +494% — a degenerate runner; RSI 89).
- Note: v2 approximates the gap by change-at-capture; a stock that gapped and faded by 10:30
  is missed. Tends to produce few, concentrated picks — quality over quantity so far.

### top-gainers — "Top Gainers Research"
Filters: biggest % gainers with volume >500K, price >$2. No float/quality filter.
- 2026-07-30: 50% win, +1.68% avg. The list was almost entirely 2x leveraged ETFs — this
  screen without an ETF exclusion mostly measures whatever underlying already ran.
- 2026-07-31: mix of real earnings movers (AMZN +14%, AXTI, NWL) and the FCUV/REPL runners.
- Note: chasing the top of the gainers list intraday has the worst risk profile of the
  group in the literature; the tracker will show whether the data agrees.

### unusual-volume — "Unusual Volume Breakouts"
Filters: rel-vol >3, up on the day, price above MA20 (v2: above MA50).
- 2026-07-30: 50% win, **-0.49% avg — the only negative screen of the first session.**
- 2026-07-31: FCUV, MGRX, CIGL.
- Note: high relative volume without a float or price filter admits a lot of churny junk.

### penny-stock-momentum — "Penny Stock Momentum"
Filters: price <$5, volume >1M, rel-vol >3. Direction-agnostic.
- 2026-07-30: 57.9% win, **+20.71% avg — best of day 1**, but the average is carried by
  CAPR's dead-cat bounce (+35%) and the NUWE squeeze continuation; median tells a calmer
  story. This screen's distribution is extreme in both tails.
- 2026-07-31: 16 picks — the biggest book of the day (WETO, MGRX, ZBAO, CYCU, KUST…).
- Note: fills at these prices are fantasy relative to delayed quotes; treat its numbers as
  an upper bound on anything real.

### low-float — "Low Float Runners"
Filters: float <20M, rel-vol >3, up on the day.
- 2026-07-30: **30% win but +14.7% avg** — the purest lottery-ticket profile: most picks
  bled, one or two runners paid for everything. Position-sizing sensitivity is maximal.
- 2026-07-31: FCUV, MGRX, ZBAO, LNKS, LBGJ, ONFO, KUST.

### short-squeeze — "Short Squeeze Candidates"
Filters: short >20% of float, rel-vol >2, up on the day.
- 2026-07-30: 46.7% win, +8.4% avg — the crypto-miner cluster (APLD, CLSK, CORZ, BTDR,
  WULF) held its gains into the close.
- 2026-07-31: REPL (39.6% short, +76% on data news) and KUST (47% short). Textbook setups.
- Note: short-interest data lags (bi-weekly exchange reporting) on Finviz and on the v2
  source alike.

### top-losers — "Top Losers / Reversal"
Filters: down big, volume >1M, RSI <20 — capitulation bounce hunting.
- 2026-07-30: only 4 picks (RSI<20 is a hard gate), 75% win, +9.85% avg — CAPR's bounce.
- 2026-07-31: KPTI (RSI 16.5 after -66%), RITR (RSI 14.8).
- Note: small-N screen by design; its average will be lumpy. RSI is prior-close daily RSI.

### most-volatile — "Most Volatile / Options"
Filters: high volatility, volume >1M, optionable (v2: |change| ≥5%, optionability unchecked).
- 2026-07-30: **80% win, +2.02% avg — best win rate of day 1**, modest per-pick size.
- 2026-07-31: 25 picks (capped) — the broadest screen, effectively "everything moving."
- Note: as a *universe* it looks useful; as a *signal* it says nothing about direction.

---

## SwingTrading screens (11) — status in the cloud pipeline

classic-swing (channel-up + above SMA 20/50/200) got one accidental day-trade-horizon
score on 2026-07-30: 73.7% win, +0.95% avg — exactly what a trend screen should look like
on a one-day horizon: high hit rate, small moves. The other ten (ma-bounce, pure-breakout,
oversold-bounce, high-momentum, post-earnings, golden-cross, volatility-squeeze,
god-like-pullback, smooth-momentum, institutional-whale-trail, institutional-shadow) need a
full-market technical scan that no cloud-fetchable source currently provides, so **they are
not tracked by the v2 daily runs.** Two honest paths, not yet built:
1. Accumulate our own daily price history in the repo (the exit runs already collect
   closes); after ~40 sessions, SMA20/RSI screens become computable in-repo, and SMA200
   screens after ~10 months — restricted to the ticker universe the runs have touched.
2. Measure swing screens on their proper multi-day horizon (entry to N-day exit), which the
   current day-trade scoring does not do. Worth deciding before adding them back.

## Value / Growth / Income screens (21) — not tracked in cloud v2

These need full-market fundamental scans (P/E, margins, dividend streaks…) that the
accessible source only exposes ticker-by-ticker. They also answer a different question than
day/swing trading — their daily "performance" is nearly a static basket's. Deliberately
parked; the runbook's cross-category warning applies with full force.

---

## Stock notes from the first two sessions

- **FCUV** (Focus Universal, float 0.58M): 2026-07-31's monster (+494% at capture). Flagged
  by four screens at once (gap-up, top-gainers, unusual-volume, low-float) — when screens
  overlap like this it is one bet, not four confirmations.
- **REPL** (Replimune, 39.6% short float): +76% on regulatory news, RSI 24 even after the
  move — the short-squeeze screen's archetype pick. Watch the follow-through day.
- **KPTI** (Karyopharm, RSI 16.5, -66%): top-losers' main 2026-07-31 pick; short float 42.6%
  means bounce-hunters and squeeze-hunters are in the same trade.
- **NUWE** (Nuwellis, float 0.12M, short 99% of float): 2026-07-30 runner (+116% at entry,
  closed higher, +8.5% entry-to-close for the screen), then **-59% on 2026-07-31** — the
  canonical low-float round trip inside 24 hours. The best argument the data has produced
  yet for the day-horizon exit discipline this tracker measures.
- **CAPR** (Capricor, -53% on 2026-07-30 entry): bounced +35% into the close, single-handedly
  flattering both top-losers and penny-momentum. One stock carried two screens' day-1 stats
  — check `perf/<id>.csv` medians before believing averages.
- **CMCO, BOOM, BRUN** (2026-07-30 gap-up picks): the quiet, orderly gappers that gave the
  screen its 65% win rate — no headlines, just the setup working.
- **AMZN / AAPL** (2026-07-31): earnings day put two mega-caps into the movers lists (+14% /
  -9%). They'll show up in top-gainers/most-volatile stats; remember they are a different
  species from the small-cap picks around them.
- ETF contamination: the 2026-07-30 top-gainers list was nearly all 2x single-stock ETFs
  (AAPB, NBIL, NEBX…). Rows are tagged ETF in data/*.csv notes; consider whether the screen
  should exclude them — Finviz's original had no such filter, so v2 keeps them for fidelity.

---

## Provisional read: best screeners so far

Day-trading, after ONE session, by different definitions of "best":
- Most consistent: **most-volatile** (80% win) and **gap-up-momentum** (65% win, +4.07%,
  real setups, no lottery dependence).
- Biggest average: **penny-stock-momentum** (+20.7%) and **low-float** (+14.7%) — both are
  tail-driven; their medians and 30% win rate (low-float) reveal the cost of that average.
- Avoid-so-far: **unusual-volume** (negative day 1) and **top-gainers** (ETF noise, +1.68%).

Swing: no honest data yet (classic-swing's +0.95%/73.7% was measured on the wrong horizon).

What would change these rankings: 15-20 sessions, median-vs-mean comparison, and a
max-drawdown column — all of which accumulate automatically now that the daily runs are
scheduled. Re-rank weekly with `python3 report.py --by-date`; consistency across days, not
one day's average, is the thing to trust.

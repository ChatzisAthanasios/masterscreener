# Filter code corrections

The URLs in `screeners.json` originally came from `data/strategies.ts`. Twelve of the 102
distinct Finviz filter codes they used **did not exist**, and Finviz silently ignores codes it
does not recognise rather than returning an error. Eleven of the 40 screeners were therefore
running with one or more constraints missing — they looked healthy but screened a much wider
universe than their name claimed, and their performance figures would not have been comparable
to the screeners that worked.

## How the dud codes were identified

Each of the 102 codes was requested on its own and its result count compared against the
unfiltered universe (**11,525** securities on 2026-07-30):

```
https://finviz.com/screener.ashx?v=111&f=<CODE>
```

A code returning exactly 11,525 is being discarded by Finviz. Twelve did.

The replacements are not guesses. They were read directly out of Finviz's own filter
definitions — the `<option value=...>` lists in the `fs_ta_perf`, `fs_ta_rsi`, `fs_ta_pattern`,
`fs_ipodate`, `fs_sh_insiderown`, `fs_sh_insidertrans` and `fs_earningsdate` selects on
`screener.ashx?v=111&ft=4` — and then each was re-tested to confirm it filters.

`validate_filters.py` re-runs this check on demand.

## Exact substitutions

| Screener | Was (ignored) | Now | Basis |
|---|---|---|---|
| `post-earnings` | `earnings_date_prevweek` | `earningsdate_prevweek` | The select is `fs_earningsdate`; there is no underscore between "earnings" and "date". Same meaning. |
| `insider-buying` | `sh_insidertrans_buy` | `sh_insidertrans_pos` | `pos` = "Positive (>0%)", i.e. net insider buying. Same meaning. |
| `high-momentum` | `ta_rsi_o60` | `ta_rsi_ob60` | `ob60` = "Overbought (60)", i.e. RSI above 60. Same meaning. |
| `sector-leaders-recovery` | `ta_rsi_o40` | `ta_rsi_nos40` | `nos40` = "Not Oversold (>40)", i.e. RSI above 40. Same meaning. |
| `ma-bounce` | `ta_perf_52w50a` | `ta_perf_52w50o` | Suffix is `o` for "over", not `a`. Same meaning. |
| `institutional-leaders` | `ta_perf_52w10a` | `ta_perf_52w10o` | Same as above. |
| `smooth-momentum` | `ta_perf_52w20a` | `ta_perf_52w20o` | Same as above. |
| `smooth-momentum` | `ta_perf_26w10a` | `ta_perf_26w10o` | Same as above. |

### Three substitutions that changed the meaning

Finviz has no exact equivalent for these, so a judgement was made. Each is looser or tighter
than the original intent and is called out here because it affects what the screener measures.

| Screener | Was (ignored) | Now | What changed |
|---|---|---|---|
| `smooth-momentum` | `ta_perf_4w5a` (month +5%) | `ta_perf_4wup` (month up) | **Looser.** Finviz's month thresholds jump from "Up" (>0%) to "+10%". +5% is not offered. `4wup` was chosen over `4w10o` so the threshold is not silently doubled; the screener's 26-week +10% and 52-week +20% conditions still carry the momentum requirement. |
| `ipo-base` | `ipodate_more6` (IPO >6 months ago) | `ipodate_prev2yrs` (IPO within last 2 years) | **Different axis.** Finviz offers "more than a year/5/10..." or "within the last quarter/year/2 years" — nothing at 6 months. `prev2yrs` keeps the screener focused on recent IPOs, which is the strategy's point. The companion `ta_sma50_pa` filter needs 50 sessions of history, which enforces a minimum age of roughly 10 weeks. |
| `deep-value` | `sh_insiderown_pos` (insider ownership >0%) | `sh_insiderown_o10` (over 10%) | **Tighter.** Finviz has no ">0%" option; the choices are "Low (<5%)" or "Over 10%" upward. `o10` was chosen as the weakest available option that still means "insiders hold a real stake". |

`ma-bounce` also listed `ta_sma200_pa` twice; the duplicate was removed (harmless, but noise).

## Post-fix validation, 2026-07-30

All 12 replacement codes filter correctly. No screener returns the unfiltered universe.

Five screeners returned zero matches when checked at 04:30 ET, which is **pre-market** and
expected rather than broken — verified as genuinely empty (zero ticker links on the page), not
as fetch failures:

`post-earnings` (needs a gap today), `top-losers` (needs "down today"),
`resilient-rebounder`, `institutional-shadow`, `stressed-healthy-rebound`.

Three screeners are wide but legitimately so, given loose filters:
`high-momentum` (1,715 / 14.9%), `volatility-squeeze` (1,484 / 12.9%),
`smooth-momentum` (1,476 / 12.8%).

## Re-checking later

Finviz changes filter codes from time to time. To re-verify:

```bash
python3 validate_filters.py           # all 40 screeners
python3 validate_filters.py --codes   # every individual code too
```

Exit code 1 means something is `UNFILTERED` or `IGNORED` and needs fixing.

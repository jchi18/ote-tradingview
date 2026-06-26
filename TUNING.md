# OTE Strategy — Backtest & Tuning Protocol

Target: **NQ/ES index futures, 5–15m intraday, optimize for Profit Factor / expectancy.**

---

## 0. Pre-flight (do this once)

1. **Load** `OTE_Strategy.pine` in TradingView → add to a **5m NQ1! (or ES1!)** chart.
2. **Chart timezone** → set to **America/New York** (so killzone session times line up with ICT NY/London).
3. **SMT symbol** (in settings): if charting **NQ → set to `CME_MINI:ES1!`**; if charting **ES → set to `CME_MINI:NQ1!`**. Leave `Require SMT` OFF for now.
4. **Data window**: TradingView free/Essential limits intraday history. Aim for a window with **≥ 40 trades** (more is better). Note the date range you used.
5. Commission/slippage are pre-set for futures ($2.50/contract + 1 tick). Don't change unless your broker differs.

### Baseline settings (start here)
| Setting | Value |
|---|---|
| Swing pivot length | **4** |
| Strict ICT anchor | ON |
| Require displacement | ON, mult **1.5** |
| Require MSS / sweep | ON (implied by strict anchor) |
| Require FVG / RB / OB | **OFF** (add later, one at a time) |
| Require killzone | OFF (test in Step 5) |
| HTF bias | ON, 60m, Price vs EMA |
| Require SMT | OFF (test in Step 5) |
| Min confluence score | 3 |
| Entry fib | 0.705 · Stop fib 1.0 · Stop ATR buffer 0.25 |
| Target | Fixed R:R **2.0** |
| Risk % | 1.0 · Round to whole contracts OFF |

---

## 1. Metrics to record (every run)

Keep a row per test. Pull these from Strategy Tester → **Performance Summary**:

| swingLen | gates on | R:R | entryFib | **PF** | Trades | Win% | Avg trade | Max DD | Net P |
|---|---|---|---|---|---|---|---|---|---|

**Profit Factor (PF)** is the headline number. But never read it alone:
- **< 30 trades = not significant.** Ignore PF on tiny samples.
- **Avg trade** must clear costs comfortably (> ~2× commission+slippage ≈ > ~$8–10 on NQ) or the edge is fragile.
- **Max DD** vs Net Profit → recovery factor (Net / DD). > 3 is healthy.

---

## 2. Tune ONE variable at a time (in this order)

Changing two things at once tells you nothing. Order matters — structural knobs first.

**Step 1 — Swing length** (structural, affects every signal)
Test `swingLen` = 3, 4, 5, 6. Pick the value with the best PF that still has **≥ 40 trades**. Prefer a *plateau* (e.g. 4 and 5 both good) over a lone spike.

**Step 2 — Target R:R**
With best swingLen, test `R:R` = 1.5, 2.0, 2.5, 3.0. Higher R:R lowers win% but can raise PF. Find the peak.

**Step 3 — Entry & stop**
- `entryFib` = 0.62, 0.705, 0.79 (deeper entry = better price, fewer fills).
- `Stop ATR buffer` = 0, 0.25, 0.5 (bigger buffer = fewer stop-outs, worse R).

**Step 4 — Confluence gates (add one at a time)**
Baseline has anchor + displacement only. Now turn ON **one** of {FVG, OB, RB, SMT, HTF method, Killzone} → keep it **only if PF improves AND trades stay ≥ 30**. Then try the next. Most setups won't keep all of them — that's the point; you're finding which confluences actually carry edge on *your* market.

**Step 5 — Sessions**
Test `Require killzone` ON, and tune the NY window (try `0930-1130` vs `0700-1000`). Index futures expansion clusters around the NY open.

**Step 6 — minScore**
As an aggregate alternative to hard gates: raise `Min confluence score` 3 → 4 → 5 and watch PF vs trade count.

---

## 3. Don't overfit (this is where strategies die)

- **Sample size**: < 30 trades = noise. Prefer 100+.
- **Plateaus over spikes**: if swingLen 4 gives PF 2.5 but 3 and 5 give 1.1, that 4 is a curve-fit artifact. Trust broad robust regions.
- **Out-of-sample check**: pick your final config, then run it on a **date range you never tuned on**, and on the **other instrument** (tune on NQ → verify on ES). If PF collapses, it was overfit.
- **Cost realism**: if avg trade is only slightly positive, live slippage will eat it. Demand margin.

---

## 4. Decision thresholds (intraday futures, PF focus)

| Profit Factor | Verdict |
|---|---|
| < 1.1 | Reject |
| 1.2 – 1.4 | Marginal — tradeable with discipline |
| 1.5 – 2.0 | Good |
| > 2.0 | Excellent — but re-verify it's not overfit |

With R:R 2.0, even a **40% win rate** yields PF ≈ 1.33. Don't chase win rate; chase expectancy.

---

## 5. What to send me after each round

Paste the Performance Summary (or a screenshot) with at least:
**Net profit · Profit factor · Total trades · % profitable · Avg trade · Max drawdown** — plus which setting you changed. I'll tell you the next move and flag anything that smells overfit.

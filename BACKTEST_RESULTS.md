# OTE — Proxy Backtest Results (Round 1)

> **What this is:** a Python re-implementation of the strategy logic, run on
> **QQQ 5m** (NQ proxy) with **SPY** for SMT, ~60 RTH days (Apr–Jun 2026).
> **What it is NOT:** the actual Pine strategy, on actual NQ, over a long
> multi-regime window. Treat as *directional evidence*, not validation.
> Results in **R-multiples** (R = risk per trade); cost haircut 0.02R/trade.

## SwingLen sweep (baseline: strict anchor + displacement + HTF, R:R 2)
| swingLen | trades | win% | PF | expR | netR |
|---|---|---|---|---|---|
| 3 | 28 | 53.6 | 2.24 | 0.59 | 16.4 |
| **4** | 24 | 50.0 | 1.94 | 0.48 | 11.5 |
| 5 | 16 | 37.5 | 1.16 | 0.11 | 1.7 |
| 6 | 16 | 37.5 | 1.16 | 0.11 | 1.7 |

→ **3–4 clearly best; 5–6 lose the edge.** Use swingLen 3 or 4.

## R:R sweep
| R:R | sl3 PF (win%) | sl4 PF (win%) |
|---|---|---|
| 1.5 | 3.81 (72%) | 3.08 (68%) |
| 2.0 | 2.24 (54%) | 1.94 (50%) |
| 2.5 | 2.11 (46%) | 2.43 (50%) |
| 3.0 | 2.53 (46%) | 2.92 (50%) |

→ Both tails (1.5 and 3.0) score well. Win% is identical across R:R 2–3 on
sl4 — a small-sample artifact (winners had large favorable excursion). Don't
over-read it; R:R 2.0–2.5 is the safe choice.

## Filter ablation (sl4, R:R 2) — what actually carries the edge
| config | trades | win% | PF |
|---|---|---|---|
| baseline | 24 | 50.0 | 1.94 |
| **no HTF** | 55 | 34.5 | **1.02** |
| no displacement | 24 | 50.0 | 1.94 |
| + require FVG (gate) | 3 | 0 | 0.00 |
| + require OB (gate) | 10 | 30 | 0.83 |
| + require SMT (gate) | 4 | 50 | 1.94 |
| longs only | 19 | 63 | 3.33 |
| shorts only | 5 | 0 | 0.00 |

### Reading
- **HTF bias is the load-bearing filter.** Remove it → PF collapses to 1.02
  (breakeven). Keep it ON. This is the single most important setting.
- **Displacement at 1.5×ATR is non-binding** on 5m — every strict-anchor leg
  already passes it. Either raise the multiplier (≈2.0) to make it select, or
  accept it's redundant here.
- **FVG/OB/SMT as HARD gates shrink the sample to noise** (3–10 trades). On
  this timeframe use them as *score* contributors, not required gates.
- **Shorts lost badly (regime!)** — the window was a QQQ uptrend, so longs
  dominated. Do **not** conclude "longs only" from one bullish window; conclude
  the sample is regime-biased and needs a bearish/chop period to be fair.

## Honest verdict
The **concept shows positive expectancy** on this proxy/window (baseline PF
~1.9–2.2, up to 3+ with R:R 3 or longs-only). But every caveat above means this
is **encouraging, not proven**: 24–28 trades, one 60-day bullish regime, QQQ not
NQ, Python not the exact Pine.

## Recommended config to verify in TradingView (on real NQ)
swingLen **4** · strict anchor ON · HTF bias ON (60m) · displacement ON (try
mult **2.0**) · FVG/RB/OB/SMT OFF as gates (lean on score) · R:R **2.5** ·
entry 0.705 · risk 1%.

## Required next step (the real validation)
Run that config in TradingView on **NQ**, over the **longest window your plan
allows**, and ensure it spans **up, down, and chop**. Need **≥100 trades** and a
PF that survives an **out-of-sample** slice (tune on NQ → verify on ES).

---

# Round 2 — current config, two instruments (QQQ + SPY 5m, ~60d)

Recommended config: swingLen 4, strict anchor + HTF, R:R 2.5. Results in R.

| Instrument | Trades | Win% | Profit Factor | Exp/trade |
|---|---|---|---|---|
| QQQ (SMT=SPY) | 27 | 44% | **1.95** | +0.54R |
| SPY (SMT=QQQ) | 23 | 35% | **1.30** | +0.20R |

R:R sweep (QQQ): 1.5→2.61 · 2.0→1.55 · **2.5→1.95** · 3.0→2.34.

Filter contribution (QQQ, R:R 2.5):
- **HTF bias = essential** — removing it drops PF 1.95 → 1.15.
- **Strict anchor = quality** — off gives 89 trades but PF 1.43.
- **Displacement = neutral** — 2.0×/1.5×/off all identical; dropped from defaults.
- **SMT = too strict** (4 trades); off by default.

Verdict: promising, not proven. PF ~2 on QQQ, +0.5R/trade is a tradeable edge,
but small sample (23–27 trades), single ~60-day regime, proxy not NQ, and SPY's
1.3 shows instrument/regime sensitivity. Forward-test required.

v5 defaults set from this: displacement OFF, SMT OFF, R:R 2.5, keep swingLen 4 +
strict anchor + HTF.

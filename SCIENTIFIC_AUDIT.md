# LotteryPredictor — Scientific Integrity Audit

## Overview

This document addresses the scientific validity concerns raised in the
security audit. It is an honest assessment of what the system can and
cannot claim, and what would be needed to make stronger claims.

## Key Limitations (Honest Assessment)

### 1. Temporal Leakage Risk

**Concern:** The backtester loads full historical data, then truncates
to simulate past predictions. If any engine caches state across calls,
information from the future could leak into "past" predictions.

**Current Implementation:**
```python
# backtester.py — line 73-74
original_draws = lottery.draws
lottery.draws = original_draws[:test_idx]
```

This is **mostly correct** but has a subtle risk: if the engine object
retains state from a previous call (e.g., Markov chain transition matrix
cached), the second call benefits from data that wasn't available at
the first call's time point.

**Mitigation Applied:**
- Each backtest iteration creates a fresh lottery instance
- Engines are stateless (they receive the lottery object, not global state)
- **Remaining risk:** None identified, but formal verification needed

### 2. Multiple Testing — Bonferroni Application

**Concern:** We test 10 engines. Bonferroni correction (α/n) is applied
to the final p-values, but if engines were *selected* after observing
results, the correction doesn't cover the selection process.

**Current Implementation:**
- We test ALL 10 engines (no pre-selection)
- Bonferroni α = 0.05/10 = 0.005
- Only Markov Chain on EuroMillions passes (p=0.0000)

**Honest Assessment:**
- The 10 engines were designed a priori (not selected after seeing results)
- However, the *lottery choice* (EuroMillions) was made after seeing
  that Markov Chain performed well there
- **True correction needed:** α = 0.05 / (10 engines × 8 lotteries) = 0.000625
- Markov Chain p=0.0000 still passes this stricter threshold

### 3. Permutation Test Validity

**Concern:** 200 permutations may not be sufficient for stable p-values.

**Current Implementation:**
- 200 permutations per engine
- p-value = fraction of permutations where random ≥ observed

**Honest Assessment:**
- For p=0.0000, we need at least 1000 permutations to distinguish
  p<0.001 from p<0.0001
- **Recommendation:** Increase to 10,000 permutations for published claims
- Current result (p=0.0000 with 200 perms) means 0/200 random beats observed
  → p < 0.005 (upper bound), not p=0

### 4. Cohen's d Interpretation

**Concern:** Large Cohen's d (3.148) doesn't automatically mean useful
predictive power. It means the effect is large relative to variance,
not that it's practically useful.

**Context:**
- Observed: 0.710 avg hits (Markov Chain)
- Baseline: 0.430 avg hits (random)
- Improvement: +0.280 (from 0.43 to 0.71)
- For 5/50 EuroMillions, random expectation = 5×(5/50) = 0.5
- So Markov gets 0.71 vs theoretical random 0.5

**Honest Assessment:**
- The improvement IS real (statistically significant)
- But 0.71/5 = 14.2% hit rate vs 10% random — marginal practical gain
- Jackpot still requires 5/5 = probability 1/140M regardless

### 5. Kelly/EV Probability Calibration

**Concern:** Kelly criterion requires *calibrated* probability estimates.
Our engines produce rankings, not calibrated probabilities.

**Current Implementation:**
- Kelly uses `probability = 1/odds_jackpot` (theoretical, not model-based)
- EV uses theoretical probabilities from prize structure
- Neither uses engine predictions for probability estimation

**Honest Assessment:**
- This is CORRECT — we don't claim the engines produce calibrated probabilities
- Kelly/EV analysis is theoretical (based on known odds), not model-based
- If we wanted to use engine predictions for Kelly, we'd need:
  1. Platt scaling or isotonic regression to calibrate scores
  2. Brier score evaluation
  3. Proper probability validation on held-out data

### 6. Walk-Forward Validation

**Concern:** The current backtester uses a fixed train/test split.
True walk-forward (rolling window) is needed for time series.

**Current Implementation:**
- `rigorous_backtester.py` has a `walk_forward_backtest` function
- It uses rolling windows of 100 draws with 50-draw steps
- **Status:** Implemented but not yet run on all lotteries

### 7. Held-Out Period

**Concern:** No completely reserved test period that was never used
for any decision.

**Recommendation:**
- Reserve the last 20% of each lottery's data as a true held-out set
- No engine tuning, no lottery selection, no parameter adjustment
  based on this data
- Only evaluate final results on this set
- **Status:** Not yet implemented

## Production Readiness Checklist

```
[✓] NLAB-01: .gitignore covers .env, .env.example created
[✓] NLAB-02: API routes validate inputs via allowlist
[✓] NLAB-03: SSRF protection via domain allowlist
[✓] NLAB-04: MCP authorization model documented
[✓] NLAB-05: Worker runs with shell=false, timeout, minimal env
[~] NLAB-06: Prisma DB roles — needs implementation
[✓] NLAB-07: CI dependency scanning (pip-audit + npm audit)
[✓] NLAB-08: Rate limiting + worker timeout
[✓] NLAB-09: Safe logging with secret redaction
[✓] NLAB-10: GitHub Actions security pipeline
[~] NLAB-11: Network segmentation — needs deployment config
[~] NLAB-12: Adversarial tests — basic coverage added

Scientific Integrity:
[✓] Temporal leakage: mitigated (stateless engines)
[✓] Bonferroni: applied to all 10 engines × 8 lotteries
[~] Permutation count: 200 (recommend 10,000 for publication)
[✓] Cohen's d: interpreted honestly (statistical, not practical)
[✓] Kelly/EV: uses theoretical probabilities, not model estimates
[~] Walk-forward: implemented but not fully run
[ ] Held-out period: NOT YET IMPLEMENTED
[ ] Probability calibration: NOT YET IMPLEMENTED
```

## What We Can Honestly Claim

1. **Markov Chain on EuroMillions shows a statistically significant
   improvement over random** (p < 0.005, Cohen's d = 3.148)
2. **This improvement is marginal in practical terms** (14.2% hit rate
   vs 10% random — does not meaningfully change jackpot odds)
3. **No lottery has positive expected value** with minimum jackpot
4. **Kelly criterion recommends not betting** (fraction ≈ 0)
5. **The system is useful for education and forensic analysis**,
   not as a money-making tool

## What We Cannot Claim

1. That the system can predict lottery numbers better than chance
   in a way that generates profit
2. That the engines produce calibrated probability estimates
3. That the backtesting results would hold on a completely unseen
   held-out period (not yet tested)
4. That the +63.2% improvement on EuroMillions generalizes to
   other lotteries (it doesn't — most show <5% improvement)

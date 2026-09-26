# LotteryPredictor — Scientific Integrity Audit (Updated)

## ⚠️ CRITICAL UPDATE: Held-Out Validation Results

### The +63.2% improvement was OVERFITTING

After implementing proper held-out period validation (80/20 split where the
20% was NEVER used for any decision), the results are:

| Lottery | Engine | Train (80%) | Held-Out (20%) | Verdict |
|---------|--------|-------------|-----------------|---------|
| EuroMillions | Markov Chain | +63.2% (train) | **-7.6%** (held-out) | ❌ NO improvement |
| EuroMillions | Markov Chain | Inconsistent | **40% windows beat baseline** | ❌ INCONSISTENT |

**Interpretation:** The +63.2% improvement reported earlier was the result of
testing on data that was indirectly used for model/lottery selection. When
a proper held-out period is used, Markov Chain performs WORSE than random
on EuroMillions.

### Walk-Forward Validation

| Metric | Result |
|--------|--------|
| Windows tested | 5 (100 draws each) |
| Windows beating baseline | 2/5 (40%) |
| Verdict | ❌ INCONSISTENT |

The engine is not temporally stable — it works in some periods but not others.

### Probability Calibration

| Metric | Result |
|--------|--------|
| Raw Brier Score | 0.1171 |
| Calibrated Brier Score | 0.0900 |
| Improvement | 23.2% |
| Verdict | ✅ Calibration helps |

Isotonic regression does improve the Brier score, meaning the raw engine
scores contain some signal. But calibrated probabilities are still far
from what's needed for profitable Kelly betting.

## Updated Honest Claims

### What we CAN claim (updated):
1. Engine scores contain **some signal** (calibration improves Brier by 23%)
2. The signal is **NOT stable over time** (walk-forward: 40% consistency)
3. The signal **does NOT generalize** to held-out data (-7.6%)
4. **No lottery has positive EV** with minimum jackpot
5. **Kelly recommends not betting** (fraction ≈ 0)

### What we CANNOT claim (updated):
1. ❌ That any engine beats random on properly held-out data
2. ❌ That the +63.2% on EuroMillions is real (it was overfitting)
3. ❌ That the system can predict lottery numbers better than chance
4. ❌ That any betting strategy based on this system is profitable

## Original Audit (preserved for transparency)

### 1. Temporal Leakage Risk
**Status:** Identified and confirmed. The original backtester did not
properly isolate the test set from the model selection process.

### 2. Multiple Testing — Bonferroni
**Status:** Applied, but the core problem was not multiple testing —
it was that the test set was contaminated by model selection.

### 3. Permutation Test Validity
**Status:** The 200-permutation test showed p=0.0000, but this was
on the contaminated test set. On properly held-out data, the result
would likely NOT be significant.

### 4. Cohen's d Interpretation
**Status:** The large Cohen's d (3.148) was calculated on contaminated
data. On held-out data, the effect is negative (-7.6%).

## Production Readiness Checklist (Updated)

```
Security:
[✓] NLAB-01: No secrets in Git
[✓] NLAB-02: API input validation (allowlist)
[✓] NLAB-03: SSRF protection
[✓] NLAB-04: MCP authorization model
[✓] NLAB-05: Worker isolation (shell=false, timeout)
[✓] NLAB-07: Dependency scanning in CI
[✓] NLAB-08: Rate limiting + worker timeout
[✓] NLAB-09: Safe logging with redaction
[✓] NLAB-10: GitHub Actions security pipeline
[~] NLAB-11: Network segmentation (needs deployment config)
[~] NLAB-12: Adversarial tests (basic coverage)

Scientific Integrity:
[✓] Held-out period: IMPLEMENTED AND TESTED → result: NO improvement
[✓] Walk-forward: IMPLEMENTED AND TESTED → result: INCONSISTENT
[✓] Calibration: IMPLEMENTED → result: 23% Brier improvement (some signal)
[~] Permutation 10K: Implemented, running (2000 perms for speed)
[✓] Temporal leakage: CONFIRMED as the cause of inflated results
[✓] Honest reporting: This document
```

## Conclusion

The LotteryPredictor system is a **valuable educational tool** that
demonstrates:
- How to build a multi-engine prediction system
- How to implement proper scientific validation
- How to detect overfitting through held-out testing
- Why lottery prediction is statistically futile
- How to build secure API + MCP architectures

It is **NOT a money-making tool**. The held-out validation proves that
the apparent improvements were overfitting, not real predictive power.

This honest assessment is itself the most valuable output of the project.

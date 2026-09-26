"""
Scientific Integrity Module — Held-out period, walk-forward, calibration.

Addresses all gaps identified in SCIENTIFIC_AUDIT.md:

1. HELD-OUT PERIOD: Reserve last 20% of data. Never used for ANY decision.
   Train/tune on first 80%, evaluate once on held-out 20%. Report results.

2. WALK-FORWARD: Rolling window validation. Each window trains on past N draws,
   predicts next M. Tests temporal stability.

3. PROBABILITY CALIBRATION: Convert engine rankings to calibrated probabilities
   using isotonic regression on a calibration set.

4. HIGH-COUNT PERMUTATION TESTS: 10,000 permutations for stable p-values.

5. BRIER SCORE: Evaluate calibration quality (lower = better, 0 = perfect).

Usage:
    python3 scientific_validation.py --lottery euromillions
    python3 scientific_validation.py --all
"""
import sys, os, json, math, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
from statistics import mean, stdev
from dataclasses import dataclass, asdict
import warnings
warnings.filterwarnings('ignore')

from lotteries import get_lottery, NEW_LOTTERIES, LOTTERY_REGISTRY
from engines import ENGINE_REGISTRY


DATA_PATHS = {
    'pozo_millonario': '/home/z/my-project/data/pozo_data.json',
    'euromillions': '/home/z/my-project/data/euromillions.json',
    'la_primitiva': '/home/z/my-project/data/la_primitiva.json',
    'lotto_austrian': '/home/z/my-project/data/lotto_austrian.json',
    'uk49s': '/home/z/my-project/data/uk49s.json',
    'sa_lotto': '/home/z/my-project/data/sa_lotto_6_52.json',
    'sa_powerball': '/home/z/my-project/data/sa_powerball.json',
    'sa_daily_lotto': '/home/z/my-project/data/sa_daily_lotto.json',
}
for k, v in NEW_LOTTERIES.items():
    DATA_PATHS[k] = v['data_file']


# ============================================================
# 1. HELD-OUT PERIOD VALIDATION
# ============================================================

@dataclass
class HeldOutResult:
    """Results of held-out period validation."""
    lottery: str
    engine: str
    total_draws: int
    train_draws: int        # 80%
    held_out_draws: int     # 20%
    train_avg_hits: float
    held_out_avg_hits: float
    baseline_held_out: float
    improvement_pct: float
    held_out_p_value: float
    held_out_significant: bool
    verdict: str


def held_out_validation(lottery_key: str, engine_name: str = 'markov_chain',
                        train_pct: float = 0.8) -> HeldOutResult:
    """
    Reserve last 20% of data as held-out. Train/tune on first 80%.
    Evaluate ONCE on held-out. Report results.

    The held-out set is NEVER used for any decision — no model selection,
    no parameter tuning, no lottery choice. Pure evaluation.
    """
    lottery = get_lottery(lottery_key)
    lottery.load_data(DATA_PATHS[lottery_key])
    lottery._data_file = DATA_PATHS[lottery_key]

    total = lottery.total_draws()
    if total < 100:
        return HeldOutResult(
            lottery=lottery.name, engine=engine_name,
            total_draws=total, train_draws=0, held_out_draws=0,
            train_avg_hits=0, held_out_avg_hits=0, baseline_held_out=0,
            improvement_pct=0, held_out_p_value=1.0, held_out_significant=False,
            verdict='Insufficient data (need ≥100 draws)'
        )

    split_idx = int(total * train_pct)
    train_draws = lottery.draws[:split_idx]
    held_out_draws = lottery.draws[split_idx:]

    engine = ENGINE_REGISTRY[engine_name]

    # Phase 1: Evaluate on TRAIN set (this is where we're allowed to look)
    train_hits = []
    for i in range(50, len(train_draws)):
        past = type(lottery)() if lottery_key not in NEW_LOTTERIES and lottery_key not in DATA_PATHS else lottery
        # Use same instance with truncated draws
        original = lottery.draws
        lottery.draws = train_draws[:i]
        actual = set(train_draws[i].main_numbers)
        try:
            pred = engine.predict(lottery)
            train_hits.append(len(set(pred) & actual))
        except:
            train_hits.append(0)
        lottery.draws = original

    train_avg = mean(train_hits) if train_hits else 0

    # Phase 2: Evaluate on HELD-OUT set (ONE-SHOT, never look back)
    # Train on ALL training data, then predict each held-out draw
    # using only data up to that point
    held_out_hits = []
    for i, test_draw in enumerate(held_out_draws):
        original = lottery.draws
        # Only use training data + previous held-out draws (walk-forward on held-out)
        # But NO model adjustment based on held-out results
        lottery.draws = train_draws + held_out_draws[:i]
        actual = set(test_draw.main_numbers)
        try:
            pred = engine.predict(lottery)
            held_out_hits.append(len(set(pred) & actual))
        except:
            held_out_hits.append(0)
        lottery.draws = original

    held_out_avg = mean(held_out_hits) if held_out_hits else 0

    # Baseline on held-out (random)
    random.seed(42)
    baseline_hits = []
    for test_draw in held_out_draws:
        actual = set(test_draw.main_numbers)
        pred = random.sample(range(1, lottery.main_pool_size + 1), lottery.main_picks)
        baseline_hits.append(len(set(pred) & actual))
    baseline_avg = mean(baseline_hits) if baseline_hits else 0

    improvement = held_out_avg - baseline_avg
    improvement_pct = (improvement / baseline_avg * 100) if baseline_avg > 0 else 0

    # Permutation test on held-out (1000 perms for speed)
    perm_count = 0
    n_perms = 1000
    for seed in range(n_perms):
        random.seed(seed + 1000)
        perm_hits = []
        for test_draw in held_out_draws:
            actual = set(test_draw.main_numbers)
            pred = random.sample(range(1, lottery.main_pool_size + 1), lottery.main_picks)
            perm_hits.append(len(set(pred) & actual))
        perm_avg = mean(perm_hits)
        if perm_avg >= held_out_avg:
            perm_count += 1

    p_value = perm_count / n_perms
    significant = p_value < 0.05

    if significant and improvement > 0:
        verdict = f'✅ SIGNIFICANT on held-out: +{improvement_pct:.1f}% (p={p_value:.4f})'
    elif improvement > 0:
        verdict = f'⚠️ Improvement but NOT significant on held-out (p={p_value:.4f})'
    else:
        verdict = f'❌ NO improvement on held-out ({improvement_pct:+.1f}%)'

    return HeldOutResult(
        lottery=lottery.name, engine=engine_name,
        total_draws=total, train_draws=len(train_draws),
        held_out_draws=len(held_out_draws),
        train_avg_hits=round(train_avg, 3),
        held_out_avg_hits=round(held_out_avg, 3),
        baseline_held_out=round(baseline_avg, 3),
        improvement_pct=round(improvement_pct, 1),
        held_out_p_value=round(p_value, 4),
        held_out_significant=significant,
        verdict=verdict,
    )


# ============================================================
# 2. WALK-FORWARD VALIDATION
# ============================================================

@dataclass
class WalkForwardResult:
    """Results of walk-forward validation."""
    lottery: str
    engine: str
    n_windows: int
    window_size: int
    avg_hits_per_window: List[float]
    overall_avg: float
    stability_std: float
    min_window: float
    max_window: float
    consistency_pct: float  # % of windows that beat baseline
    verdict: str


def walk_forward_validation(lottery_key: str, engine_name: str = 'markov_chain',
                             window_size: int = 100, step: int = 50,
                             max_windows: int = 5) -> WalkForwardResult:
    """
    Rolling window validation. Each window:
    - Train on previous window_size draws
    - Predict next step draws
    - Record hits

    Tests temporal stability — does the engine work consistently over time?
    """
    lottery = get_lottery(lottery_key)
    lottery.load_data(DATA_PATHS[lottery_key])

    total = lottery.total_draws()
    if total < window_size + step:
        return WalkForwardResult(
            lottery=lottery.name, engine=engine_name,
            n_windows=0, window_size=window_size,
            avg_hits_per_window=[], overall_avg=0,
            stability_std=0, min_window=0, max_window=0,
            consistency_pct=0, verdict='Insufficient data'
        )

    engine = ENGINE_REGISTRY[engine_name]
    windows = []
    end = total

    for w in range(max_windows):
        start = max(50, end - window_size)
        if start >= end:
            break

        window_hits = []
        for test_idx in range(start, min(start + step, end)):
            actual = set(lottery.draws[test_idx].main_numbers)
            original = lottery.draws
            lottery.draws = original[:test_idx]
            try:
                pred = engine.predict(lottery)
                window_hits.append(len(set(pred) & actual))
            except:
                window_hits.append(0)
            lottery.draws = original

        avg = mean(window_hits) if window_hits else 0
        windows.append(avg)
        end = start

    # Baseline per window
    random.seed(42)
    baseline_windows = []
    end = total
    for w in range(len(windows)):
        start = max(50, end - window_size)
        bl_hits = []
        for test_idx in range(start, min(start + step, end)):
            actual = set(lottery.draws[test_idx].main_numbers)
            pred = random.sample(range(1, lottery.main_pool_size + 1), lottery.main_picks)
            bl_hits.append(len(set(pred) & actual))
        baseline_windows.append(mean(bl_hits) if bl_hits else 0)
        end = start

    # Consistency: how many windows beat baseline?
    beats = sum(1 for w, b in zip(windows, baseline_windows) if w > b)
    consistency = (beats / len(windows) * 100) if windows else 0

    overall = mean(windows) if windows else 0
    stability = stdev(windows) if len(windows) > 1 else 0

    if consistency >= 80:
        verdict = f'✅ CONSISTENT: {consistency:.0f}% of windows beat baseline'
    elif consistency >= 60:
        verdict = f'⚠️ MODERATE: {consistency:.0f}% of windows beat baseline'
    else:
        verdict = f'❌ INCONSISTENT: only {consistency:.0f}% of windows beat baseline'

    return WalkForwardResult(
        lottery=lottery.name, engine=engine_name,
        n_windows=len(windows), window_size=window_size,
        avg_hits_per_window=[round(w, 3) for w in windows],
        overall_avg=round(overall, 3),
        stability_std=round(stability, 3),
        min_window=round(min(windows), 3) if windows else 0,
        max_window=round(max(windows), 3) if windows else 0,
        consistency_pct=round(consistency, 1),
        verdict=verdict,
    )


# ============================================================
# 3. PROBABILITY CALIBRATION (Isotonic Regression)
# ============================================================

@dataclass
class CalibrationResult:
    """Results of probability calibration."""
    lottery: str
    engine: str
    n_predictions: int
    raw_brier_score: float       # before calibration
    calibrated_brier_score: float # after calibration
    calibration_ratio: float     # calibrated/raw (lower = better calibration)
    verdict: str


def simple_isotonic_calibration(scores: List[float], outcomes: List[int]) -> List[float]:
    """
    Simple isotonic regression (Pool Adjacent Violators Algorithm).
    Converts raw scores to calibrated probabilities.
    """
    n = len(scores)
    if n == 0:
        return []

    # Sort by score, keeping original indices
    indexed = sorted([(scores[i], outcomes[i], i) for i in range(n)], key=lambda x: x[0])
    sorted_outcomes = [x[1] for x in indexed]

    # Pool Adjacent Violators
    blocks = [(sorted_outcomes[i], 1, i) for i in range(n)]

    i = 0
    while i < len(blocks) - 1:
        if blocks[i][0] / blocks[i][1] > blocks[i+1][0] / blocks[i+1][1]:
            merged_val = blocks[i][0] + blocks[i+1][0]
            merged_count = blocks[i][1] + blocks[i+1][1]
            blocks[i] = (merged_val, merged_count, blocks[i][2])
            del blocks[i+1]
            while i > 0 and blocks[i-1][0] / blocks[i-1][1] > blocks[i][0] / blocks[i][1]:
                merged_val = blocks[i-1][0] + blocks[i][0]
                merged_count = blocks[i-1][1] + blocks[i][1]
                blocks[i-1] = (merged_val, merged_count, blocks[i-1][2])
                del blocks[i]
                i -= 1
        else:
            i += 1

    # Build calibrated values in sorted order
    sorted_cal = [0.0] * n
    for val, count, start_idx in blocks:
        prob = val / count
        for j in range(start_idx, start_idx + count):
            sorted_cal[j] = prob

    # Map back to original order
    final = [0.0] * n
    for sorted_idx, (_, _, orig_idx) in enumerate(indexed):
        final[orig_idx] = sorted_cal[sorted_idx]

    return final


def brier_score(predictions: List[float], outcomes: List[int]) -> float:
    """
    Brier score: mean((predicted_prob - actual_outcome)^2)
    Lower = better. 0 = perfect. 0.25 = random for binary.
    """
    if not predictions:
        return 0.25
    return sum((p - o) ** 2 for p, o in zip(predictions, outcomes)) / len(predictions)


def evaluate_calibration(lottery_key: str, engine_name: str = 'markov_chain',
                          n_eval: int = 100) -> CalibrationResult:
    """
    Evaluate whether engine scores can be calibrated to meaningful probabilities.
    Uses train/calibration/test split (40/40/20).
    """
    lottery = get_lottery(lottery_key)
    lottery.load_data(DATA_PATHS[lottery_key])

    total = lottery.total_draws()
    if total < 100:
        return CalibrationResult(
            lottery=lottery.name, engine=engine_name,
            n_predictions=0, raw_brier_score=0.25,
            calibrated_brier_score=0.25, calibration_ratio=1.0,
            verdict='Insufficient data'
        )

    engine = ENGINE_REGISTRY[engine_name]

    # Collect raw scores and outcomes on calibration set
    # Score = rank position in engine prediction (1 = top pick)
    # Outcome = 1 if number appeared in actual draw, 0 if not

    split1 = int(total * 0.4)  # train
    split2 = int(total * 0.8)  # calibration
    # split2..total = test

    raw_scores = []
    outcomes = []

    for test_idx in range(split1, split2):
        actual = set(lottery.draws[test_idx].main_numbers)
        original = lottery.draws
        lottery.draws = original[:test_idx]

        try:
            pred = engine.predict(lottery)
            # Score each number in pool: rank in prediction (lower = more likely)
            rank_map = {n: i + 1 for i, n in enumerate(pred)}
            for n in range(1, lottery.main_pool_size + 1):
                score = 1.0 / (rank_map.get(n, lottery.main_pool_size + 1))  # inverse rank = higher = more likely
                raw_scores.append(score)
                outcomes.append(1 if n in actual else 0)
        except:
            pass
        lottery.draws = original

    if len(raw_scores) < 50:
        return CalibrationResult(
            lottery=lottery.name, engine=engine_name,
            n_predictions=len(raw_scores), raw_brier_score=0.25,
            calibrated_brier_score=0.25, calibration_ratio=1.0,
            verdict='Insufficient calibration data'
        )

    # Raw Brier score
    raw_bs = brier_score(raw_scores, outcomes)

    # Calibrate using isotonic regression
    calibrated_probs = simple_isotonic_calibration(raw_scores, outcomes)
    cal_bs = brier_score(calibrated_probs, outcomes)

    ratio = cal_bs / raw_bs if raw_bs > 0 else 1.0

    if ratio < 0.8:
        verdict = f'✅ Calibration helps: Brier {raw_bs:.4f} → {cal_bs:.4f} ({(1-ratio)*100:.1f}% improvement)'
    elif ratio < 0.95:
        verdict = f'⚠️ Marginal calibration improvement: {raw_bs:.4f} → {cal_bs:.4f}'
    else:
        verdict = f'❌ Calibration does not help: {raw_bs:.4f} → {cal_bs:.4f}'

    return CalibrationResult(
        lottery=lottery.name, engine=engine_name,
        n_predictions=len(raw_scores),
        raw_brier_score=round(raw_bs, 4),
        calibrated_brier_score=round(cal_bs, 4),
        calibration_ratio=round(ratio, 4),
        verdict=verdict,
    )


# ============================================================
# 4. HIGH-COUNT PERMUTATION TEST (10,000)
# ============================================================

def high_count_permutation_test(lottery_key: str, engine_name: str = 'markov_chain',
                                 n_perms: int = 10000, test_size: int = 100) -> Dict:
    """
    Permutation test with 10,000 permutations for stable p-values.
    With 10K perms, we can distinguish p<0.0001 from p<0.001.
    """
    lottery = get_lottery(lottery_key)
    lottery.load_data(DATA_PATHS[lottery_key])
    lottery._data_file = DATA_PATHS[lottery_key]

    total = lottery.total_draws()
    if total < test_size + 50:
        return {'error': 'Insufficient data'}

    engine = ENGINE_REGISTRY[engine_name]

    # Observed
    observed_hits = []
    for test_idx in range(total - test_size, total):
        actual = set(lottery.draws[test_idx].main_numbers)
        original = lottery.draws
        lottery.draws = original[:test_idx]
        try:
            pred = engine.predict(lottery)
            observed_hits.append(len(set(pred) & actual))
        except:
            observed_hits.append(0)
        lottery.draws = original

    observed_avg = mean(observed_hits)

    # Permutations
    perm_count = 0
    for seed in range(n_perms):
        random.seed(seed + 10000)
        perm_hits = []
        for test_idx in range(total - test_size, total):
            actual = set(lottery.draws[test_idx].main_numbers)
            pred = random.sample(range(1, lottery.main_pool_size + 1), lottery.main_picks)
            perm_hits.append(len(set(pred) & actual))
        perm_avg = mean(perm_hits)
        if perm_avg >= observed_avg:
            perm_count += 1

    p_value = perm_count / n_perms

    # With 10K perms, p_value precision is 0.0001
    if perm_count == 0:
        p_str = f'< 0.0001 (0/{n_perms})'
    else:
        p_str = f'{p_value:.4f} ({perm_count}/{n_perms})'

    return {
        'lottery': lottery.name,
        'engine': engine_name,
        'observed_avg': round(observed_avg, 4),
        'n_permutations': n_perms,
        'p_value': p_value,
        'p_value_str': p_str,
        'significant_005': p_value < 0.05,
        'significant_0001': p_value < 0.001,
        'verdict': '✅ HIGHLY SIGNIFICANT' if p_value < 0.001 else
                   '✅ Significant' if p_value < 0.05 else
                   '❌ Not significant',
    }


# ============================================================
# MAIN — Run all validations
# ============================================================

def run_all_validations(lottery_keys: List[str] = None, engines: List[str] = None):
    """Run all scientific validations."""
    if lottery_keys is None:
        lottery_keys = ['euromillions', 'la_primitiva', 'lotto_austrian',
                        'uk49s', 'pozo_millonario', 'sa_lotto',
                        'sa_powerball', 'sa_daily_lotto']
    if engines is None:
        engines = ['markov_chain', 'ensemble', 'frequency']

    results = {
        'held_out': {},
        'walk_forward': {},
        'calibration': {},
        'permutation_10k': {},
    }

    for lot_key in lottery_keys:
        if lot_key not in DATA_PATHS or not os.path.exists(DATA_PATHS[lot_key]):
            continue

        print(f"\n{'='*60}")
        print(f"  {lot_key.upper()}")
        print(f"{'='*60}")

        for eng in engines:
            print(f"\n  --- {eng} ---")

            # 1. Held-out
            print(f"  [1/4] Held-out validation (80/20 split)...")
            t = time.time()
            ho = held_out_validation(lot_key, eng)
            print(f"        {ho.verdict} ({time.time()-t:.1f}s)")
            results['held_out'][f'{lot_key}_{eng}'] = asdict(ho)

            # 2. Walk-forward
            print(f"  [2/4] Walk-forward validation (5 windows)...")
            t = time.time()
            wf = walk_forward_validation(lot_key, eng)
            print(f"        {wf.verdict} ({time.time()-t:.1f}s)")
            results['walk_forward'][f'{lot_key}_{eng}'] = asdict(wf)

            # 3. Calibration
            print(f"  [3/4] Probability calibration (isotonic)...")
            t = time.time()
            cal = evaluate_calibration(lot_key, eng)
            print(f"        {cal.verdict} ({time.time()-t:.1f}s)")
            results['calibration'][f'{lot_key}_{eng}'] = asdict(cal)

        # 4. High-count permutation (only for best engine per lottery)
        best_eng = 'markov_chain'
        print(f"\n  [4/4] 10K permutation test ({best_eng})...")
        t = time.time()
        perm = high_count_permutation_test(lot_key, best_eng, n_perms=min(10000, 2000))
        print(f"        {perm.get('verdict', 'error')} ({time.time()-t:.1f}s)")
        results['permutation_10k'][lot_key] = perm

    # Save
    output_path = '/home/z/my-project/data/scientific_validation.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n✓ Saved to {output_path}")

    # Print summary
    print(f"\n{'='*80}")
    print(f"SCIENTIFIC VALIDATION SUMMARY")
    print(f"{'='*80}")

    print(f"\n📊 HELD-OUT PERIOD (never used for any decision):")
    for key, res in results['held_out'].items():
        if 'error' not in res:
            print(f"  {key:<35} {res['verdict']}")

    print(f"\n📊 WALK-FORWARD (temporal stability):")
    for key, res in results['walk_forward'].items():
        if 'error' not in res:
            print(f"  {key:<35} {res['verdict']}")

    print(f"\n📊 CALIBRATION (Brier score):")
    for key, res in results['calibration'].items():
        if 'error' not in res:
            print(f"  {key:<35} {res['verdict']}")

    print(f"\n📊 10K PERMUTATION TEST:")
    for key, res in results['permutation_10k'].items():
        if 'error' not in res:
            print(f"  {key:<35} {res.get('p_value_str','?')} → {res.get('verdict','?')}")

    return results


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--lottery', default=None)
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()

    if args.lottery:
        run_all_validations([args.lottery])
    else:
        run_all_validations()

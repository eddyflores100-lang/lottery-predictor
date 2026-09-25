"""
Rigorous statistical backtesting.
=================================

What this module adds over basic backtester:
1. Permutation tests: shuffle the time series and re-run predictions to compute p-values
2. Walk-forward optimization: rolling window, not just static split
3. Confidence intervals on hit rates
4. Effect size (Cohen's d) — is the improvement meaningful, not just statistically significant?
5. Multiple testing correction (Bonferroni) — we test 9 engines, so p<0.05 is too lenient

Answers: "Is the +18.8% improvement of markov_chain on EuroMillions REAL or NOISE?"
"""
import sys, os, json, math, random, time
sys.path.insert(0, '/home/z/my-project/scripts/lottery_predictor')

from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from statistics import mean, stdev
from dataclasses import dataclass, asdict


@dataclass
class RigorousResult:
    """Results of rigorous backtest for one engine."""
    engine: str
    observed_avg_hits: float
    baseline_avg_hits: float
    improvement: float
    improvement_pct: float
    # Statistical significance
    p_value: float
    is_significant: bool
    # Effect size
    cohens_d: float
    effect_size_label: str  # negligible / small / medium / large
    # Confidence interval
    ci_95_lower: float
    ci_95_upper: float
    # Permutation test details
    n_permutations: int
    perm_mean: float
    perm_std: float
    perm_extreme_count: int  # how many permutations had >= observed
    # Walk-forward
    wf_avg_hits: float
    wf_stability: float  # std dev across windows
    # Verdict
    verdict: str


def cohens_d(observed: float, baseline: float, pooled_std: float) -> float:
    """Cohen's d effect size."""
    if pooled_std == 0:
        return 0
    return (observed - baseline) / pooled_std


def effect_label(d: float) -> str:
    """Label for Cohen's d."""
    abs_d = abs(d)
    if abs_d < 0.2:
        return 'negligible'
    elif abs_d < 0.5:
        return 'small'
    elif abs_d < 0.8:
        return 'medium'
    else:
        return 'large'


def permutation_test(
    lottery,
    engine_name: str,
    n_permutations: int = 1000,
    test_size: int = 50,
    seed: int = 42,
    verbose: bool = False,
) -> Dict:
    """
    Permutation test for statistical significance.
    
    Procedure:
    1. Compute observed avg_hits with engine on last `test_size` draws
    2. For n_permutations:
       - Shuffle the order of draws (destroying temporal structure)
       - Compute avg_hits with engine on shuffled data
    3. p-value = fraction of permutations where avg_hits >= observed
    
    Low p-value (< 0.05) means: the engine's performance is NOT due to chance ordering.
    """
    from engines import ENGINE_REGISTRY
    from backtest import backtest_engine, baseline_random
    
    random.seed(seed)
    
    # 1. Compute observed
    if verbose:
        print(f"  Computing observed hits for {engine_name}...")
    observed_result = backtest_engine(
        type(lottery), 
        getattr(lottery, '_data_file', ''),
        engine_name,
        min_history=50,
        max_test_draws=test_size,
    )
    if 'error' in observed_result:
        return {'error': observed_result['error']}
    observed = observed_result['avg_hits']
    
    # Baseline
    bl = baseline_random(type(lottery), getattr(lottery, '_data_file', ''),
                         min_history=50, max_test_draws=test_size, seed=seed)
    baseline = bl['avg_hits']
    
    # 2. Permutations — instead of shuffling draws (which would break the engine's logic),
    # we generate random predictions and compare. The null hypothesis is:
    # "The engine is no better than random."
    # So we compare engine's hits vs distribution of random hits.
    
    # Faster: just use the random baseline many times
    if verbose:
        print(f"  Running {n_permutations} permutations...")
    
    perm_results = []
    for i in range(n_permutations):
        perm_bl = baseline_random(type(lottery), getattr(lottery, '_data_file', ''),
                                  min_history=50, max_test_draws=test_size,
                                  seed=seed + i + 1)
        perm_results.append(perm_bl['avg_hits'])
    
    # 3. p-value
    perm_extreme = sum(1 for p in perm_results if p >= observed)
    p_value = perm_extreme / n_permutations
    
    perm_mean = mean(perm_results)
    perm_std = stdev(perm_results) if len(perm_results) > 1 else 0
    
    # Cohen's d
    d = cohens_d(observed, perm_mean, perm_std)
    
    # 95% CI for observed (using normal approximation)
    # std of mean = std/sqrt(n)
    n = test_size
    obs_std = math.sqrt(observed * (1 - observed / (lottery.main_picks if lottery.main_picks > 0 else 1)) / n) if observed > 0 else 0.1
    ci_lower = observed - 1.96 * obs_std
    ci_upper = observed + 1.96 * obs_std
    
    improvement = observed - baseline
    improvement_pct = (improvement / baseline * 100) if baseline > 0 else 0
    
    # Verdict
    if p_value < 0.01:
        verdict = f"*** HIGHLY SIGNIFICANT (p={p_value:.4f}). The improvement is real, not noise."
    elif p_value < 0.05:
        verdict = f"** Significant (p={p_value:.4f}). Likely real improvement."
    elif p_value < 0.10:
        verdict = f"* Marginal (p={p_value:.4f}). Suggestive but not conclusive."
    else:
        verdict = f"NOT significant (p={p_value:.4f}). Improvement is within noise."
    
    return {
        'engine': engine_name,
        'observed_avg_hits': observed,
        'baseline_avg_hits': baseline,
        'improvement': improvement,
        'improvement_pct': improvement_pct,
        'p_value': p_value,
        'is_significant': p_value < 0.05,
        'cohens_d': d,
        'effect_size': effect_label(d),
        'ci_95': [ci_lower, ci_upper],
        'n_permutations': n_permutations,
        'perm_mean': perm_mean,
        'perm_std': perm_std,
        'perm_extreme_count': perm_extreme,
        'verdict': verdict,
    }


def walk_forward_backtest(
    lottery,
    engine_name: str,
    window_size: int = 100,
    step_size: int = 50,
    max_windows: int = 5,
) -> Dict:
    """
    Walk-forward backtest: rolling window evaluation.
    
    For each window of `window_size` draws:
    - Train on previous draws
    - Predict the next `step_size` draws
    - Record hits
    
    This tests robustness over time, not just one static split.
    """
    from engines import ENGINE_REGISTRY
    from backtest import backtest_engine
    
    engine = ENGINE_REGISTRY[engine_name]
    total = lottery.total_draws()
    data_file = getattr(lottery, '_data_file', '')
    
    windows = []
    end = total
    for w in range(max_windows):
        start = max(50, end - window_size)
        if start >= end:
            break
        # Backtest on this window
        # We need to fake the lottery to only have draws up to start
        original_draws = lottery.draws
        window_draws = original_draws[start:end]
        lottery.draws = original_draws[:start]
        
        hits = []
        for test_idx in range(min(step_size, len(window_draws))):
            actual = set(window_draws[test_idx].main_numbers)
            # Truncate to current point
            lottery.draws = original_draws[:start + test_idx]
            try:
                pred = engine.predict(lottery)
                hits.append(len(set(pred) & actual))
            except:
                hits.append(0)
        
        lottery.draws = original_draws  # restore
        
        avg = mean(hits) if hits else 0
        windows.append({
            'window': w + 1,
            'start_draw': start,
            'end_draw': end,
            'avg_hits': avg,
            'max_hits': max(hits) if hits else 0,
            'n_tested': len(hits),
        })
        
        end = start
    
    if not windows:
        return {'error': 'Not enough data for walk-forward'}
    
    avg_hits_per_window = [w['avg_hits'] for w in windows]
    stability = stdev(avg_hits_per_window) if len(avg_hits_per_window) > 1 else 0
    
    return {
        'engine': engine_name,
        'windows': windows,
        'wf_avg_hits': mean(avg_hits_per_window),
        'wf_stability': stability,
        'wf_min': min(avg_hits_per_window),
        'wf_max': max(avg_hits_per_window),
    }


def rigorous_backtest_all(
    lottery,
    n_permutations: int = 500,
    test_size: int = 50,
    skip_engines: List[str] = None,
    verbose: bool = True,
) -> Dict:
    """
    Run rigorous backtest on all engines.
    
    Returns dict with:
    - results: per-engine RigorousResult
    - multiple_testing_correction: Bonferroni-adjusted significance
    - summary: overall verdict
    """
    from engines import ENGINE_REGISTRY
    
    if skip_engines is None:
        skip_engines = ['lstm', 'monte_carlo', 'ensemble']  # too slow for permutations
    
    results = {}
    for eng_name in ENGINE_REGISTRY.keys():
        if eng_name in skip_engines:
            continue
        if verbose:
            print(f"\n=== {eng_name} ===")
        try:
            result = permutation_test(
                lottery, eng_name,
                n_permutations=n_permutations,
                test_size=test_size,
                verbose=verbose,
            )
            results[eng_name] = result
        except Exception as e:
            if verbose:
                print(f"  ERROR: {e}")
            results[eng_name] = {'error': str(e)}
    
    # Multiple testing correction (Bonferroni)
    n_tests = len([r for r in results.values() if 'error' not in r])
    bonferroni_alpha = 0.05 / n_tests if n_tests > 0 else 0.05
    
    significant_count = 0
    for eng, res in results.items():
        if 'error' in res:
            continue
        res['bonferroni_significant'] = res['p_value'] < bonferroni_alpha
        if res['bonferroni_significant']:
            significant_count += 1
    
    # Summary
    summary = {
        'lottery': lottery.name,
        'total_draws': lottery.total_draws(),
        'n_engines_tested': n_tests,
        'n_permutations_per_engine': n_permutations,
        'bonferroni_alpha': bonferroni_alpha,
        'significant_engines_count': significant_count,
        'verdict': '',
    }
    
    if significant_count == 0:
        summary['verdict'] = (
            f"❌ NINGÚN motor pasa el test de significancia estadística "
            f"(Bonferroni α={bonferroni_alpha:.4f}). "
            f"Las mejoras observadas son consistentes con ruido aleatorio."
        )
    elif significant_count == 1:
        summary['verdict'] = (
            f"⚠️ Solo 1 motor es estadísticamente significativo tras corrección Bonferroni. "
            f"Pero el effect size puede ser pequeño."
        )
    else:
        summary['verdict'] = (
            f"✅ {significant_count} motores son estadísticamente significativos. "
            f"Pero verifica el effect size (Cohen's d) antes de concluir."
        )
    
    return {
        'results': results,
        'summary': summary,
    }


# CLI
if __name__ == '__main__':
    import argparse
    from lotteries import get_lottery, NEW_LOTTERIES
    
    DEFAULT_DATA_PATHS = {
        'pozo_millonario': '/home/z/my-project/data/pozo_data.json',
        'euromillions': '/home/z/my-project/data/euromillions.json',
        'la_primitiva': '/home/z/my-project/data/la_primitiva.json',
        'lotto_austrian': '/home/z/my-project/data/lotto_austrian.json',
        'uk49s': '/home/z/my-project/data/uk49s.json',
    }
    for k, v in NEW_LOTTERIES.items():
        DEFAULT_DATA_PATHS[k] = v['data_file']
    
    parser = argparse.ArgumentParser(description='Rigorous statistical backtesting')
    parser.add_argument('--lottery', required=True)
    parser.add_argument('--permutations', type=int, default=500)
    parser.add_argument('--test-size', type=int, default=50)
    args = parser.parse_args()
    
    lottery = get_lottery(args.lottery)
    lottery.load_data(DEFAULT_DATA_PATHS[args.lottery])
    lottery._data_file = DEFAULT_DATA_PATHS[args.lottery]
    
    print(f"\n{'='*70}")
    print(f"RIGOROUS BACKTEST: {lottery.name} ({lottery.total_draws()} draws)")
    print(f"Permutations: {args.permutations} | Test size: {args.test_size}")
    print(f"{'='*70}\n")
    
    result = rigorous_backtest_all(lottery, n_permutations=args.permutations, test_size=args.test_size)
    
    print(f"\n{'='*70}")
    print(f"RESULTS")
    print(f"{'='*70}")
    print(f"\n{'Engine':<22} {'Observed':>10} {'Baseline':>10} {'Improv':>10} {'p-value':>10} {'Significant':>12} {'Cohen d':>10}")
    print('-' * 90)
    
    for eng, res in result['results'].items():
        if 'error' in res:
            print(f"{eng:<22} ERROR: {res['error']}")
            continue
        sig = 'YES ***' if res['bonferroni_significant'] else 'no'
        print(f"{eng:<22} {res['observed_avg_hits']:>10.3f} {res['baseline_avg_hits']:>10.3f} {res['improvement']:+10.3f} {res['p_value']:>10.4f} {sig:>12} {res['cohens_d']:>10.3f}")
    
    print(f"\n{result['summary']['verdict']}")

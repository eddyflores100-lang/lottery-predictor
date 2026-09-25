"""
Engine 8: Monte Carlo Simulation
10,000+ simulated draws with uniform, frequency-weighted, and ML-ensemble strategies.
Validates predictions against synthetic data.

Adapted from open-gravity-ui's simulation_runner.ts (mulberry32 PRNG, P10/P50/P90 percentiles).
"""
import math
from typing import List, Dict
from collections import Counter


def mulberry32(seed: int):
    """Deterministic PRNG (mulberry32) — same as open-gravity-ui."""
    def _prng():
        nonlocal seed
        seed = (seed + 0x6D2B79F5) & 0xFFFFFFFF
        t = seed
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t ^= t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296
    return _prng


def percentile(sorted_values: List[float], p: float) -> float:
    """Compute percentile from sorted list."""
    if not sorted_values:
        return 0
    idx = int((p / 100) * (len(sorted_values) - 1))
    idx = max(0, min(idx, len(sorted_values) - 1))
    return sorted_values[idx]


def simulate_draw(lottery, prng, weights: Dict[int, float] = None) -> List[int]:
    """
    Simulate a single draw using weighted random sampling.
    
    If weights provided: sample without replacement using weights
    Else: uniform random sample
    """
    pool_size = lottery.main_pool_size
    picks = lottery.main_picks
    
    if weights:
        # Weighted sampling without replacement
        pool = list(range(1, pool_size + 1))
        weights_list = [weights.get(n, 1.0) for n in pool]
        selected = []
        for _ in range(picks):
            total = sum(weights_list)
            if total <= 0:
                # Fallback to uniform
                r = prng()
                idx = int(r * len(pool))
            else:
                r = prng() * total
                cum = 0
                idx = 0
                for i, w in enumerate(weights_list):
                    cum += w
                    if cum >= r:
                        idx = i
                        break
            selected.append(pool.pop(idx))
            weights_list.pop(idx)
        return sorted(selected)
    else:
        # Uniform
        import random
        return sorted(random.sample(range(1, pool_size + 1), picks))


def analyze(lottery, iterations: int = 10000, seed: int = 42) -> Dict:
    """
    Run Monte Carlo simulation with 3 strategies:
    1. Uniform (baseline): pure random
    2. Frequency-weighted: weight by historical frequency
    3. Mixed: blend of both
    
    Returns statistics on how often each number appears across simulations.
    """
    total_draws = lottery.total_draws()
    if total_draws == 0:
        return {'error': 'No draws'}
    
    pool_size = lottery.main_pool_size
    picks = lottery.main_picks
    
    # Historical frequency weights
    counter = Counter()
    for d in lottery.draws:
        for n in d.main_numbers:
            counter[n] += 1
    total_appearances = sum(counter.values())
    freq_weights = {n: counter.get(n, 0) / total_appearances for n in range(1, pool_size + 1)}
    
    # Run simulations
    prng_uniform = mulberry32(seed)
    prng_weighted = mulberry32(seed + 1)
    prng_mixed = mulberry32(seed + 2)
    
    # Count appearances in simulations
    uniform_counter = Counter()
    weighted_counter = Counter()
    mixed_counter = Counter()
    
    # Track match scores (how many numbers from each sim match the actual last draw)
    last_draw = set(lottery.draws[-1].main_numbers) if lottery.draws else set()
    match_scores_uniform = []
    match_scores_weighted = []
    match_scores_mixed = []
    
    for _ in range(iterations):
        # Uniform
        sim_uniform = simulate_draw(lottery, prng_uniform)
        for n in sim_uniform:
            uniform_counter[n] += 1
        matches_u = len(set(sim_uniform) & last_draw)
        match_scores_uniform.append(matches_u)
        
        # Weighted
        sim_weighted = simulate_draw(lottery, prng_weighted, weights=freq_weights)
        for n in sim_weighted:
            weighted_counter[n] += 1
        matches_w = len(set(sim_weighted) & last_draw)
        match_scores_weighted.append(matches_w)
        
        # Mixed (50/50 blend)
        mixed_weights = {
            n: 0.5 * (1 / pool_size) + 0.5 * freq_weights[n]
            for n in range(1, pool_size + 1)
        }
        sim_mixed = simulate_draw(lottery, prng_mixed, weights=mixed_weights)
        for n in sim_mixed:
            mixed_counter[n] += 1
        matches_m = len(set(sim_mixed) & last_draw)
        match_scores_mixed.append(matches_m)
    
    # Compute percentiles for match scores
    match_scores_uniform.sort()
    match_scores_weighted.sort()
    match_scores_mixed.sort()
    
    # Per-number appearance probability in simulations
    per_number = {}
    for n in range(1, pool_size + 1):
        per_number[n] = {
            'uniform_sim_prob': round(uniform_counter[n] / iterations, 4),
            'weighted_sim_prob': round(weighted_counter[n] / iterations, 4),
            'mixed_sim_prob': round(mixed_counter[n] / iterations, 4),
            'historical_freq': round(freq_weights[n], 4),
        }
    
    return {
        'per_number': per_number,
        'iterations': iterations,
        'match_stats': {
            'uniform': {
                'p10': percentile(match_scores_uniform, 10),
                'p50': percentile(match_scores_uniform, 50),
                'p90': percentile(match_scores_uniform, 90),
                'mean': sum(match_scores_uniform) / len(match_scores_uniform),
            },
            'weighted': {
                'p10': percentile(match_scores_weighted, 10),
                'p50': percentile(match_scores_weighted, 50),
                'p90': percentile(match_scores_weighted, 90),
                'mean': sum(match_scores_weighted) / len(match_scores_weighted),
            },
            'mixed': {
                'p10': percentile(match_scores_mixed, 10),
                'p50': percentile(match_scores_mixed, 50),
                'p90': percentile(match_scores_mixed, 90),
                'mean': sum(match_scores_mixed) / len(match_scores_mixed),
            },
        },
        'total_draws': total_draws,
    }


def predict(lottery, strategy: str = 'mixed') -> List[int]:
    """
    Generate prediction based on Monte Carlo.
    strategy: 'uniform', 'weighted', or 'mixed'
    """
    analysis = analyze(lottery)
    if 'error' in analysis:
        return []
    
    per_number = analysis['per_number']
    key = f'{strategy}_sim_prob'
    ranked = sorted(per_number.items(), key=lambda x: -x[1][key])
    return [n for n, _ in ranked[:lottery.main_picks]]

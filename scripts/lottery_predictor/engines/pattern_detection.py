"""
Engine 6: Pattern Detection
Consecutive pairs, range clustering, even/odd anomalies, sum-range analysis, and runs test for randomness.
"""
from typing import List, Dict, Tuple
from collections import Counter
import math


def analyze(lottery) -> Dict:
    """
    Detect patterns in historical draws:
    - Most common consecutive pairs
    - Range distribution (low/mid/high)
    - Even/odd distribution
    - Sum distribution
    - Runs test for randomness
    """
    total_draws = lottery.total_draws()
    if total_draws == 0:
        return {'error': 'No draws'}
    
    pool_size = lottery.main_pool_size
    picks = lottery.main_picks
    
    # 1. Consecutive pairs (e.g., 5-6, 17-18)
    consecutive_pairs = Counter()
    for d in lottery.draws:
        sorted_nums = sorted(set(d.main_numbers))
        for i in range(len(sorted_nums) - 1):
            if sorted_nums[i+1] - sorted_nums[i] == 1:
                consecutive_pairs[(sorted_nums[i], sorted_nums[i+1])] += 1
    
    # 2. Range distribution (low=1-8, mid=9-17, high=18-25 for Pozo Millonario)
    # Adjust based on pool size
    low_max = pool_size // 3
    mid_max = (pool_size * 2) // 3
    
    range_dist = Counter()
    for d in lottery.draws:
        low = sum(1 for n in d.main_numbers if n <= low_max)
        mid = sum(1 for n in d.main_numbers if low_max < n <= mid_max)
        high = sum(1 for n in d.main_numbers if n > mid_max)
        range_dist[(low, mid, high)] += 1
    
    # 3. Even/odd distribution
    even_odd_dist = Counter()
    for d in lottery.draws:
        even = sum(1 for n in d.main_numbers if n % 2 == 0)
        odd = picks - even
        even_odd_dist[(even, odd)] += 1
    
    # 4. Sum distribution
    sums = [sum(set(d.main_numbers)) for d in lottery.draws]
    avg_sum = sum(sums) / len(sums) if sums else 0
    min_sum = min(sums) if sums else 0
    max_sum = max(sums) if sums else 0
    # Bin sums
    sum_bins = Counter()
    for s in sums:
        bin_idx = (s // 20) * 20  # bin every 20 units
        sum_bins[bin_idx] += 1
    
    # 5. Runs test for randomness
    # For each number, sequence of 1 (appeared) / 0 (didn't) over draws
    # Then compute runs statistic
    runs_test_results = {}
    for n in range(1, pool_size + 1):
        sequence = [1 if n in d.main_numbers else 0 for d in lottery.draws]
        runs_test_results[n] = _runs_test(sequence)
    
    # 6. Most common combinations (subsets)
    combo_counter = Counter()
    for d in lottery.draws:
        nums = sorted(set(d.main_numbers))
        # All pairs
        for i in range(len(nums)):
            for j in range(i+1, len(nums)):
                combo_counter[(nums[i], nums[j])] += 1
    
    return {
        'consecutive_pairs_top10': [
            {'pair': list(p), 'count': c}
            for p, c in consecutive_pairs.most_common(10)
        ],
        'range_distribution_top10': [
            {'ranges': list(r), 'count': c, 'pct': round(c/total_draws*100, 2)}
            for r, c in range_dist.most_common(10)
        ],
        'even_odd_distribution_top10': [
            {'even': e, 'odd': o, 'count': c, 'pct': round(c/total_draws*100, 2)}
            for (e, o), c in even_odd_dist.most_common(10)
        ],
        'sum_stats': {
            'avg': round(avg_sum, 2),
            'min': min_sum,
            'max': max_sum,
            'median': sorted(sums)[len(sums)//2] if sums else 0,
        },
        'sum_bins': dict(sorted(sum_bins.items())),
        'runs_test': runs_test_results,
        'top_co_occurring_pairs': [
            {'pair': list(p), 'count': c, 'pct': round(c/total_draws*100, 2)}
            for p, c in combo_counter.most_common(15)
        ],
        'total_draws': total_draws,
    }


def _runs_test(sequence: List[int]) -> Dict:
    """
    Wald-Wolfowitz runs test for randomness.
    A "run" is a sequence of consecutive same values.
    H0: sequence is random
    """
    if len(sequence) < 2:
        return {'z_score': 0, 'is_random': True}
    
    n1 = sum(sequence)  # ones
    n0 = len(sequence) - n1  # zeros
    
    if n1 == 0 or n0 == 0:
        return {'z_score': 0, 'is_random': True, 'note': 'No variation'}
    
    # Count runs
    runs = 1
    for i in range(1, len(sequence)):
        if sequence[i] != sequence[i-1]:
            runs += 1
    
    # Expected runs
    expected_runs = (2 * n1 * n0) / (n1 + n0) + 1
    # Variance
    variance = (2 * n1 * n0 * (2 * n1 * n0 - n1 - n0)) / ((n1 + n0) ** 2 * (n1 + n0 - 1))
    
    if variance <= 0:
        return {'z_score': 0, 'is_random': True}
    
    z = (runs - expected_runs) / math.sqrt(variance)
    
    return {
        'runs': runs,
        'expected_runs': round(expected_runs, 2),
        'z_score': round(z, 3),
        'is_random': abs(z) < 1.96,  # 5% significance
    }


def predict(lottery) -> List[int]:
    """
    Generate a prediction that matches the most common historical patterns:
    - Use most common even/odd ratio
    - Use most common range distribution
    - Pick from top co-occurring pairs
    - Match sum to median range
    """
    analysis = analyze(lottery)
    if 'error' in analysis:
        return []
    
    # Most common even/odd distribution
    eo = analysis['even_odd_distribution_top10'][0]
    target_even = eo['even']
    target_odd = eo['odd']
    
    # Most common range distribution
    rd = analysis['range_distribution_top10'][0]
    target_low, target_mid, target_high = rd['ranges']
    
    # Top co-occurring pairs
    top_pairs = [tuple(p['pair']) for p in analysis['top_co_occurring_pairs'][:10]]
    
    # Build selection: try to use top pairs, respecting even/odd and range targets
    pool_size = lottery.main_pool_size
    low_max = pool_size // 3
    mid_max = (pool_size * 2) // 3
    
    selected = set()
    # Add numbers from top pairs
    for a, b in top_pairs:
        if len(selected) >= lottery.main_picks:
            break
        # Check even/odd balance
        current_even = sum(1 for x in selected if x % 2 == 0)
        current_odd = len(selected) - current_even
        
        for x in [a, b]:
            if x not in selected and len(selected) < lottery.main_picks:
                # Check if adding x keeps us close to target
                is_even = x % 2 == 0
                if is_even and current_even < target_even:
                    selected.add(x)
                    current_even += 1
                elif not is_even and current_odd < target_odd:
                    selected.add(x)
                    current_odd += 1
                elif len(selected) < lottery.main_picks - 1:  # allow some flexibility
                    selected.add(x)
                    if is_even:
                        current_even += 1
                    else:
                        current_odd += 1
    
    # Fill remaining slots with frequent numbers
    if len(selected) < lottery.main_picks:
        # Use frequency analysis
        from .frequency import analyze as freq_analyze
        freq = freq_analyze(lottery)
        ranked = sorted(freq['per_number'].items(), key=lambda x: -x[1]['freq'])
        for n, _ in ranked:
            if n not in selected and len(selected) < lottery.main_picks:
                selected.add(n)
    
    return sorted(selected)

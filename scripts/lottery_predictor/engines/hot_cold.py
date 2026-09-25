"""
Engine 2: Hot/Cold Tracker
Temperature scoring (-1.0 to +1.0) with mean reversion probability estimates.
"""
from collections import Counter, deque
from typing import List, Dict, Tuple
import math


def analyze(lottery, recent_window: int = 20) -> Dict:
    """
    Compare recent frequency vs overall frequency to determine "temperature".
    Hot = appears more in recent than overall (positive score)
    Cold = appears less in recent than overall (negative score)
    
    Args:
        recent_window: Number of recent draws to consider "recent"
    
    Returns:
        {n: {temperature, recent_freq, overall_freq, hot_streak, cold_streak, mean_reversion_prob}}
    """
    total_draws = lottery.total_draws()
    if total_draws == 0:
        return {'error': 'No draws'}
    
    recent_draws = lottery.get_recent_draws(recent_window)
    pool_size = lottery.main_pool_size
    
    # Overall frequency
    overall_counter = Counter()
    for d in lottery.draws:
        for n in d.main_numbers:
            overall_counter[n] += 1
    overall_freq = {n: overall_counter.get(n, 0) / total_draws for n in range(1, pool_size + 1)}
    
    # Recent frequency
    recent_counter = Counter()
    for d in recent_draws:
        for n in d.main_numbers:
            recent_counter[n] += 1
    recent_freq = {n: recent_counter.get(n, 0) / len(recent_draws) for n in range(1, pool_size + 1)}
    
    # Temperature: difference between recent and overall, normalized
    # Range: -1.0 (very cold) to +1.0 (very hot)
    per_number = {}
    for n in range(1, pool_size + 1):
        diff = recent_freq[n] - overall_freq[n]
        # Normalize: max possible diff is +1.0, min is -1.0
        temperature = max(-1.0, min(1.0, diff * 2))  # scale for visibility
        
        # Hot streak: consecutive recent draws where n appeared
        hot_streak = 0
        for d in reversed(recent_draws):
            if n in d.main_numbers:
                hot_streak += 1
            else:
                break
        
        # Cold streak: consecutive recent draws where n did NOT appear
        cold_streak = 0
        for d in reversed(recent_draws):
            if n not in d.main_numbers:
                cold_streak += 1
            else:
                break
        
        # Mean reversion probability: if cold for too long, more likely to appear
        # Use geometric distribution: P(X > k) = (1-p)^k
        # If cold_streak > expected gap, mean reversion probability increases
        p_overall = overall_freq[n]
        expected_gap = 1 / p_overall if p_overall > 0 else float('inf')
        if cold_streak > expected_gap:
            mean_reversion_prob = 1 - ((1 - p_overall) ** cold_streak)
        else:
            mean_reversion_prob = p_overall
        
        per_number[n] = {
            'temperature': round(temperature, 3),
            'recent_freq': round(recent_freq[n], 3),
            'overall_freq': round(overall_freq[n], 3),
            'hot_streak': hot_streak,
            'cold_streak': cold_streak,
            'mean_reversion_prob': round(mean_reversion_prob, 3),
        }
    
    return {
        'per_number': per_number,
        'recent_window': recent_window,
        'total_draws': total_draws,
    }


def get_hot_numbers(analysis: Dict, top_n: int = 5) -> List[int]:
    """Get the hottest N numbers."""
    per_number = analysis.get('per_number', {})
    ranked = sorted(per_number.items(), key=lambda x: -x[1]['temperature'])
    return [n for n, _ in ranked[:top_n]]


def get_cold_numbers(analysis: Dict, top_n: int = 5) -> List[int]:
    """Get the coldest N numbers."""
    per_number = analysis.get('per_number', {})
    ranked = sorted(per_number.items(), key=lambda x: x[1]['temperature'])
    return [n for n, _ in ranked[:top_n]]


def predict(lottery, strategy: str = 'balanced') -> List[int]:
    """
    Generate prediction.
    Strategies:
        'hot': Top N hottest numbers
        'cold': Top N coldest numbers (mean reversion play)
        'balanced': Mix of hot and cold
    """
    analysis = analyze(lottery)
    n = lottery.main_picks
    
    if strategy == 'hot':
        return get_hot_numbers(analysis, n)
    elif strategy == 'cold':
        return get_cold_numbers(analysis, n)
    else:  # balanced
        # Take ceil(n/2) hot + floor(n/2) cold, avoid duplicates
        hot = get_hot_numbers(analysis, math.ceil(n / 2) + 2)
        cold = get_cold_numbers(analysis, math.floor(n / 2) + 2)
        result = []
        for x in hot:
            if x not in result:
                result.append(x)
            if len(result) >= math.ceil(n / 2):
                break
        for x in cold:
            if x not in result:
                result.append(x)
            if len(result) >= n:
                break
        return result[:n]

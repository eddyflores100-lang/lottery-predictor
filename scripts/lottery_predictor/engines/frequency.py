"""
Engine 1: Frequency Analysis
Computes raw frequency, Z-scores, and chi-squared uniformity test for each number.
"""
from collections import Counter
from typing import List, Dict, Tuple
import math


def analyze(lottery, window: int = None) -> Dict:
    """
    Args:
        lottery: Lottery instance
        window: Optional - only analyze last N draws
    
    Returns:
        {
            'per_number': {n: {freq, expected, z_score, pct}},
            'chi_squared': float,
            'chi_critical_5pct': float,
            'is_uniform': bool,
            'total_draws': int,
        }
    """
    draws = lottery.get_recent_draws(window) if window else lottery.draws
    total_draws = len(draws)
    if total_draws == 0:
        return {'error': 'No draws available'}
    
    pool_size = lottery.main_pool_size
    picks = lottery.main_picks
    
    # Count appearances per number
    counter = Counter()
    for d in draws:
        for n in d.main_numbers:
            counter[n] += 1
    
    # Expected frequency if uniform: each number should appear in (picks/pool) * total_draws
    expected = (picks / pool_size) * total_draws
    
    # Chi-squared test
    chi_squared = 0
    for n in range(1, pool_size + 1):
        observed = counter.get(n, 0)
        chi_squared += ((observed - expected) ** 2) / expected
    
    # Critical value for chi-squared at 5% significance, df = pool_size - 1
    # For 24 df (Pozo Millonario): 36.42
    # For 48 df (La Primitiva): 65.17
    # For 49 df (EuroMillions main): 66.34
    # We'll compute approximate critical value
    df = pool_size - 1
    chi_critical = _chi_squared_critical(df, alpha=0.05)
    
    # Z-scores per number
    per_number = {}
    # Standard deviation under binomial: sqrt(n * p * (1-p)) where n=draws, p=picks/pool
    p = picks / pool_size
    std_dev = math.sqrt(total_draws * p * (1 - p))
    
    for n in range(1, pool_size + 1):
        freq = counter.get(n, 0)
        z = (freq - expected) / std_dev if std_dev > 0 else 0
        per_number[n] = {
            'freq': freq,
            'expected': expected,
            'z_score': round(z, 3),
            'pct': round(freq / total_draws * 100, 2),
            'deviation': round((freq - expected) / expected * 100, 2) if expected > 0 else 0,
        }
    
    return {
        'per_number': per_number,
        'chi_squared': round(chi_squared, 2),
        'chi_critical_5pct': round(chi_critical, 2),
        'is_uniform': chi_squared < chi_critical,
        'total_draws': total_draws,
        'expected_per_number': round(expected, 2),
        'std_dev': round(std_dev, 2),
    }


def _chi_squared_critical(df: int, alpha: float = 0.05) -> float:
    """Approximate chi-squared critical value using Wilson-Hilferty approximation."""
    z = 1.6449  # z for alpha=0.05 (one-tailed)
    if alpha != 0.05:
        # Approximate z for common alphas
        z_map = {0.10: 1.2816, 0.05: 1.6449, 0.01: 2.3263, 0.001: 3.0902}
        z = z_map.get(alpha, 1.6449)
    return df * (1 - 2 / (9 * df) + z * math.sqrt(2 / (9 * df))) ** 3


def rank_numbers(analysis: Dict, top_n: int = None) -> List[Tuple[int, float]]:
    """Rank numbers by frequency descending. Returns list of (number, freq)."""
    per_number = analysis.get('per_number', {})
    ranked = sorted(per_number.items(), key=lambda x: -x[1]['freq'])
    ranked = [(n, info['freq']) for n, info in ranked]
    return ranked[:top_n] if top_n else ranked


def predict(lottery, top_n: int = None) -> List[int]:
    """Return top N most frequent numbers as prediction."""
    analysis = analyze(lottery)
    ranked = rank_numbers(analysis, top_n or lottery.main_picks)
    return [n for n, _ in ranked[:lottery.main_picks]]

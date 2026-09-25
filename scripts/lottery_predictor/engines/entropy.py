"""
Engine 7: Entropy Scoring
Shannon entropy, rolling entropy averages, autocorrelation analysis, randomness quality scoring.
"""
from typing import List, Dict
from collections import Counter
import math


def analyze(lottery, window: int = 50) -> Dict:
    """
    Compute entropy metrics to assess randomness of the lottery.
    
    High entropy = random (hard to predict)
    Low entropy = patterns exist (potentially predictable)
    """
    total_draws = lottery.total_draws()
    if total_draws == 0:
        return {'error': 'No draws'}
    
    pool_size = lottery.main_pool_size
    picks = lottery.main_picks
    
    # 1. Overall Shannon entropy of number frequencies
    counter = Counter()
    for d in lottery.draws:
        for n in d.main_numbers:
            counter[n] += 1
    
    total_appearances = sum(counter.values())
    entropy = 0
    for n in range(1, pool_size + 1):
        p = counter.get(n, 0) / total_appearances
        if p > 0:
            entropy -= p * math.log2(p)
    
    max_entropy = math.log2(pool_size)  # max possible entropy
    normalized_entropy = entropy / max_entropy  # 0 to 1
    
    # 2. Rolling entropy over windows
    rolling_entropies = []
    for i in range(window, total_draws + 1):
        window_draws = lottery.draws[i-window:i]
        wc = Counter()
        for d in window_draws:
            for n in d.main_numbers:
                wc[n] += 1
        wt = sum(wc.values())
        we = 0
        for n in range(1, pool_size + 1):
            p = wc.get(n, 0) / wt
            if p > 0:
                we -= p * math.log2(p)
        rolling_entropies.append(we / max_entropy)
    
    avg_rolling_entropy = sum(rolling_entropies) / len(rolling_entropies) if rolling_entropies else 0
    
    # 3. Autocorrelation of number appearances
    # For each number, compute autocorrelation at lag 1
    autocorr_per_number = {}
    for n in range(1, pool_size + 1):
        sequence = [1 if n in d.main_numbers else 0 for d in lottery.draws]
        autocorr_per_number[n] = _autocorrelation(sequence, lag=1)
    
    # 4. Randomness quality score (0-100)
    # Combine: entropy (50%) + autocorrelation penalty (50%)
    avg_autocorr = sum(abs(v) for v in autocorr_per_number.values()) / pool_size
    # High autocorrelation = less random = lower score
    randomness_score = (normalized_entropy * 50) + ((1 - min(1, avg_autocorr * 5)) * 50)
    
    return {
        'shannon_entropy': round(entropy, 3),
        'max_entropy': round(max_entropy, 3),
        'normalized_entropy': round(normalized_entropy, 3),
        'avg_rolling_entropy': round(avg_rolling_entropy, 3),
        'rolling_window': window,
        'autocorrelation_per_number': {n: round(v, 3) for n, v in autocorr_per_number.items()},
        'avg_abs_autocorrelation': round(avg_autocorr, 3),
        'randomness_score': round(randomness_score, 1),
        'total_draws': total_draws,
    }


def _autocorrelation(sequence: List[float], lag: int = 1) -> float:
    """Compute autocorrelation at given lag."""
    n = len(sequence)
    if n <= lag:
        return 0
    
    mean = sum(sequence) / n
    variance = sum((x - mean) ** 2 for x in sequence) / n
    if variance == 0:
        return 0
    
    cov = sum((sequence[i] - mean) * (sequence[i + lag] - mean) for i in range(n - lag)) / (n - lag)
    return cov / variance


def predict(lottery) -> List[int]:
    """
    Predict using entropy-aware strategy:
    - If randomness is high, use frequency (most neutral signal)
    - If randomness is low (patterns exist), use autocorrelation to pick numbers
      likely to appear after recent numbers
    """
    analysis = analyze(lottery)
    if 'error' in analysis:
        return []
    
    if analysis['randomness_score'] > 70:
        # High randomness: use frequency
        from .frequency import predict as freq_predict
        return freq_predict(lottery)
    else:
        # Low randomness: use autocorrelation + frequency
        from .frequency import analyze as freq_analyze
        freq = freq_analyze(lottery)
        # Numbers with positive autocorrelation AND high frequency
        autocorr = analysis['autocorrelation_per_number']
        per_number = freq['per_number']
        
        scored = []
        for n in range(1, lottery.main_pool_size + 1):
            # Score = freq z-score + autocorr bonus
            z = per_number[n]['z_score']
            ac = autocorr.get(n, 0)
            # If autocorr is positive, this number tends to cluster (appear in streaks)
            score = z + (ac * 5)  # weight autocorr
            scored.append((n, score))
        
        scored.sort(key=lambda x: -x[1])
        return [n for n, _ in scored[:lottery.main_picks]]

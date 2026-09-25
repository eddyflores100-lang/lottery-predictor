"""
Backtesting framework — validates each engine against historical data.
For each draw at position t, predict using data up to t-1, then check matches.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Tuple
from collections import defaultdict
from statistics import mean
import time

from lotteries.base import Lottery, DrawResult
from engines import ENGINE_REGISTRY


def backtest_engine(lottery_class, data_source: str, engine_name: str,
                    min_history: int = 50, max_test_draws: int = None,
                    verbose: bool = False) -> Dict:
    """
    Backtest a single engine on a lottery.
    
    Args:
        lottery_class: Class to instantiate (e.g., PozoMillonario) OR a factory function
        data_source: Path to data file
        engine_name: Name of engine to test
        min_history: Minimum draws needed before making predictions
        max_test_draws: Max draws to test (None = all)
        verbose: Print progress
    
    Returns:
        {
            'engine': str,
            'total_tested': int,
            'avg_hits': float,
            'hits_distribution': {0: count, 1: count, ...},
            'max_hits': int,
            'min_hits': int,
            'avg_time_per_pred': float,
            'predictions': [{draw, predicted, actual, hits}, ...]
        }
    """
    # Load full data
    try:
        lottery = lottery_class()
    except TypeError:
        # If lottery_class is a factory function (e.g., for generic lotteries), call it directly
        lottery = lottery_class
        if hasattr(lottery, '__class__') and lottery.__class__.__name__ == 'function':
            lottery = lottery_class()
    
    lottery.load_data(data_source)
    
    if lottery.total_draws() < min_history + 1:
        return {'error': f'Not enough draws. Need {min_history+1}, have {lottery.total_draws()}'}
    
    engine = ENGINE_REGISTRY[engine_name]
    
    # Test draws: from min_history to end
    test_indices = list(range(min_history, lottery.total_draws()))
    if max_test_draws:
        test_indices = test_indices[:max_test_draws]
    
    hits_distribution = defaultdict(int)
    all_hits = []
    predictions = []
    total_time = 0
    
    for i, test_idx in enumerate(test_indices):
        # Build a "past" lottery with only draws up to test_idx - 1
        # Use the same instance but with truncated draws (more efficient)
        original_draws = lottery.draws
        lottery.draws = original_draws[:test_idx]
        
        actual_draw = original_draws[test_idx]
        actual_numbers = set(actual_draw.main_numbers)
        
        # Predict
        start_time = time.time()
        try:
            predicted = engine.predict(lottery)
        except Exception as e:
            if verbose:
                print(f"  Error at draw {actual_draw.draw_number}: {e}")
            predicted = []
        elapsed = time.time() - start_time
        total_time += elapsed
        
        # Restore draws
        lottery.draws = original_draws
        
        # Count hits
        hits = len(set(predicted) & actual_numbers) if predicted else 0
        hits_distribution[hits] += 1
        all_hits.append(hits)
        
        predictions.append({
            'draw_number': actual_draw.draw_number,
            'date': actual_draw.date,
            'predicted': predicted,
            'actual': sorted(actual_numbers),
            'hits': hits,
        })
        
        if verbose and (i + 1) % 20 == 0:
            print(f"  Tested {i+1}/{len(test_indices)} draws, avg hits so far: {mean(all_hits):.2f}")
    
    avg_hits = mean(all_hits) if all_hits else 0
    
    return {
        'engine': engine_name,
        'lottery': lottery.name,
        'total_tested': len(all_hits),
        'avg_hits': round(avg_hits, 3),
        'max_hits': max(all_hits) if all_hits else 0,
        'min_hits': min(all_hits) if all_hits else 0,
        'hits_distribution': dict(hits_distribution),
        'avg_time_per_pred_ms': round(total_time / len(all_hits) * 1000, 2) if all_hits else 0,
        'predictions': predictions,
    }


def backtest_all_engines(lottery_class, data_source: str,
                         min_history: int = 50, max_test_draws: int = None,
                         verbose: bool = False, skip_engines=None) -> Dict:
    """Backtest all engines on a lottery."""
    if skip_engines is None:
        skip_engines = []
    results = {}
    for engine_name in ENGINE_REGISTRY.keys():
        if engine_name in skip_engines:
            continue
        if verbose:
            print(f"\n=== Backtesting engine: {engine_name} ===")
        result = backtest_engine(
            lottery_class, data_source, engine_name,
            min_history=min_history, max_test_draws=max_test_draws,
            verbose=verbose
        )
        results[engine_name] = result
        if verbose and 'error' not in result:
            print(f"  → Avg hits: {result['avg_hits']}, max: {result['max_hits']}")
    
    return results


def compare_engines(backtest_results: Dict) -> List[Dict]:
    """Compare engines by average hits."""
    comparison = []
    for engine_name, result in backtest_results.items():
        if 'error' in result:
            continue
        comparison.append({
            'engine': engine_name,
            'avg_hits': result['avg_hits'],
            'max_hits': result['max_hits'],
            'avg_time_ms': result['avg_time_per_pred_ms'],
            'tested': result['total_tested'],
        })
        # Sort by avg_hits descending
    comparison.sort(key=lambda x: -x['avg_hits'])
    return comparison


def baseline_random(lottery_class, data_source: str, min_history: int = 50,
                    max_test_draws: int = None, seed: int = 42) -> Dict:
    """Compute baseline: random prediction."""
    import random
    random.seed(seed)
    
    try:
        lottery = lottery_class()
    except TypeError:
        lottery = lottery_class
        if hasattr(lottery, '__class__') and lottery.__class__.__name__ == 'function':
            lottery = lottery_class()
    
    lottery.load_data(data_source)
    
    test_indices = list(range(min_history, lottery.total_draws()))
    if max_test_draws:
        test_indices = test_indices[:max_test_draws]
    
    all_hits = []
    for test_idx in test_indices:
        actual = set(lottery.draws[test_idx].main_numbers)
        predicted = random.sample(range(1, lottery.main_pool_size + 1), lottery.main_picks)
        hits = len(set(predicted) & actual)
        all_hits.append(hits)
    
    return {
        'engine': 'random_baseline',
        'total_tested': len(all_hits),
        'avg_hits': round(mean(all_hits), 3),
        'max_hits': max(all_hits),
        'hits_distribution': dict(__import__('collections').Counter(all_hits)),
    }

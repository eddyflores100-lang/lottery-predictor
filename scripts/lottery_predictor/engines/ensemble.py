"""
Engine 9: Ensemble Prediction
Combines all 8 engines with weighted averaging and diversity enforcement.
"""
from typing import List, Dict, Tuple
from collections import Counter
import math


# Engine weights (sum to 1.0)
# These can be tuned via backtesting
DEFAULT_WEIGHTS = {
    'frequency': 0.15,
    'hot_cold': 0.10,
    'gap_analysis': 0.10,
    'markov_chain': 0.15,
    'bayesian': 0.15,
    'pattern_detection': 0.10,
    'entropy': 0.10,
    'monte_carlo': 0.15,
}


def analyze(lottery, weights: Dict[str, float] = None) -> Dict:
    """
    Run all 8 engines and combine their predictions.
    """
    from . import (frequency, hot_cold, gap_analysis, markov_chain,
                   bayesian, pattern_detection, entropy, monte_carlo)
    
    if weights is None:
        weights = DEFAULT_WEIGHTS
    
    # Run all engines
    engines_results = {}
    engine_predictions = {}
    
    try:
        engines_results['frequency'] = frequency.analyze(lottery)
        engine_predictions['frequency'] = frequency.predict(lottery)
    except Exception as e:
        engines_results['frequency'] = {'error': str(e)}
        engine_predictions['frequency'] = []
    
    try:
        engines_results['hot_cold'] = hot_cold.analyze(lottery)
        engine_predictions['hot_cold'] = hot_cold.predict(lottery)
    except Exception as e:
        engines_results['hot_cold'] = {'error': str(e)}
        engine_predictions['hot_cold'] = []
    
    try:
        engines_results['gap_analysis'] = gap_analysis.analyze(lottery)
        engine_predictions['gap_analysis'] = gap_analysis.predict(lottery)
    except Exception as e:
        engines_results['gap_analysis'] = {'error': str(e)}
        engine_predictions['gap_analysis'] = []
    
    try:
        engines_results['markov_chain'] = markov_chain.analyze(lottery, order=1)
        engine_predictions['markov_chain'] = markov_chain.predict(lottery, order=1)
    except Exception as e:
        engines_results['markov_chain'] = {'error': str(e)}
        engine_predictions['markov_chain'] = []
    
    try:
        engines_results['bayesian'] = bayesian.analyze(lottery)
        engine_predictions['bayesian'] = bayesian.predict(lottery)
    except Exception as e:
        engines_results['bayesian'] = {'error': str(e)}
        engine_predictions['bayesian'] = []
    
    try:
        engines_results['pattern_detection'] = pattern_detection.analyze(lottery)
        engine_predictions['pattern_detection'] = pattern_detection.predict(lottery)
    except Exception as e:
        engines_results['pattern_detection'] = {'error': str(e)}
        engine_predictions['pattern_detection'] = []
    
    try:
        engines_results['entropy'] = entropy.analyze(lottery)
        engine_predictions['entropy'] = entropy.predict(lottery)
    except Exception as e:
        engines_results['entropy'] = {'error': str(e)}
        engine_predictions['entropy'] = []
    
    try:
        engines_results['monte_carlo'] = monte_carlo.analyze(lottery, iterations=2000)  # fewer for speed
        engine_predictions['monte_carlo'] = monte_carlo.predict(lottery)
    except Exception as e:
        engines_results['monte_carlo'] = {'error': str(e)}
        engine_predictions['monte_carlo'] = []
    
    # Combine: each number gets a score from each engine
    # Engine votes: top pick = main_picks points, second = main_picks-1, etc.
    pool_size = lottery.main_pool_size
    picks = lottery.main_picks
    
    number_scores = Counter()
    engine_contributions = {n: {} for n in range(1, pool_size + 1)}
    
    for engine_name, pred in engine_predictions.items():
        if not pred or engine_name not in weights:
            continue
        weight = weights[engine_name]
        for rank, n in enumerate(pred):
            # Score: (picks - rank) * weight
            score = (picks - rank) * weight
            number_scores[n] += score
            engine_contributions[n][engine_name] = {
                'rank': rank + 1,
                'weight': weight,
                'score': round(score, 3),
            }
    
    # Rank numbers by combined score
    ranked = sorted(number_scores.items(), key=lambda x: -x[1])
    
    return {
        'engine_predictions': engine_predictions,
        'engine_results': engines_results,
        'combined_scores': {n: round(s, 3) for n, s in number_scores.items()},
        'ranked_numbers': [(n, round(s, 3)) for n, s in ranked],
        'engine_contributions': engine_contributions,
        'weights_used': weights,
        'total_draws': lottery.total_draws(),
    }


def predict(lottery, weights: Dict[str, float] = None) -> List[int]:
    """Final ensemble prediction: top N numbers by combined score."""
    analysis = analyze(lottery, weights)
    ranked = analysis['ranked_numbers']
    return [n for n, _ in ranked[:lottery.main_picks]]


def predict_with_explanation(lottery, weights: Dict[str, float] = None) -> Dict:
    """Predict and return explanation of why each number was chosen."""
    analysis = analyze(lottery, weights)
    pred = [n for n, _ in analysis['ranked_numbers'][:lottery.main_picks]]
    
    explanations = []
    for rank, n in enumerate(pred, 1):
        contribs = analysis['engine_contributions'].get(n, {})
        # Find top 3 contributing engines
        top_engines = sorted(contribs.items(), key=lambda x: -x[1]['score'])[:3]
        reasons = []
        for eng, info in top_engines:
            if info['score'] > 0:
                reasons.append(f"{eng} (rank #{info['rank']}, peso {info['weight']:.2f})")
        
        explanations.append({
            'rank': rank,
            'number': n,
            'combined_score': analysis['combined_scores'].get(n, 0),
            'top_reasons': reasons,
        })
    
    return {
        'prediction': pred,
        'explanations': explanations,
        'analysis': analysis,
    }

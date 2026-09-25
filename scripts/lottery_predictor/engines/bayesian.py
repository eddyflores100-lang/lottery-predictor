"""
Engine 5: Bayesian Inference
Beta prior/posterior updating with credible intervals.
"""
from typing import List, Dict, Tuple
import math


def analyze(lottery, prior_alpha: float = 1.0, prior_beta: float = None) -> Dict:
    """
    For each number, model its appearance probability using Beta distribution.
    
    Prior: Beta(alpha, beta) where alpha=beta=1 (uniform) by default
    Update with observed data: number appeared k times in n draws
    Posterior: Beta(alpha + k, beta + n - k)
    
    We report the posterior mean (MAP estimate) and 95% credible interval.
    """
    total_draws = lottery.total_draws()
    if total_draws == 0:
        return {'error': 'No draws'}
    
    pool_size = lottery.main_pool_size
    picks = lottery.main_picks
    
    # Default prior: weak Beta centered on uniform probability
    if prior_beta is None:
        # Set prior mean = picks/pool, with weak strength
        prior_mean = picks / pool_size
        # Effective sample size of prior = 10 (weak)
        prior_strength = 10
        prior_alpha = prior_mean * prior_strength
        prior_beta = (1 - prior_mean) * prior_strength
    
    # Count appearances per number
    from collections import Counter
    counter = Counter()
    for d in lottery.draws:
        for n in d.main_numbers:
            counter[n] += 1
    
    per_number = {}
    for n in range(1, pool_size + 1):
        k = counter.get(n, 0)  # successes
        n_trials = total_draws  # total draws
        
        # Posterior parameters
        post_alpha = prior_alpha + k
        post_beta = prior_beta + (n_trials - k)
        
        # Posterior mean (MAP estimate of probability)
        post_mean = post_alpha / (post_alpha + post_beta)
        
        # 95% credible interval using normal approximation
        # std = sqrt((a*b) / ((a+b)^2 * (a+b+1)))
        post_var = (post_alpha * post_beta) / ((post_alpha + post_beta) ** 2 * (post_alpha + post_beta + 1))
        post_std = math.sqrt(post_var)
        
        # 95% CI: ±1.96 * std
        ci_lower = max(0, post_mean - 1.96 * post_std)
        ci_upper = min(1, post_mean + 1.96 * post_std)
        
        # Prior mean for comparison
        prior_mean = prior_alpha / (prior_alpha + prior_beta)
        
        per_number[n] = {
            'posterior_mean': round(post_mean, 4),
            'prior_mean': round(prior_mean, 4),
            'posterior_std': round(post_std, 4),
            'ci_95': [round(ci_lower, 4), round(ci_upper, 4)],
            'observed_freq': round(k / n_trials, 4) if n_trials > 0 else 0,
            'observed_count': k,
            'total_draws': n_trials,
            'bayes_factor': round(post_mean / prior_mean, 3) if prior_mean > 0 else 0,
        }
    
    return {
        'per_number': per_number,
        'prior_alpha': prior_alpha,
        'prior_beta': prior_beta,
        'total_draws': total_draws,
    }


def predict(lottery) -> List[int]:
    """Predict by selecting numbers with highest posterior mean."""
    analysis = analyze(lottery)
    if 'error' in analysis:
        return []
    
    per_number = analysis['per_number']
    ranked = sorted(per_number.items(), key=lambda x: -x[1]['posterior_mean'])
    return [n for n, _ in ranked[:lottery.main_picks]]

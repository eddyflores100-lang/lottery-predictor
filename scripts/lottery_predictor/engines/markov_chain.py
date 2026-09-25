"""
Engine 4: Markov Chain
First-order and second-order transition matrices for sequential dependency capture.
"""
from collections import defaultdict, Counter
from typing import List, Dict, Tuple
import math


def analyze(lottery, order: int = 1) -> Dict:
    """
    Build Markov transition matrix.
    
    For order=1: P(number n appears in next draw | number m appeared in last draw)
    For order=2: P(number n appears | (m1, m2) appeared in last 2 draws)
    
    Note: This is a "soft" Markov chain since multiple numbers appear in each draw.
    We track co-occurrence transition: which numbers tend to follow which.
    """
    total_draws = lottery.total_draws()
    if total_draws < 2:
        return {'error': 'Need at least 2 draws'}
    
    pool_size = lottery.main_pool_size
    draws = lottery.draws
    
    if order == 1:
        # First-order: for each number m, count what numbers appear in the NEXT draw
        transitions = defaultdict(Counter)
        for i in range(len(draws) - 1):
            current_nums = set(draws[i].main_numbers)
            next_nums = draws[i + 1].main_numbers
            for m in current_nums:
                for n in next_nums:
                    transitions[m][n] += 1
        
        # Normalize to probabilities
        transition_matrix = {}
        for m in range(1, pool_size + 1):
            total = sum(transitions[m].values())
            if total > 0:
                transition_matrix[m] = {
                    n: transitions[m].get(n, 0) / total
                    for n in range(1, pool_size + 1)
                }
            else:
                # Uniform prior
                transition_matrix[m] = {n: 1 / pool_size for n in range(1, pool_size + 1)}
        
        # Predict: based on the LAST draw's numbers, what's most likely next?
        last_draw_nums = draws[-1].main_numbers
        next_probs = Counter()
        for m in last_draw_nums:
            if m in transition_matrix:
                for n, p in transition_matrix[m].items():
                    next_probs[n] += p
        # Average over the numbers in last draw
        for n in next_probs:
            next_probs[n] /= len(last_draw_nums)
        
        return {
            'order': 1,
            'transition_matrix': transition_matrix,
            'next_draw_probs': dict(next_probs),
            'last_draw': last_draw_nums,
            'total_draws': total_draws,
        }
    
    elif order == 2:
        # Second-order: track (m1, m2) -> next
        transitions = defaultdict(Counter)
        for i in range(len(draws) - 2):
            nums_2_ago = frozenset(draws[i].main_numbers)
            nums_1_ago = frozenset(draws[i + 1].main_numbers)
            next_nums = draws[i + 2].main_numbers
            
            # For each pair (m1 from 2 ago, m2 from 1 ago)
            for m1 in nums_2_ago:
                for m2 in nums_1_ago:
                    key = (m1, m2)
                    for n in next_nums:
                        transitions[key][n] += 1
        
        # Predict based on last 2 draws
        if len(draws) >= 2:
            last_2_ago = frozenset(draws[-2].main_numbers)
            last_1_ago = frozenset(draws[-1].main_numbers)
            next_probs = Counter()
            count = 0
            for m1 in last_2_ago:
                for m2 in last_1_ago:
                    key = (m1, m2)
                    if key in transitions:
                        total = sum(transitions[key].values())
                        for n, c in transitions[key].items():
                            next_probs[n] += c / total
                        count += 1
            if count > 0:
                for n in next_probs:
                    next_probs[n] /= count
        else:
            next_probs = Counter()
        
        return {
            'order': 2,
            'next_draw_probs': dict(next_probs),
            'last_2_draws': [draws[-2].main_numbers, draws[-1].main_numbers],
            'total_draws': total_draws,
        }


def predict(lottery, order: int = 1) -> List[int]:
    """Predict next draw numbers using Markov chain."""
    analysis = analyze(lottery, order=order)
    if 'error' in analysis:
        return []
    
    probs = analysis.get('next_draw_probs', {})
    # Sort by probability descending
    ranked = sorted(probs.items(), key=lambda x: -x[1])
    return [n for n, _ in ranked[:lottery.main_picks]]

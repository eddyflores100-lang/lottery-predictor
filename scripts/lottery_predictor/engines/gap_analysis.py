"""
Engine 3: Gap Analysis
Tracks draws since last appearance, overdue detection, and next-appearance probability modeling.
"""
from collections import defaultdict
from typing import List, Dict, Tuple
import math


def analyze(lottery) -> Dict:
    """
    For each number, compute:
    - Current gap (draws since last appearance)
    - Average gap (historical mean between appearances)
    - Max gap (historical maximum)
    - Overdue score (current_gap / average_gap)
    - Next appearance probability (using geometric distribution)
    """
    total_draws = lottery.total_draws()
    if total_draws == 0:
        return {'error': 'No draws'}
    
    pool_size = lottery.main_pool_size
    draws = lottery.draws
    
    # For each number, track all appearance draw numbers
    appearances = defaultdict(list)
    for d in draws:
        for n in d.main_numbers:
            appearances[n].append(d.draw_number)
    
    latest_draw = draws[-1].draw_number
    
    per_number = {}
    for n in range(1, pool_size + 1):
        apps = appearances.get(n, [])
        
        if not apps:
            # Never appeared
            current_gap = total_draws
            avg_gap = total_draws
            max_gap = total_draws
            next_prob = 1 - (1 - lottery.main_picks/pool_size) ** 1  # one draw ahead
        else:
            current_gap = latest_draw - apps[-1]
            if len(apps) > 1:
                gaps = [apps[i+1] - apps[i] for i in range(len(apps)-1)]
                avg_gap = sum(gaps) / len(gaps)
                max_gap = max(gaps)
            else:
                avg_gap = current_gap
                max_gap = current_gap
            
            # Next appearance probability using geometric distribution
            # p = 1/avg_gap (probability of appearing in next draw given historical avg)
            if avg_gap > 0:
                p = 1 / avg_gap
                # Probability of appearing in next 1 draw
                next_prob = p
            else:
                next_prob = 0
        
        # Overdue score: 1.0 = on schedule, >1.0 = overdue
        overdue_score = current_gap / avg_gap if avg_gap > 0 else 0
        
        per_number[n] = {
            'current_gap': current_gap,
            'avg_gap': round(avg_gap, 2),
            'max_gap': max_gap,
            'overdue_score': round(overdue_score, 2),
            'next_appearance_prob': round(next_prob, 3),
            'total_appearances': len(apps),
            'last_appearance_draw': apps[-1] if apps else None,
        }
    
    return {
        'per_number': per_number,
        'total_draws': total_draws,
        'latest_draw': latest_draw,
    }


def get_overdue_numbers(analysis: Dict, top_n: int = 5) -> List[int]:
    """Get the most overdue numbers (highest overdue_score)."""
    per_number = analysis.get('per_number', {})
    ranked = sorted(per_number.items(), key=lambda x: -x[1]['overdue_score'])
    return [n for n, _ in ranked[:top_n]]


def predict(lottery) -> List[int]:
    """Predict by selecting the most overdue N numbers."""
    analysis = analyze(lottery)
    return get_overdue_numbers(analysis, lottery.main_picks)

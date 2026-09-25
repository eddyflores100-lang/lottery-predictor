"""
Expected Value Calculator
==========================

For each lottery, computes:
- EV per $1 ticket = (P_jackpot × jackpot) + (P_minor_prizes × minor_prizes) - 1
- Edge over house
- Kelly fraction
- Ranking by EV

The key insight: most lotteries have NEGATIVE EV. But when jackpots accumulate
(roll over), EV can become positive. This module identifies those moments.
"""
import sys, os, json, math
sys.path.insert(0, '/home/z/my-project/scripts/lottery_predictor')

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict


# Typical prize structures for major lotteries (approximate, in USD)
# Format: {n_matches: (probability, prize)}
# Probability is per-ticket; prize is average payout
PRIZE_STRUCTURES = {
    'pozo_millonario': {
        # 11/25 + mascota
        11: (1/4_457_400, 500_000),  # jackpot (varies, but min)
        10: (1/120_741, 500),         # 10 aciertos
        9: (1/1_625, 10),
        8: (1/100, 2),
        7: (1/9, 1),
        'mascota': (1/15, 1),
    },
    'euromillions': {
        # 5/50 + 2/12
        '5+2': (1/139_838_160, 17_000_000),  # jackpot
        '5+1': (1/6_991_908, 300_000),
        '5+0': (1/3_107_515, 50_000),
        '4+2': (1/621_503, 2_000),
        '4+1': (1/31_075, 100),
        '4+0': (1/13_811, 50),
        '3+2': (1/14_125, 50),
        '3+1': (1/706, 15),
        '2+2': (1/985, 10),
        '3+0': (1/314, 10),
        '1+2': (1/188, 5),
        '2+1': (1/49, 5),
        '2+0': (1/22, 3),
    },
    'la_primitiva': {
        # 6/49 + reintegro (0-9)
        '6+R': (1/139_838_160, 8_000_000),
        6: (1/13_983_816, 100_000),
        5: (1/55_491, 2_500),
        4: (1/1_032, 30),
        3: (1/57, 8),
    },
    'lotto_austrian': {
        6: (1/8_145_060, 1_500_000),
        5: (1/35_724, 1_500),
        4: (1/1_033, 35),
        3: (1/58, 5),
    },
    'us_powerball': {
        '5+1': (1/292_201_338, 20_000_000),
        5: (1/11_688_053, 1_000_000),
        '4+1': (1/913_129, 50_000),
        4: (1/36_525, 100),
        '3+1': (1/14_494, 100),
        3: (1/580, 7),
        '2+1': (1/701, 7),
        1: (1/92, 4),
        '0+1': (1/38, 4),
    },
    'mega_millions': {
        '5+1': (1/302_575_350, 20_000_000),
        5: (1/12_607_306, 1_000_000),
        '4+1': (1/931_001, 10_000),
        4: (1/38_792, 500),
        '3+1': (1/14_547, 200),
        3: (1/606, 10),
        '2+1': (1/693, 10),
        '1+1': (1/89, 4),
        '0+1': (1/37, 2),
    },
}

# Default ticket costs in USD
TICKET_COSTS = {
    'pozo_millonario': 1.0,
    'euromillions': 2.50,
    'la_primitiva': 1.50,
    'lotto_austrian': 2.20,
    'us_powerball': 2.0,
    'mega_millions': 2.0,
    'uk49s': 1.0,
    'sa_lotto': 0.50,
    'sa_powerball': 0.50,
    'sa_daily_lotto': 0.30,
}


@dataclass
class EVResult:
    """Expected Value analysis for one lottery."""
    lottery_key: str
    lottery_name: str
    ticket_cost: float
    jackpot: float
    total_probability_win_anything: float
    ev_per_dollar: float
    ev_absolute: float
    edge_percent: float
    kelly_fraction: float
    should_play: bool
    rank: int = 0  # set later when ranking
    
    def to_dict(self):
        return asdict(self)


def compute_ev_for_lottery(lottery_key: str, lottery_name: str,
                            jackpot_override: Optional[float] = None) -> Optional[EVResult]:
    """
    Compute EV for a lottery.
    
    Args:
        lottery_key: key in PRIZE_STRUCTURES
        lottery_name: display name
        jackpot_override: current jackpot (if rolled over, can be much higher than min)
    """
    if lottery_key not in PRIZE_STRUCTURES:
        return None
    
    prizes = PRIZE_STRUCTURES[lottery_key]
    cost = TICKET_COSTS.get(lottery_key, 1.0)
    
    # Use override jackpot if provided
    if jackpot_override:
        # Update the top prize
        prizes = dict(prizes)
        first_key = list(prizes.keys())[0]
        prizes[first_key] = (prizes[first_key][0], jackpot_override)
    
    # Compute EV
    ev_absolute = 0
    total_prob = 0
    for tier, (prob, prize) in prizes.items():
        ev_absolute += prob * prize
        total_prob += prob
    
    ev_per_dollar = (ev_absolute - cost) / cost
    edge = ev_per_dollar * 100
    
    # Kelly
    # For lottery, we have multiple outcomes, but the dominant one is the jackpot
    # Simplified Kelly: use jackpot probability and prize
    main_tier = list(prizes.keys())[0]
    main_prob, main_prize = prizes[main_tier]
    if main_prize > 0 and main_prob > 0:
        b = main_prize / cost
        p = main_prob
        q = 1 - p
        kelly = (p * b - q) / b
    else:
        kelly = 0
    
    should_play = ev_per_dollar > 0  # positive EV
    
    return EVResult(
        lottery_key=lottery_key,
        lottery_name=lottery_name,
        ticket_cost=cost,
        jackpot=jackpot_override or list(prizes.values())[0][1],
        total_probability_win_anything=total_prob,
        ev_per_dollar=ev_per_dollar,
        ev_absolute=ev_absolute,
        edge_percent=edge,
        kelly_fraction=kelly,
        should_play=should_play,
    )


def compute_all_evs(jackpot_overrides: Optional[Dict[str, float]] = None) -> List[EVResult]:
    """
    Compute EV for all lotteries with known prize structures.
    
    Args:
        jackpot_overrides: dict of lottery_key -> current jackpot (for rollover analysis)
    """
    if jackpot_overrides is None:
        jackpot_overrides = {}
    
    name_map = {
        'pozo_millonario': 'Pozo Millonario',
        'euromillions': 'EuroMillions',
        'la_primitiva': 'La Primitiva',
        'lotto_austrian': 'Lotto 6aus45',
        'us_powerball': 'US PowerBall',
        'mega_millions': 'Mega Millions',
    }
    
    results = []
    for key in PRIZE_STRUCTURES.keys():
        result = compute_ev_for_lottery(
            key, name_map.get(key, key),
            jackpot_override=jackpot_overrides.get(key),
        )
        if result:
            results.append(result)
    
    # Rank by EV
    results.sort(key=lambda x: -x.ev_per_dollar)
    for i, r in enumerate(results, 1):
        r.rank = i
    
    return results


def print_ev_ranking(jackpot_overrides: Optional[Dict[str, float]] = None):
    """Print EV ranking for all lotteries."""
    results = compute_all_evs(jackpot_overrides)
    
    print(f"\n{'='*100}")
    print(f"EXPECTED VALUE RANKING — ¿Qué lotería vale la pena jugar?")
    print(f"{'='*100}")
    print(f"\n{'Rank':<5} {'Lotería':<22} {'Ticket':>7} {'Jackpot':>15} {'EV/$1':>10} {'Edge':>10} {'Kelly':>10} {'Jugar?':>8}")
    print('-' * 100)
    
    for r in results:
        jugar = '✅ SÍ' if r.should_play else '❌ no'
        print(f"{r.rank:<5} {r.lottery_name:<22} ${r.ticket_cost:>5.2f} ${r.jackpot:>12,.0f} {r.ev_per_dollar:>+10.4f} {r.edge_percent:>+9.2f}% {r.kelly_fraction:>10.4f} {jugar:>8}")
    
    # Highlight
    positive = [r for r in results if r.should_play]
    print(f"\n📊 RESUMEN:")
    print(f"  Loterías con EV positivo: {len(positive)}/{len(results)}")
    if positive:
        best = positive[0]
        print(f"  🏆 Mejor opción: {best.lottery_name} (EV ${best.ev_per_dollar:+.4f} por $1)")
    else:
        print(f"  ❌ Ninguna lotería tiene EV positivo con jackpot mínimo.")
        print(f"     Las loterías se vuelven jugables cuando el jackpot acumula (rollover).")
    
    return results


def simulate_rollover(lottery_key: str, min_jackpot: float, max_jackpot: float,
                       step: float = 1_000_000) -> List[Dict]:
    """
    Simulate how EV changes as jackpot rolls over (accumulates).
    
    Returns list of {jackpot, ev_per_dollar, should_play, kelly} for each step.
    """
    name_map = {
        'pozo_millonario': 'Pozo Millonario',
        'euromillions': 'EuroMillions',
        'la_primitiva': 'La Primitiva',
        'lotto_austrian': 'Lotto 6aus45',
        'us_powerball': 'US PowerBall',
        'mega_millions': 'Mega Millions',
    }
    
    results = []
    jackpot = min_jackpot
    while jackpot <= max_jackpot:
        r = compute_ev_for_lottery(lottery_key, name_map.get(lottery_key, lottery_key),
                                    jackpot_override=jackpot)
        if r:
            results.append({
                'jackpot': jackpot,
                'ev_per_dollar': r.ev_per_dollar,
                'edge_percent': r.edge_percent,
                'should_play': r.should_play,
                'kelly_fraction': r.kelly_fraction,
            })
        jackpot += step
    
    return results


def find_break_even_jackpot(lottery_key: str) -> Optional[float]:
    """
    Find the jackpot amount at which EV becomes positive (break-even).
    
    For most lotteries this is much higher than the minimum jackpot.
    """
    name_map = {
        'pozo_millonario': 'Pozo Millonario',
        'euromillions': 'EuroMillions',
        'la_primitiva': 'La Primitiva',
        'lotto_austrian': 'Lotto 6aus45',
        'us_powerball': 'US PowerBall',
        'mega_millions': 'Mega Millions',
    }
    
    if lottery_key not in PRIZE_STRUCTURES:
        return None
    
    # Binary search for break-even
    lo, hi = 100_000, 1_000_000_000
    for _ in range(50):
        mid = (lo + hi) / 2
        r = compute_ev_for_lottery(lottery_key, name_map.get(lottery_key, lottery_key),
                                    jackpot_override=mid)
        if r and r.ev_per_dollar > 0:
            hi = mid
        else:
            lo = mid
    
    return hi


if __name__ == '__main__':
    print_ev_ranking()
    
    print(f"\n\n{'='*80}")
    print(f"BREAK-EVEN JACKPOT (EV = 0)")
    print(f"{'='*80}")
    for key in PRIZE_STRUCTURES.keys():
        be = find_break_even_jackpot(key)
        if be:
            print(f"  {key:<22} ${be:>15,.0f}")
    
    print(f"\n\n{'='*80}")
    print(f"SIMULACIÓN DE ROLLOVER — EuroMillions")
    print(f"{'='*80}")
    results = simulate_rollover('euromillions', 17_000_000, 200_000_000, 10_000_000)
    print(f"\n{'Jackpot':>15} {'EV/$1':>10} {'Edge':>10} {'Jugar?':>8}")
    for r in results:
        jugar = '✅' if r['should_play'] else '❌'
        print(f"${r['jackpot']:>12,.0f} {r['ev_per_dollar']:>+10.4f} {r['edge_percent']:>+9.2f}% {jugar:>8}")

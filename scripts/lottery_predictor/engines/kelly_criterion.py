"""
Engine 11: Kelly Criterion + Bankroll Management
================================================
The mathematically optimal way to size bets when you have an edge.

Key formulas:
- Expected Value: EV = (P_win × Prize) - Cost
- Kelly fraction: f = (p × b - q) / b  where b = Prize/Cost, p = P_win, q = 1-p
- Full Kelly is too aggressive; we use fractional Kelly (1/4, 1/2) for safety
- Stop-loss: stop playing if bankroll drops below X% of initial
- Take-profit: lock profits when bankroll grows Y%

This module answers the question: "Given my bankroll and the predicted edge,
should I play, and if so, how much should I bet?"
"""
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class BetRecommendation:
    """Result of Kelly analysis for a single lottery ticket purchase."""
    should_play: bool
    bet_size_usd: float          # recommended bet amount
    bet_fraction: float          # fraction of bankroll (0 to 1)
    kelly_fraction: float        # raw Kelly (can be negative)
    ev_per_dollar: float         # expected value per $1 bet
    edge_percent: float          # edge over the house
    confidence: str              # LOW / MEDIUM / HIGH
    reasoning: str               # human-readable explanation
    stop_loss_triggered: bool = False
    take_profit_triggered: bool = False


def compute_kelly(probability: float, prize: float, cost: float) -> float:
    """
    Compute Kelly fraction.
    
    f* = (p × b - q) / b
    where:
      p = probability of winning
      q = 1 - p = probability of losing
      b = prize / cost (the odds ratio)
    
    Returns:
        Kelly fraction (can be negative = don't bet)
    """
    if cost <= 0 or prize <= 0 or probability <= 0:
        return 0.0
    
    b = prize / cost
    p = probability
    q = 1 - p
    
    f = (p * b - q) / b
    return f


def compute_ev(probability: float, prize: float, cost: float) -> float:
    """Compute expected value per $1 bet."""
    if cost <= 0:
        return 0
    return (probability * prize - cost) / cost


def recommend_bet(
    probability: float,
    prize: float,
    cost: float,
    bankroll: float,
    kelly_fraction: float = 0.25,  # 1/4 Kelly for safety
    max_bet_pct: float = 0.05,     # never bet more than 5% of bankroll
    min_bet: float = 1.0,
    stop_loss_pct: float = 0.5,    # stop if bankroll drops to 50% of initial
    take_profit_pct: float = 2.0,  # take profits at 2x bankroll
    initial_bankroll: Optional[float] = None,
) -> BetRecommendation:
    """
    Generate a betting recommendation using Kelly Criterion.
    
    Args:
        probability: P(win jackpot) — usually 1/odds_jackpot
        prize: jackpot amount
        cost: ticket cost
        bankroll: current bankroll
        kelly_fraction: fraction of full Kelly to use (0.25 = quarter Kelly)
        max_bet_pct: max % of bankroll to bet on single draw
        min_bet: minimum bet (typically 1 ticket = $1-2)
        stop_loss_pct: stop playing if bankroll drops below this fraction of initial
        take_profit_pct: take profits when bankroll reaches this multiple
        initial_bankroll: starting bankroll (defaults to current bankroll)
    
    Returns:
        BetRecommendation with all analysis
    """
    if initial_bankroll is None:
        initial_bankroll = bankroll
    
    # Check stop-loss / take-profit
    stop_loss = bankroll < initial_bankroll * stop_loss_pct
    take_profit = bankroll >= initial_bankroll * take_profit_pct
    
    if stop_loss:
        return BetRecommendation(
            should_play=False,
            bet_size_usd=0,
            bet_fraction=0,
            kelly_fraction=0,
            ev_per_dollar=0,
            edge_percent=0,
            confidence='STOP-LOSS',
            reasoning=f"Stop-loss triggered: bankroll (${bankroll:,.2f}) below ${initial_bankroll * stop_loss_pct:,.2f} ({stop_loss_pct*100:.0f}% of initial). Stop playing.",
            stop_loss_triggered=True,
        )
    
    if take_profit:
        return BetRecommendation(
            should_play=False,
            bet_size_usd=0,
            bet_fraction=0,
            kelly_fraction=0,
            ev_per_dollar=0,
            edge_percent=0,
            confidence='TAKE-PROFIT',
            reasoning=f"Take-profit triggered: bankroll (${bankroll:,.2f}) reached ${initial_bankroll * take_profit_pct:,.2f} ({take_profit_pct}x initial). Lock profits.",
            take_profit_triggered=True,
        )
    
    # Compute Kelly and EV
    full_kelly = compute_kelly(probability, prize, cost)
    ev = compute_ev(probability, prize, cost)
    edge = ev * 100
    
    # Apply fractional Kelly
    fractional_kelly = full_kelly * kelly_fraction
    
    # Compute bet size
    if fractional_kelly <= 0:
        # No edge — don't bet
        return BetRecommendation(
            should_play=False,
            bet_size_usd=0,
            bet_fraction=0,
            kelly_fraction=full_kelly,
            ev_per_dollar=ev,
            edge_percent=edge,
            confidence='NO-EDGE',
            reasoning=f"No statistical edge. Kelly = {full_kelly:.4f} (negative). EV per $1 = ${ev:.4f}. Don't play.",
        )
    
    # Bet = fractional_kelly × bankroll, capped at max_bet_pct
    bet_fraction = min(fractional_kelly, max_bet_pct)
    bet_size = max(bet_fraction * bankroll, min_bet)
    bet_size = min(bet_size, max_bet_pct * bankroll)
    
    # Confidence level
    if full_kelly > 0.05:
        confidence = 'HIGH'
    elif full_kelly > 0.01:
        confidence = 'MEDIUM'
    else:
        confidence = 'LOW'
    
    # Reasoning
    reasoning_parts = [
        f"Kelly fraction: {full_kelly:.4f} (using {kelly_fraction*100:.0f}% = {fractional_kelly:.4f})",
        f"EV per $1: ${ev:.4f} (edge: {edge:+.2f}%)",
        f"Bet size: ${bet_size:.2f} ({bet_fraction*100:.2f}% of bankroll)",
        f"Bankroll: ${bankroll:,.2f}",
    ]
    
    if bet_size < min_bet:
        reasoning_parts.append(f"Adjusted to minimum bet (${min_bet})")
        bet_size = min_bet
    
    return BetRecommendation(
        should_play=True,
        bet_size_usd=bet_size,
        bet_fraction=bet_fraction,
        kelly_fraction=full_kelly,
        ev_per_dollar=ev,
        edge_percent=edge,
        confidence=confidence,
        reasoning=' | '.join(reasoning_parts),
    )


def simulate_bankroll(
    initial_bankroll: float,
    probability: float,
    prize: float,
    cost: float,
    n_draws: int = 100,
    kelly_fraction: float = 0.25,
    max_bet_pct: float = 0.05,
    stop_loss_pct: float = 0.5,
    take_profit_pct: float = 2.0,
    seed: int = 42,
) -> Dict:
    """
    Simulate playing n_draws with Kelly sizing.
    Returns bankroll trajectory and statistics.
    
    This is a Monte Carlo simulation — single run for a single path.
    For statistical significance, run multiple times with different seeds.
    """
    import random
    random.seed(seed)
    
    bankroll = initial_bankroll
    trajectory = [bankroll]
    bets = []
    wins = 0
    losses = 0
    stop_loss_hit = False
    take_profit_hit = False
    
    for i in range(n_draws):
        if bankroll <= 0:
            break
        
        rec = recommend_bet(
            probability=probability,
            prize=prize,
            cost=cost,
            bankroll=bankroll,
            kelly_fraction=kelly_fraction,
            max_bet_pct=max_bet_pct,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            initial_bankroll=initial_bankroll,
        )
        
        if not rec.should_play:
            if rec.stop_loss_triggered:
                stop_loss_hit = True
                break
            if rec.take_profit_triggered:
                take_profit_hit = True
                break
            # No edge — skip
            trajectory.append(bankroll)
            continue
        
        bet = rec.bet_size_usd
        bets.append(bet)
        bankroll -= bet  # pay for ticket
        
        # Did we win? (probability is per-ticket)
        if random.random() < probability:
            bankroll += prize
            wins += 1
        else:
            losses += 1
        
        trajectory.append(bankroll)
    
    final = bankroll
    roi = (final - initial_bankroll) / initial_bankroll * 100 if initial_bankroll > 0 else 0
    avg_bet = sum(bets) / len(bets) if bets else 0
    total_bet = sum(bets)
    max_bankroll = max(trajectory)
    min_bankroll = min(trajectory)
    
    return {
        'initial_bankroll': initial_bankroll,
        'final_bankroll': final,
        'roi_percent': roi,
        'total_wins': wins,
        'total_losses': losses,
        'total_bets': len(bets),
        'total_bet_amount': total_bet,
        'avg_bet': avg_bet,
        'max_bankroll': max_bankroll,
        'min_bankroll': min_bankroll,
        'stop_loss_hit': stop_loss_hit,
        'take_profit_hit': take_profit_hit,
        'trajectory': trajectory,
    }


def monte_carlo_bankroll(
    initial_bankroll: float,
    probability: float,
    prize: float,
    cost: float,
    n_draws: int = 100,
    n_simulations: int = 1000,
    kelly_fraction: float = 0.25,
    **kwargs
) -> Dict:
    """
    Run Monte Carlo simulation: n_simulations runs of n_draws each.
    
    Returns percentiles (P10, P50, P90) of final bankroll, bankruptcy rate,
    and other statistics.
    """
    results = []
    for seed in range(n_simulations):
        result = simulate_bankroll(
            initial_bankroll=initial_bankroll,
            probability=probability,
            prize=prize,
            cost=cost,
            n_draws=n_draws,
            kelly_fraction=kelly_fraction,
            seed=seed,
            **kwargs,
        )
        results.append(result)
    
    final_bankrolls = sorted([r['final_bankroll'] for r in results])
    rois = sorted([r['roi_percent'] for r in results])
    bankruptcies = sum(1 for r in results if r['final_bankroll'] <= 0)
    stop_losses = sum(1 for r in results if r['stop_loss_hit'])
    take_profits = sum(1 for r in results if r['take_profit_hit'])
    
    def pct(sorted_list, p):
        idx = int((p / 100) * (len(sorted_list) - 1))
        return sorted_list[max(0, min(idx, len(sorted_list) - 1))]
    
    return {
        'n_simulations': n_simulations,
        'n_draws_per_sim': n_draws,
        'final_bankroll_p10': pct(final_bankrolls, 10),
        'final_bankroll_p50': pct(final_bankrolls, 50),
        'final_bankroll_p90': pct(final_bankrolls, 90),
        'final_bankroll_mean': sum(final_bankrolls) / len(final_bankrolls),
        'roi_p10': pct(rois, 10),
        'roi_p50': pct(rois, 50),
        'roi_p90': pct(rois, 90),
        'roi_mean': sum(rois) / len(rois),
        'bankruptcy_rate': bankruptcies / n_simulations,
        'stop_loss_rate': stop_losses / n_simulations,
        'take_profit_rate': take_profits / n_simulations,
        'expected_wins_per_sim': sum(r['total_wins'] for r in results) / n_simulations,
        'kelly_fraction_used': kelly_fraction,
        'parameters': {
            'probability': probability,
            'prize': prize,
            'cost': cost,
            'initial_bankroll': initial_bankroll,
        },
    }


def analyze(lottery, bankroll: float = 1000, ticket_cost: float = 1.0,
            jackpot_override: Optional[float] = None) -> Dict:
    """
    Analyze a lottery using Kelly criterion.
    
    Args:
        lottery: Lottery instance
        bankroll: player's bankroll in USD
        ticket_cost: cost per ticket
        jackpot_override: use this jackpot instead of min_jackpot
    """
    probability = 1 / lottery.odds_jackpot
    prize = jackpot_override or lottery.min_jackpot
    
    rec = recommend_bet(
        probability=probability,
        prize=prize,
        cost=ticket_cost,
        bankroll=bankroll,
    )
    
    ev = compute_ev(probability, prize, ticket_cost)
    
    return {
        'lottery_name': lottery.name,
        'probability': probability,
        'prize': prize,
        'ticket_cost': ticket_cost,
        'kelly_fraction': rec.kelly_fraction,
        'ev_per_dollar': ev,
        'edge_percent': rec.edge_percent,
        'should_play': rec.should_play,
        'bet_size': rec.bet_size_usd,
        'confidence': rec.confidence,
        'reasoning': rec.reasoning,
        'bankroll': bankroll,
    }


def predict(lottery, **kwargs) -> List[int]:
    """Kelly doesn't predict numbers — it predicts bet size. Falls back to frequency."""
    from .frequency import predict as freq_predict
    return freq_predict(lottery)

"""
Generic Lottery class for any lottery defined by config.
Loaded from JSON files (converted from bettip.co.za API).
"""
from pathlib import Path
import json
from .base import Lottery, DrawResult


class GenericLottery(Lottery):
    """Generic lottery that loads from JSON."""
    
    def __init__(self, name, country, main_pool_size, main_picks,
                 bonus_pool_size=0, bonus_picks=0, draws_per_week=2,
                 currency='USD', min_jackpot=1_000_000, odds_jackpot=10_000_000,
                 data_file=None):
        self.name = name
        self.country = country
        self.main_pool_size = main_pool_size
        self.main_picks = main_picks
        self.bonus_pool_size = bonus_pool_size
        self.bonus_picks = bonus_picks
        self.draws_per_week = draws_per_week
        self.currency = currency
        self.min_jackpot = min_jackpot
        self.odds_jackpot = odds_jackpot
        self._data_file = data_file
        self.draws = []
        if data_file:
            self.load_data(data_file)
    
    def load_data(self, source: str) -> None:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {source}")
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        # Handle both formats:
        # 1. List of draws directly: [{draw_number, date, main_numbers, ...}, ...]
        # 2. Quicklotto format: {lottery: {...}, draws: [...]}
        if isinstance(data, dict) and 'draws' in data:
            draws_data = data['draws']
        elif isinstance(data, list):
            draws_data = data
        else:
            draws_data = []
        
        self.draws = []
        for r in draws_data:
            draw = DrawResult(
                draw_number=r['draw_number'],
                date=r['date'],
                main_numbers=r['main_numbers'],
                bonus_numbers=r.get('bonus_numbers', []),
                jackpot_won=r.get('jackpot_won', False),
                jackpot_amount=r.get('jackpot_amount'),
                raw_data=r.get('raw_data', {})
            )
            self.draws.append(draw)
        self.draws.sort(key=lambda d: d.draw_number)


# ============================================================
# Lottery configurations (10 new lotteries from bettip.co.za)
# ============================================================

DATA_DIR = '/home/z/my-project/data'

# Compute odds for n/k format
import math
def odds(picks, pool, bonus_pool=0, bonus_picks=0):
    main = math.comb(pool, picks)
    if bonus_picks > 0:
        return main * math.comb(bonus_pool, bonus_picks)
    return main


NEW_LOTTERIES = {
    'uk49s': {
        'name': 'UK49s Lunchtime',
        'country': 'United Kingdom',
        'main_pool_size': 49,
        'main_picks': 6,
        'bonus_pool_size': 49,
        'bonus_picks': 1,  # booster
        'draws_per_week': 14,  # 2 per day
        'currency': 'GBP',
        'min_jackpot': 125_000,
        'data_file': f'{DATA_DIR}/uk49s.json',
    },
    'sa_lotto': {
        'name': 'SA Lotto',
        'country': 'South Africa',
        'main_pool_size': 52,
        'main_picks': 6,
        'bonus_pool_size': 52,
        'bonus_picks': 1,  # bonus
        'draws_per_week': 2,
        'currency': 'ZAR',
        'min_jackpot': 5_000_000,
        'data_file': f'{DATA_DIR}/sa_lotto_6_52.json',
    },
    'sa_powerball': {
        'name': 'SA PowerBall',
        'country': 'South Africa',
        'main_pool_size': 50,
        'main_picks': 5,
        'bonus_pool_size': 20,  # PowerBall
        'bonus_picks': 1,
        'draws_per_week': 2,
        'currency': 'ZAR',
        'min_jackpot': 30_000_000,
        'data_file': f'{DATA_DIR}/sa_powerball.json',
    },
    'sa_daily_lotto': {
        'name': 'SA Daily Lotto',
        'country': 'South Africa',
        'main_pool_size': 36,
        'main_picks': 5,
        'bonus_pool_size': 0,
        'bonus_picks': 0,
        'draws_per_week': 7,
        'currency': 'ZAR',
        'min_jackpot': 100_000,
        'data_file': f'{DATA_DIR}/sa_daily_lotto.json',
    },
    'uk_lotto': {
        'name': 'UK Lotto',
        'country': 'United Kingdom',
        'main_pool_size': 59,
        'main_picks': 6,
        'bonus_pool_size': 59,
        'bonus_picks': 1,  # Bonus Ball
        'draws_per_week': 2,
        'currency': 'GBP',
        'min_jackpot': 2_000_000,
        'data_file': f'{DATA_DIR}/uk_lotto.json',
    },
    'irish_lotto': {
        'name': 'Irish Lotto',
        'country': 'Ireland',
        'main_pool_size': 47,
        'main_picks': 6,
        'bonus_pool_size': 47,
        'bonus_picks': 1,
        'draws_per_week': 2,
        'currency': 'EUR',
        'min_jackpot': 2_000_000,
        'data_file': f'{DATA_DIR}/irish_lotto.json',
    },
    'france_lotto': {
        'name': 'France Lotto (Loto)',
        'country': 'France',
        'main_pool_size': 49,
        'main_picks': 5,
        'bonus_pool_size': 10,  # Numéro Chance
        'bonus_picks': 1,
        'draws_per_week': 3,
        'currency': 'EUR',
        'min_jackpot': 2_000_000,
        'data_file': f'{DATA_DIR}/france_lotto.json',
    },
    'us_powerball': {
        'name': 'US PowerBall',
        'country': 'United States',
        'main_pool_size': 69,
        'main_picks': 5,
        'bonus_pool_size': 26,  # Powerball
        'bonus_picks': 1,
        'draws_per_week': 3,
        'currency': 'USD',
        'min_jackpot': 20_000_000,
        'data_file': f'{DATA_DIR}/us_powerball.json',
    },
    'mega_millions': {
        'name': 'Mega Millions',
        'country': 'United States',
        'main_pool_size': 70,
        'main_picks': 5,
        'bonus_pool_size': 25,  # Mega Ball
        'bonus_picks': 1,
        'draws_per_week': 2,
        'currency': 'USD',
        'min_jackpot': 20_000_000,
        'data_file': f'{DATA_DIR}/mega_millions.json',
    },
    'greece_powerball': {
        'name': 'Greece Powerball (TZOKER)',
        'country': 'Greece',
        'main_pool_size': 45,
        'main_picks': 5,
        'bonus_pool_size': 20,  # Powerball
        'bonus_picks': 1,
        'draws_per_week': 2,
        'currency': 'EUR',
        'min_jackpot': 100_000,
        'data_file': f'{DATA_DIR}/greece_powerball.json',
    },
    'greek_lotto': {
        'name': 'Greek Lotto',
        'country': 'Greece',
        'main_pool_size': 49,
        'main_picks': 6,
        'bonus_pool_size': 0,
        'bonus_picks': 0,
        'draws_per_week': 2,
        'currency': 'EUR',
        'min_jackpot': 100_000,
        'data_file': f'{DATA_DIR}/greek_lotto.json',
    },
    'thunderball': {
        'name': 'UK Thunderball',
        'country': 'United Kingdom',
        'main_pool_size': 39,
        'main_picks': 5,
        'bonus_pool_size': 14,  # Thunderball
        'bonus_picks': 1,
        'draws_per_week': 4,
        'currency': 'GBP',
        'min_jackpot': 500_000,
        'data_file': f'{DATA_DIR}/thunderball.json',
    },
}


def make_lottery(key):
    """Create a generic lottery instance by key."""
    # Check quicklotto registry first (extended catalog)
    try:
        from .quicklotto_registry import merge_with_existing, merge_with_existing_v2
        all_configs = merge_with_existing_v2()
    except Exception:
        all_configs = NEW_LOTTERIES
    
    config = all_configs.get(key) or NEW_LOTTERIES.get(key)
    if not config:
        return None
    # Compute odds
    main_odds = math.comb(config['main_pool_size'], config['main_picks'])
    if config.get('bonus_picks', 0) > 0:
        odds_jackpot = main_odds * math.comb(config['bonus_pool_size'], config['bonus_picks'])
    else:
        odds_jackpot = main_odds
    
    return GenericLottery(
        name=config['name'],
        country=config['country'],
        main_pool_size=config['main_pool_size'],
        main_picks=config['main_picks'],
        bonus_pool_size=config.get('bonus_pool_size', 0),
        bonus_picks=config.get('bonus_picks', 0),
        draws_per_week=config.get('draws_per_week', 2),
        currency=config.get('currency', 'USD'),
        min_jackpot=config.get('min_jackpot', 1_000_000),
        odds_jackpot=odds_jackpot,
        data_file=config['data_file'],
    )


def get_all_lottery_keys():
    """Get all available lottery keys (existing + quicklotto)."""
    try:
        from .quicklotto_registry import merge_with_existing, merge_with_existing_v2
        all_configs = merge_with_existing_v2()
        return list(all_configs.keys())
    except Exception:
        return list(NEW_LOTTERIES.keys())

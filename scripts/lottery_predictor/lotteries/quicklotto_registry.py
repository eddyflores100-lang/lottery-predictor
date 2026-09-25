"""
Integrate quicklotto.io 39 lotteries into the LotteryPredictor system.
Adds 31 new lotteries to the registry on top of the 8 we already have.
"""
import sys, os, json, math
sys.path.insert(0, '/home/z/my-project/scripts/lottery_predictor')

from pathlib import Path
from lotteries.generic import GenericLottery, NEW_LOTTERIES

QUICKLOTTO_DIR = Path('/home/z/my-project/data/quicklotto')
CATALOG_PATH = QUICKLOTTO_DIR / '_catalog.json'


def load_quicklotto_catalog():
    """Load quicklotto catalog of 39 lotteries."""
    if not CATALOG_PATH.exists():
        return []
    with open(CATALOG_PATH) as f:
        return json.load(f)


def get_quicklotto_lottery_configs():
    """
    Build lottery configs for ALL 39 quicklotto lotteries.
    Returns dict of lottery_key -> config dict.
    """
    catalog = load_quicklotto_catalog()
    configs = {}
    
    for lot_meta in catalog:
        code = lot_meta['code']
        data_file = str(QUICKLOTTO_DIR / f'{code}.json')
        
        if not os.path.exists(data_file):
            continue
        
        # Skip if no draws
        with open(data_file) as f:
            data = json.load(f)
        if not data.get('draws'):
            continue
        
        # Use code as key (with ql_ prefix to avoid collision)
        key = f'ql_{code}'
        
        configs[key] = {
            'name': lot_meta['name'] + (' [sim]' if lot_meta.get('is_inhouse') else ''),
            'country': _infer_country(lot_meta['name'], lot_meta['code']),
            'main_pool_size': lot_meta['main_pool_size'],
            'main_picks': lot_meta['main_picks'],
            'bonus_pool_size': lot_meta.get('bonus_pool_size', 0),
            'bonus_picks': lot_meta.get('bonus_picks', 0),
            'draws_per_week': _infer_draws_per_week(lot_meta['name']),
            'currency': _infer_currency(lot_meta['name']),
            'min_jackpot': _infer_min_jackpot(lot_meta['name']),
            'data_file': data_file,
        }
    
    return configs


def _infer_country(name, code):
    """Infer country from lottery name/code."""
    name_lower = name.lower()
    code_lower = code.lower()
    
    if 'euro' in name_lower or 'euro' in code_lower:
        return 'Europa'
    if 'us ' in name_lower or 'powerball' in name_lower or 'mega' in name_lower or 'america' in name_lower:
        return 'USA'
    if 'uk ' in name_lower or 'british' in name_lower or 'thunderball' in name_lower:
        return 'UK'
    if 'irish' in name_lower or 'ireland' in name_lower:
        return 'Ireland'
    if 'french' in name_lower or 'france' in name_lower:
        return 'France'
    if 'german' in name_lower or 'germany' in name_lower or 'keno' in code_lower:
        return 'Germany'
    if 'spanish' in name_lower or 'primitiva' in name_lower or 'gordo' in name_lower:
        return 'Spain'
    if 'superenalotto' in name_lower or 'italy' in name_lower:
        return 'Italy'
    if 'polish' in name_lower or 'poland' in name_lower or 'kaskada' in code_lower or 'szybkie' in code_lower or 'ekstra' in code_lower or 'mini-lotto' in code_lower:
        return 'Poland'
    if 'brazil' in name_lower or 'mega-sena' in code_lower or 'quina' in code_lower or 'lotofacil' in code_lower or 'dupla' in code_lower or 'dia-de-sorte' in code_lower or 'mais-milionaria' in code_lower:
        return 'Brazil'
    if 'canada' in code_lower or 'canadian' in name_lower:
        return 'Canada'
    if 'south africa' in name_lower or 'south-africa' in code_lower:
        return 'South Africa'
    if 'thai' in name_lower or 'thai' in code_lower:
        return 'Thailand'
    if 'kerala' in name_lower:
        return 'India'
    if 'shubh' in name_lower or 'gullak' in name_lower:
        return 'India'
    if 'set for life' in name_lower:
        return 'UK'
    if 'cash4life' in name_lower:
        return 'USA'
    return 'Various'


def _infer_draws_per_week(name):
    """Infer draws per week from name."""
    name_lower = name.lower()
    if 'daily' in name_lower:
        return 7
    if 'euro' in name_lower:
        return 2
    if 'superenalotto' in name_lower:
        return 3
    if 'powerball' in name_lower and 'us' not in name_lower:
        return 2
    return 2


def _infer_currency(name):
    """Infer currency from name."""
    name_lower = name.lower()
    if 'euro' in name_lower or 'primitiva' in name_lower or 'gordo' in name_lower or 'french' in name_lower or 'german' in name_lower or 'superenalotto' in name_lower or 'irish' in name_lower or 'thunderball' in name_lower or 'polish' in name_lower or 'poland' in name_lower or 'kaskada' in name_lower:
        return 'EUR'
    if 'uk ' in name_lower or 'thunderball' in name_lower or 'set for life' in name_lower:
        return 'GBP'
    if 'us ' in name_lower or 'powerball' in name_lower or 'mega' in name_lower or 'america' in name_lower or 'cash4life' in name_lower:
        return 'USD'
    if 'brazil' in name_lower or 'mega-sena' in name_lower or 'quina' in name_lower:
        return 'BRL'
    if 'south africa' in name_lower:
        return 'ZAR'
    if 'canada' in name_lower:
        return 'CAD'
    if 'thai' in name_lower:
        return 'THB'
    if 'kerala' in name_lower or 'shubh' in name_lower or 'gullak' in name_lower:
        return 'INR'
    return 'USD'


def _infer_min_jackpot(name):
    """Infer min jackpot from name."""
    name_lower = name.lower()
    if 'mega' in name_lower and 'sena' not in name_lower:
        return 20_000_000
    if 'powerball' in name_lower and 'sa' not in name_lower:
        return 20_000_000
    if 'euro' in name_lower:
        return 17_000_000
    if 'superenalotto' in name_lower:
        return 25_000_000
    if 'primitiva' in name_lower or 'gordo' in name_lower:
        return 5_000_000
    return 1_000_000


def merge_with_existing():
    """Merge quicklotto lotteries with existing NEW_LOTTERIES dict."""
    ql_configs = get_quicklotto_lottery_configs()
    
    # We don't modify NEW_LOTTERIES directly (it's imported)
    # Instead, create a unified dict
    all_configs = dict(NEW_LOTTERIES)  # existing 12
    
    # Add quicklotto configs that don't duplicate existing ones
    for key, config in ql_configs.items():
        # Check for duplicates by format + similar name
        is_duplicate = False
        for existing_key, existing_config in all_configs.items():
            if (existing_config['main_picks'] == config['main_picks'] and
                existing_config['main_pool_size'] == config['main_pool_size'] and
                existing_config.get('bonus_picks', 0) == config.get('bonus_picks', 0)):
                # Same format - check if same lottery
                # Heuristic: if names share a significant word
                existing_words = set(existing_config['name'].lower().split())
                new_words = set(config['name'].lower().replace('[sim]', '').split())
                common = existing_words & new_words - {'lotto', 'the', '-', '+'}
                if common:
                    is_duplicate = True
                    break
        if not is_duplicate:
            all_configs[key] = config
    
    return all_configs


if __name__ == '__main__':
    # Test
    configs = merge_with_existing()
    print(f"Total lotteries available: {len(configs)}")
    print(f"\nNew quicklotto lotteries added:")
    for key, cfg in configs.items():
        if key.startswith('ql_'):
            print(f"  {key:<28} - {cfg['name']:<30} {cfg['main_picks']}/{cfg['main_pool_size']} ({cfg['country']})")

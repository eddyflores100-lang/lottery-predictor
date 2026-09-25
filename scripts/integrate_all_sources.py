"""
Integrate ALL data sources into the LotteryPredictor system:
1. quicklotto.io MCP — 39 lotteries, 20 draws each (fresh data)
2. bettip.co.za API — 10 lotteries, deep history
3. daowa89/lottery-archive — EuroMillions, German Lotto, Austrian Lotto
4. pozomillonario.info — Pozo Millonario Ecuador (scraped)

This script merges all sources and creates a unified lottery registry.
"""
import sys, os, json, math
sys.path.insert(0, '/home/z/my-project/scripts/lottery_predictor')

from pathlib import Path
from lotteries.base import Lottery, DrawResult
from lotteries.generic import GenericLottery

QUICKLOTTO_DIR = Path('/home/z/my-project/data/quicklotto')
EXISTING_DATA = {
    'pozo_millonario': {'path': '/home/z/my-project/data/pozo_data.json', 'config': {
        'name': 'Pozo Millonario', 'country': 'Ecuador', 'main_pool_size': 25, 'main_picks': 11,
        'bonus_pool_size': 0, 'bonus_picks': 0, 'draws_per_week': 2, 'currency': 'USD', 'min_jackpot': 500000,
    }},
    'euromillions': {'path': '/home/z/my-project/data/euromillions.json', 'config': {
        'name': 'EuroMillions', 'country': 'Europa', 'main_pool_size': 50, 'main_picks': 5,
        'bonus_pool_size': 12, 'bonus_picks': 2, 'draws_per_week': 2, 'currency': 'EUR', 'min_jackpot': 17000000,
    }},
    'la_primitiva': {'path': '/home/z/my-project/data/la_primitiva.json', 'config': {
        'name': 'La Primitiva (proxy DE)', 'country': 'España/DE', 'main_pool_size': 49, 'main_picks': 6,
        'bonus_pool_size': 10, 'bonus_picks': 1, 'draws_per_week': 2, 'currency': 'EUR', 'min_jackpot': 8000000,
    }},
    'lotto_austrian': {'path': '/home/z/my-project/data/lotto_austrian.json', 'config': {
        'name': 'Lotto 6 aus 45', 'country': 'Austria', 'main_pool_size': 45, 'main_picks': 6,
        'bonus_pool_size': 45, 'bonus_picks': 1, 'draws_per_week': 2, 'currency': 'EUR', 'min_jackpot': 1500000,
    }},
    'uk49s': {'path': '/home/z/my-project/data/uk49s.json', 'config': {
        'name': 'UK49s Lunchtime', 'country': 'UK', 'main_pool_size': 49, 'main_picks': 6,
        'bonus_pool_size': 49, 'bonus_picks': 1, 'draws_per_week': 14, 'currency': 'GBP', 'min_jackpot': 125000,
    }},
    'sa_lotto': {'path': '/home/z/my-project/data/sa_lotto_6_52.json', 'config': {
        'name': 'SA Lotto', 'country': 'South Africa', 'main_pool_size': 52, 'main_picks': 6,
        'bonus_pool_size': 52, 'bonus_picks': 1, 'draws_per_week': 2, 'currency': 'ZAR', 'min_jackpot': 5000000,
    }},
    'sa_powerball': {'path': '/home/z/my-project/data/sa_powerball.json', 'config': {
        'name': 'SA PowerBall', 'country': 'South Africa', 'main_pool_size': 50, 'main_picks': 5,
        'bonus_pool_size': 20, 'bonus_picks': 1, 'draws_per_week': 2, 'currency': 'ZAR', 'min_jackpot': 30000000,
    }},
    'sa_daily_lotto': {'path': '/home/z/my-project/data/sa_daily_lotto.json', 'config': {
        'name': 'SA Daily Lotto', 'country': 'South Africa', 'main_pool_size': 36, 'main_picks': 5,
        'bonus_pool_size': 0, 'bonus_picks': 0, 'draws_per_week': 7, 'currency': 'ZAR', 'min_jackpot': 100000,
    }},
}


def compute_odds(main_picks, main_pool, bonus_picks=0, bonus_pool=0):
    """Compute jackpot odds."""
    main = math.comb(main_pool, main_picks)
    if bonus_picks > 0 and bonus_pool > 0:
        return main * math.comb(bonus_pool, bonus_picks)
    return main


def load_quicklotto_lotteries():
    """Load all lotteries from quicklotto MCP data."""
    catalog_path = QUICKLOTTO_DIR / '_catalog.json'
    if not catalog_path.exists():
        return {}
    
    with open(catalog_path) as f:
        catalog = json.load(f)
    
    lotteries = {}
    for lot_meta in catalog:
        code = lot_meta['code']
        data_file = QUICKLOTTO_DIR / f'{code}.json'
        if not data_file.exists():
            continue
        
        with open(data_file) as f:
            data = json.load(f)
        
        draws = data.get('draws', [])
        if not draws:
            continue
        
        lotteries[f'ql_{code}'] = {
            'name': lot_meta['name'] + (' [IN-HOUSE]' if lot_meta.get('is_inhouse') else ''),
            'country': 'Various',
            'main_pool_size': lot_meta['main_pool_size'],
            'main_picks': lot_meta['main_picks'],
            'bonus_pool_size': lot_meta.get('bonus_pool_size', 0),
            'bonus_picks': lot_meta.get('bonus_picks', 0),
            'draws_per_week': 2,  # default
            'currency': 'USD',
            'min_jackpot': 1000000,
            'data_file': str(data_file),
            'source': 'quicklotto.io MCP',
            'total_draws': len(draws),
            'is_inhouse': lot_meta.get('is_inhouse', False),
        }
    
    return lotteries


def load_all_lotteries():
    """Load ALL lotteries from all sources."""
    all_lotteries = {}
    
    # 1. Existing deep datasets
    for key, info in EXISTING_DATA.items():
        config = info['config']
        path = info['path']
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            total = len(data) if isinstance(data, list) else 0
            
            all_lotteries[key] = {
                **config,
                'data_file': path,
                'source': 'local',
                'total_draws': total,
                'is_inhouse': False,
            }
    
    # 2. QuickLotto MCP lotteries (39 lotteries, 20 draws each)
    ql_lotteries = load_quicklotto_lotteries()
    
    # Merge: if a quicklotto lottery has the same format as an existing one, keep the existing (more data)
    # But add new ones from quicklotto
    for key, lot in ql_lotteries.items():
        # Check if we already have this lottery (by format match)
        already_have = False
        for existing_key, existing in all_lotteries.items():
            if (existing['main_picks'] == lot['main_picks'] and 
                existing['main_pool_size'] == lot['main_pool_size'] and
                existing.get('bonus_picks', 0) == lot.get('bonus_picks', 0)):
                # Same format — check if same lottery by name
                if any(word in lot['name'].lower() for word in existing['name'].lower().split()):
                    already_have = True
                    break
        
        if not already_have:
            all_lotteries[key] = lot
    
    # Compute odds for each
    for key, lot in all_lotteries.items():
        lot['odds_jackpot'] = compute_odds(
            lot['main_picks'], lot['main_pool_size'],
            lot.get('bonus_picks', 0), lot.get('bonus_pool_size', 0)
        )
    
    return all_lotteries


def print_catalogue():
    """Print the full catalogue of all lotteries."""
    all_lots = load_all_lotteries()
    
    print(f"\n{'='*120}")
    print(f"CATÁLOGO MAESTRO — {len(all_lots)} LOTERÍAS DE TODO EL MUNDO")
    print(f"{'='*120}")
    print(f"\n{'Key':<25} {'Nombre':<30} {'País':<15} {'Formato':<15} {'Sorteos':>7} {'Odds':>15} {'Fuente'}")
    print(f"{'-'*120}")
    
    # Sort by total_draws desc
    sorted_lots = sorted(all_lots.items(), key=lambda x: -x[1].get('total_draws', 0))
    
    for key, lot in sorted_lots:
        format_str = f"{lot['main_picks']}/{lot['main_pool_size']}"
        if lot.get('bonus_picks', 0) > 0:
            format_str += f"+{lot['bonus_picks']}/{lot['bonus_pool_size']}"
        odds_str = f"1:{lot['odds_jackpot']:,}"
        source = lot.get('source', '?')
        if lot.get('is_inhouse'):
            source += ' [IN-HOUSE]'
        
        print(f"{key:<25} {lot['name'][:29]:<30} {lot.get('country','?')[:14]:<15} {format_str:<15} {lot.get('total_draws',0):>7} {odds_str:>15} {source}")
    
    # Save to JSON
    output_path = '/home/z/my-project/data/master_catalogue.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_lots, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n✓ Saved to {output_path}")
    
    # Stats
    total_draws = sum(lot.get('total_draws', 0) for lot in all_lots.values())
    official = sum(1 for lot in all_lots.values() if not lot.get('is_inhouse'))
    inhouse = sum(1 for lot in all_lots.values() if lot.get('is_inhouse'))
    
    print(f"\n📊 ESTADÍSTICAS:")
    print(f"  Total loterías: {len(all_lots)}")
    print(f"  Oficiales: {official}")
    print(f"  In-house (quicklotto): {inhouse}")
    print(f"  Total sorteos acumulados: {total_draws:,}")
    print(f"  Fuentes: quicklotto.io MCP, bettip.co.za API, daowa89/lottery-archive, pozomillonario.info")


if __name__ == '__main__':
    print_catalogue()

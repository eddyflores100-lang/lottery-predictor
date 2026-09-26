"""
Master Lottery Catalogue — Definitive worldwide registry.
Organized by purchasability: Tier 1 (international), Tier 2 (local), Tier 3 (case study).
"""
import json, os, math
from pathlib import Path

DATA_DIR = Path('/home/z/my-project/data')

# ============================================================
# TIER 1: INTERNATIONALLY BUYABLE ONLINE
# (via thelotter.com, lottoland, multilotto, etc.)
# ============================================================
TIER_1 = {
    'us_powerball': {
        'name': 'US Powerball', 'country': 'USA', 'format': '5/69+1/26',
        'odds': 292_201_338, 'currency': 'USD', 'min_jackpot': 20_000_000,
        'buy_online': True, 'platforms': ['thelotter.com', 'lottoland', 'multilotto'],
        'draws_per_week': 3, 'data_file': 'us_powerball.json', 'draws': 13,
    },
    'mega_millions': {
        'name': 'Mega Millions', 'country': 'USA', 'format': '5/70+1/25',
        'odds': 302_575_350, 'currency': 'USD', 'min_jackpot': 20_000_000,
        'buy_online': True, 'platforms': ['thelotter.com', 'lottoland'],
        'draws_per_week': 2, 'data_file': 'mega_millions.json', 'draws': 8,
    },
    'euromillions': {
        'name': 'EuroMillions', 'country': 'Europe', 'format': '5/50+2/12',
        'odds': 139_838_160, 'currency': 'EUR', 'min_jackpot': 17_000_000,
        'buy_online': True, 'platforms': ['thelotter.com', 'lottoland', 'multilotto'],
        'draws_per_week': 2, 'data_file': 'euromillions.json', 'draws': 1977,
    },
    'eurojackpot': {
        'name': 'EuroJackpot', 'country': 'Europe', 'format': '5/50+2/10',
        'odds': 139_838_160, 'currency': 'EUR', 'min_jackpot': 10_000_000,
        'buy_online': True, 'platforms': ['thelotter.com', 'lottoland'],
        'draws_per_week': 2, 'data_file': 'eurojackpot.json', 'draws': 993,
    },
    'superenalotto': {
        'name': 'SuperEnalotto', 'country': 'Italy', 'format': '6/90',
        'odds': 622_614_630, 'currency': 'EUR', 'min_jackpot': 25_000_000,
        'buy_online': True, 'platforms': ['thelotter.com', 'lottoland'],
        'draws_per_week': 3, 'data_file': 'ql_superenalotto.json', 'draws': 20,
    },
    'la_primitiva': {
        'name': 'La Primitiva', 'country': 'Spain', 'format': '6/49+1/9',
        'odds': 13_983_816, 'currency': 'EUR', 'min_jackpot': 8_000_000,
        'buy_online': True, 'platforms': ['thelotter.com', 'lottoland'],
        'draws_per_week': 2, 'data_file': 'la_primitiva.json', 'draws': 5049,
    },
    'el_gordo': {
        'name': 'El Gordo', 'country': 'Spain', 'format': '5/54+1/9',
        'odds': 31_625_100, 'currency': 'EUR', 'min_jackpot': 5_000_000,
        'buy_online': True, 'platforms': ['thelotter.com'],
        'draws_per_week': 1, 'data_file': None, 'draws': 0,
    },
    'french_lotto': {
        'name': 'French Lotto', 'country': 'France', 'format': '5/49+1/10',
        'odds': 19_068_840, 'currency': 'EUR', 'min_jackpot': 2_000_000,
        'buy_online': True, 'platforms': ['thelotter.com'],
        'draws_per_week': 3, 'data_file': 'france_lotto.json', 'draws': 13,
    },
    'uk_lotto': {
        'name': 'UK Lotto', 'country': 'UK', 'format': '6/59',
        'odds': 45_057_474, 'currency': 'GBP', 'min_jackpot': 2_000_000,
        'buy_online': True, 'platforms': ['thelotter.com', 'lottoland'],
        'draws_per_week': 2, 'data_file': 'uk_lotto.json', 'draws': 56,
    },
    'irish_lotto': {
        'name': 'Irish Lotto', 'country': 'Ireland', 'format': '6/47',
        'odds': 10_737_573, 'currency': 'EUR', 'min_jackpot': 2_000_000,
        'buy_online': True, 'platforms': ['thelotter.com', 'lottoland'],
        'draws_per_week': 2, 'data_file': 'irish_lotto.json', 'draws': 34,
    },
    'german_lotto': {
        'name': 'German Lotto 6aus49', 'country': 'Germany', 'format': '6/49+1/9',
        'odds': 139_838_160, 'currency': 'EUR', 'min_jackpot': 1_000_000,
        'buy_online': True, 'platforms': ['thelotter.com', 'lottoland'],
        'draws_per_week': 2, 'data_file': 'la_primitiva.json', 'draws': 5049,
    },
    'austrian_lotto': {
        'name': 'Austrian Lotto 6aus45', 'country': 'Austria', 'format': '6/45',
        'odds': 8_145_060, 'currency': 'EUR', 'min_jackpot': 1_500_000,
        'buy_online': True, 'platforms': ['thelotter.com'],
        'draws_per_week': 2, 'data_file': 'lotto_austrian.json', 'draws': 3684,
    },
    'thunderball': {
        'name': 'UK Thunderball', 'country': 'UK', 'format': '5/39+1/14',
        'odds': 8_060_598, 'currency': 'GBP', 'min_jackpot': 500_000,
        'buy_online': True, 'platforms': ['thelotter.com'],
        'draws_per_week': 4, 'data_file': 'thunderball.json', 'draws': 16,
    },
    'set_for_life': {
        'name': 'Set For Life', 'country': 'UK', 'format': '5/47+1/10',
        'odds': 15_339_390, 'currency': 'GBP', 'min_jackpot': 390_000,
        'buy_online': True, 'platforms': ['thelotter.com'],
        'draws_per_week': 2, 'data_file': None, 'draws': 0,
    },
    'cash4life': {
        'name': 'Cash4Life', 'country': 'USA', 'format': '5/60+1/4',
        'odds': 21_846_048, 'currency': 'USD', 'min_jackpot': 365_000,
        'buy_online': True, 'platforms': ['thelotter.com'],
        'draws_per_week': 2, 'data_file': None, 'draws': 0,
    },
    'sa_lotto': {
        'name': 'SA Lotto', 'country': 'South Africa', 'format': '6/52',
        'odds': 20_358_520, 'currency': 'ZAR', 'min_jackpot': 5_000_000,
        'buy_online': True, 'platforms': ['thelotter.com', 'lottoland'],
        'draws_per_week': 2, 'data_file': 'sa_lotto_6_52.json', 'draws': 1221,
    },
    'sa_powerball': {
        'name': 'SA PowerBall', 'country': 'South Africa', 'format': '5/50+1/20',
        'odds': 42_375_200, 'currency': 'ZAR', 'min_jackpot': 30_000_000,
        'buy_online': True, 'platforms': ['thelotter.com', 'lottoland'],
        'draws_per_week': 2, 'data_file': 'sa_powerball.json', 'draws': 1221,
    },
    'greek_lotto': {
        'name': 'Greek Lotto', 'country': 'Greece', 'format': '6/49',
        'odds': 13_983_816, 'currency': 'EUR', 'min_jackpot': 100_000,
        'buy_online': True, 'platforms': ['thelotter.com'],
        'draws_per_week': 2, 'data_file': 'greek_lotto.json', 'draws': 9,
    },
    'greece_powerball': {
        'name': 'Greece Powerball (TZOKER)', 'country': 'Greece', 'format': '5/45+1/20',
        'odds': 24_435_180, 'currency': 'EUR', 'min_jackpot': 100_000,
        'buy_online': True, 'platforms': ['thelotter.com'],
        'draws_per_week': 2, 'data_file': 'greece_powerball.json', 'draws': 13,
    },
}

# ============================================================
# TIER 2: LOCAL ONLY (need to be in country or special agent)
# ============================================================
TIER_2 = {
    'pozo_millonario': {
        'name': 'Pozo Millonario', 'country': 'Ecuador', 'format': '11/25',
        'odds': 4_457_400, 'currency': 'USD', 'min_jackpot': 500_000,
        'buy_online': False, 'platforms': ['Puntos de la Suerte (Ecuador only)'],
        'draws_per_week': 2, 'data_file': 'pozo_data.json', 'draws': 308,
    },
    'ec_loteria': {
        'name': 'La Lotería (Ecuador)', 'country': 'Ecuador', 'format': '5/10',
        'odds': 100_000, 'currency': 'USD', 'min_jackpot': 50_000,
        'buy_online': False, 'platforms': ['Puntos de la Suerte (Ecuador only)'],
        'draws_per_week': 7, 'data_file': 'ec_la_loteria.json', 'draws': 102,
    },
    'ec_lotto': {
        'name': 'Lotto (Ecuador)', 'country': 'Ecuador', 'format': '6/10',
        'odds': 1_000_000, 'currency': 'USD', 'min_jackpot': 100_000,
        'buy_online': False, 'platforms': ['Ecuador only'],
        'draws_per_week': 3, 'data_file': 'ec_lotto.json', 'draws': 104,
    },
    'ec_pega': {
        'name': 'Pega (Ecuador)', 'country': 'Ecuador', 'format': '3/10',
        'odds': 1_000, 'currency': 'USD', 'min_jackpot': 500,
        'buy_online': False, 'platforms': ['Ecuador only'],
        'draws_per_week': 7, 'data_file': 'ec_pega.json', 'draws': 77,
    },
    'uk49s': {
        'name': 'UK49s', 'country': 'UK', 'format': '6/49+1/49',
        'odds': 13_983_816, 'currency': 'GBP', 'min_jackpot': 125_000,
        'buy_online': False, 'platforms': ['UK betting shops only'],
        'draws_per_week': 14, 'data_file': 'uk49s.json', 'draws': 5867,
    },
    'cn_ssq': {
        'name': '双色球 SSQ', 'country': 'China', 'format': '6/33+1/16',
        'odds': 17_721_088, 'currency': 'CNY', 'min_jackpot': 5_000_000,
        'buy_online': False, 'platforms': ['China only'],
        'draws_per_week': 3, 'data_file': 'cn_ssq_standard.json', 'draws': 3508,
    },
    'cn_dlt': {
        'name': '大乐透 DLT', 'country': 'China', 'format': '5/35+2/12',
        'odds': 21_425_712, 'currency': 'CNY', 'min_jackpot': 10_000_000,
        'buy_online': False, 'platforms': ['China only'],
        'draws_per_week': 3, 'data_file': 'cn_dlt_standard.json', 'draws': 2903,
    },
    'cn_qxc': {
        'name': '七星彩 QXC', 'country': 'China', 'format': '7 digits',
        'odds': 10_000_000, 'currency': 'CNY', 'min_jackpot': 5_000_000,
        'buy_online': False, 'platforms': ['China only'],
        'draws_per_week': 3, 'data_file': 'cn_qxc_standard.json', 'draws': 3062,
    },
    'cn_qlc': {
        'name': '七乐彩 QLC', 'country': 'China', 'format': '7/30+1',
        'odds': 2_035_800, 'currency': 'CNY', 'min_jackpot': 1_000_000,
        'buy_online': False, 'platforms': ['China only'],
        'draws_per_week': 3, 'data_file': 'cn_qlc_standard.json', 'draws': 2045,
    },
    'cn_fc3d': {
        'name': '福彩3D FC3D', 'country': 'China', 'format': '3 digits',
        'odds': 1_000, 'currency': 'CNY', 'min_jackpot': 1_040,
        'buy_online': False, 'platforms': ['China only'],
        'draws_per_week': 7, 'data_file': 'cn_fc3d_standard.json', 'draws': 4705,
    },
    'cn_pl3': {
        'name': '排列3 PL3', 'country': 'China', 'format': '3 digits',
        'odds': 1_000, 'currency': 'CNY', 'min_jackpot': 1_040,
        'buy_online': False, 'platforms': ['China only'],
        'draws_per_week': 7, 'data_file': 'cn_pl3_standard.json', 'draws': 7675,
    },
    'cn_pl5': {
        'name': '排列5 PL5', 'country': 'China', 'format': '5 digits',
        'odds': 100_000, 'currency': 'CNY', 'min_jackpot': 10_000,
        'buy_online': False, 'platforms': ['China only'],
        'draws_per_week': 7, 'data_file': 'cn_pl5_standard.json', 'draws': 7675,
    },
    'sa_daily_lotto': {
        'name': 'SA Daily Lotto', 'country': 'South Africa', 'format': '5/36',
        'odds': 376_992, 'currency': 'ZAR', 'min_jackpot': 100_000,
        'buy_online': False, 'platforms': ['SA only'],
        'draws_per_week': 7, 'data_file': 'sa_daily_lotto.json', 'draws': 2749,
    },
    'megasena': {
        'name': 'Mega-Sena', 'country': 'Brazil', 'format': '6/60',
        'odds': 50_063_860, 'currency': 'BRL', 'min_jackpot': 3_000_000,
        'buy_online': False, 'platforms': ['Caixa (Brazil only)'],
        'draws_per_week': 2, 'data_file': 'ql_mega-sena.json', 'draws': 20,
    },
    'lotofacil': {
        'name': 'Lotofácil', 'country': 'Brazil', 'format': '15/25',
        'odds': 3_268_760, 'currency': 'BRL', 'min_jackpot': 500_000,
        'buy_online': False, 'platforms': ['Caixa (Brazil only)'],
        'draws_per_week': 6, 'data_file': 'ql_lotofacil.json', 'draws': 20,
    },
    'quina': {
        'name': 'Quina', 'country': 'Brazil', 'format': '5/80',
        'odds': 24_040_016, 'currency': 'BRL', 'min_jackpot': 500_000,
        'buy_online': False, 'platforms': ['Caixa (Brazil only)'],
        'draws_per_week': 6, 'data_file': 'ql_brazil-quina.json', 'draws': 20,
    },
    'gosloto': {
        'name': 'Gosloto (Russia)', 'country': 'Russia', 'format': 'varies',
        'odds': 0, 'currency': 'RUB', 'min_jackpot': 10_000_000,
        'buy_online': False, 'platforms': ['Russia only'],
        'draws_per_week': 7, 'data_file': 'raw_sources/gosloto.csv', 'draws': 2041,
    },
}

# ============================================================
# TIER 3: CASE STUDY ONLY (historical, no purchase, special)
# ============================================================
TIER_3 = {
    'thai_lottery': {
        'name': 'Thai Government Lottery', 'country': 'Thailand', 'format': '6-digit',
        'odds': 1_000_000, 'currency': 'THB', 'min_jackpot': 6_000_000,
        'buy_online': False, 'platforms': ['Thailand only (government)'],
        'draws_per_week': 0.5, 'data_file': None, 'draws': 0,
    },
    'kerala_lottery': {
        'name': 'Kerala State Lottery', 'country': 'India', 'format': '6-digit+series',
        'odds': 1_000_000, 'currency': 'INR', 'min_jackpot': 5_000_000,
        'buy_online': False, 'platforms': ['Kerala only (government)'],
        'draws_per_week': 7, 'data_file': None, 'draws': 0,
    },
    'la_millonaria': {
        'name': 'La Millonaria (discontinued)', 'country': 'Ecuador', 'format': 'entero+serie',
        'odds': 0, 'currency': 'USD', 'min_jackpot': 0,
        'buy_online': False, 'platforms': ['Discontinued'],
        'draws_per_week': 0, 'data_file': None, 'draws': 0,
    },
    'singapore_toto': {
        'name': 'Singapore TOTO', 'country': 'Singapore', 'format': '6/49',
        'odds': 13_983_816, 'currency': 'SGD', 'min_jackpot': 1_000_000,
        'buy_online': False, 'platforms': ['Singapore only'],
        'draws_per_week': 2, 'data_file': None, 'draws': 0,
    },
    'taiwan_power': {
        'name': 'Taiwan Power Lottery (威力彩)', 'country': 'Taiwan', 'format': '6/38+1/8',
        'odds': 38_140_680, 'currency': 'TWD', 'min_jackpot': 30_000_000,
        'buy_online': False, 'platforms': ['Taiwan only'],
        'draws_per_week': 1, 'data_file': None, 'draws': 0,
    },
    'taiwan_lotto649': {
        'name': 'Taiwan Lotto 6/49 (大樂透)', 'country': 'Taiwan', 'format': '6/49',
        'odds': 13_983_816, 'currency': 'TWD', 'min_jackpot': 50_000_000,
        'buy_online': False, 'platforms': ['Taiwan only'],
        'draws_per_week': 2, 'data_file': None, 'draws': 0,
    },
    'polish_lotto': {
        'name': 'Polish Lotto', 'country': 'Poland', 'format': '6/49',
        'odds': 13_983_816, 'currency': 'PLN', 'min_jackpot': 2_000_000,
        'buy_online': False, 'platforms': ['Poland only'],
        'draws_per_week': 4, 'data_file': None, 'draws': 0,
    },
    'argentina_quiniela': {
        'name': 'Quiniela (Argentina)', 'country': 'Argentina', 'format': '4-digit',
        'odds': 10_000, 'currency': 'ARS', 'min_jackpot': 0,
        'buy_online': False, 'platforms': ['Argentina only'],
        'draws_per_week': 14, 'data_file': None, 'draws': 0,
    },
}

# Also add quicklotto-only lotteries (20 draws each, various tiers)
QUICKLOTTO_EXTRA = [
    ('mais_milionaria', '+Milionária', 'Brazil', '6/50+2/6', 'BRL', False, 2),
    ('dia_de_sorte', 'Dia de Sorte', 'Brazil', '7/31+1/12', 'BRL', False, 2),
    ('dupla_sena', 'Dupla Sena', 'Brazil', '6/50', 'BRL', False, 2),
    ('eurodreams', 'EuroDreams', 'Europe', '6/40+1/5', 'EUR', True, 2),
    ('lotto_america', 'Lotto America', 'USA', '5/52+1/10', 'USD', True, 2),
    ('canada_lotto_649', 'Lotto 6/49 (Canada)', 'Canada', '6/49', 'CAD', True, 2),
    ('irish_daily_million', 'Irish Daily Million', 'Ireland', '6/39', 'EUR', True, 7),
    ('keno_10', 'German Keno', 'Germany', '10/70', 'EUR', True, 7),
    ('shubh_lotto', 'Shubh Lotto (India)', 'India', '5/10', 'INR', False, 7),
    ('gullak_gold', 'Gullak Gold (India)', 'India', '15/25', 'INR', False, 7),
    ('kaskada', 'Kaskada (Poland)', 'Poland', '6/24', 'PLN', False, 7),
    ('mini_lotto', 'Mini Lotto (Poland)', 'Poland', '5/42', 'PLN', False, 4),
    ('polish_lotto_ql', 'Polish Lotto (Poland)', 'Poland', '6/49', 'PLN', False, 2),
    ('rapid_riches', 'Rapid Riches', 'Various', '5/36', 'USD', False, 7),
    ('ekstra_pensja', 'Ekstra Pensja (Poland)', 'Poland', '5/35+1/5', 'PLN', False, 2),
    ('ekstra_premia', 'Ekstra Premia (Poland)', 'Poland', '5/35+1/5', 'PLN', False, 2),
    ('lotto_plus', 'Lotto Plus (Poland)', 'Poland', '6/49', 'PLN', False, 2),
    ('szybkie_600', 'Szybkie 600 (Poland)', 'Poland', '6/32', 'PLN', False, 7),
    ('south_africa_lotto_ql', 'SA Lotto (quicklotto)', 'South Africa', '6/52', 'ZAR', True, 2),
]


def build_master_catalogue():
    """Build the complete master catalogue."""
    catalogue = {
        'metadata': {
            'version': '5.0',
            'generated': '2026-09-26',
            'total_lotteries': 0,
            'total_draws': 0,
            'sources': [
                'quicklotto.io MCP (39 lotteries, free)',
                'bettip.co.za API (10 lotteries, free)',
                'daowa89/lottery-archive (GitHub, 3 lotteries)',
                'dev-baris/lottery-archive (GitHub, EuroJackpot)',
                'Zhang-0122/Multi-Lottery (GitHub, 7 Chinese lotteries)',
                'zaiqltd/bettip-draws-api (GitHub, Gosloto)',
                'pozomillonario.info (scraping, Pozo Millonario)',
                'contenidos.loteria.com.ec (scraping, Ecuador lotteries)',
            ],
        },
        'tier_1_international': {},
        'tier_2_local': {},
        'tier_3_case_study': {},
    }
    
    total_draws = 0
    
    # Tier 1
    for key, lot in TIER_1.items():
        catalogue['tier_1_international'][key] = lot
        total_draws += lot['draws']
    
    # Tier 2
    for key, lot in TIER_2.items():
        catalogue['tier_2_local'][key] = lot
        total_draws += lot['draws']
    
    # Tier 3
    for key, lot in TIER_3.items():
        catalogue['tier_3_case_study'][key] = lot
        total_draws += lot['draws']
    
    # Quicklotto extras
    for key, name, country, fmt, curr, international, dpw in QUICKLOTTO_EXTRA:
        tier = 'tier_1_international' if international else 'tier_2_local'
        catalogue[tier][f'ql_{key}'] = {
            'name': name, 'country': country, 'format': fmt,
            'odds': 0, 'currency': curr, 'min_jackpot': 0,
            'buy_online': international,
            'platforms': ['quicklotto.io (data only)' if not international else 'thelotter.com'],
            'draws_per_week': dpw, 'data_file': f'quicklotto/{key.replace("_", "-")}.json',
            'draws': 20,
        }
        total_draws += 20
    
    catalogue['metadata']['total_lotteries'] = (
        len(catalogue['tier_1_international']) +
        len(catalogue['tier_2_local']) +
        len(catalogue['tier_3_case_study'])
    )
    catalogue['metadata']['total_draws'] = total_draws
    
    return catalogue


if __name__ == '__main__':
    cat = build_master_catalogue()
    
    # Save
    output = DATA_DIR / 'MASTER_CATALOGUE.json'
    with open(output, 'w') as f:
        json.dump(cat, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"MASTER CATALOGUE v5.0 — {cat['metadata']['total_lotteries']} lotteries worldwide")
    print(f"{'='*80}")
    
    print(f"\n📊 TIER 1 — INTERNATIONALLY BUYABLE ONLINE ({len(cat['tier_1_international'])} lotteries):")
    print(f"   Comprable via thelotter.com, lottoland, multilotto, etc.")
    print(f"{'Lottery':<28} {'Country':<12} {'Format':<14} {'Sorteos':>8} {'Odds':>15}")
    print('-' * 80)
    for key, lot in sorted(cat['tier_1_international'].items(), key=lambda x: -x[1]['draws']):
        odds = f"1:{lot['odds']:,}" if lot['odds'] else '?'
        print(f"   {lot['name']:<25} {lot['country']:<12} {lot['format']:<14} {lot['draws']:>8} {odds:>15}")
    
    print(f"\n📊 TIER 2 — LOCAL ONLY ({len(cat['tier_2_local'])} lotteries):")
    print(f"   Need to be in the country or use special agents")
    print(f"{'Lottery':<28} {'Country':<12} {'Format':<14} {'Sorteos':>8} {'Odds':>15}")
    print('-' * 80)
    for key, lot in sorted(cat['tier_2_local'].items(), key=lambda x: -x[1]['draws']):
        odds = f"1:{lot['odds']:,}" if lot['odds'] else '?'
        print(f"   {lot['name']:<25} {lot['country']:<12} {lot['format']:<14} {lot['draws']:>8} {odds:>15}")
    
    print(f"\n📊 TIER 3 — CASE STUDY ONLY ({len(cat['tier_3_case_study'])} lotteries):")
    print(f"   Historical data only, no purchase possible")
    print(f"{'Lottery':<28} {'Country':<12} {'Format':<14} {'Sorteos':>8}")
    print('-' * 80)
    for key, lot in sorted(cat['tier_3_case_study'].items(), key=lambda x: -x[1]['draws']):
        print(f"   {lot['name']:<25} {lot['country']:<12} {lot['format']:<14} {lot['draws']:>8}")
    
    print(f"\n{'='*80}")
    print(f"TOTAL: {cat['metadata']['total_lotteries']} lotteries | {cat['metadata']['total_draws']:,} sorteos")
    print(f"{'='*80}")

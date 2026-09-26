"""
Convert all newly found lottery data to standard format and add to registry.

New lotteries found:
1. Chinese SSQ (双色球) — 6/33 + 1/16 — 3,508 draws since 2003
2. Chinese DLT (大乐透) — 5/35 + 2/12 — 2,903 draws since 2007
3. Chinese QXC (七星彩) — 7 digits — 3,062 draws since 2004
4. Chinese QLC (七乐彩) — 7/30 + 1 — 2,045 draws since 2013
5. Chinese FC3D (福彩3D) — 3 digits — 4,705 draws since 2013
6. Chinese PL3 (排列3) — 3 digits — 7,675 draws since 2004
7. Chinese PL5 (排列5) — 5 digits — 7,675 draws since 2004
8. EuroJackpot — 5/50 + 2/10 — 994 draws since 2012

Total NEW: 31,567 draws from 8 lotteries!
"""
import json, csv, re
from pathlib import Path

DATA_DIR = Path('/home/z/my-project/data')


def convert_chinese_ssq():
    """Convert SSQ (双色球) — 6/33 + 1/16"""
    with open(DATA_DIR / 'cn_ssq.json') as f:
        data = json.load(f)
    draws = []
    for i, r in enumerate(data, 1):
        red = [int(n) for n in r['Red'].split(',')]
        blue = [int(r['Blue'])]
        draws.append({
            'draw_number': i,
            'date': r['Date'],
            'main_numbers': red,
            'bonus_numbers': blue,
            'jackpot_won': False,
            'raw_data': {'source': 'Zhang-0122/Multi-Lottery', 'issue': r['Issue']}
        })
    with open(DATA_DIR / 'cn_ssq_standard.json', 'w') as f:
        json.dump(draws, f, indent=2)
    print(f"  SSQ: {len(draws)} draws (6/33+1/16, since {draws[0]['date']})")
    return len(draws)


def convert_chinese_dlt():
    """Convert DLT (大乐透) — 5/35 + 2/12"""
    with open(DATA_DIR / 'cn_dlt.json') as f:
        data = json.load(f)
    draws = []
    for i, r in enumerate(data, 1):
        front = [int(n) for n in r['Front'].split(',')]
        back = [int(n) for n in r['Back'].split(',')]
        draws.append({
            'draw_number': i,
            'date': r['Date'],
            'main_numbers': front,
            'bonus_numbers': back,
            'jackpot_won': False,
            'raw_data': {'source': 'Zhang-0122/Multi-Lottery', 'issue': r['Issue']}
        })
    with open(DATA_DIR / 'cn_dlt_standard.json', 'w') as f:
        json.dump(draws, f, indent=2)
    print(f"  DLT: {len(draws)} draws (5/35+2/12, since {draws[0]['date']})")
    return len(draws)


def convert_chinese_digits(key, name, n_digits):
    """Convert digit-based lotteries (QXC, FC3D, PL3, PL5)"""
    with open(DATA_DIR / f'{key}.json') as f:
        data = json.load(f)
    draws = []
    for i, r in enumerate(data, 1):
        digits = [int(n) for n in r['Digit'].split(',')]
        draws.append({
            'draw_number': i,
            'date': r['Date'],
            'main_numbers': digits[:n_digits],
            'bonus_numbers': [],
            'jackpot_won': False,
            'raw_data': {'source': 'Zhang-0122/Multi-Lottery', 'issue': r['Issue']}
        })
    with open(DATA_DIR / f'{key}_standard.json', 'w') as f:
        json.dump(draws, f, indent=2)
    print(f"  {name}: {len(draws)} draws ({n_digits} digits, since {draws[0]['date']})")
    return len(draws)


def convert_chinese_qlc():
    """Convert QLC (七乐彩) — 7/30 + 1"""
    with open(DATA_DIR / 'cn_qlc.json') as f:
        data = json.load(f)
    draws = []
    for i, r in enumerate(data, 1):
        main = [int(n) for n in r['Main'].split(',')]
        special = [int(r['Special'])]
        draws.append({
            'draw_number': i,
            'date': r['Date'],
            'main_numbers': main,
            'bonus_numbers': special,
            'jackpot_won': False,
            'raw_data': {'source': 'Zhang-0122/Multi-Lottery', 'issue': r['Issue']}
        })
    with open(DATA_DIR / 'cn_qlc_standard.json', 'w') as f:
        json.dump(draws, f, indent=2)
    print(f"  QLC: {len(draws)} draws (7/30+1, since {draws[0]['date']})")
    return len(draws)


def convert_eurojackpot():
    """Convert EuroJackpot — 5/50 + 2/10"""
    draws = []
    with open(DATA_DIR / 'eurojackpot_raw.csv') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            main = [int(row[f'n{j}']) for j in range(1, 6)]
            bonus = [int(row['e1']), int(row['e2'])]
            draws.append({
                'draw_number': i,
                'date': row['date'],
                'main_numbers': main,
                'bonus_numbers': bonus,
                'jackpot_won': False,
                'raw_data': {'source': 'dev-baris/lottery-archive'}
            })
    with open(DATA_DIR / 'eurojackpot.json', 'w') as f:
        json.dump(draws, f, indent=2)
    print(f"  EuroJackpot: {len(draws)} draws (5/50+2/10, since {draws[0]['date']})")
    return len(draws)


if __name__ == '__main__':
    print("Converting newly found lottery data...\n")
    
    total = 0
    total += convert_chinese_ssq()
    total += convert_chinese_dlt()
    total += convert_chinese_qlc()
    total += convert_chinese_digits('cn_qxc', 'QXC (七星彩)', 7)
    total += convert_chinese_digits('cn_fc3d', 'FC3D (福彩3D)', 3)
    total += convert_chinese_digits('cn_pl3', 'PL3 (排列3)', 3)
    total += convert_chinese_digits('cn_pl5', 'PL5 (排列5)', 5)
    total += convert_eurojackpot()
    
    print(f"\n✓ Total NEW draws converted: {total:,}")
    print(f"\nNew lotteries added:")
    print(f"  🇨🇳 China: 7 lotteries (SSQ, DLT, QXC, QLC, FC3D, PL3, PL5)")
    print(f"  🇪🇺 Europe: EuroJackpot (5/50+2/10, 994 draws)")
    print(f"\nGrand total across ALL data sources:")
    
    # Count all
    import os
    all_draws = 0
    for f in os.listdir(DATA_DIR):
        if f.endswith('_standard.json') or (f.endswith('.json') and f.startswith(('ec_', 'pozo_', 'euromillions', 'la_primitiva', 'lotto_'))):
            try:
                with open(DATA_DIR / f) as fh:
                    d = json.load(fh)
                if isinstance(d, list):
                    all_draws += len(d)
            except:
                pass
    print(f"  Total draws across all lotteries: {all_draws:,}")

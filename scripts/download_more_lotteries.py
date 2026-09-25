"""
Download ALL lottery data from bettip.co.za free API.
No auth required. CC BY 4.0 license (attribution required).

Sources:
- bettip.co.za/api/v1 — UK49s, Gosloto, SA Lotto (Lotto, Powerball, Daily), World (UK Lotto, Irish, France, Greece, US Powerball, Mega Millions, EuroMillions)
- daowa89/lottery-archive on GitHub (already downloaded: EuroMillions, Lotto DE, Lotto AT)

Output: JSON files in /home/z/my-project/data/ for each lottery.
"""
import json
import urllib.request
import os
from pathlib import Path
from collections import Counter

DATA_DIR = Path('/home/z/my-project/data')
DATA_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  ✗ Error fetching {url}: {e}")
        return None

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    size = os.path.getsize(path)
    print(f"  ✓ Saved {path.name} ({size:,} bytes)")

print("=" * 70)
print("DESCARGANDO DATOS DE LOTERÍAS DESDE BETTIP.CO.ZA (API GRATUITA)")
print("=" * 70)

# 1. UK49s
print("\n1. UK49s...")
data = fetch_json('https://bettip.co.za/api/v1/uk49s/draws.json')
if data:
    save_json(data, DATA_DIR / 'uk49s_full.json')
    print(f"   Total draws: {data['count']}")
    print(f"   Date range: {data['data'][0]['date']} → {data['data'][-1]['date']}")

# 2. SA Lotto (all games: lotto, lotto-plus-1, lotto-plus-2, powerball, powerball-plus, daily-lotto)
print("\n2. SA Lotto (all games)...")
data = fetch_json('https://bettip.co.za/api/v1/lotto/draws.json')
if data:
    save_json(data, DATA_DIR / 'sa_lotto_full.json')
    print(f"   Total draws: {data['count']}")
    games = Counter(x.get('game','?') for x in data['data'])
    print(f"   Games: {dict(games)}")

# 3. Gosloto
print("\n3. Gosloto (Russia)...")
data = fetch_json('https://bettip.co.za/api/v1/gosloto/draws.json')
if data:
    save_json(data, DATA_DIR / 'gosloto_full.json')
    print(f"   Total draws: {data['count']}")

# 4. World lotteries (UK Lotto, Irish, France, Greece, US Powerball, Mega Millions, EuroMillions)
print("\n4. World lotteries (UK, Ireland, France, Greece, USA, Europe)...")
data = fetch_json('https://bettip.co.za/api/v1/world/draws.json')
if data:
    save_json(data, DATA_DIR / 'world_lotto_full.json')
    print(f"   Total draws: {data['count']}")
    games = Counter(x.get('game','?') for x in data['data'])
    print(f"   Games: {dict(games)}")

print("\n" + "=" * 70)
print("CONVERTIR A FORMATO ESTÁNDAR PARA EL PREDICTOR")
print("=" * 70)

def convert_bettip_uk49s(input_path, output_path, game_name='uk49s'):
    """Convert UK49s to standard format. Game: 6/49 + booster (1-49)"""
    with open(input_path) as f:
        data = json.load(f)
    draws = []
    for i, d in enumerate(data['data'], 1):
        main = d.get('numbers', [])
        booster = d.get('booster')
        bonus = [booster] if booster is not None else []
        draws.append({
            'draw_number': i,
            'date': d['date'],
            'main_numbers': main,
            'bonus_numbers': bonus,
            'jackpot_won': False,
            'jackpot_amount': None,
            'raw_data': {'source': 'bettip.co.za', 'game': game_name, 'draw_time': d.get('draw')}
        })
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(draws, f, ensure_ascii=False, indent=2)
    print(f"  ✓ {output_path.name}: {len(draws)} draws")

def convert_bettip_sa_lotto(input_path, output_path, game_filter):
    """Convert SA Lotto to standard format. Each draw has numbers (6) + optional bonus."""
    with open(input_path) as f:
        data = json.load(f)
    draws = []
    for i, d in enumerate(data['data'], 1):
        if d.get('game') != game_filter:
            continue
        main = d.get('numbers', [])
        bonus = d.get('bonus') or d.get('special')
        bonus_list = [bonus] if bonus is not None else []
        draws.append({
            'draw_number': len(draws) + 1,
            'date': d['date'],
            'main_numbers': main,
            'bonus_numbers': bonus_list,
            'jackpot_won': False,
            'jackpot_amount': None,
            'raw_data': {'source': 'bettip.co.za', 'game': game_filter}
        })
    if draws:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(draws, f, ensure_ascii=False, indent=2)
        print(f"  ✓ {output_path.name}: {len(draws)} draws")

def convert_bettip_world(input_path, output_path, game_filter):
    """Convert world lotteries to standard format."""
    with open(input_path) as f:
        data = json.load(f)
    draws = []
    for d in data['data']:
        if d.get('game') != game_filter:
            continue
        main = d.get('numbers', [])
        special = d.get('special')
        bonus = [special] if special is not None else []
        draws.append({
            'draw_number': len(draws) + 1,
            'date': d['date'],
            'main_numbers': main,
            'bonus_numbers': bonus,
            'jackpot_won': False,
            'jackpot_amount': None,
            'raw_data': {'source': 'bettip.co.za', 'game': game_filter, 'country': d.get('country')}
        })
    if draws:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(draws, f, ensure_ascii=False, indent=2)
        print(f"  ✓ {output_path.name}: {len(draws)} draws")

# UK49s
convert_bettip_uk49s(DATA_DIR / 'uk49s_full.json', DATA_DIR / 'uk49s.json')

# SA Lotto games (split by game)
convert_bettip_sa_lotto(DATA_DIR / 'sa_lotto_full.json', DATA_DIR / 'sa_lotto_6_52.json', 'lotto')
convert_bettip_sa_lotto(DATA_DIR / 'sa_lotto_full.json', DATA_DIR / 'sa_powerball.json', 'powerball')
convert_bettip_sa_lotto(DATA_DIR / 'sa_lotto_full.json', DATA_DIR / 'sa_daily_lotto.json', 'daily-lotto')

# World lotteries
convert_bettip_world(DATA_DIR / 'world_lotto_full.json', DATA_DIR / 'uk_lotto.json', 'uk-lotto')
convert_bettip_world(DATA_DIR / 'world_lotto_full.json', DATA_DIR / 'irish_lotto.json', 'irish-lotto')
convert_bettip_world(DATA_DIR / 'world_lotto_full.json', DATA_DIR / 'france_lotto.json', 'france-lotto')
convert_bettip_world(DATA_DIR / 'world_lotto_full.json', DATA_DIR / 'us_powerball.json', 'us-powerball')
convert_bettip_world(DATA_DIR / 'world_lotto_full.json', DATA_DIR / 'mega_millions.json', 'mega-millions')
convert_bettip_world(DATA_DIR / 'world_lotto_full.json', DATA_DIR / 'greece_powerball.json', 'greece-powerball')
convert_bettip_world(DATA_DIR / 'world_lotto_full.json', DATA_DIR / 'greek_lotto.json', 'greek-lotto')
convert_bettip_world(DATA_DIR / 'world_lotto_full.json', DATA_DIR / 'thunderball.json', 'thunderball')

print("\n" + "=" * 70)
print("✓ DESCARGA COMPLETA")
print("=" * 70)
print(f"\nTotal archivos JSON en {DATA_DIR}:")
for f in sorted(DATA_DIR.glob('*.json')):
    if f.name.endswith('_full.json') or f.name.startswith('search') or 'backtest' in f.name or 'patterns' in f.name or 'sorteo' in f.name or 'page' in f.name:
        continue
    if any(x in f.name for x in ['pozo', 'euromillions', 'la_primitiva', 'lotto_austrian']):
        continue
    size = f.stat().st_size
    print(f"  {f.name}: {size:,} bytes")

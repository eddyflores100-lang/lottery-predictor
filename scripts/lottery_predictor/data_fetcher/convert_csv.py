"""
Data fetcher/converters for external lottery data sources.
Converts raw CSV files to the JSON format expected by our Lottery classes.
"""
import csv
import json
from pathlib import Path
from datetime import datetime


def convert_euromillions_csv(csv_path: str, json_output: str) -> int:
    """
    Convert EuroMillions CSV (daowa89/lottery-archive format) to our JSON format.
    CSV: date,n1,n2,n3,n4,n5,s1,s2
    """
    draws = []
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            try:
                main = [int(row[f'n{j}']) for j in range(1, 6)]
                stars = [int(row['s1']), int(row['s2'])]
                draws.append({
                    'draw_number': i,
                    'date': row['date'],
                    'main_numbers': main,
                    'bonus_numbers': stars,
                    'jackpot_won': False,  # not in source
                    'jackpot_amount': None,
                    'raw_data': {'source': 'lottery-archive (daowa89)'}
                })
            except (KeyError, ValueError) as e:
                print(f"  Skipping row {i}: {e}")
    
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(draws, f, ensure_ascii=False, indent=2)
    
    print(f"  ✓ Converted {len(draws)} EuroMillions draws → {json_output}")
    return len(draws)


def convert_lotto6aus49_csv(csv_path: str, json_output: str) -> int:
    """
    Convert German Lotto 6aus49 CSV to JSON.
    CSV: date,n1,n2,n3,n4,n5,n6,superzahl
    Format identical to La Primitiva (6/49 + 1 bonus 0-9).
    We use this as proxy for La Primitiva since both are 6/49 format.
    """
    draws = []
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            try:
                main = [int(row[f'n{j}']) for j in range(1, 7)]
                superzahl_str = row.get('superzahl', '').strip()
                bonus = [int(superzahl_str)] if superzahl_str else []
                draws.append({
                    'draw_number': i,
                    'date': row['date'],
                    'main_numbers': main,
                    'bonus_numbers': bonus,
                    'jackpot_won': False,
                    'jackpot_amount': None,
                    'raw_data': {'source': 'lottery-archive (daowa89)', 'lottery': 'German Lotto 6aus49'}
                })
            except (KeyError, ValueError) as e:
                print(f"  Skipping row {i}: {e}")
    
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(draws, f, ensure_ascii=False, indent=2)
    
    print(f"  ✓ Converted {len(draws)} Lotto 6aus49 draws → {json_output}")
    return len(draws)


def convert_lotto6aus45_csv(csv_path: str, json_output: str) -> int:
    """
    Convert Austrian Lotto 6aus45 CSV to JSON.
    CSV: date,n1,n2,n3,n4,n5,n6,zusatzzahl
    """
    draws = []
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            try:
                main = [int(row[f'n{j}']) for j in range(1, 7)]
                zz_str = row.get('zusatzzahl', '').strip()
                bonus = [int(zz_str)] if zz_str else []
                draws.append({
                    'draw_number': i,
                    'date': row['date'],
                    'main_numbers': main,
                    'bonus_numbers': bonus,
                    'jackpot_won': False,
                    'jackpot_amount': None,
                    'raw_data': {'source': 'lottery-archive (daowa89)', 'lottery': 'Austrian Lotto 6aus45'}
                })
            except (KeyError, ValueError) as e:
                print(f"  Skipping row {i}: {e}")
    
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(draws, f, ensure_ascii=False, indent=2)
    
    print(f"  ✓ Converted {len(draws)} Lotto 6aus45 draws → {json_output}")
    return len(draws)


if __name__ == '__main__':
    import sys
    DATA_DIR = '/home/z/my-project/data'
    
    print("Converting lottery data files...\n")
    
    # EuroMillions
    convert_euromillions_csv(
        f'{DATA_DIR}/euromillions_raw.csv',
        f'{DATA_DIR}/euromillions.json'
    )
    
    # German Lotto 6aus49 (proxy for La Primitiva - same format)
    convert_lotto6aus49_csv(
        f'{DATA_DIR}/lotto_de_raw.csv',
        f'{DATA_DIR}/la_primitiva.json'  # reuse as La Primitiva
    )
    
    # Austrian Lotto 6aus45
    convert_lotto6aus45_csv(
        f'{DATA_DIR}/lotto_at_raw.csv',
        f'{DATA_DIR}/lotto_austrian.json'
    )
    
    print("\n✓ All conversions done.")

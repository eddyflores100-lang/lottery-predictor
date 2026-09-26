"""
OCR Worker v3 — extracts numbers from z-ai page_reader image descriptions.

The page_reader returns an AI-generated description of each image.
Sometimes the description includes the actual winning numbers
(e.g., "A scanned lottery ticket from the winning numbers 722001").

This worker:
1. Fetches each result page via z-ai (bypasses Cloudflare)
2. Extracts the image URL
3. Fetches the image description via z-ai page_reader
4. Extracts numbers from the description using regex + LLM
5. Updates the JSON data file

Usage:
  python3 ocr_worker_v3.py --lottery la_loteria --batch 50
  python3 ocr_worker_v3.py --all
"""
import json
import re
import os
import sys
import subprocess
import time
from pathlib import Path

DATA_DIR = Path('/home/z/my-project/data')

LOTTERIES = {
    'la_loteria': {
        'name': 'La Lotería',
        'data_file': DATA_DIR / 'ec_la_loteria.json',
        'expected_numbers': 5,
        'img_pattern': 'T1',  # T1 + sorteo number
    },
    'lotto': {
        'name': 'Lotto',
        'data_file': DATA_DIR / 'ec_lotto.json',
        'expected_numbers': 6,
        'img_pattern': 'T2',  # T2 + sorteo number
    },
    'pega': {
        'name': 'Pega',
        'data_file': DATA_DIR / 'ec_pega.json',
        'expected_numbers': 3,
        'img_pattern': 'T-',  # T- + sequential
    },
}


def fetch_page(url):
    """Fetch a page via z-ai page_reader (bypasses Cloudflare)."""
    try:
        result = subprocess.run(
            ['z-ai', 'function', '-n', 'page_reader',
             '-a', json.dumps({"url": url}),
             '-o', '/tmp/ocr3_page.json'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and os.path.exists('/tmp/ocr3_page.json'):
            with open('/tmp/ocr3_page.json') as f:
                return json.load(f).get('data', {}).get('html', '')
    except:
        pass
    return ''


def fetch_image_description(img_url):
    """Fetch image description via z-ai page_reader."""
    try:
        result = subprocess.run(
            ['z-ai', 'function', '-n', 'page_reader',
             '-a', json.dumps({"url": img_url}),
             '-o', '/tmp/ocr3_img.json'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and os.path.exists('/tmp/ocr3_img.json'):
            with open('/tmp/ocr3_img.json') as f:
                d = json.load(f)
            html = d.get('data', {}).get('html', '')
            # Extract description from <p> tag
            desc = re.search(r'<p>(.*?)</p>', html)
            if desc:
                return desc.group(1)
            # Or from the full text
            text = re.sub(r'<[^>]+>', ' ', html).strip()
            return text
    except:
        pass
    return ''


def extract_numbers_from_description(desc, sorteo, expected_count, img_pattern):
    """
    Extract winning numbers from the AI image description.
    
    The description sometimes contains phrases like:
    - "winning numbers 722001"
    - "numbers 8 2 1 3 6"
    - "the numbers are 8, 2, 1, 3, 6"
    - "resultado 82136"
    """
    # Remove the filename from the description (e.g., "T17345-211x300.jpg")
    desc_clean = re.sub(r'T\d[\w\-]*\.jpg', '', desc)
    
    # Pattern 1: "winning numbers NNNNN" or "numbers NNNNN"
    m = re.search(r'(?:winning\s+)?numbers?\s+(\d{' + str(expected_count) + r'})', desc_clean, flags=re.I)
    if m:
        digits = [int(d) for d in m.group(1)]
        if len(digits) == expected_count:
            return digits
    
    # Pattern 2: "numbers N N N N N" (space-separated)
    m = re.search(r'numbers?\s+((?:\d\s*){' + str(expected_count) + r'})', desc_clean, flags=re.I)
    if m:
        digits = [int(d) for d in re.findall(r'\d', m.group(1))]
        if len(digits) == expected_count:
            return digits
    
    # Pattern 3: Any sequence of exactly expected_count digits in the description
    # (excluding the sorteo number and image dimensions)
    # Remove known numbers (sorteo, dimensions like 211x300)
    desc_filtered = desc_clean
    desc_filtered = re.sub(r'\d{2,}x\d{2,}', '', desc_filtered)  # dimensions
    desc_filtered = re.sub(str(sorteo), '', desc_filtered)  # sorteo number
    desc_filtered = re.sub(r'\b\d{4,}\b', '', desc_filtered)  # 4+ digit numbers (years, etc.)
    
    # Find sequences of exactly expected_count digits
    matches = re.findall(r'\b(\d{' + str(expected_count) + r'})\b', desc_filtered)
    for match in matches:
        digits = [int(d) for d in match]
        # Validate: for La Lotería all digits should be 0-9
        if all(0 <= d <= 9 for d in digits):
            return digits
    
    # Pattern 4: Digits mentioned individually in the description
    # "the numbers 8, 2, 1, 3, 6 are shown"
    m = re.search(r'(\d)[,\s]+(\d)[,\s]+(\d)[,\s]+(\d)[,\s]+(\d)', desc_clean)
    if m and expected_count == 5:
        return [int(m.group(i)) for i in range(1, 6)]
    
    m = re.search(r'(\d)[,\s]+(\d)[,\s]+(\d)[,\s]+(\d)[,\s]+(\d)[,\s]+(\d)', desc_clean)
    if m and expected_count == 6:
        return [int(m.group(i)) for i in range(1, 7)]
    
    return None


def process_lottery(lottery_key, batch_size=50, start_index=0):
    """Process a lottery: fetch image descriptions and extract numbers."""
    config = LOTTERIES[lottery_key]
    data_file = config['data_file']
    
    with open(data_file) as f:
        draws = json.load(f)
    
    pending = [(i, d) for i, d in enumerate(draws) if not d.get('main_numbers')]
    print(f"\n{'='*60}")
    print(f"  {config['name']} — {len(pending)} draws pending")
    print(f"{'='*60}")
    
    if not pending:
        print("  ✅ All draws have numbers!")
        return
    
    batch = pending[start_index:start_index + batch_size]
    success = 0
    
    for processed, (idx, draw) in enumerate(batch):
        sorteo = draw['draw_number']
        date = draw['date']
        url = draw.get('raw_data', {}).get('url', '')
        
        print(f"\n  [{processed+1}/{len(batch)}] Sorteo {sorteo} ({date})...", end=' ')
        
        # Step 1: Fetch result page to get image URL
        html = fetch_page(url)
        if not html:
            print('❌ page fetch failed')
            continue
        
        # Step 2: Find image URL
        img_pattern = config['img_pattern']
        img_urls = re.findall(
            rf'(https?://contenidos\.loteria\.com\.ec/wp-content/uploads/[^\s"\'<>]*{img_pattern}{sorteo}[^\s"\'<>]*\.jpg)',
            html
        )
        
        # Prefer smaller size (211x300) for faster processing
        img_url = None
        for u in img_urls:
            if '211x300' in u:
                img_url = u
                break
        if not img_url and img_urls:
            img_url = img_urls[0]
        
        if not img_url:
            print('❌ no image URL')
            continue
        
        # Step 3: Fetch image description
        desc = fetch_image_description(img_url)
        if not desc:
            print('❌ no description')
            continue
        
        # Step 4: Extract numbers from description
        numbers = extract_numbers_from_description(desc, sorteo, config['expected_numbers'], img_pattern)
        
        if numbers:
            draw['main_numbers'] = numbers
            print(f'✅ {numbers}')
            success += 1
        else:
            # Save the description for manual review
            print(f'⚠️ desc: "{desc[:80]}..."')
            draw['raw_data']['img_description'] = desc
        
        time.sleep(1)  # rate limit safety
    
    # Save
    with open(data_file, 'w') as f:
        json.dump(draws, f, indent=2)
    
    with_numbers = sum(1 for d in draws if d.get('main_numbers'))
    print(f"\n  📊 Batch: {success}/{len(batch)} extracted")
    print(f"  📈 Total: {with_numbers}/{len(draws)} have numbers")
    print(f"  💾 Saved to {data_file}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='OCR Worker v3 — AI description extraction')
    parser.add_argument('--lottery', choices=['la_loteria', 'lotto', 'pega', 'all'], default='all')
    parser.add_argument('--batch', type=int, default=50)
    parser.add_argument('--start', type=int, default=0)
    args = parser.parse_args()
    
    if args.lottery == 'all':
        for lot_key in ['la_loteria', 'lotto', 'pega']:
            process_lottery(lot_key, args.batch, args.start)
    else:
        process_lottery(args.lottery, args.batch, args.start)


if __name__ == '__main__':
    main()

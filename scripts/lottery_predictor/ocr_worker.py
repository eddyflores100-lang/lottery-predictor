"""
OCR Worker for Ecuadorian Lottery Images
=========================================
Downloads result images from contenidos.loteria.com.ec and extracts
the winning numbers using Tesseract OCR (offline, no API limits).

Image URL patterns:
  La Lotería:  T1{sorteo}.jpg       (e.g. T17436.jpg for sorteo 7436)
  Lotto:       T2{sorteo}.jpg       (e.g. T23461.jpg for sorteo 3461)
  Pega:        T-{sequential}.jpg   (e.g. T-1000.jpg)

Usage:
  python3 ocr_worker.py --lottery la_loteria --batch 20
  python3 ocr_worker.py --lottery lotto --batch 20
  python3 ocr_worker.py --lottery pega --batch 20
  python3 ocr_worker.py --all
"""
import json
import re
import os
import sys
import subprocess
import time
import urllib.request
from pathlib import Path
from datetime import datetime

DATA_DIR = Path('/home/z/my-project/data')
IMG_DIR = Path('/home/z/my-project/data/lottery_images')
IMG_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = 'https://contenidos.loteria.com.ec/wp-content/uploads'
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}

# Lottery configurations
LOTTERIES = {
    'la_loteria': {
        'name': 'La Lotería',
        'data_file': DATA_DIR / 'ec_la_loteria.json',
        'img_prefix': 'T1',      # T1 + sorteo_number (without leading digit offset)
        'img_sorteo_offset': 0,  # sorteo 7436 → T17436
        'expected_numbers': 5,
        'number_range': (0, 9),
    },
    'lotto': {
        'name': 'Lotto',
        'data_file': DATA_DIR / 'ec_lotto.json',
        'img_prefix': 'T2',      # T2 + sorteo_number
        'img_sorteo_offset': 0,  # sorteo 3461 → T23461
        'expected_numbers': 6,
        'number_range': (0, 9),
    },
    'pega': {
        'name': 'Pega',
        'data_file': DATA_DIR / 'ec_pega.json',
        'img_prefix': 'T-',     # T- + sequential number
        'img_sorteo_offset': 0,
        'expected_numbers': 3,
        'number_range': (0, 9),
    },
}


def check_tesseract():
    """Check if Tesseract OCR is installed."""
    try:
        result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ Tesseract found: {version}")
            return True
    except FileNotFoundError:
        pass
    return False


def install_tesseract():
    """Install Tesseract OCR."""
    print("Installing Tesseract OCR...")
    os.system('apt-get update -qq && apt-get install -y -qq tesseract-ocr tesseract-ocr-spa 2>&1 | tail -3')
    return check_tesseract()


def download_image(url, filepath, retries=3):
    """Download an image with retries."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as r:
                data = r.read()
                if len(data) > 1000:  # valid image
                    with open(filepath, 'wb') as f:
                        f.write(data)
                    return True
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
    return False


def find_image_urls_for_sorteo(html, sorteo_number, lottery_key):
    """
    Find the actual image URL for a given sorteo number from the page HTML.
    Returns the best quality image URL.
    """
    # Pattern: T1{sorteo} or T2{sorteo} followed by optional size suffix
    if lottery_key == 'la_loteria':
        pattern = rf'(https?://contenidos\.loteria\.com\.ec/wp-content/uploads/[^\s"\'<>]*T1{sorteo_number}[^\s"\'<>]*\.jpg)'
    elif lottery_key == 'lotto':
        pattern = rf'(https?://contenidos\.loteria\.com\.ec/wp-content/uploads/[^\s"\'<>]*T2{sorteo_number}[^\s"\'<>]*\.jpg)'
    else:
        return None
    
    matches = re.findall(pattern, html)
    if not matches:
        return None
    
    # Prefer the 719x1024 or original (no suffix) version
    for url in matches:
        if '719x1024' in url or re.search(r'T\d+\.jpg$', url):
            return url
    
    return matches[0]  # any version


def ocr_image(filepath):
    """
    Run Tesseract OCR on an image and extract digits.
    Returns list of integers found.
    """
    try:
        # Run Tesseract with digit-only whitelist
        result = subprocess.run(
            ['tesseract', str(filepath), '-', '-l', 'spa', '--psm', '6',
             '-c', 'tessedit_char_whitelist=0123456789'],
            capture_output=True, text=True, timeout=10
        )
        text = result.stdout.strip()
        
        # Extract all single digits from the OCR output
        # The numbers should be 0-9, possibly with spaces/newlines
        digits = re.findall(r'\d', text)
        return [int(d) for d in digits]
    except Exception as e:
        return []


def ocr_image_enhanced(filepath, expected_count, number_range=(0, 9)):
    """
    Enhanced OCR: try multiple PSM modes and pick the best result.
    """
    best_digits = []
    
    for psm in [6, 7, 8, 11, 13]:
        try:
            result = subprocess.run(
                ['tesseract', str(filepath), '-', '-l', 'spa', '--psm', str(psm),
                 '-c', 'tessedit_char_whitelist=0123456789'],
                capture_output=True, text=True, timeout=10
            )
            text = result.stdout.strip()
            digits = [int(d) for d in re.findall(r'\d', text)]
            
            # Filter to valid range
            lo, hi = number_range
            digits = [d for d in digits if lo <= d <= hi]
            
            # If we got exactly the expected count, use this
            if len(digits) == expected_count:
                return digits
            
            # Track the best (closest to expected count)
            if len(digits) > len(best_digits) and len(digits) <= expected_count + 2:
                best_digits = digits
        except:
            pass
    
    # Return best_digits trimmed to expected count
    return best_digits[:expected_count] if best_digits else []


def process_lottery(lottery_key, batch_size=20, start_index=0):
    """
    Process a lottery: download images, OCR them, update JSON.
    """
    config = LOTTERIES[lottery_key]
    data_file = config['data_file']
    
    # Load existing data
    with open(data_file) as f:
        draws = json.load(f)
    
    # Find draws without numbers
    pending = [(i, d) for i, d in enumerate(draws) if not d.get('main_numbers')]
    print(f"\n{'='*60}")
    print(f"  {config['name']} — {len(pending)} draws pending OCR")
    print(f"{'='*60}")
    
    if not pending:
        print("  ✅ All draws already have numbers!")
        return
    
    # Process in batches
    batch = pending[start_index:start_index + batch_size]
    processed = 0
    success = 0
    
    for idx, draw in batch:
        sorteo = draw['draw_number']
        date = draw['date']
        url = draw.get('raw_data', {}).get('url', '')
        
        print(f"\n  [{processed+1}/{len(batch)}] Sorteo {sorteo} ({date})...")
        
        # We need to find the image URL
        # Strategy 1: try to construct URL from sorteo number
        # Strategy 2: fetch the page and extract image URL
        
        img_url = None
        
        # Strategy 1: construct URL
        if lottery_key == 'la_loteria':
            # Sorteo 7436 → T17436.jpg, upload year from date
            year = date[:4]
            month = date[5:7]
            for size in ['', '-719x1024', '-768x1094', '-211x300']:
                candidate = f"{BASE_URL}/{year}/{month}/T1{sorteo}{size}.jpg"
                # Try downloading
                img_path = IMG_DIR / f"la_loteria_{sorteo}.jpg"
                if download_image(candidate, img_path):
                    img_url = candidate
                    break
        
        elif lottery_key == 'lotto':
            year = date[:4]
            month = date[5:7]
            for size in ['', '-719x1024', '-768x1093', '-211x300']:
                candidate = f"{BASE_URL}/{year}/{month}/T2{sorteo}{size}.jpg"
                img_path = IMG_DIR / f"lotto_{sorteo}.jpg"
                if download_image(candidate, img_path):
                    img_url = candidate
                    break
        
        elif lottery_key == 'pega':
            # Pega uses sequential image numbers, not sorteo numbers
            # Try T-{sorteo}.jpg pattern
            year = date[:4]
            month = date[5:7]
            for size in ['', '-576x1024', '-169x300']:
                candidate = f"{BASE_URL}/{year}/{month}/T-{sorteo}{size}.jpg"
                img_path = IMG_DIR / f"pega_{sorteo}.jpg"
                if download_image(candidate, img_path):
                    img_url = candidate
                    break
        
        if not img_url:
            # Strategy 2: fetch the page via z-ai and extract image URL
            if url:
                try:
                    result = subprocess.run(
                        ['z-ai', 'function', '-n', 'page_reader',
                         '-a', json.dumps({"url": url}),
                         '-o', '/tmp/ocr_page.json'],
                        capture_output=True, text=True, timeout=30
                    )
                    if result.returncode == 0 and os.path.exists('/tmp/ocr_page.json'):
                        with open('/tmp/ocr_page.json') as f:
                            pd = json.load(f)
                        html = pd.get('data', {}).get('html', '')
                        img_url = find_image_urls_for_sorteo(html, sorteo, lottery_key)
                        if img_url:
                            img_path = IMG_DIR / f"{lottery_key}_{sorteo}.jpg"
                            if not download_image(img_url, img_path):
                                img_url = None
                except:
                    pass
        
        if not img_url or not img_path.exists():
            print(f"    ❌ Could not find/download image")
            processed += 1
            continue
        
        print(f"    📥 Image: {img_url}")
        
        # OCR the image
        digits = ocr_image_enhanced(img_path, config['expected_numbers'], config['number_range'])
        
        if digits and len(digits) >= config['expected_numbers'] - 1:
            draw['main_numbers'] = digits[:config['expected_numbers']]
            print(f"    ✅ Numbers: {draw['main_numbers']}")
            success += 1
        else:
            print(f"    ⚠️ OCR returned: {digits} (expected {config['expected_numbers']})")
            if digits:
                draw['main_numbers'] = digits[:config['expected_numbers']]
                success += 1
        
        processed += 1
        time.sleep(0.5)  # small delay between images
    
    # Save updated data
    with open(data_file, 'w') as f:
        json.dump(draws, f, indent=2)
    
    print(f"\n  📊 Results: {success}/{processed} successfully extracted")
    print(f"  💾 Saved to {data_file}")
    
    # Show total progress
    with_numbers = sum(1 for d in draws if d.get('main_numbers'))
    print(f"  📈 Total progress: {with_numbers}/{len(draws)} draws have numbers")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='OCR Worker for Ecuadorian Lotteries')
    parser.add_argument('--lottery', choices=['la_loteria', 'lotto', 'pega', 'all'], default='all')
    parser.add_argument('--batch', type=int, default=20, help='Number of draws to process per batch')
    parser.add_argument('--start', type=int, default=0, help='Start index within pending draws')
    args = parser.parse_args()
    
    # Check/install Tesseract
    if not check_tesseract():
        if not install_tesseract():
            print("❌ Cannot install Tesseract. Install manually: apt-get install tesseract-ocr tesseract-ocr-spa")
            sys.exit(1)
    
    if args.lottery == 'all':
        for lot_key in ['la_loteria', 'lotto', 'pega']:
            process_lottery(lot_key, args.batch, args.start)
    else:
        process_lottery(args.lottery, args.batch, args.start)


if __name__ == '__main__':
    main()

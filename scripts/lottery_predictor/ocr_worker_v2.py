"""
OCR Worker v2 — uses Playwright to bypass Cloudflare and download images.
Then Tesseract OCR extracts the numbers.

This is the production worker that processes all Ecuadorian lottery images.
"""
import json
import re
import os
import sys
import subprocess
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

DATA_DIR = Path('/home/z/my-project/data')
IMG_DIR = Path('/home/z/my-project/data/lottery_images')
IMG_DIR.mkdir(parents=True, exist_ok=True)

LOTTERIES = {
    'la_loteria': {
        'name': 'La Lotería',
        'data_file': DATA_DIR / 'ec_la_loteria.json',
        'expected_numbers': 5,
        'number_range': (0, 9),
        'img_pattern': r'T1(\d+)',
    },
    'lotto': {
        'name': 'Lotto',
        'data_file': DATA_DIR / 'ec_lotto.json',
        'expected_numbers': 6,
        'number_range': (0, 9),
        'img_pattern': r'T2(\d+)',
    },
    'pega': {
        'name': 'Pega',
        'data_file': DATA_DIR / 'ec_pega.json',
        'expected_numbers': 3,
        'number_range': (0, 9),
        'img_pattern': r'T-(\d+)',
    },
}


def download_image_with_playwright(url, filepath, page):
    """Download an image using Playwright (bypasses Cloudflare)."""
    try:
        # Navigate to the image URL — Playwright handles Cloudflare challenge
        response = page.goto(url, wait_until='networkidle', timeout=20000)
        if response and response.status == 200:
            # Get the image as bytes
            img_data = response.body()
            if img_data and len(img_data) > 5000:
                with open(filepath, 'wb') as f:
                    f.write(img_data)
                return True
        return False
    except Exception as e:
        return False


def ocr_image(filepath, expected_count, number_range=(0, 9)):
    """Run Tesseract OCR with multiple PSM modes."""
    best_digits = []
    
    for psm in [6, 7, 8, 11, 13, 3]:
        try:
            result = subprocess.run(
                ['tesseract', str(filepath), '-', '--psm', str(psm),
                 '-c', 'tessedit_char_whitelist=0123456789'],
                capture_output=True, text=True, timeout=10
            )
            text = result.stdout.strip()
            digits = [int(d) for d in re.findall(r'\d', text)]
            lo, hi = number_range
            digits = [d for d in digits if lo <= d <= hi]
            
            if len(digits) == expected_count:
                return digits
            if len(digits) > len(best_digits) and len(digits) <= expected_count + 2:
                best_digits = digits
        except:
            pass
    
    return best_digits[:expected_count] if best_digits else []


def find_image_url_from_page(html, lottery_key, sorteo):
    """Find the result image URL from a page's HTML."""
    config = LOTTERIES[lottery_key]
    pattern = config['img_pattern']
    
    # Find all image URLs matching the pattern
    imgs = re.findall(r'(https?://contenidos\.loteria\.com\.ec/wp-content/uploads/[^\s"\'<>]*\.jpg)', html)
    
    # Filter to result images for this specific sorteo
    matching = []
    for u in imgs:
        m = re.search(pattern, u)
        if m:
            # For La Lotería: T1 + sorteo number (e.g. T17435 for sorteo 7435)
            # For Lotto: T2 + sorteo number (e.g. T23460 for sorteo 3460)
            if lottery_key == 'la_loteria' and f'T1{sorteo}' in u:
                matching.append(u)
            elif lottery_key == 'lotto' and f'T2{sorteo}' in u:
                matching.append(u)
            elif lottery_key == 'pega':
                matching.append(u)
    
    if not matching:
        return None
    
    # Prefer 719x1024 size (good quality, not too large)
    for u in matching:
        if '719x1024' in u:
            return u
    # Or 211x300 (smaller, faster)
    for u in matching:
        if '211x300' in u:
            return u
    # Or original
    for u in matching:
        if re.search(r'T\d+\.jpg$', u):
            return u
    
    return matching[0]


def process_lottery(lottery_key, batch_size=20, start_index=0):
    """Process a lottery: download images via Playwright, OCR, update JSON."""
    config = LOTTERIES[lottery_key]
    data_file = config['data_file']
    
    with open(data_file) as f:
        draws = json.load(f)
    
    pending = [(i, d) for i, d in enumerate(draws) if not d.get('main_numbers')]
    print(f"\n{'='*60}")
    print(f"  {config['name']} — {len(pending)} draws pending OCR")
    print(f"{'='*60}")
    
    if not pending:
        print("  ✅ All draws already have numbers!")
        return
    
    batch = pending[start_index:start_index + batch_size]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        
        success = 0
        processed = 0
        
        for idx, draw in batch:
            sorteo = draw['draw_number']
            date = draw['date']
            url = draw.get('raw_data', {}).get('url', '')
            
            print(f"\n  [{processed+1}/{len(batch)}] Sorteo {sorteo} ({date})...", end=' ')
            
            # Step 1: Find the image URL by fetching the result page
            img_url = None
            if url:
                try:
                    response = page.goto(url, wait_until='domcontentloaded', timeout=15000)
                    if response and response.status == 200:
                        html = page.content()
                        img_url = find_image_url_from_page(html, lottery_key, sorteo)
                except:
                    pass
            
            if not img_url:
                # Try constructing URL directly
                year = date[:4]
                month = date[5:7]
                if lottery_key == 'la_loteria':
                    img_url = f"https://contenidos.loteria.com.ec/wp-content/uploads/{year}/{month}/T1{sorteo}-211x300.jpg"
                elif lottery_key == 'lotto':
                    img_url = f"https://contenidos.loteria.com.ec/wp-content/uploads/{year}/{month}/T2{sorteo}-211x300.jpg"
                elif lottery_key == 'pega':
                    img_url = f"https://contenidos.loteria.com.ec/wp-content/uploads/{year}/{month}/T-{sorteo}-169x300.jpg"
            
            if not img_url:
                print("❌ No image URL found")
                processed += 1
                continue
            
            # Step 2: Download the image via Playwright (bypasses Cloudflare)
            img_path = IMG_DIR / f"{lottery_key}_{sorteo}.jpg"
            
            try:
                response = page.goto(img_url, wait_until='networkidle', timeout=15000)
                if response and response.status == 200:
                    img_data = response.body()
                    if img_data and len(img_data) > 3000:
                        with open(img_path, 'wb') as f:
                            f.write(img_data)
                        print(f"📥 ", end='')
                    else:
                        print("❌ Image too small", end='')
                        processed += 1
                        continue
                else:
                    print(f"❌ HTTP {response.status_code if response else '?'}", end='')
                    processed += 1
                    continue
            except Exception as e:
                print(f"❌ Download error", end='')
                processed += 1
                continue
            
            # Step 3: OCR the image
            digits = ocr_image(img_path, config['expected_numbers'], config['number_range'])
            
            if digits and len(digits) >= config['expected_numbers'] - 1:
                draw['main_numbers'] = digits[:config['expected_numbers']]
                print(f"✅ {draw['main_numbers']}")
                success += 1
            elif digits:
                draw['main_numbers'] = digits[:config['expected_numbers']]
                print(f"⚠️ {digits}")
                success += 1
            else:
                print(f"❌ OCR failed")
            
            processed += 1
            time.sleep(0.3)
        
        browser.close()
    
    # Save updated data
    with open(data_file, 'w') as f:
        json.dump(draws, f, indent=2)
    
    with_numbers = sum(1 for d in draws if d.get('main_numbers'))
    print(f"\n  📊 Batch: {success}/{processed} success")
    print(f"  📈 Total: {with_numbers}/{len(draws)} draws have numbers")
    print(f"  💾 Saved to {data_file}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='OCR Worker v2 — Playwright + Tesseract')
    parser.add_argument('--lottery', choices=['la_loteria', 'lotto', 'pega', 'all'], default='all')
    parser.add_argument('--batch', type=int, default=20)
    parser.add_argument('--start', type=int, default=0)
    args = parser.parse_args()
    
    # Verify Tesseract
    try:
        subprocess.run(['tesseract', '--version'], capture_output=True, check=True)
        print("✅ Tesseract ready")
    except:
        print("❌ Tesseract not found")
        sys.exit(1)
    
    if args.lottery == 'all':
        for lot_key in ['la_loteria', 'lotto', 'pega']:
            process_lottery(lot_key, args.batch, args.start)
    else:
        process_lottery(args.lottery, args.batch, args.start)


if __name__ == '__main__':
    main()

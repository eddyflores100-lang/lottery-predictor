"""
Fetch Pozo Millonario result pages from the official loteria.com.ec site.
These pages contain both Pozo Millonario AND Pozo Revancha data.
We'll parse them later to fill in missing revancha data and verify prize info.
"""
import subprocess
import os
import time
import json
import re
from pathlib import Path

DATA_DIR = Path("/home/z/my-project/data/loteria_html")
DATA_DIR.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def fetch_url(url, out_file, max_retries=2):
    """Fetch URL with curl."""
    if out_file.exists() and out_file.stat().st_size > 5000:
        return True
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                ['curl', '-s', '-A', UA, '-L', '--max-time', '30', url, '-o', str(out_file)],
                capture_output=True, text=True, timeout=60
            )
            if out_file.exists() and out_file.stat().st_size > 5000:
                return True
            time.sleep(2)
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(2)
    return False

def main():
    # First, get the category pages to extract URLs
    # We already have pozo_category.json and pozo_page_2-10.json
    # Extract URLs from those
    all_urls = set()
    
    pages_dir = Path("/home/z/my-project/data")
    for fname in ["pozo_category.json"] + [f"pozo_page_{i}.json" for i in range(2, 11)]:
        fpath = pages_dir / fname
        if not fpath.exists():
            continue
        with open(fpath) as f:
            d = json.load(f)
        html = d.get('data', {}).get('html', '')
        urls = re.findall(
            r'https?://contenidos\.loteria\.com\.ec/[a-z0-9\-]*pozo[a-z0-9\-]*[^\s"\'<>]*',
            html, flags=re.I
        )
        for u in urls:
            u = u.split('?')[0].split('#')[0]
            if '/categoria/' in u or '/feed/' in u or '/page/' in u or '/wp-content/' in u or 'como-jugar' in u:
                continue
            all_urls.add(u)
    
    print(f"Found {len(all_urls)} URLs to fetch from loteria.com.ec")
    
    # Sort by sorteo number
    def sorteo_num(url):
        m = re.search(r'sorteo[s]?[- _]?(\d+)', url, flags=re.I)
        if not m:
            return 0
        nums = re.findall(r'sorteo[s]?[- _]?(\d+)', url, flags=re.I)
        nums = [int(n) for n in nums if 100 < int(n) < 2000]
        return max(nums) if nums else 0
    
    sorted_urls = sorted(all_urls, key=sorteo_num)
    
    # Fetch each URL
    success = 0
    failed = []
    for i, url in enumerate(sorted_urls):
        # Generate filename based on sorteo number
        sn = sorteo_num(url)
        if sn == 0:
            continue  # skip URLs we can't parse
        out_file = DATA_DIR / f"pozo_{sn:04d}.html"
        if i % 10 == 0:
            print(f"[{i}/{len(sorted_urls)}] Fetching sorteo {sn}...")
        ok = fetch_url(url, out_file)
        if ok:
            success += 1
        else:
            failed.append(sn)
        time.sleep(0.5)
    
    print(f"\nDone! Success: {success}/{len(sorted_urls)}, Failed: {len(failed)}")
    if failed:
        print(f"Failed: {failed}")
    
    # Also fetch the loteria.com.ec "Pozo" category pages 11+ if they exist (they probably don't)
    # But let me also try to search for older content via the WP search API
    # Skip this for now

if __name__ == '__main__':
    main()

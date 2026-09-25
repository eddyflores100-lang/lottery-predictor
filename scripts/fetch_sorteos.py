"""
Fetch all Pozo Millonario result pages from pozomillonario.info.
Iterates through sorteo numbers and saves each page as JSON.
Handles rate limits with backoff. Can be resumed.
"""
import subprocess
import os
import time
import json
import sys
from pathlib import Path

DATA_DIR = Path("/home/z/my-project/data/sorteos")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Range: sorteo 950 to 1257 covers ~3.5 years back from Sept 2026
# Sorteo 950 ≈ March 2022, Sorteo 1256 = Sept 21 2026
START = 950
END = 1257

def fetch_one(sorteo_num, max_retries=3):
    """Fetch one sorteo page using z-ai CLI. Returns True on success."""
    out_file = DATA_DIR / f"sorteo_{sorteo_num:04d}.json"
    if out_file.exists() and out_file.stat().st_size > 1000:
        # Check if it's a valid sorteo page (not 404)
        try:
            with open(out_file) as f:
                d = json.load(f)
            html = d.get('data', {}).get('html', '')
            if 'Pozo Millonario' in html and str(sorteo_num) in html:
                return True  # Already fetched
        except Exception:
            pass
    
    url = f"https://pozomillonario.info/pozo-millonario-sorteo-{sorteo_num}"
    
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                ['z-ai', 'function', '-n', 'page_reader',
                 '-a', json.dumps({"url": url}),
                 '-o', str(out_file)],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0 and out_file.exists():
                # Verify content
                try:
                    with open(out_file) as f:
                        d = json.load(f)
                    html = d.get('data', {}).get('html', '')
                    if 'Pozo Millonario' in html and str(sorteo_num) in html:
                        return True
                    elif '404' in d.get('data', {}).get('title', '') or 'no encontrada' in d.get('data', {}).get('title', ''):
                        # Page doesn't exist - delete and mark as missing
                        out_file.unlink()
                        return False
                except Exception as e:
                    print(f"  Parse error for {sorteo_num}: {e}")
            
            # If we got a 429, backoff
            stderr = result.stderr or ''
            stdout = result.stdout or ''
            if '429' in stderr or '429' in stdout:
                wait = 30 * (attempt + 1)
                print(f"  Rate limited on {sorteo_num}, waiting {wait}s...")
                time.sleep(wait)
                continue
            elif '500' in stderr or '500' in stdout:
                wait = 10 * (attempt + 1)
                print(f"  Server error on {sorteo_num}, waiting {wait}s...")
                time.sleep(wait)
                continue
            else:
                # Unknown error - try again
                print(f"  Attempt {attempt+1} failed for {sorteo_num}: {stderr[:200]}")
                time.sleep(8)
        except subprocess.TimeoutExpired:
            print(f"  Timeout for {sorteo_num}, retrying...")
            time.sleep(10)
    
    return False

def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else START
    end = int(sys.argv[2]) if len(sys.argv) > 2 else END
    
    total = end - start + 1
    success = 0
    failed = []
    
    print(f"Fetching sorteos {start} to {end} ({total} pages)...")
    
    for i, num in enumerate(range(start, end + 1)):
        if i % 10 == 0:
            print(f"[{i}/{total}] Processing sorteo {num}... (success so far: {success})")
        
        ok = fetch_one(num)
        if ok:
            success += 1
        else:
            failed.append(num)
        
        # Small delay between requests to avoid rate limit
        time.sleep(3)
    
    print(f"\nDone! Success: {success}/{total}, Failed: {len(failed)}")
    if failed:
        print(f"Failed sorteos: {failed}")
        # Save failed list
        with open('/home/z/my-project/data/failed_sorteos.json', 'w') as f:
            json.dump(failed, f)

if __name__ == '__main__':
    main()

"""
Fetch missing sorteo pages using direct curl (pozomillonario.info doesn't have Cloudflare).
Saves raw HTML, then we'll parse it.
"""
import subprocess
import os
import time
import sys
from pathlib import Path

DATA_DIR = Path("/home/z/my-project/data/sorteos_html")
DATA_DIR.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def fetch_one(sorteo_num):
    out_file = DATA_DIR / f"sorteo_{sorteo_num:04d}.html"
    if out_file.exists() and out_file.stat().st_size > 5000:
        return True
    url = f"https://pozomillonario.info/pozo-millonario-sorteo-{sorteo_num}"
    try:
        result = subprocess.run(
            ['curl', '-s', '-A', UA, '-L', '--max-time', '30', url, '-o', str(out_file)],
            capture_output=True, text=True, timeout=60
        )
        if out_file.exists() and out_file.stat().st_size > 5000:
            # Quick check for 404
            with open(out_file, errors='ignore') as f:
                content = f.read()
            if 'Pozo Millonario' in content and str(sorteo_num) in content:
                return True
            else:
                out_file.unlink()
                return False
        return False
    except Exception as e:
        print(f"  Error for {sorteo_num}: {e}")
        return False

def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 950
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 1260
    
    total = end - start + 1
    success = 0
    failed = []
    
    print(f"Curl-fetching sorteos {start} to {end}...")
    
    for i, num in enumerate(range(start, end + 1)):
        if i % 20 == 0:
            print(f"[{i}/{total}] Processing sorteo {num}... (success: {success})")
        ok = fetch_one(num)
        if ok:
            success += 1
        else:
            failed.append(num)
        time.sleep(0.3)  # Be gentle
    
    print(f"\nDone! Success: {success}/{total}, Failed: {len(failed)}")
    if failed:
        print(f"Failed: {failed}")

if __name__ == '__main__':
    main()

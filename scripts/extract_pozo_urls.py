"""Extract all Pozo Millonario result URLs from paginated archive pages - more generic pattern."""
import json
import re
from pathlib import Path

DATA_DIR = Path("/home/z/my-project/data")
all_urls = set()

# Page 1 is the category page itself
for fname in ["pozo_category.json"] + [f"pozo_page_{i}.json" for i in range(2, 11)]:
    fpath = DATA_DIR / fname
    if not fpath.exists():
        print(f"MISSING: {fname}")
        continue
    with open(fpath) as f:
        data = json.load(f)
    html = data.get("data", {}).get("html", "")
    # Match any URL that has pozo-millonario or pozo-revancha in the path and starts with contenidos.loteria.com.ec
    urls = re.findall(
        r'https?://contenidos\.loteria\.com\.ec/[a-z0-9\-]*pozo[a-z0-9\-]*[^\s"\'<>]*',
        html,
        flags=re.I,
    )
    # Filter: only keep URLs that look like result posts (not category pages)
    clean = set()
    for u in urls:
        u = u.split("?")[0]
        u = u.split("#")[0]
        # Skip category, feed, page urls
        if "/categoria/" in u or "/feed/" in u or "/page/" in u:
            continue
        # Skip URLs that are just asset uploads
        if "/wp-content/" in u:
            continue
        # Skip "como-jugar" and similar
        if "como-jugar" in u:
            continue
        clean.add(u)
    print(f"{fname}: {len(clean)} URLs")
    for u in sorted(clean):
        print(f"  {u}")
    all_urls.update(clean)

# Sort by sorteo number extracted from URL
def sorteo_num(url):
    m = re.search(r'sorteo[- _]?(\d+)', url, flags=re.I)
    if not m:
        return 0
    # Take the larger number (Pozo Millonario sorteo is usually > 1000)
    nums = re.findall(r'sorteo[- _]?(\d+)', url, flags=re.I)
    nums = [int(n) for n in nums if int(n) > 100]
    return max(nums) if nums else 0

sorted_urls = sorted(all_urls, key=sorteo_num)
print(f"\nTotal unique URLs: {len(sorted_urls)}")

# Print oldest & newest
if sorted_urls:
    print(f"Oldest: {sorted_urls[0]}")
    print(f"Newest: {sorted_urls[-1]}")

# Save to file
with open(DATA_DIR / "pozo_urls.txt", "w") as f:
    for u in sorted_urls:
        f.write(u + "\n")

print(f"\nSaved to {DATA_DIR / 'pozo_urls.txt'}")

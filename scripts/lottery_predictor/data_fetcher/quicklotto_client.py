"""
QuickLotto MCP Client — Free lottery results via MCP protocol.
Endpoint: https://quicklotto.io/mcp
39 lotteries supported, no auth required.

Tools available:
- list_lotteries: List all supported lotteries
- latest_results: Get latest results for all lotteries in one call
- lottery_results: Get historical results for a specific lottery (by code)
"""
import json
import urllib.request
from typing import Dict, List, Optional
import re
import os
from pathlib import Path

MCP_URL = "https://quicklotto.io/mcp"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

def _call_mcp(tool_name: str, arguments: dict = None, id_: int = 1) -> dict:
    """Call a QuickLotto MCP tool."""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments or {},
        },
        "id": id_,
    }
    req = urllib.request.Request(
        MCP_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers=HEADERS,
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=30) as r:  # nosec B310 — reviewed urlopen (https quicklotto API)
        return json.loads(r.read())


def list_lotteries() -> List[dict]:
    """List all 39 supported lotteries."""
    result = _call_mcp('list_lotteries', {}, 1)
    text = result['result']['content'][0]['text']
    
    # Parse the text response
    # Format: "- Name (code: code-name): pick X from Y, plus Z bonus from W. URL"
    lotteries = []
    for line in text.split('\n'):
        m = re.match(r'-\s+([^(]+)\s+\(code:\s*([^)]+)\):\s+(.+?)(?:https?://\S+)?$', line)
        if m:
            name = m.group(1).strip()
            code = m.group(2).strip()
            desc = m.group(3).strip().rstrip('.')
            
            # Parse "pick 6 from 49, plus 1 bonus from 9" or "pick 10 from 70"
            main_match = re.search(r'pick\s+(\d+)\s+from\s+(\d+)', desc)
            bonus_match = re.search(r'plus\s+(\d+)\s+bonus\s+from\s+(\d+)', desc)
            
            main_picks = int(main_match.group(1)) if main_match else 0
            main_pool = int(main_match.group(2)) if main_match else 0
            bonus_picks = int(bonus_match.group(1)) if bonus_match else 0
            bonus_pool = int(bonus_match.group(2)) if bonus_match else 0
            
            is_inhouse = 'IN-HOUSE' in desc.upper()
            
            lotteries.append({
                'name': name,
                'code': code,
                'main_picks': main_picks,
                'main_pool_size': main_pool,
                'bonus_picks': bonus_picks,
                'bonus_pool_size': bonus_pool,
                'is_inhouse': is_inhouse,
                'description': desc,
            })
    return lotteries


def get_lottery_results(code: str) -> List[dict]:
    """Get historical results for a specific lottery (returns ~30-50 draws)."""
    result = _call_mcp('lottery_results', {'lottery': code}, 2)
    text = result['result']['content'][0]['text']
    return _parse_results(text, code)


def get_latest_results() -> Dict[str, dict]:
    """Get latest results for all lotteries in one call."""
    result = _call_mcp('latest_results', {}, 3)
    text = result['result']['content'][0]['text']
    
    # Parse all entries
    latest = {}
    # Split by double newline (each result is a paragraph)
    entries = re.split(r'\n\n(?=[A-Z])', text)
    
    for entry in entries:
        # Find lottery name in the entry
        # Format: "The winning <Name> numbers on <date> were X, Y, Z..."
        # or: "<Name> is an in-house draw..."
        m = re.match(r'(?:The winning\s+)?([A-Za-z][A-Za-z\s/+]+?)(?:\s+is an in-house draw run by this site, not an official lottery)?\s+(?:numbers|on)', entry)
        if not m:
            continue
        name = m.group(1).strip()
        parsed = _parse_results(entry, '')
        if parsed:
            latest[name] = parsed[0]
    return latest


def _parse_results(text: str, code: str) -> List[dict]:
    """Parse the text response into structured draw data."""
    draws = []
    # Split by double newlines - each entry is a paragraph
    entries = text.split('\n\n')
    
    for entry in entries:
        entry = entry.strip()
        if not entry or 'Source:' not in entry:
            # Could be the last entry without Source, or a header line
            # Try to parse it anyway if it has the right pattern
            if 'were' not in entry:
                continue
        
        # Extract date - "on 2026-09-24 were"
        date_match = re.search(r'on\s+(\d{4}-\d{2}-\d{2})\s+were', entry)
        if not date_match:
            continue
        date = date_match.group(1)
        
        # Extract main numbers - "were X, Y, Z, ..." (numbers before "The bonus" or end)
        # Pattern: "were <numbers>." or "were <numbers>. The bonus"
        nums_match = re.search(r'were\s+([\d,\s]+?)\.', entry)
        if not nums_match:
            continue
        try:
            main_numbers = [int(n.strip()) for n in nums_match.group(1).split(',') if n.strip().isdigit()]
        except:
            continue
        
        if not main_numbers:
            continue
        
        # Extract bonus number(s)
        bonus_numbers = []
        # "The bonus number was X."
        bonus_match = re.search(r'bonus number was\s+(\d+)', entry)
        if bonus_match:
            bonus_numbers = [int(bonus_match.group(1))]
        else:
            # "The bonus numbers were X, Y."
            bonus_match = re.search(r'bonus numbers were\s+([\d,\s]+?)\.', entry)
            if bonus_match:
                try:
                    bonus_numbers = [int(n.strip()) for n in bonus_match.group(1).split(',') if n.strip().isdigit()]
                except:
                    pass
        
        draws.append({
            'date': date,
            'main_numbers': main_numbers,
            'bonus_numbers': bonus_numbers,
            'source': 'quicklotto.io',
            'code': code,
        })
    
    # Sort by date ascending
    draws.sort(key=lambda d: d['date'])
    
    # Add draw_number (1-indexed)
    for i, d in enumerate(draws, 1):
        d['draw_number'] = i
    
    return draws


def fetch_all_lotteries(output_dir: str = '/home/z/my-project/data/quicklotto'):
    """Fetch all 39 lotteries and save to JSON files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Fetching lottery list...")
    lotteries = list_lotteries()
    print(f"Found {len(lotteries)} lotteries")
    
    # Save catalog
    with open(output_dir / '_catalog.json', 'w', encoding='utf-8') as f:
        json.dump(lotteries, f, ensure_ascii=False, indent=2)
    
    # Fetch each lottery
    for lot in lotteries:
        code = lot['code']
        name = lot['name']
        print(f"\n  Fetching {name} ({code})...", end=' ')
        try:
            draws = get_lottery_results(code)
            print(f"{len(draws)} draws")
            
            # Save with code as filename
            output_file = output_dir / f'{code}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'lottery': lot,
                    'draws': draws,
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"ERROR: {e}")
    
    print(f"\n✓ All lotteries saved to {output_dir}")


if __name__ == '__main__':
    # Test
    print("=== Testing QuickLotto MCP Client ===\n")
    
    lotteries = list_lotteries()
    print(f"Total lotteries: {len(lotteries)}")
    for l in lotteries[:5]:
        print(f"  - {l['name']} ({l['code']}): {l['main_picks']}/{l['main_pool_size']}" +
              (f" +{l['bonus_picks']}/{l['bonus_pool_size']}" if l['bonus_picks'] else "") +
              (" [IN-HOUSE]" if l['is_inhouse'] else ""))
    
    print(f"\n=== Fetching ALL lotteries ===")
    fetch_all_lotteries()

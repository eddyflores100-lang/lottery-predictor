"""
Daily cron job to fetch fresh lottery data from quicklotto.io MCP.

Updates all 39 quicklotto lotteries daily. Can be run via:
- cron: 0 6 * * * python3 /home/z/my-project/scripts/lottery_predictor/daily_update.py
- manually: python3 daily_update.py
"""
import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/home/z/my-project/scripts/lottery_predictor')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/z/my-project/data/daily_update.log'),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Fetch fresh data from all sources."""
    start = datetime.now()
    logger.info("="*60)
    logger.info("LotteryPredictor daily update started")
    logger.info("="*60)
    
    # 1. Fetch all quicklotto data (39 lotteries)
    logger.info("\n[1/3] Fetching quicklotto.io MCP data (39 lotteries)...")
    try:
        sys.path.insert(0, '/home/z/my-project/scripts/lottery_predictor/data_fetcher')
        from quicklotto_client import fetch_all_lotteries, list_lotteries
        
        lotteries = list_lotteries()
        logger.info(f"  Found {len(lotteries)} lotteries on quicklotto.io")
        
        fetch_all_lotteries(output_dir='/home/z/my-project/data/quicklotto')
        logger.info("  ✓ quicklotto.io data updated")
    except Exception as e:
        logger.error(f"  ✗ quicklotto.io fetch failed: {e}")
    
    # 2. Fetch bettip.co.za data (UK49s, SA Lotto, World)
    logger.info("\n[2/3] Fetching bettip.co.za API data (UK49s, SA Lotto, World)...")
    try:
        sys.path.insert(0, '/home/z/my-project/scripts')
        # Reuse the download script
        from download_more_lotteries import fetch_json, save_json, DATA_DIR
        
        sources = [
            ('https://bettip.co.za/api/v1/uk49s/draws.json', 'uk49s_full.json'),
            ('https://bettip.co.za/api/v1/lotto/draws.json', 'sa_lotto_full.json'),
            ('https://bettip.co.za/api/v1/world/draws.json', 'world_lotto_full.json'),
        ]
        
        for url, filename in sources:
            data = fetch_json(url)
            if data:
                save_json(data, DATA_DIR / filename)
                logger.info(f"  ✓ {filename}: {data.get('count', 0)} draws")
        
        # Re-convert to standard format
        from download_more_lotteries import (convert_bettip_uk49s, convert_bettip_sa_lotto,
                                              convert_bettip_world)
        convert_bettip_uk49s(DATA_DIR / 'uk49s_full.json', DATA_DIR / 'uk49s.json')
        convert_bettip_sa_lotto(DATA_DIR / 'sa_lotto_full.json', DATA_DIR / 'sa_lotto_6_52.json', 'lotto')
        convert_bettip_sa_lotto(DATA_DIR / 'sa_lotto_full.json', DATA_DIR / 'sa_powerball.json', 'powerball')
        convert_bettip_sa_lotto(DATA_DIR / 'sa_lotto_full.json', DATA_DIR / 'sa_daily_lotto.json', 'daily-lotto')
        convert_bettip_world(DATA_DIR / 'world_lotto_full.json', DATA_DIR / 'uk_lotto.json', 'uk-lotto')
        convert_bettip_world(DATA_DIR / 'world_lotto_full.json', DATA_DIR / 'irish_lotto.json', 'irish-lotto')
        convert_bettip_world(DATA_DIR / 'world_lotto_full.json', DATA_DIR / 'france_lotto.json', 'france-lotto')
        convert_bettip_world(DATA_DIR / 'world_lotto_full.json', DATA_DIR / 'us_powerball.json', 'us-powerball')
        convert_bettip_world(DATA_DIR / 'world_lotto_full.json', DATA_DIR / 'mega_millions.json', 'mega-millions')
        
        logger.info("  ✓ bettip.co.za data updated")
    except Exception as e:
        logger.error(f"  ✗ bettip.co.za fetch failed: {e}")
    
    # 3. Update master catalogue
    logger.info("\n[3/3] Updating master catalogue...")
    try:
        sys.path.insert(0, '/home/z/my-project/scripts')
        from integrate_all_sources import load_all_lotteries
        
        all_lots = load_all_lotteries()
        catalogue_path = '/home/z/my-project/data/master_catalogue.json'
        with open(catalogue_path, 'w', encoding='utf-8') as f:
            json.dump(all_lots, f, ensure_ascii=False, indent=2, default=str)
        
        total_draws = sum(lot.get('total_draws', 0) for lot in all_lots.values())
        logger.info(f"  ✓ Catalogue updated: {len(all_lots)} lotteries, {total_draws:,} total draws")
    except Exception as e:
        logger.error(f"  ✗ Catalogue update failed: {e}")
    
    elapsed = (datetime.now() - start).total_seconds()
    logger.info("\n" + "="*60)
    logger.info(f"Daily update completed in {elapsed:.1f}s")
    logger.info("="*60 + "\n")


if __name__ == '__main__':
    main()

"""
Run backtest on new lotteries in parallel.
Skip LSTM and Monte Carlo for speed.
"""
import sys, os, json, time
sys.path.insert(0, '/home/z/my-project/scripts/lottery_predictor')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from lotteries import get_lottery, NEW_LOTTERIES, make_lottery
from engines import ENGINE_REGISTRY
from backtest import backtest_engine, baseline_random

# Engines to test (skip lstm + monte_carlo for speed)
test_engines = ['frequency', 'hot_cold', 'gap_analysis', 'markov_chain', 'bayesian', 'pattern_detection', 'entropy', 'ensemble']

lotteries_to_test = ['uk49s', 'sa_daily_lotto', 'sa_powerball', 'sa_lotto']

for lot_name in lotteries_to_test:
    print(f'\n=== {lot_name.upper()} ===')
    
    # Create a factory function
    def factory():
        return make_lottery(lot_name)
    
    path = NEW_LOTTERIES[lot_name]['data_file']
    
    # Load to get total
    lottery = make_lottery(lot_name)
    print(f'  Total draws: {lottery.total_draws()}')
    
    # Baseline
    bl = baseline_random(factory, path, min_history=50, max_test_draws=50, seed=42)
    print(f'  Baseline (random): {bl["avg_hits"]:.3f}')
    
    out = {
        'random_baseline': bl,
        'comparison': []
    }
    
    # Test each engine
    for eng_name in test_engines:
        start = time.time()
        try:
            result = backtest_engine(factory, path, eng_name, min_history=50, max_test_draws=50)
            elapsed = time.time() - start
            if 'error' in result:
                print(f'    {eng_name}: ERROR {result["error"]}')
            else:
                diff = result['avg_hits'] - bl['avg_hits']
                pct = (diff / bl['avg_hits']) * 100 if bl['avg_hits'] > 0 else 0
                print(f'    {eng_name:<20} avg={result["avg_hits"]:.3f} max={result["max_hits"]} diff={diff:+.3f} ({pct:+.1f}%) {elapsed:.1f}s')
                out['comparison'].append({
                    'engine': eng_name,
                    'avg_hits': result['avg_hits'],
                    'max_hits': result['max_hits'],
                    'avg_time_ms': result['avg_time_per_pred_ms'],
                    'tested': result['total_tested'],
                })
        except Exception as e:
            print(f'    {eng_name}: EXCEPTION {e}')
    
    # Sort by avg_hits
    out['comparison'].sort(key=lambda x: -x['avg_hits'])
    
    with open(f'/home/z/my-project/data/backtest_{lot_name}.json', 'w') as f:
        json.dump(out, f, indent=2)
    print(f'  ✓ Saved backtest_{lot_name}.json')

print('\n✓ Done')

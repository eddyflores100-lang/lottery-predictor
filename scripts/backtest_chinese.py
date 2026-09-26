import sys, os, json, time
sys.path.insert(0, '.')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
from lotteries import get_lottery, NEW_LOTTERIES
from engines import ENGINE_REGISTRY
from backtest import backtest_engine, baseline_random

lotteries_to_test = ['cn_pl3', 'cn_pl5', 'cn_ssq', 'cn_dlt', 'cn_fc3d']
test_engines = ['frequency', 'hot_cold', 'gap_analysis', 'markov_chain', 'bayesian', 'pattern_detection', 'entropy', 'ensemble']

for lot_name in lotteries_to_test:
    print(f'\n=== {lot_name.upper()} ===')
    
    def factory():
        return get_lottery(lot_name)
    
    from lotteries.generic import make_lottery
    lottery = make_lottery(lot_name)
    if not lottery:
        print(f'  SKIP: lottery not found')
        continue
    path = lottery._data_file if hasattr(lottery, '_data_file') else ''
    if not path:
        # Get from configs
        from lotteries.quicklotto_registry import merge_with_existing_v2
        configs = merge_with_existing_v2()
        path = configs.get(lot_name, {}).get('data_file', '')
    
    lottery2 = make_lottery(lot_name)
    lottery2.load_data(path)
    print(f'  Total draws: {lottery2.total_draws()}')
    
    bl = baseline_random(factory, path, min_history=50, max_test_draws=50, seed=42)
    print(f'  Baseline: {bl["avg_hits"]:.3f}')
    
    out = {'random_baseline': bl, 'comparison': []}
    for eng_name in test_engines:
        start = time.time()
        try:
            result = backtest_engine(factory, path, eng_name, min_history=50, max_test_draws=50)
            elapsed = time.time() - start
            if 'error' in result:
                print(f'    {eng_name}: ERROR')
            else:
                diff = result['avg_hits'] - bl['avg_hits']
                pct = (diff / bl['avg_hits']) * 100 if bl['avg_hits'] > 0 else 0
                print(f'    {eng_name:<22} avg={result["avg_hits"]:.3f} max={result["max_hits"]} {pct:+.1f}% ({elapsed:.1f}s)')
                out['comparison'].append({
                    'engine': eng_name,
                    'avg_hits': result['avg_hits'],
                    'max_hits': result['max_hits'],
                    'avg_time_ms': result['avg_time_per_pred_ms'],
                    'tested': result['total_tested'],
                })
        except Exception as e:
            print(f'    {eng_name}: EXCEPTION {e}')
    
    out['comparison'].sort(key=lambda x: -x['avg_hits'])
    with open(f'/home/z/my-project/data/backtest_{lot_name}.json', 'w') as f:
        json.dump(out, f, indent=2)
    print(f'  ✓ Saved backtest_{lot_name}.json')

print('\n✓ All Chinese lotteries backtested')

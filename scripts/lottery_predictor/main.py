"""
LotteryPredictor CLI — Usage:
    python main.py --lottery pozo_millonario --engine ensemble --predict
    python main.py --lottery pozo_millonario --backtest all
    python main.py --lottery pozo_millonario --engine frequency --analyze
"""
import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lotteries import get_lottery, LOTTERY_REGISTRY, NEW_LOTTERIES
from engines import ENGINE_REGISTRY
from backtest import backtest_engine, backtest_all_engines, compare_engines, baseline_random


# Default data paths per lottery
DEFAULT_DATA_PATHS = {
    'pozo_millonario': '/home/z/my-project/data/pozo_data.json',
    'la_primitiva': '/home/z/my-project/data/la_primitiva.json',  # Using German Lotto 6aus49 as proxy
    'euromillions': '/home/z/my-project/data/euromillions.json',
    'eurojackpot': '/home/z/my-project/data/eurojackpot.json',
    'el_gordo': '/home/z/my-project/data/el_gordo.json',
    'lotto_austrian': '/home/z/my-project/data/lotto_austrian.json',
}
# Add new generic lotteries
for k, v in NEW_LOTTERIES.items():
    DEFAULT_DATA_PATHS[k] = v['data_file']


# All available lotteries (existing + new)
ALL_LOTTERY_KEYS = list(LOTTERY_REGISTRY.keys()) + list(NEW_LOTTERIES.keys())


def load_lottery(name: str, data_path: str = None):
    """Load a lottery with its data."""
    lottery = get_lottery(name)
    path = data_path or DEFAULT_DATA_PATHS.get(name)
    if not path:
        raise ValueError(f"No data path configured for lottery: {name}")
    if not os.path.exists(path):
        print(f"❌ Data file not found: {path}")
        print(f"   Available lotteries with data: " +
              ", ".join(k for k, v in DEFAULT_DATA_PATHS.items() if os.path.exists(v)))
        sys.exit(1)
    lottery.load_data(path)
    return lottery


def cmd_describe(lottery):
    """Print lottery description."""
    print("\n" + "="*60)
    print(lottery.describe())
    print("="*60 + "\n")


def cmd_analyze(lottery, engine_name):
    """Run analysis and print results."""
    engine = ENGINE_REGISTRY[engine_name]
    print(f"\n🔍 Running {engine_name} analysis on {lottery.name}...\n")
    
    analysis = engine.analyze(lottery)
    
    # Pretty print key results
    print(json.dumps(_truncate_for_display(analysis), indent=2, ensure_ascii=False, default=str)[:3000])
    print("\n[Truncated for display. Full analysis available in code.]")


def cmd_predict(lottery, engine_name):
    """Generate prediction."""
    engine = ENGINE_REGISTRY[engine_name]
    print(f"\n🔮 Generating prediction with {engine_name} for {lottery.name}...\n")
    
    if engine_name == 'ensemble':
        result = engine.predict_with_explanation(lottery)
        pred = result['prediction']
        explanations = result['explanations']
        
        print(f"🎯 PREDICCIÓN: {' '.join(f'{n:02d}' for n in pred)}")
        print(f"\n📊 EXPLICACIÓN POR NÚMERO:")
        for exp in explanations:
            print(f"\n  #{exp['rank']}: Número {exp['number']:02d} (score: {exp['combined_score']:.3f})")
            for reason in exp['top_reasons']:
                print(f"      ← {reason}")
    else:
        pred = engine.predict(lottery)
        print(f"🎯 PREDICCIÓN: {' '.join(f'{n:02d}' for n in pred)}")
    
    print(f"\n⚠️  Recuerda: la lotería es aleatoria. Esta predicción es solo estadística.")


def cmd_backtest(lottery_name, data_path, engine_name, max_test):
    """Run backtesting."""
    # Get lottery class — either from registry or build a generic one
    if lottery_name in LOTTERY_REGISTRY:
        lottery_class = LOTTERY_REGISTRY[lottery_name]
    elif lottery_name in NEW_LOTTERIES:
        from lotteries import make_lottery
        # Use a factory that creates a fresh instance each time
        def lottery_class():
            return make_lottery(lottery_name)
    else:
        print(f"❌ Unknown lottery: {lottery_name}")
        return
    
    if engine_name == 'all':
        print(f"\n📊 Backtesting ALL engines on {lottery_name}...\n")
        results = backtest_all_engines(
            lottery_class, data_path,
            min_history=50, max_test_draws=max_test, verbose=True
        )
        
        # Also run random baseline
        print("\n=== Random baseline ===")
        baseline = baseline_random(lottery_class, data_path, min_history=50,
                                   max_test_draws=max_test)
        print(f"  → Avg hits: {baseline['avg_hits']}")
        
        # Compare
        print("\n" + "="*70)
        print(f"{'Engine':<25} {'Avg Hits':>10} {'Max':>5} {'Time/draw':>12} {'Tested':>8}")
        print("="*70)
        print(f"{'random_baseline':<25} {baseline['avg_hits']:>10.3f} {baseline['max_hits']:>5} {'N/A':>12} {baseline['total_tested']:>8}")
        
        comparison = compare_engines(results)
        for c in comparison:
            print(f"{c['engine']:<25} {c['avg_hits']:>10.3f} {c['max_hits']:>5} {c['avg_time_ms']:>10.1f}ms {c['tested']:>8}")
        print("="*70)
        
        # Save full results
        out_path = f"/home/z/my-project/data/backtest_{lottery_name}.json"
        with open(out_path, 'w', encoding='utf-8') as f:
            serializable = {
                engine: {k: v for k, v in r.items() if k != 'predictions'}
                for engine, r in results.items() if 'error' not in r
            }
            serializable['random_baseline'] = baseline
            serializable['comparison'] = comparison
            json.dump(serializable, f, indent=2, default=str)
        print(f"\n💾 Full results saved to: {out_path}")
        
    else:
        print(f"\n📊 Backtesting {engine_name} on {lottery_name}...\n")
        result = backtest_engine(
            lottery_class, data_path, engine_name,
            min_history=50, max_test_draws=max_test, verbose=True
        )
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return
        
        print(f"\n📈 Results:")
        print(f"  Total tested: {result['total_tested']}")
        print(f"  Average hits: {result['avg_hits']:.3f}")
        print(f"  Max hits: {result['max_hits']}")
        print(f"  Min hits: {result['min_hits']}")
        print(f"  Hits distribution: {dict(sorted(result['hits_distribution'].items()))}")
        print(f"  Avg time per prediction: {result['avg_time_per_pred_ms']:.1f}ms")


def cmd_list():
    """List available lotteries and engines."""
    print("\n🎰 AVAILABLE LOTTERIES:")
    # Existing lotteries from registry
    for name, cls in LOTTERY_REGISTRY.items():
        path = DEFAULT_DATA_PATHS.get(name, '')
        has_data = '✓' if os.path.exists(path) else '✗'
        instance = cls()
        print(f"  {has_data} {name:<20} - {instance.name} ({instance.country}) "
              f"- {instance.main_picks}/{instance.main_pool_size} - Odds 1:{instance.odds_jackpot:,}")
    # New generic lotteries
    from lotteries import make_lottery
    for name in NEW_LOTTERIES.keys():
        path = DEFAULT_DATA_PATHS.get(name, '')
        has_data = '✓' if os.path.exists(path) else '✗'
        instance = make_lottery(name)
        if instance:
            print(f"  {has_data} {name:<20} - {instance.name} ({instance.country}) "
                  f"- {instance.main_picks}/{instance.main_pool_size} - Odds 1:{instance.odds_jackpot:,}")
    
    print(f"\n⚙️  AVAILABLE ENGINES:")
    for name, eng in ENGINE_REGISTRY.items():
        doc = (eng.__doc__ or '').strip().split('\n')[0][:80]
        print(f"  {name:<20} - {doc}")
    
    print()


def _truncate_for_display(obj, max_items=10):
    """Truncate long dicts/lists for display."""
    if isinstance(obj, dict):
        if len(obj) > max_items:
            keys = list(obj.keys())[:max_items]
            return {k: _truncate_for_display(obj[k], max_items) for k in keys} | {'...': f'({len(obj)-max_items} more)'}
        return {k: _truncate_for_display(v, max_items) for k, v in obj.items()}
    elif isinstance(obj, list):
        if len(obj) > max_items:
            return [_truncate_for_display(x, max_items) for x in obj[:max_items]] + [f'... ({len(obj)-max_items} more)']
        return [_truncate_for_display(x, max_items) for x in obj]
    return obj


def main():
    parser = argparse.ArgumentParser(
        description='LotteryPredictor — Multi-lottery prediction system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --list
  python main.py --lottery pozo_millonario --describe
  python main.py --lottery pozo_millonario --engine ensemble --predict
  python main.py --lottery pozo_millonario --engine frequency --analyze
  python main.py --lottery pozo_millonario --backtest all --max-test 100
        """
    )
    parser.add_argument('--list', action='store_true', help='List available lotteries and engines')
    parser.add_argument('--lottery', type=str, help='Lottery name (e.g. pozo_millonario)')
    parser.add_argument('--data', type=str, help='Custom data file path')
    parser.add_argument('--describe', action='store_true', help='Show lottery description')
    parser.add_argument('--engine', type=str, help='Engine to use (frequency, ensemble, etc.)')
    parser.add_argument('--analyze', action='store_true', help='Run engine analysis')
    parser.add_argument('--predict', action='store_true', help='Generate prediction')
    parser.add_argument('--backtest', type=str, help='Backtest engine (or "all")')
    parser.add_argument('--max-test', type=int, default=None, help='Max draws to test in backtest')
    
    args = parser.parse_args()
    
    if args.list:
        cmd_list()
        return
    
    if not args.lottery:
        parser.print_help()
        return
    
    if args.lottery not in ALL_LOTTERY_KEYS:
        print(f"❌ Unknown lottery: {args.lottery}")
        print(f"   Available: {ALL_LOTTERY_KEYS}")
        sys.exit(1)
    
    if args.describe:
        lottery = load_lottery(args.lottery, args.data)
        cmd_describe(lottery)
        return
    
    if args.backtest:
        cmd_backtest(args.lottery, args.data or DEFAULT_DATA_PATHS.get(args.lottery),
                     args.backtest, args.max_test)
        return
    
    if args.analyze or args.predict:
        if not args.engine:
            print("❌ --engine required for --analyze or --predict")
            sys.exit(1)
        if args.engine not in ENGINE_REGISTRY:
            print(f"❌ Unknown engine: {args.engine}")
            print(f"   Available: {list(ENGINE_REGISTRY.keys())}")
            sys.exit(1)
        
        lottery = load_lottery(args.lottery, args.data)
        
        if args.describe:
            cmd_describe(lottery)
        
        if args.analyze:
            cmd_analyze(lottery, args.engine)
        
        if args.predict:
            cmd_predict(lottery, args.engine)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

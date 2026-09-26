"""
CLI wrapper that outputs JSON for the web API.
Usage: python3 cli_json.py lotteries
       python3 cli_json.py engines
       python3 cli_json.py predict <lottery> <engine>
       python3 cli_json.py backtest <lottery>
       python3 cli_json.py describe <lottery>
"""
import sys
import os
import json

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def cmd_lotteries():
    from lotteries import LOTTERY_REGISTRY, NEW_LOTTERIES, make_lottery
    from lotteries.generic import get_all_lottery_keys
    try:
        from lotteries.quicklotto_registry import merge_with_existing, merge_with_existing_v2
        all_configs = merge_with_existing_v2()
    except Exception:
        all_configs = dict(NEW_LOTTERIES)
    
    DEFAULT_DATA_PATHS = {
        'pozo_millonario': '/home/z/my-project/data/pozo_data.json',
        'la_primitiva': '/home/z/my-project/data/la_primitiva.json',
        'euromillions': '/home/z/my-project/data/euromillions.json',
        'eurojackpot': '/home/z/my-project/data/eurojackpot.json',
        'el_gordo': '/home/z/my-project/data/el_gordo.json',
        'lotto_austrian': '/home/z/my-project/data/lotto_austrian.json',
    }
    # Add all generic + quicklotto lotteries
    for k, v in all_configs.items():
        DEFAULT_DATA_PATHS[k] = v['data_file']
    
    result = []
    seen_keys = set()
    
    # Existing lotteries from registry
    for name, cls in LOTTERY_REGISTRY.items():
        path = DEFAULT_DATA_PATHS.get(name, '')
        has_data = os.path.exists(path)
        instance = cls()
        result.append({
            'key': name,
            'name': instance.name,
            'country': instance.country,
            'main_pool_size': instance.main_pool_size,
            'main_picks': instance.main_picks,
            'bonus_pool_size': instance.bonus_pool_size,
            'bonus_picks': instance.bonus_picks,
            'draws_per_week': instance.draws_per_week,
            'currency': instance.currency,
            'min_jackpot': instance.min_jackpot,
            'odds_jackpot': instance.odds_jackpot,
            'has_data': has_data,
            'data_path': path,
        })
        seen_keys.add(name)
    
    # All generic + quicklotto lotteries
    for name in all_configs.keys():
        if name in seen_keys:
            continue
        instance = make_lottery(name)
        if instance is None:
            continue
        path = DEFAULT_DATA_PATHS.get(name, '')
        has_data = os.path.exists(path)
        result.append({
            'key': name,
            'name': instance.name,
            'country': instance.country,
            'main_pool_size': instance.main_pool_size,
            'main_picks': instance.main_picks,
            'bonus_pool_size': instance.bonus_pool_size,
            'bonus_picks': instance.bonus_picks,
            'draws_per_week': instance.draws_per_week,
            'currency': instance.currency,
            'min_jackpot': instance.min_jackpot,
            'odds_jackpot': instance.odds_jackpot,
            'has_data': has_data,
            'data_path': path,
        })
        seen_keys.add(name)
    return result


def cmd_engines():
    from engines import ENGINE_REGISTRY
    result = []
    for name, eng in ENGINE_REGISTRY.items():
        doc = (eng.__doc__ or '').strip().split('\n')[0]
        result.append({
            'key': name,
            'name': name.replace('_', ' ').title(),
            'description': doc,
        })
    return result


def cmd_describe(lottery_name):
    from lotteries import get_lottery, NEW_LOTTERIES
    try:
        from lotteries.quicklotto_registry import merge_with_existing, merge_with_existing_v2
        all_configs = merge_with_existing_v2()
    except Exception:
        all_configs = dict(NEW_LOTTERIES)
    DEFAULT_DATA_PATHS = {
        'pozo_millonario': '/home/z/my-project/data/pozo_data.json',
        'la_primitiva': '/home/z/my-project/data/la_primitiva.json',
        'euromillions': '/home/z/my-project/data/euromillions.json',
        'eurojackpot': '/home/z/my-project/data/eurojackpot.json',
        'el_gordo': '/home/z/my-project/data/el_gordo.json',
        'lotto_austrian': '/home/z/my-project/data/lotto_austrian.json',
    }
    for k, v in all_configs.items():
        DEFAULT_DATA_PATHS[k] = v['data_file']
    
    lottery = get_lottery(lottery_name)
    path = DEFAULT_DATA_PATHS.get(lottery_name)
    if path and os.path.exists(path):
        lottery.load_data(path)
    return {
        'name': lottery.name,
        'country': lottery.country,
        'main_pool_size': lottery.main_pool_size,
        'main_picks': lottery.main_picks,
        'bonus_pool_size': lottery.bonus_pool_size,
        'bonus_picks': lottery.bonus_picks,
        'draws_per_week': lottery.draws_per_week,
        'currency': lottery.currency,
        'min_jackpot': lottery.min_jackpot,
        'odds_jackpot': lottery.odds_jackpot,
        'total_draws': lottery.total_draws(),
        'date_range': lottery.date_range(),
        'last_draw': ({
            'draw_number': lottery.draws[-1].draw_number,
            'date': lottery.draws[-1].date,
            'main_numbers': lottery.draws[-1].main_numbers,
        } if lottery.draws else None),
    }


def cmd_predict(lottery_name, engine_name):
    from lotteries import get_lottery, NEW_LOTTERIES
    from engines import ENGINE_REGISTRY
    try:
        from lotteries.quicklotto_registry import merge_with_existing, merge_with_existing_v2
        all_configs = merge_with_existing_v2()
    except Exception:
        all_configs = dict(NEW_LOTTERIES)
    DEFAULT_DATA_PATHS = {
        'pozo_millonario': '/home/z/my-project/data/pozo_data.json',
        'la_primitiva': '/home/z/my-project/data/la_primitiva.json',
        'euromillions': '/home/z/my-project/data/euromillions.json',
        'eurojackpot': '/home/z/my-project/data/eurojackpot.json',
        'el_gordo': '/home/z/my-project/data/el_gordo.json',
        'lotto_austrian': '/home/z/my-project/data/lotto_austrian.json',
    }
    for k, v in all_configs.items():
        DEFAULT_DATA_PATHS[k] = v['data_file']
    
    lottery = get_lottery(lottery_name)
    path = DEFAULT_DATA_PATHS.get(lottery_name)
    lottery.load_data(path)
    
    engine = ENGINE_REGISTRY[engine_name]
    
    if engine_name == 'ensemble':
        result = engine.predict_with_explanation(lottery)
        return {
            'lottery': lottery.name,
            'engine': engine_name,
            'prediction': result['prediction'],
            'explanations': result['explanations'],
            'last_draw': ({
                'draw_number': lottery.draws[-1].draw_number,
                'date': lottery.draws[-1].date,
                'main_numbers': lottery.draws[-1].main_numbers,
            } if lottery.draws else None),
        }
    else:
        prediction = engine.predict(lottery)
        return {
            'lottery': lottery.name,
            'engine': engine_name,
            'prediction': prediction,
            'last_draw': ({
                'draw_number': lottery.draws[-1].draw_number,
                'date': lottery.draws[-1].date,
                'main_numbers': lottery.draws[-1].main_numbers,
            } if lottery.draws else None),
        }


def cmd_backtest(lottery_name):
    """Return cached backtest results if available."""
    path = f'/home/z/my-project/data/backtest_{lottery_name}.json'
    if not os.path.exists(path):
        return {'error': f'No backtest available for {lottery_name}'}
    with open(path) as f:
        return json.load(f)


def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Missing command'}))
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    # Suppress TF logs
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
    
    try:
        if cmd == 'lotteries':
            result = cmd_lotteries()
        elif cmd == 'engines':
            result = cmd_engines()
        elif cmd == 'describe':
            result = cmd_describe(sys.argv[2])
        elif cmd == 'predict':
            result = cmd_predict(sys.argv[2], sys.argv[3])
        elif cmd == 'backtest':
            result = cmd_backtest(sys.argv[2])
        else:
            result = {'error': f'Unknown command: {cmd}'}
        
        print(json.dumps(result, ensure_ascii=False, default=str))
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == '__main__':
    main()

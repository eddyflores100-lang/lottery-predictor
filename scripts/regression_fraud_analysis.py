"""
Regresión numérica + detección de trampas.

Para cada uno de los últimos N sorteos de cada lotería:
1. Predecir usando datos previos (con cada motor)
2. Comparar con resultado real
3. Calcular proximidad (aciertos exactos + cercanía por diferencia numérica)

Detección de trampa:
- Chi-cuadrado por lotería (¿distribución uniforme?)
- Runs test por número (¿secuencia aleatoria?)
- Autocorrelación por número (¿hay memoria?)
- Detección de sorteos sospechosos (combinaciones imposibles)
- Detección de patrones repetidos exactos
- Análisis de varianza entre períodos
- Hot/cold extremos (¿alguno fuera de 3 sigma?)
"""
import sys, os, json, math
sys.path.insert(0, '/home/z/my-project/scripts/lottery_predictor')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from collections import Counter, defaultdict
from statistics import mean, median, stdev
from datetime import datetime

from lotteries import get_lottery, LOTTERY_REGISTRY
from engines import ENGINE_REGISTRY

DATA_PATHS = {
    'pozo_millonario': '/home/z/my-project/data/pozo_data.json',
    'euromillions': '/home/z/my-project/data/euromillions.json',
    'la_primitiva': '/home/z/my-project/data/la_primitiva.json',
    'lotto_austrian': '/home/z/my-project/data/lotto_austrian.json',
}

# ============================================================
# 1. REGRESIÓN NUMÉRICA — Predicción vs Real
# ============================================================
print("="*80)
print("ANÁLISIS DE REGRESIÓN NUMÉRICA — PREDICCIÓN vs RESULTADO REAL")
print("="*80)

# Test on Pozo Millonario (we'll use last 30 draws for testing)
print("\n🔍 Pozo Millonario — últimos 30 sorteos\n")

lottery = get_lottery('pozo_millonario')
lottery.load_data(DATA_PATHS['pozo_millonario'])
total = lottery.total_draws()
print(f"Total sorteos: {total}")

# Engines to test (skip lstm + monte_carlo for speed)
test_engines = ['frequency', 'markov_chain', 'bayesian', 'hot_cold', 'gap_analysis',
                'pattern_detection', 'entropy', 'ensemble']

test_indices = list(range(total - 30, total))
results_per_engine = defaultdict(list)
predictions_log = []  # for detailed analysis

for i, test_idx in enumerate(test_indices):
    past_lottery = get_lottery('pozo_millonario')
    past_lottery.draws = lottery.draws[:test_idx]
    
    actual = set(lottery.draws[test_idx].main_numbers)
    actual_sorted = sorted(actual)
    
    draw_predictions = {'draw': lottery.draws[test_idx], 'actual': sorted(actual), 'predictions': {}}
    
    for eng_name in test_engines:
        engine = ENGINE_REGISTRY[eng_name]
        try:
            pred = engine.predict(past_lottery)
            pred_set = set(pred)
            hits = len(pred_set & actual)
            
            # Cercanía: suma de diferencias absolutas entre predicción y realidad
            # Para cada número predicho, calcular distancia mínima a un número real
            total_distance = 0
            for p in sorted(pred_set):
                min_dist = min(abs(p - a) for a in actual_sorted)
                total_distance += min_dist
            
            avg_distance = total_distance / len(pred_set) if pred_set else 0
            
            results_per_engine[eng_name].append({
                'draw_number': lottery.draws[test_idx].draw_number,
                'date': lottery.draws[test_idx].date,
                'hits': hits,
                'avg_distance': avg_distance,
                'prediction': sorted(pred_set),
            })
            
            draw_predictions['predictions'][eng_name] = {
                'prediction': sorted(pred_set),
                'hits': hits,
                'avg_distance': avg_distance,
            }
        except Exception as e:
            print(f"  Error {eng_name} en sorteo {lottery.draws[test_idx].draw_number}: {e}")
    
    predictions_log.append(draw_predictions)
    
    if (i+1) % 10 == 0:
        print(f"  Procesado {i+1}/30 sorteos...")

# Print summary per engine
print(f"\n{'Motor':<22} {'Aciertos prom':>14} {'Cercanía prom':>14} {'Mejor sorteo':>14} {'Peor sorteo':>14}")
print("-"*82)
for eng_name in test_engines:
    results = results_per_engine[eng_name]
    if not results:
        continue
    avg_hits = mean(r['hits'] for r in results)
    avg_dist = mean(r['avg_distance'] for r in results)
    best = max(results, key=lambda x: x['hits'])
    worst = min(results, key=lambda x: x['hits'])
    print(f"{eng_name:<22} {avg_hits:>14.3f} {avg_dist:>14.3f} {best['hits']:>14} {worst['hits']:>14}")

# Top 5 mejores predicciones individuales
print(f"\n🎯 TOP 5 PREDICCIONES MÁS CERCANAS (cualquier motor)")
print(f"{'Sorteo':>7} {'Fecha':>12} {'Motor':<20} {'Aciertos':>10} {'Dist':>7} {'Predicción':<35} {'Real':<35}")
print("-"*130)

all_predictions = []
for eng_name, results in results_per_engine.items():
    for r in results:
        all_predictions.append({**r, 'engine': eng_name})

# Sort by hits desc, then by avg_distance asc
all_predictions.sort(key=lambda x: (-x['hits'], x['avg_distance']))
for p in all_predictions[:5]:
    actual = next(d['actual'] for d in predictions_log if d['draw'].draw_number == p['draw_number'])
    pred_str = ' '.join(f'{n:02d}' for n in p['prediction'])
    actual_str = ' '.join(f'{n:02d}' for n in actual)
    print(f"  {p['draw_number']:>5} {p['date']:>12} {p['engine']:<20} {p['hits']:>10} {p['avg_distance']:>7.2f} {pred_str:<35} {actual_str:<35}")

# ============================================================
# 2. DETECCIÓN DE TRAMPA — Tests estadísticos
# ============================================================
print("\n\n" + "="*80)
print("DETECCIÓN DE TRAMPA — TESTS ESTADÍSTICOS DE ALEATORIEDAD")
print("="*80)

def chi_squared_test(lottery):
    """¿La distribución de números es uniforme?"""
    pool_size = lottery.main_pool_size
    picks = lottery.main_picks
    total = lottery.total_draws()
    
    counter = Counter()
    for d in lottery.draws:
        for n in d.main_numbers:
            counter[n] += 1
    
    expected = (picks / pool_size) * total
    chi_sq = sum((counter.get(n, 0) - expected) ** 2 / expected for n in range(1, pool_size + 1))
    
    # df = pool_size - 1, critical value at 5% significance
    df = pool_size - 1
    # Approximate critical value
    z = 1.6449
    critical = df * (1 - 2/(9*df) + z * math.sqrt(2/(9*df)))**3
    
    return {
        'chi_squared': round(chi_sq, 2),
        'critical_5pct': round(critical, 2),
        'is_uniform': chi_sq < critical,
        'expected_per_number': round(expected, 2),
        'max_deviation': round(max(abs(counter.get(n, 0) - expected) for n in range(1, pool_size + 1)) / expected * 100, 2),
    }


def runs_test_per_number(lottery):
    """Para cada número, ¿la secuencia aparición/no-aparición es aleatoria?"""
    pool_size = lottery.main_pool_size
    results = {}
    for n in range(1, pool_size + 1):
        sequence = [1 if n in d.main_numbers else 0 for d in lottery.draws]
        n1 = sum(sequence)
        n0 = len(sequence) - n1
        if n1 == 0 or n0 == 0:
            results[n] = {'z_score': 0, 'is_random': True}
            continue
        # Count runs
        runs = 1
        for i in range(1, len(sequence)):
            if sequence[i] != sequence[i-1]:
                runs += 1
        expected_runs = (2 * n1 * n0) / (n1 + n0) + 1
        variance = (2 * n1 * n0 * (2 * n1 * n0 - n1 - n0)) / ((n1 + n0)**2 * (n1 + n0 - 1))
        if variance <= 0:
            results[n] = {'z_score': 0, 'is_random': True, 'runs': runs}
            continue
        z = (runs - expected_runs) / math.sqrt(variance)
        results[n] = {
            'runs': runs,
            'expected_runs': round(expected_runs, 1),
            'z_score': round(z, 3),
            'is_random': abs(z) < 1.96,
        }
    return results


def autocorrelation_per_number(lottery, lag=1):
    """¿Hay memoria en la secuencia de apariciones?"""
    pool_size = lottery.main_pool_size
    results = {}
    for n in range(1, pool_size + 1):
        seq = [1 if n in d.main_numbers else 0 for d in lottery.draws]
        if len(seq) <= lag:
            results[n] = 0
            continue
        mean_val = sum(seq) / len(seq)
        variance = sum((x - mean_val)**2 for x in seq) / len(seq)
        if variance == 0:
            results[n] = 0
            continue
        cov = sum((seq[i] - mean_val) * (seq[i+lag] - mean_val) for i in range(len(seq) - lag)) / (len(seq) - lag)
        results[n] = round(cov / variance, 4)
    return results


def detect_suspicious_draws(lottery):
    """Detectar sorteos con patrones sospechosos."""
    suspicious = []
    for d in lottery.draws:
        nums = sorted(set(d.main_numbers))
        reasons = []
        
        # 1. Números consecutivos largos (4+ seguidos): muy improbable
        consecutive = 1
        max_consec = 1
        for i in range(1, len(nums)):
            if nums[i] == nums[i-1] + 1:
                consecutive += 1
                max_consec = max(max_consec, consecutive)
            else:
                consecutive = 1
        if max_consec >= 4:
            reasons.append(f"{max_consec} números consecutivos")
        
        # 2. Suma fuera de 3 desviaciones estándar
        s = sum(nums)
        # Expected sum: picks * (pool_size + 1) / 2
        # Variance: picks * (pool_size^2 - 1) / 12
        expected_sum = lottery.main_picks * (lottery.main_pool_size + 1) / 2
        std_sum = math.sqrt(lottery.main_picks * (lottery.main_pool_size**2 - 1) / 12)
        z = (s - expected_sum) / std_sum
        if abs(z) > 3:
            reasons.append(f"suma {s} (z={z:.2f}, esperado {expected_sum:.0f}±{std_sum:.0f})")
        
        # 3. Todos pares o todos impares (muy improbable si picks >= 6)
        pares = sum(1 for n in nums if n % 2 == 0)
        if pares == 0 or pares == len(nums):
            reasons.append(f"todos {'pares' if pares == len(nums) else 'impares'}")
        
        # 4. Todos en un mismo tercio
        low = sum(1 for n in nums if n <= lottery.main_pool_size / 3)
        mid = sum(1 for n in nums if lottery.main_pool_size / 3 < n <= 2 * lottery.main_pool_size / 3)
        high = sum(1 for n in nums if n > 2 * lottery.main_pool_size / 3)
        if low == len(nums) or mid == len(nums) or high == len(nums):
            reasons.append(f"todos en un mismo tercio (low={low}, mid={mid}, high={high})")
        
        # 5. Duplicados (datos mal cargados)
        if len(nums) < len(d.main_numbers):
            reasons.append(f"DÚPLICADO: {len(d.main_numbers) - len(nums)} números repetidos")
        
        if reasons:
            suspicious.append({
                'draw_number': d.draw_number,
                'date': d.date,
                'numbers': nums,
                'reasons': reasons,
            })
    
    return suspicious


def detect_repeated_combinations(lottery):
    """Detectar si la MISMA combinación salió más de una vez (casi imposible por azar)."""
    combos = Counter()
    for d in lottery.draws:
        combo = tuple(sorted(set(d.main_numbers)))
        combos[combo] += 1
    repeated = [(combo, count) for combo, count in combos.items() if count > 1]
    return repeated


def detect_extreme_hot_cold(lottery):
    """Detectar números con frecuencia fuera de 3 sigma."""
    pool_size = lottery.main_pool_size
    picks = lottery.main_picks
    total = lottery.total_draws()
    
    p = picks / pool_size  # probability per number per draw
    expected = p * total
    std_dev = math.sqrt(total * p * (1 - p))
    
    counter = Counter()
    for d in lottery.draws:
        for n in d.main_numbers:
            counter[n] += 1
    
    hot = []
    cold = []
    for n in range(1, pool_size + 1):
        freq = counter.get(n, 0)
        z = (freq - expected) / std_dev
        if z > 3:
            hot.append({'number': n, 'freq': freq, 'z_score': round(z, 2), 'expected': round(expected, 1)})
        elif z < -3:
            cold.append({'number': n, 'freq': freq, 'z_score': round(z, 2), 'expected': round(expected, 1)})
    
    return {'hot_extreme': hot, 'cold_extreme': cold, 'expected': expected, 'std_dev': std_dev}


def variance_between_periods(lottery, n_periods=4):
    """¿La frecuencia cambia significativamente entre períodos?"""
    total = lottery.total_draws()
    period_size = total // n_periods
    pool_size = lottery.main_pool_size
    
    period_freqs = []
    for p in range(n_periods):
        start = p * period_size
        end = (p + 1) * period_size if p < n_periods - 1 else total
        counter = Counter()
        for d in lottery.draws[start:end]:
            for n in d.main_numbers:
                counter[n] += 1
        period_freqs.append(counter)
    
    # Para cada número, ¿la frecuencia cambia entre períodos?
    suspicious_changes = []
    for n in range(1, pool_size + 1):
        freqs = [period_freqs[p].get(n, 0) for p in range(n_periods)]
        avg = mean(freqs)
        if avg > 0:
            std = stdev(freqs) if len(freqs) > 1 else 0
            cv = std / avg  # coefficient of variation
            if cv > 0.5:  # more than 50% variation
                suspicious_changes.append({
                    'number': n,
                    'frequencies': freqs,
                    'mean': round(avg, 1),
                    'std': round(std, 2),
                    'cv': round(cv, 3),
                })
    
    return {
        'n_periods': n_periods,
        'period_size': period_size,
        'numbers_with_high_variance': suspicious_changes,
    }


# Run all fraud detection tests on each lottery
fraud_results = {}
for lot_key in DATA_PATHS:
    print(f"\n🔍 {lot_key.upper()}")
    print("-"*60)
    
    lottery = get_lottery(lot_key)
    lottery.load_data(DATA_PATHS[lot_key])
    
    print(f"  Total sorteos: {lottery.total_draws()}")
    
    # 1. Chi-cuadrado
    chi = chi_squared_test(lottery)
    print(f"  Chi-cuadrado: {chi['chi_squared']} (crítico 5%: {chi['critical_5pct']}) → {'UNIFORME' if chi['is_uniform'] else 'NO UNIFORME ⚠️'}")
    print(f"    Desviación máxima: {chi['max_deviation']}%")
    
    # 2. Runs test (resumen)
    runs = runs_test_per_number(lottery)
    non_random_numbers = [n for n, r in runs.items() if not r['is_random']]
    print(f"  Runs test: {len(non_random_numbers)}/{lottery.main_pool_size} números NO aleatorios")
    if non_random_numbers:
        print(f"    Números sospechosos: {non_random_numbers}")
    
    # 3. Autocorrelación
    autocorr = autocorrelation_per_number(lottery, lag=1)
    high_autocorr = [(n, v) for n, v in autocorr.items() if abs(v) > 0.1]
    print(f"  Autocorrelación lag-1: {len(high_autocorr)} números con |ac| > 0.1")
    if high_autocorr:
        print(f"    Top: {sorted(high_autocorr, key=lambda x: -abs(x[1]))[:5]}")
    
    # 4. Sorteos sospechosos
    suspicious = detect_suspicious_draws(lottery)
    print(f"  Sorteos sospechosos: {len(suspicious)}")
    if suspicious:
        for s in suspicious[:3]:
            print(f"    Sorteo #{s['draw_number']} ({s['date']}): {s['numbers']} → {', '.join(s['reasons'])}")
    
    # 5. Combinaciones repetidas
    repeated = detect_repeated_combinations(lottery)
    print(f"  Combinaciones EXACTAS repetidas: {len(repeated)}")
    if repeated:
        for combo, count in repeated[:3]:
            print(f"    {combo}: {count} veces")
    
    # 6. Hot/cold extremo
    extreme = detect_extreme_hot_cold(lottery)
    print(f"  Hot extremo (>3σ): {len(extreme['hot_extreme'])} → {extreme['hot_extreme']}")
    print(f"  Cold extremo (<-3σ): {len(extreme['cold_extreme'])} → {extreme['cold_extreme']}")
    
    # 7. Varianza entre períodos
    variance = variance_between_periods(lottery)
    print(f"  Números con alta varianza entre {variance['n_periods']} períodos: {len(variance['numbers_with_high_variance'])}")
    
    fraud_results[lot_key] = {
        'lottery_name': lottery.name,
        'total_draws': lottery.total_draws(),
        'chi_squared': chi,
        'runs_test_non_random': non_random_numbers,
        'autocorrelation_high': high_autocorr,
        'suspicious_draws': suspicious,
        'repeated_combinations': repeated,
        'extreme_hot_cold': extreme,
        'variance_analysis': variance,
    }

# Save full results
output = {
    'regression_analysis': {
        'lottery': 'pozo_millonario',
        'engines_tested': test_engines,
        'sorteos_testeados': len(test_indices),
        'predictions_per_engine': dict(results_per_engine),
        'top_5_closest': [
            {
                'draw_number': p['draw_number'],
                'date': p['date'],
                'engine': p['engine'],
                'hits': p['hits'],
                'avg_distance': p['avg_distance'],
                'prediction': p['prediction'],
            } for p in all_predictions[:5]
        ],
    },
    'fraud_detection': fraud_results,
}

with open('/home/z/my-project/data/regression_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2, default=str)

print(f"\n\n✓ Resultados guardados en /home/z/my-project/data/regression_analysis.json")
print(f"  Tamaño: {len(json.dumps(output)):,} caracteres")

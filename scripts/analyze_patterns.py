"""
Deep pattern analysis on Pozo Millonario data.
Outputs: data/patterns.json with all findings.
"""
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from statistics import mean, median, stdev

with open('/home/z/my-project/data/pozo_data.json') as f:
    data = json.load(f)

# Normalize prize keys
for r in data:
    new_premios = {}
    for k, v in r['premios'].items():
        if isinstance(k, str) and k.isdigit():
            new_premios[int(k)] = v
        else:
            new_premios[k] = v
    r['premios'] = new_premios

# Sort by sorteo_num
data.sort(key=lambda x: x['sorteo_num'])

print(f"Analyzing {len(data)} sorteos...")

# ============================================================
# 1. PATTERN: Cuando se pagan MÁS premios (total pagado por sorteo)
# ============================================================
print("\n=== 1. ANÁLISIS DE PAGOS POR SORTEO ===")

# Compute total paid per draw (where data is available)
records_with_payment = []
for r in data:
    p = r['premios']
    total_paid = 0
    has_data = False
    for k, v in p.items():
        if isinstance(v, dict) and v.get('total') is not None:
            total_paid += v['total']
            has_data = True
    if has_data and total_paid > 0:
        records_with_payment.append({
            **r,
            'total_paid': total_paid
        })

print(f"Sorteos con datos de pago: {len(records_with_payment)}")

# Sort by total_paid descending
top_paid = sorted(records_with_payment, key=lambda x: -x['total_paid'])
print(f"\nTop 15 sorteos con MAYOR pago total:")
print(f"{'Sorteo':>6} {'Fecha':>12} {'Día':>8} {'Total Pagado':>15} {'Gan11':>6} {'Gan10':>6} {'Mascota':>10}")
for r in top_paid[:15]:
    p = r['premios']
    g11 = p.get(11, {}).get('ganadores', '-')
    g10 = p.get(10, {}).get('ganadores', '-')
    print(f"{r['sorteo_num']:>6} {r['fecha']:>12} {r.get('dia_semana',''):>8} ${r['total_paid']:>13,.2f} {str(g11):>6} {str(g10):>6} {r.get('mascota',''):>10}")

# ============================================================
# 2. PATTERN: Pagos por día de la semana
# ============================================================
print("\n=== 2. PAGOS POR DÍA DE LA SEMANA ===")
day_stats = defaultdict(lambda: {'count': 0, 'total_paid': 0, 'sorteos': [], 'avg_paid': 0, 'max_paid': 0})
for r in records_with_payment:
    dia = (r.get('dia_semana') or '').lower().strip()
    if dia:
        day_stats[dia]['count'] += 1
        day_stats[dia]['total_paid'] += r['total_paid']
        day_stats[dia]['sorteos'].append(r['total_paid'])
        day_stats[dia]['max_paid'] = max(day_stats[dia]['max_paid'], r['total_paid'])

print(f"{'Día':<12} {'Sorteos':>8} {'Total Pagado':>15} {'Promedio':>15} {'Máximo':>15}")
for dia in ['lunes', 'martes', 'miércoles', 'miercoles', 'jueves', 'viernes', 'sábado', 'sabado', 'domingo']:
    if dia in day_stats:
        s = day_stats[dia]
        if s['count'] > 0:
            avg = s['total_paid'] / s['count']
            print(f"{dia:<12} {s['count']:>8} ${s['total_paid']:>13,.2f} ${avg:>13,.2f} ${s['max_paid']:>13,.2f}")

# ============================================================
# 3. PATTERN: Pagos por mes del año
# ============================================================
print("\n=== 3. PAGOS POR MES DEL AÑO ===")
month_stats = defaultdict(lambda: {'count': 0, 'total_paid': 0, 'sorteos': []})
for r in records_with_payment:
    if r['fecha']:
        try:
            dt = datetime.strptime(r['fecha'], '%Y-%m-%d')
            month_stats[dt.month]['count'] += 1
            month_stats[dt.month]['total_paid'] += r['total_paid']
            month_stats[dt.month]['sorteos'].append(r['total_paid'])
        except:
            pass

MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
print(f"{'Mes':<5} {'Sorteos':>8} {'Total Pagado':>15} {'Promedio':>15} {'Mediana':>15}")
for m in range(1, 13):
    if m in month_stats:
        s = month_stats[m]
        if s['count'] > 0:
            avg = s['total_paid'] / s['count']
            med = median(s['sorteos'])
            print(f"{MONTHS[m-1]:<5} {s['count']:>8} ${s['total_paid']:>13,.2f} ${avg:>13,.2f} ${med:>13,.2f}")

# ============================================================
# 4. PATTERN: Pagos por trimestre / estación
# ============================================================
print("\n=== 4. PAGOS POR TRIMESTRE ===")
quarter_stats = defaultdict(lambda: {'count': 0, 'total_paid': 0, 'sorteos': []})
for r in records_with_payment:
    if r['fecha']:
        try:
            dt = datetime.strptime(r['fecha'], '%Y-%m-%d')
            q = (dt.month - 1) // 3 + 1
            quarter_stats[q]['count'] += 1
            quarter_stats[q]['total_paid'] += r['total_paid']
            quarter_stats[q]['sorteos'].append(r['total_paid'])
        except:
            pass

for q in range(1, 5):
    if q in quarter_stats:
        s = quarter_stats[q]
        if s['count'] > 0:
            avg = s['total_paid'] / s['count']
            med = median(s['sorteos'])
            print(f"Q{q}: {s['count']} sorteos, total ${s['total_paid']:,.2f}, promedio ${avg:,.2f}, mediana ${med:,.2f}")

# ============================================================
# 5. PATTERN: Pagos por semana del mes (1ra, 2da, 3ra, 4ta)
# ============================================================
print("\n=== 5. PAGOS POR SEMANA DEL MES ===")
week_of_month_stats = defaultdict(lambda: {'count': 0, 'total_paid': 0, 'sorteos': []})
for r in records_with_payment:
    if r['fecha']:
        try:
            dt = datetime.strptime(r['fecha'], '%Y-%m-%d')
            # Week of month: 1-5
            wom = (dt.day - 1) // 7 + 1
            week_of_month_stats[wom]['count'] += 1
            week_of_month_stats[wom]['total_paid'] += r['total_paid']
            week_of_month_stats[wom]['sorteos'].append(r['total_paid'])
        except:
            pass

for w in sorted(week_of_month_stats.keys()):
    s = week_of_month_stats[w]
    if s['count'] > 0:
        avg = s['total_paid'] / s['count']
        print(f"Semana {w}: {s['count']} sorteos, total ${s['total_paid']:,.2f}, promedio ${avg:,.2f}")

# ============================================================
# 6. SUMATORIA DE NÚMEROS - Análisis estadístico
# ============================================================
print("\n=== 6. SUMATORIA DE NÚMEROS POR SORTEO ===")
sums = []
for r in data:
    if r['numeros']:
        # Use unique numbers (some sources have duplicates)
        unique_nums = list(dict.fromkeys(r['numeros']))
        s = sum(unique_nums)
        sums.append({
            'sorteo': r['sorteo_num'],
            'fecha': r['fecha'],
            'dia': r.get('dia_semana', ''),
            'sum': s,
            'pares': sum(1 for n in unique_nums if n % 2 == 0),
            'impares': sum(1 for n in unique_nums if n % 2 != 0),
            'bajos': sum(1 for n in unique_nums if n <= 8),  # 1-8
            'medios': sum(1 for n in unique_nums if 9 <= n <= 17),  # 9-17
            'altos': sum(1 for n in unique_nums if n >= 18),  # 18-25
            'numeros': unique_nums,
        })

print(f"Total sorteos con números: {len(sums)}")
sum_values = [s['sum'] for s in sums]
print(f"Suma mínima: {min(sum_values)} (sorteo {sums[sum_values.index(min(sum_values))]['sorteo']})")
print(f"Suma máxima: {max(sum_values)} (sorteo {sums[sum_values.index(max(sum_values))]['sorteo']})")
print(f"Suma promedio: {mean(sum_values):.2f}")
print(f"Suma mediana: {median(sum_values):.2f}")
print(f"Desviación estándar: {stdev(sum_values):.2f}")

# Distribución por rangos
print("\nDistribución por rangos de suma:")
ranges = [(0, 100), (100, 120), (120, 140), (140, 160), (160, 180), (180, 200), (200, 220), (220, 300)]
for lo, hi in ranges:
    count = sum(1 for s in sum_values if lo <= s < hi)
    pct = count / len(sum_values) * 100
    print(f"  {lo}-{hi}: {count} sorteos ({pct:.1f}%)")

# ============================================================
# 7. PATTERN: Días con sorteos consecutivos y racha de acumulación
# ============================================================
print("\n=== 7. RACHAS DE ACUMULACIÓN (pozo no ganado) ===")
streaks = []
current_streak = []
prev_sorteo = None
for r in data:
    p = r['premios']
    p11 = p.get(11, {})
    g11 = p11.get('ganadores')
    p11_ind = p11.get('premio_indiv')
    
    # Was the pozo accumulated (no winner)?
    acumulado = False
    monto = None
    if g11 == 0 and p11_ind is not None and p11_ind > 500:
        acumulado = True
        monto = p11_ind
    
    if acumulado:
        current_streak.append({**r, 'monto_acum': monto})
    else:
        if current_streak:
            streaks.append(current_streak)
            current_streak = []
        # Reset on winner (g11 > 0) or unknown

if current_streak:
    streaks.append(current_streak)

print(f"Total rachas de acumulación detectadas: {len(streaks)}")
print(f"\nRachas más largas:")
sorted_streaks = sorted(streaks, key=lambda x: -len(x))
for i, streak in enumerate(sorted_streaks[:5]):
    if not streak:
        continue
    start = streak[0]
    end = streak[-1]
    max_monto = max((s.get('monto_acum') or 0) for s in streak)
    print(f"  Racha {i+1}: {len(streak)} sorteos (#{start['sorteo_num']} a #{end['sorteo_num']})")
    print(f"    Inicio: {start['fecha']} - Fin: {end['fecha']}")
    print(f"    Monto máximo acumulado: ${max_monto:,.2f}")

# ============================================================
# 8. PATTERN: Combinaciones de números repetidas (coincidencias)
# ============================================================
print("\n=== 8. COMBINACIONES REPETIDAS ===")
# Build normalized combination string for each draw
combos = []
for r in data:
    if r['numeros']:
        unique_nums = sorted(set(r['numeros']))
        if len(unique_nums) >= 10:  # use first 10 if there are duplicates
            combo_str = ','.join(f'{n:02d}' for n in unique_nums[:11])
            combos.append((combo_str, r))

combo_counter = Counter(c[0] for c in combos)
print(f"Total combinaciones únicas: {len(combo_counter)}")
print(f"Combinaciones repetidas:")
repeated = [(c, count) for c, count in combo_counter.most_common() if count > 1]
for combo, count in repeated[:10]:
    print(f"  {combo}: {count} veces")
    # Find the sorteos where this combo appeared
    sorteos = [r['sorteo_num'] for c, r in combos if c == combo]
    print(f"    Sorteos: {sorteos}")

# ============================================================
# 9. PATTERN: Pares de números que salen juntos (co-ocurrencia)
# ============================================================
print("\n=== 9. PARES DE NÚMEROS MÁS CO-OCURRENTES ===")
pair_counter = Counter()
for r in data:
    if r['numeros']:
        unique_nums = sorted(set(r['numeros']))
        for i in range(len(unique_nums)):
            for j in range(i+1, len(unique_nums)):
                pair_counter[(unique_nums[i], unique_nums[j])] += 1

print("Top 15 pares que más salen juntos:")
for (a, b), count in pair_counter.most_common(15):
    pct = count / len(data) * 100
    print(f"  ({a:02d}, {b:02d}): {count} veces ({pct:.1f}%)")

# Expected frequency if independent: each pair should appear
# P(two specific numbers) = C(23,9)/C(25,11) ≈ 0.1833 per draw
expected_pair_freq = len(data) * 0.1833
print(f"\nFrecuencia esperada (si independiente): {expected_pair_freq:.1f}")
print(f"Frecuencia observada promedio: {mean(pair_counter.values()):.2f}")

# ============================================================
# 10. PATTERN: Suma de números vs día de la semana
# ============================================================
print("\n=== 10. SUMA DE NÚMEROS POR DÍA DE LA SEMANA ===")
sum_by_day = defaultdict(list)
for s in sums:
    dia = (s['dia'] or '').lower().strip()
    if dia:
        sum_by_day[dia].append(s['sum'])

for dia in ['lunes', 'martes', 'miércoles', 'miercoles', 'jueves', 'viernes', 'sábado', 'sabado']:
    if dia in sum_by_day and sum_by_day[dia]:
        vals = sum_by_day[dia]
        print(f"{dia:<12}: n={len(vals)}, promedio={mean(vals):.1f}, mediana={median(vals):.1f}, min={min(vals)}, max={max(vals)}")

# ============================================================
# 11. PATTERN: Distribución par/impar
# ============================================================
print("\n=== 11. DISTRIBUCIÓN PAR/IMPAR ===")
par_dist = Counter()
for s in sums:
    par_dist[(s['pares'], s['impares'])] += 1

print("Distribución pares/impares (top 10):")
for (pares, impares), count in par_dist.most_common(10):
    pct = count / len(sums) * 100
    print(f"  {pares} par / {impares} impar: {count} sorteos ({pct:.1f}%)")

# ============================================================
# 12. PATTERN: Distribución por rangos (bajos/medios/altos)
# ============================================================
print("\n=== 12. DISTRIBUCIÓN POR RANGOS (1-8 / 9-17 / 18-25) ===")
range_dist = Counter()
for s in sums:
    range_dist[(s['bajos'], s['medios'], s['altos'])] += 1

print("Distribución por rangos (top 10):")
for (b, m, a), count in range_dist.most_common(10):
    pct = count / len(sums) * 100
    print(f"  {b} bajos / {m} medios / {a} altos: {count} sorteos ({pct:.1f}%)")

# ============================================================
# 13. PATTERN: Meses con más ganadores 11 / pagos grandes
# ============================================================
print("\n=== 13. MESES CON PAGOS MÁS ALTOS ===")
month_payment_avg = []
for m in range(1, 13):
    if m in month_stats:
        s = month_stats[m]
        if s['count'] > 0:
            avg = s['total_paid'] / s['count']
            month_payment_avg.append((m, avg, s['count'], s['total_paid']))

month_payment_avg.sort(key=lambda x: -x[1])
print(f"{'Mes':<5} {'Promedio pago':>15} {'Sorteos':>8} {'Total':>15}")
for m, avg, cnt, total in month_payment_avg:
    print(f"{MONTHS[m-1]:<5} ${avg:>13,.2f} {cnt:>8} ${total:>13,.2f}")

# ============================================================
# 14. PATTERN: Números que salen después de otros (transiciones)
# ============================================================
print("\n=== 14. NÚMEROS QUE SALEN JUNTOS CON FRECUENCIA (top 25) ===")
single_with_other = defaultdict(Counter)
for r in data:
    if r['numeros']:
        unique_nums = sorted(set(r['numeros']))
        for n in unique_nums:
            others = [x for x in unique_nums if x != n]
            for o in others:
                single_with_other[n][o] += 1

# For each top frequent number, show which numbers most often accompany it
top_5_numbers = [6, 2, 5, 15, 17]  # based on previous analysis
print("Top 5 números más frecuentes y sus 'acompañantes':")
for n in top_5_numbers:
    top_companions = single_with_other[n].most_common(5)
    print(f"  Número {n:02d}:")
    for comp, count in top_companions:
        print(f"    → {comp:02d}: {count} veces")

# ============================================================
# 15. SAVE FULL ANALYSIS
# ============================================================
analysis = {
    'total_sorteos': len(data),
    'total_con_pagos': len(records_with_payment),
    'top_15_mayor_pago': [
        {
            'sorteo': r['sorteo_num'],
            'fecha': r['fecha'],
            'dia': r.get('dia_semana', ''),
            'total_pagado': r['total_paid'],
            'g11': r['premios'].get(11, {}).get('ganadores'),
            'g10': r['premios'].get(10, {}).get('ganadores'),
            'mascota': r.get('mascota', ''),
            'numeros': r['numeros'],
        } for r in top_paid[:15]
    ],
    'pagos_por_dia': {
        dia: {
            'count': s['count'],
            'total': s['total_paid'],
            'promedio': s['total_paid'] / s['count'] if s['count'] > 0 else 0,
            'max': s['max_paid'],
        } for dia, s in day_stats.items()
    },
    'pagos_por_mes': {
        m: {
            'count': s['count'],
            'total': s['total_paid'],
            'promedio': s['total_paid'] / s['count'] if s['count'] > 0 else 0,
            'mediana': median(s['sorteos']) if s['sorteos'] else 0,
        } for m, s in month_stats.items()
    },
    'pagos_por_trimestre': {
        q: {
            'count': s['count'],
            'total': s['total_paid'],
            'promedio': s['total_paid'] / s['count'] if s['count'] > 0 else 0,
        } for q, s in quarter_stats.items()
    },
    'pagos_por_semana_mes': {
        w: {
            'count': s['count'],
            'total': s['total_paid'],
            'promedio': s['total_paid'] / s['count'] if s['count'] > 0 else 0,
        } for w, s in week_of_month_stats.items()
    },
    'sumatoria_numeros': {
        'min': min(sum_values),
        'max': max(sum_values),
        'promedio': mean(sum_values),
        'mediana': median(sum_values),
        'stdev': stdev(sum_values),
        'sorteos': [
            {
                'sorteo': s['sorteo'],
                'fecha': s['fecha'],
                'dia': s['dia'],
                'suma': s['sum'],
                'pares': s['pares'],
                'impares': s['impares'],
                'bajos': s['bajos'],
                'medios': s['medios'],
                'altos': s['altos'],
                'numeros': s['numeros'],
            } for s in sums
        ],
    },
    'rachas_acumulacion': [
        {
            'longitud': len(streak),
            'sorteo_inicio': streak[0]['sorteo_num'],
            'sorteo_fin': streak[-1]['sorteo_num'],
            'fecha_inicio': streak[0]['fecha'],
            'fecha_fin': streak[-1]['fecha'],
            'monto_max': max((s.get('monto_acum') or 0) for s in streak),
            'sorteos': [s['sorteo_num'] for s in streak],
        } for streak in sorted_streaks if streak
    ],
    'pares_coocurrentes_top15': [
        {'par': [a, b], 'frecuencia': count, 'pct': count/len(data)*100}
        for (a, b), count in pair_counter.most_common(15)
    ],
    'distribucion_par_impar': [
        {'pares': p, 'impares': i, 'count': c, 'pct': c/len(sums)*100}
        for (p, i), c in par_dist.most_common(10)
    ],
    'distribucion_rangos': [
        {'bajos': b, 'medios': m, 'altos': a, 'count': c, 'pct': c/len(sums)*100}
        for (b, m, a), c in range_dist.most_common(10)
    ],
}

with open('/home/z/my-project/data/patterns.json', 'w', encoding='utf-8') as f:
    json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)

print(f"\n✓ Análisis guardado en /home/z/my-project/data/patterns.json")
print(f"  Tamaño: {len(json.dumps(analysis)):,} caracteres")

"""
Build a comprehensive Excel report with:
- Backtest results
- Engine comparison
- Predictions from all engines
- Per-engine analysis details
"""
import sys, os, json
sys.path.insert(0, '/home/z/my-project/scripts/lottery_predictor')
sys.path.insert(0, '/home/z/my-project/skills/xlsx/templates')
sys.path.insert(0, '/home/z/my-project/skills/xlsx')

from base import *
use_palette_explicit("bottega")  # Dark green - financial luxury

from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Border, Side, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import DataBarRule, ColorScaleRule, CellIsRule
from openpyxl.chart import BarChart, Reference

from lotteries import get_lottery
from engines import ENGINE_REGISTRY
from engines.ensemble import predict_with_explanation

# Load lottery
lottery = get_lottery('pozo_millonario')
lottery.load_data('/home/z/my-project/data/pozo_data.json')

# Load backtest results
with open('/home/z/my-project/data/backtest_pozo_millonario.json') as f:
    backtest = json.load(f)

print(f"Loaded {lottery.total_draws()} draws for {lottery.name}")

# Create workbook
wb = Workbook()
wb.remove(wb.active)

# ============================================================
# SHEET 1: Resumen del Predictor
# ============================================================
ws = wb.create_sheet("Resumen del Predictor")
setup_sheet(ws, title="LotteryPredictor v1.0 — Sistema Multi-Lotería de Predicción", last_col=5)

row = 4
sections = [
    ("ARQUITECTURA", [
        ("Sistema modular", "9 motores de análisis independientes + ensemble combinado"),
        ("Multi-lotería", "5 loterías globales configurables (Pozo Millonario, La Primitiva, EuroMillions, EuroJackpot, El Gordo)"),
        ("Sin dependencias ML pesadas", "Python 3.8+ stdlib únicamente. Opcional: TensorFlow para LSTM."),
        ("Backtesting incluido", "Validación histórica de cada motor contra datos reales"),
    ]),
    ("MOTORES IMPLEMENTADOS (lo mejor de 3 repos GitHub)", [
        ("1. Frequency Analysis", "Frecuencia simple con Z-scores y test chi-cuadrado (de lotto-max-ml-predictor)"),
        ("2. Hot/Cold Tracker", "Temperatura con mean reversion probability (de lotto-max-ml-predictor)"),
        ("3. Gap Analysis", "Detección de números overdue (de lotto-max-ml-predictor)"),
        ("4. Markov Chain", "Transiciones 1° y 2° orden (de powerpredict)"),
        ("5. Bayesian Inference", "Beta prior/posterior con credible intervals (de lotto-max-ml-predictor)"),
        ("6. Pattern Detection", "Pares consecutivos, sumas, par/impar, runs test (combinado)"),
        ("7. Entropy Scoring", "Shannon + autocorrelación + randomness score (de lotto-max-ml-predictor)"),
        ("8. Monte Carlo", "10K simulaciones con PRNG mulberry32 + percentiles P10/P50/P90 (adaptado de open-gravity-ui)"),
        ("9. Ensemble", "Combina los 8 anteriores con pesos ponderados (de powerpredict)"),
    ]),
    ("BACKTESTING REALIZADO", [
        ("Lotería probada", "Pozo Millonario (308 sorteos disponibles)"),
        ("Sorteos backtesteados", "100 (de los últimos 158 con datos completos)"),
        ("Mínimo histórico requerido", "50 sorteos antes de predecir"),
        ("Baseline aleatorio", f"{backtest['random_baseline']['avg_hits']:.3f} aciertos promedio"),
        ("Mejor motor", f"{backtest['comparison'][0]['engine']} ({backtest['comparison'][0]['avg_hits']:.3f} aciertos)"),
        ("Mejora vs azar", f"+{(backtest['comparison'][0]['avg_hits'] - backtest['random_baseline']['avg_hits']):.3f} aciertos ({(backtest['comparison'][0]['avg_hits'] - backtest['random_baseline']['avg_hits'])/backtest['random_baseline']['avg_hits']*100:.1f}%)"),
    ]),
    ("CONCLUSIÓN ESTADÍSTICA", [
        ("⚠️ Realidad", "Ningún motor supera significativamente al azar. La lotería es esencialmente aleatoria."),
        ("Mejora marginal", "Los mejores motores ganan ~0.2 aciertos extra de 11 (4% mejora sobre baseline)"),
        ("Recomendación", "Usar el ensemble (combina todos) por robustez. No esperar milagros."),
        ("Honestidad", "Esta es la verdad estadística. Cualquier sistema que prometa >10% mejora es fraude."),
    ]),
]

for section_title, items in sections:
    ws.cell(row=row, column=2, value=section_title).font = font_subheader()
    ws.cell(row=row, column=2).alignment = align_text()
    ws.row_dimensions[row].height = 26
    row += 1
    for label, value in items:
        ws.cell(row=row, column=2, value=label).font = Font(name=FONT_NAME, size=11, bold=True, color=PRIMARY)
        ws.cell(row=row, column=2).alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        ws.cell(row=row, column=3, value=value).font = font_body()
        ws.cell(row=row, column=3).alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=5)
        ws.row_dimensions[row].height = 32
        row += 1
    row += 1

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 32
ws.column_dimensions['C'].width = 50
ws.column_dimensions['D'].width = 25
ws.column_dimensions['E'].width = 25

print("Sheet 1 done")

# ============================================================
# SHEET 2: Comparación de Motores (Backtest)
# ============================================================
ws = wb.create_sheet("Backtest Comparativo")

setup_sheet(ws, title="Backtesting — Comparación de los 9 Motores vs Azar", last_col=7)

row = 4
ws.cell(row=row, column=2, value="Metodología: para cada uno de los últimos 100 sorteos, predecir usando datos históricos previos y comparar con el sorteo real.").font = font_caption()
ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
ws.row_dimensions[row].height = 22
row += 1

headers = ["#", "Motor", "Aciertos Promedio", "Aciertos Máx", "Tiempo/draw (ms)", "Sorteos Testeados", "vs Azar"]
for i, h in enumerate(headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=8)
header_row = row
row += 1

# Add baseline first
baseline_avg = backtest['random_baseline']['avg_hits']
ws.cell(row=row, column=2, value="-")
ws.cell(row=row, column=3, value="🎲 Azar (baseline)")
ws.cell(row=row, column=4, value=baseline_avg)
ws.cell(row=row, column=5, value=backtest['random_baseline']['max_hits'])
ws.cell(row=row, column=6, value="N/A")
ws.cell(row=row, column=7, value=backtest['random_baseline']['total_tested'])
ws.cell(row=row, column=8, value="—")
style_data_row(ws, row_num=row, col_start=2, col_end=8, row_index=0)
for c in range(2, 9):
    ws.cell(row=row, column=c).font = Font(name=FONT_NAME, size=11, italic=True, color=NEUTRAL_600)
row += 1

# Add each engine
for i, eng in enumerate(backtest['comparison'], 1):
    diff = eng['avg_hits'] - baseline_avg
    diff_str = f"+{diff:.3f} ✅" if diff > 0 else f"{diff:.3f} ❌"
    ws.cell(row=row, column=2, value=i)
    ws.cell(row=row, column=3, value=eng['engine'])
    ws.cell(row=row, column=4, value=eng['avg_hits'])
    ws.cell(row=row, column=5, value=eng['max_hits'])
    ws.cell(row=row, column=6, value=eng['avg_time_ms'])
    ws.cell(row=row, column=7, value=eng['tested'])
    ws.cell(row=row, column=8, value=diff_str)
    style_data_row(ws, row_num=row, col_start=2, col_end=8, row_index=i)
    ws.cell(row=row, column=3).alignment = align_text()
    for c in [4, 5, 6, 7]:
        ws.cell(row=row, column=c).alignment = align_number()
    ws.cell(row=row, column=8).alignment = align_number()
    row += 1

# Conditional formatting on avg hits
ws.conditional_formatting.add(f'D{header_row+1}:D{row-1}',
    DataBarRule(start_type='min', end_type='max', color=ACCENT_POSITIVE, showValue=True))

# Highlight diff vs random
ws.conditional_formatting.add(f'H{header_row+1}:H{row-1}',
    CellIsRule(operator='greaterThan', formula=['0'],
               fill=PatternFill('solid', fgColor='E8F5E9'),
               font=Font(name=FONT_NAME, color=ACCENT_POSITIVE, bold=True)))

row += 2

# Insights
ws.cell(row=row, column=2, value="📊 INSIGHTS DEL BACKTEST").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 26
row += 1

insights = [
    f"• El mejor motor ({backtest['comparison'][0]['engine']}) supera al azar por +{backtest['comparison'][0]['avg_hits'] - baseline_avg:.3f} aciertos en promedio.",
    f"• La mejora porcentual es solo {(backtest['comparison'][0]['avg_hits'] - baseline_avg)/baseline_avg*100:.1f}% — estadísticamente marginal.",
    f"• El motor ensemble (que combina todos) quedó en posición {next(i for i, e in enumerate(backtest['comparison'], 1) if e['engine']=='ensemble')} — robusto pero no el mejor individualmente.",
    f"• El motor gap_analysis fue el ÚNICO peor que el azar (-{baseline_avg - backtest['comparison'][-1]['avg_hits']:.3f}). Esto sugiere que los números 'overdue' NO tienen mayor probabilidad real.",
    f"• El motor más rápido (frequency) tarda 0.2ms por predicción. El ensemble tarda 771ms pero usa los 8 motores.",
    f"• NINGÚN motor logró más de 8 aciertos de 11 en los 100 sorteos testeados. Para ganar el pozo mayor necesitas 11.",
    f"• Conclusión: la lotería es estadísticamente aleatoria. Cualquier sistema que prometa >10% mejora sobre el azar es estadísticamente sospechoso.",
]
for insight in insights:
    ws.cell(row=row, column=2, value=insight).font = font_body()
    ws.cell(row=row, column=2).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=8)
    ws.row_dimensions[row].height = 22
    row += 1

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 5
ws.column_dimensions['C'].width = 24
ws.column_dimensions['D'].width = 18
ws.column_dimensions['E'].width = 14
ws.column_dimensions['F'].width = 18
ws.column_dimensions['G'].width = 18
ws.column_dimensions['H'].width = 14

print("Sheet 2 done")

# ============================================================
# SHEET 3: Predicción Final (Ensemble)
# ============================================================
ws = wb.create_sheet("Predicción Final")

setup_sheet(ws, title=f"Predicción para próximo sorteo — {lottery.name}", last_col=5)

row = 4
result = predict_with_explanation(lottery)
pred = result['prediction']

ws.cell(row=row, column=2, value="🎯 NÚMEROS RECOMENDADOS (Ensemble de 9 motores)").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 26
row += 1

# Big display of numbers
nums_str = '  '.join(f'{n:02d}' for n in pred)
ws.cell(row=row, column=2, value=nums_str).font = Font(name=FONT_NAME, size=24, bold=True, color=ACCENT_POSITIVE)
ws.cell(row=row, column=2).alignment = Alignment(horizontal='center', vertical='center')
ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=5)
ws.row_dimensions[row].height = 50
row += 2

# Last draw info
last_draw = lottery.get_last_draw()
ws.cell(row=row, column=2, value="Sorteo más reciente:").font = font_caption()
ws.cell(row=row, column=3, value=f"#{last_draw.draw_number} ({last_draw.date})").font = font_body()
ws.cell(row=row, column=3).alignment = align_text()
ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=5)
row += 1
last_nums = '  '.join(f'{n:02d}' for n in last_draw.main_numbers)
ws.cell(row=row, column=2, value="Números ganadores:").font = font_caption()
ws.cell(row=row, column=3, value=last_nums).font = Font(name=FONT_NAME, size=14, bold=True, color=PRIMARY)
ws.cell(row=row, column=3).alignment = Alignment(horizontal='left', vertical='center')
ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=5)
ws.row_dimensions[row].height = 24
row += 2

# Explanation table
ws.cell(row=row, column=2, value="📋 JUSTIFICACIÓN POR NÚMERO").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 26
row += 1

headers = ["Rank", "Número", "Score Combinado", "Motores que lo eligieron (top 3)"]
for i, h in enumerate(headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=5)
row += 1

for i, exp in enumerate(result['explanations']):
    ws.cell(row=row, column=2, value=exp['rank'])
    ws.cell(row=row, column=3, value=exp['number']).number_format = '00'
    ws.cell(row=row, column=4, value=exp['combined_score'])
    reasons_str = '\n'.join(f"  • {r}" for r in exp['top_reasons'])
    ws.cell(row=row, column=5, value=reasons_str)
    ws.cell(row=row, column=5).alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
    style_data_row(ws, row_num=row, col_start=2, col_end=5, row_index=i)
    ws.cell(row=row, column=2).alignment = align_number()
    ws.cell(row=row, column=3).alignment = align_date()
    ws.cell(row=row, column=4).alignment = align_number()
    ws.cell(row=row, column=5).alignment = align_text()
    ws.row_dimensions[row].height = 48
    row += 1

row += 1

# Other engines predictions
ws.cell(row=row, column=2, value="🔧 COMPARACIÓN: PREDICCIÓN POR CADA MOTOR").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 26
row += 1

headers = ["Motor", "Predicción", "Score Promedio en Backtest"]
for i, h in enumerate(headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=4)
row += 1

# Get each engine's prediction
eng_predictions = {}
for eng_name in ENGINE_REGISTRY.keys():
    if eng_name == 'ensemble':
        eng_predictions[eng_name] = pred
    else:
        try:
            eng_predictions[eng_name] = ENGINE_REGISTRY[eng_name].predict(lottery)
        except:
            eng_predictions[eng_name] = []

# Get avg hits from backtest
avg_hits_map = {c['engine']: c['avg_hits'] for c in backtest['comparison']}
avg_hits_map['random_baseline'] = baseline_avg

for eng_name, eng_pred in eng_predictions.items():
    pred_str = '  '.join(f'{n:02d}' for n in eng_pred) if eng_pred else 'ERROR'
    avg_h = avg_hits_map.get(eng_name, 'N/A')
    ws.cell(row=row, column=2, value=eng_name)
    ws.cell(row=row, column=3, value=pred_str).font = Font(name=FONT_NAME, size=12, bold=True, color=PRIMARY)
    ws.cell(row=row, column=4, value=avg_h if isinstance(avg_h, str) else avg_h)
    if isinstance(avg_h, float):
        ws.cell(row=row, column=4).number_format = '0.000'
    style_data_row(ws, row_num=row, col_start=2, col_end=4, row_index=row)
    ws.cell(row=row, column=2).alignment = align_text()
    ws.cell(row=row, column=3).alignment = align_text()
    ws.cell(row=row, column=4).alignment = align_number()
    row += 1

row += 2

# Disclaimer
ws.cell(row=row, column=2, value="⚠️ AVISO IMPORTANTE").font = Font(name=FONT_NAME, size=12, bold=True, color=ACCENT_NEGATIVE)
ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=5)
row += 1
disclaimer = ("Esta predicción se basa en análisis estadístico de 308 sorteos históricos. "
              "La probabilidad de acertar 11 números es de 1 en 4,457,400. "
              "El backtesting muestra que NINGÚN motor supera significativamente al azar. "
              "Juega con responsabilidad. No es inversión, es entretenimiento.")
ws.cell(row=row, column=2, value=disclaimer).font = font_body()
ws.cell(row=row, column=2).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=5)
ws.row_dimensions[row].height = 60

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 14
ws.column_dimensions['C'].width = 36
ws.column_dimensions['D'].width = 22
ws.column_dimensions['E'].width = 60

print("Sheet 3 done")

# ============================================================
# SHEET 4: Distribución Detallada del Backtest
# ============================================================
ws = wb.create_sheet("Distribución Backtest")

setup_sheet(ws, title="Distribución de Aciertos por Motor (100 sorteos testeados)", last_col=10)

row = 4

# Build a matrix: engines × hit counts
ws.cell(row=row, column=2, value="Motor")
for h in range(0, 12):
    ws.cell(row=row, column=3+h, value=f"{h} aciertos")
ws.cell(row=row, column=15, value="Total")
style_header_row(ws, row_num=row, col_start=2, col_end=15)
row += 1

# Add baseline
ws.cell(row=row, column=2, value="🎲 Azar")
dist = backtest['random_baseline']['hits_distribution']
total = sum(dist.values())
for h in range(0, 12):
    ws.cell(row=row, column=3+h, value=dist.get(str(h) if isinstance(list(dist.keys())[0], str) else h, 0))
ws.cell(row=row, column=15, value=total)
style_data_row(ws, row_num=row, col_start=2, col_end=15, row_index=0)
row += 1

# Add each engine
for i, eng_name in enumerate(ENGINE_REGISTRY.keys(), 1):
    if eng_name in backtest and 'hits_distribution' in backtest[eng_name]:
        dist = backtest[eng_name]['hits_distribution']
        ws.cell(row=row, column=2, value=eng_name)
        for h in range(0, 12):
            key = str(h) if isinstance(list(dist.keys())[0], str) else h
            ws.cell(row=row, column=3+h, value=dist.get(key, 0))
        ws.cell(row=row, column=15, value=backtest[eng_name]['total_tested'])
        style_data_row(ws, row_num=row, col_start=2, col_end=15, row_index=i)
        row += 1

# Heat map
ws.conditional_formatting.add(f'C5:N{row-1}',
    ColorScaleRule(start_type='min', start_color='F7F7F5',
                   mid_type='percentile', mid_value=50, mid_color='D6E4F0',
                   end_type='max', end_color=PRIMARY))

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 22
for c in range(3, 15):
    ws.column_dimensions[get_column_letter(c)].width = 11
ws.column_dimensions[get_column_letter(15)].width = 10

print("Sheet 4 done")

# Save
wb.properties.creator = "Z.ai"
wb.properties.title = "LotteryPredictor v1.0 - Análisis y Predicción"

output_path = '/home/z/my-project/download/LotteryPredictor_Analisis.xlsx'
wb.save(output_path)

print(f"\n✓ Excel saved: {output_path}")
print(f"  Size: {os.path.getsize(output_path):,} bytes")

"""
Build the Excel file with detailed pattern analysis.
Multiple sheets covering all the patterns found.
"""
import sys
import os
import json
from collections import Counter, defaultdict
from datetime import datetime
from statistics import mean, median, stdev

# Add xlsx skill templates to path
sys.path.insert(0, '/home/z/my-project/skills/xlsx/templates')
sys.path.insert(0, '/home/z/my-project/skills/xlsx')

from base import (
    use_palette_explicit, setup_sheet, style_header_row, style_data_row,
    style_total_row, font_title, font_header, font_subheader, font_body,
    font_caption, font_kpi, font_kpi_label, fill_header, fill_total,
    fill_data_row, border_header, border_total, align_title, align_header,
    align_number, align_text, align_date,
    PRIMARY, PRIMARY_LIGHT, SECONDARY, ACCENT_POSITIVE, ACCENT_NEGATIVE,
    ACCENT_WARNING, NEUTRAL_900, NEUTRAL_600, NEUTRAL_200, NEUTRAL_100,
    NEUTRAL_50, NEUTRAL_0, HEADER_TEXT, CHART_COLORS, FONT_NAME, HEADER_BOLD,
    FORMATS, ROW_HEIGHTS, COLUMN_WIDTHS, create_bar_chart, create_line_chart,
    setup_chart_titles, apply_chart_colors,
)
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Border, Side, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, LineChart, PieChart, ScatterChart, Series, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule, CellIsRule

use_palette_explicit("professional")

# Load data
with open('/home/z/my-project/data/pozo_data.json') as f:
    DATA = json.load(f)

# Normalize keys
for r in DATA:
    new_premios = {}
    for k, v in r['premios'].items():
        if isinstance(k, str) and k.isdigit():
            new_premios[int(k)] = v
        else:
            new_premios[k] = v
    r['premios'] = new_premios

DATA.sort(key=lambda x: x['sorteo_num'])

with open('/home/z/my-project/data/patterns.json') as f:
    PATTERNS = json.load(f)

print(f"Loaded {len(DATA)} sorteos and patterns data")

MONTHS = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
          'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
MONTHS_SHORT = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

# ============================================================
wb = Workbook()
wb.remove(wb.active)

# ============================================================
# SHEET 1: Resumen de Hallazgos (Summary of findings)
# ============================================================
ws = wb.create_sheet("Hallazgos Clave")

setup_sheet(ws, title="Pozo Millonario Ecuador — Hallazgos Clave del Análisis de Patrones", last_col=4)

row = 4

# Section: Top Hallazgos
ws.cell(row=row, column=2, value="HALLAZGOS PRINCIPALES").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 26
row += 1

hallazgos = [
    ("1. El pozo mayor solo se ha ganado 1 vez en 5 años",
     "Sorteo 950 (18-oct-2021): 1 ganador de $4,052,937.22. En los 307 sorteos siguientes, NADIE ha acertado los 11 números."),
    
    ("2. Octubre es el mes con mayores pagos históricos",
     "Octubre concentra $4.26M pagados (90% del total histórico). Promedio por sorteo en octubre: $2.13M vs $50K-$80K en otros meses."),
    
    ("3. Racha de acumulación récord: 7 sorteos consecutivos",
     "Sorteos 951-957 (oct-25 a dic-06, 2021): pozo creció de $852K → $953K → $1.06M → $1.18M → $1.30M → $1.42M → $1.56M sin ganador."),
    
    ("4. Los LUNES son el día con más pagos",
     "Todos los 9 sorteos con datos de pago ocurrieron en lunes. Los sorteos de jueves no tienen datos de ganadores registrados."),
    
    ("5. La suma promedio de los 11 números ganadores es 138.9",
     "Rango típico: 120-160 (68% de los sorteos). Mínimo: 91 (sorteo 1148), Máximo: 184 (sorteo 1083)."),
    
    ("6. Distribución par/impar más frecuente: 6 par / 5 impar (20%)",
     "Patrón equilibrado. 37% de sorteos tienen más pares, 33% más impares. La distribución 5-5 es poco común (11.7%)."),
    
    ("7. El par de números más co-ocurrente: 05 y 06 (25.6%)",
     "Salieron juntos en 79 de 308 sorteos. Casi 1 de cada 4 sorteos incluye ambos. Pares calientes: (17,19), (06,24), (06,15)."),
    
    ("8. El número 6 es el más frecuente (147 apariciones, 47.7%)",
     "Casi la mitad de los sorteos incluyen el 6. Le siguen: 2 (138), 5 (141), 15 (140), 17 (138)."),
    
    ("9. Septiembre 2021 fue un mes 'caliente'",
     "Entre el sorteo 950 (oct-2021) y 957 (dic-2021), se pagaron $4.67M en premios — el 99% del total histórico registrado."),
    
    ("10. Distribución por rangos: 4-4-3 (bajos-medios-altos) es la más común (8.1%)",
     "Los números se reparten bastante equilibradamente entre 1-8, 9-17 y 18-25. La combinación 3-5-3 también es frecuente (5.2%)."),
]

for titulo, desc in hallazgos:
    ws.cell(row=row, column=2, value=titulo).font = Font(name=FONT_NAME, size=11, bold=True, color=PRIMARY)
    ws.cell(row=row, column=2).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
    ws.cell(row=row, column=3, value=desc).font = font_body()
    ws.cell(row=row, column=3).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
    ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=4)
    ws.row_dimensions[row].height = 42
    row += 1

row += 2

# Section: Metodología
ws.cell(row=row, column=2, value="METODOLOGÍA DEL ANÁLISIS").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 26
row += 1

metodologia = [
    ("Total de sorteos analizados", f"{len(DATA)} (oct-2021 a sep-2026)"),
    ("Sorteos con datos completos de pago", f"{PATTERNS['total_con_pagos']} (la mayoría solo registra montos fijos sin ganadores)"),
    ("Variables analizadas", "Suma de números, par/impar, rangos (bajo/medio/alto), día de la semana, mes, trimestre, semana del mes, co-ocurrencias de pares"),
    ("Técnica de rachas", "Se identifica secuencia de sorteos donde ganadores_11 = 0 Y monto acumulado > $500"),
    ("Análisis de co-ocurrencia", "Para cada par de números (a,b) se cuenta en cuántos sorteos aparecieron juntos"),
    ("Frecuencia esperada de pares (si independiente)", "Cada par debería aparecer ~56.5 veces; los observados TOP superan 65-79 veces"),
]
for label, value in metodologia:
    ws.cell(row=row, column=2, value=label).font = font_body()
    ws.cell(row=row, column=2).alignment = align_text()
    ws.cell(row=row, column=3, value=value).font = font_body()
    ws.cell(row=row, column=3).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
    ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=4)
    ws.row_dimensions[row].height = 30
    row += 1

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 42
ws.column_dimensions['C'].width = 50
ws.column_dimensions['D'].width = 30

print("Sheet 1 (Hallazgos) created")

# ============================================================
# SHEET 2: Top Sorteos con Mayor Pago
# ============================================================
ws = wb.create_sheet("Top Pagos")

setup_sheet(ws, title="Top Sorteos con Mayor Pago Total — ¿Cuándo se paga más?", last_col=11)

headers = [
    "#", "Sorteo #", "Fecha", "Día", "Mes", "Año",
    "Total Pagado", "Gan 11", "Gan 10", "Mascota", "Números Ganadores"
]
for i, h in enumerate(headers, 2):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, row_num=4, col_start=2, col_end=12)

top_pagos = PATTERNS['top_15_mayor_pago']
for i, r in enumerate(top_pagos):
    row_num = 5 + i
    ws.cell(row=row_num, column=2, value=i+1)
    ws.cell(row=row_num, column=3, value=r['sorteo'])
    if r['fecha']:
        try:
            dt = datetime.strptime(r['fecha'], '%Y-%m-%d')
            ws.cell(row=row_num, column=4, value=dt).number_format = 'YYYY-MM-DD'
            ws.cell(row=row_num, column=5, value=MONTHS_SHORT[dt.month - 1])
            ws.cell(row=row_num, column=6, value=dt.year)
        except:
            ws.cell(row=row_num, column=4, value=r['fecha'])
    ws.cell(row=row_num, column=6, value=r['dia'])
    ws.cell(row=row_num, column=7, value=r['total_pagado']).number_format = '"$"#,##0.00'
    ws.cell(row=row_num, column=8, value=r['g11'])
    ws.cell(row=row_num, column=9, value=r['g10'])
    ws.cell(row=row_num, column=10, value=r['mascota'])
    nums_str = ' '.join(f'{n:02d}' for n in r['numeros'])
    ws.cell(row=row_num, column=11, value=nums_str)
    style_data_row(ws, row_num=row_num, col_start=2, col_end=12, row_index=i)
    # Alignment
    ws.cell(row=row_num, column=2).alignment = align_number()
    ws.cell(row=row_num, column=3).alignment = align_number()
    ws.cell(row=row_num, column=4).alignment = align_date()
    ws.cell(row=row_num, column=5).alignment = align_text()
    ws.cell(row=row_num, column=6).alignment = align_text()
    ws.cell(row=row_num, column=7).alignment = align_number()
    ws.cell(row=row_num, column=8).alignment = align_number()
    ws.cell(row=row_num, column=9).alignment = align_number()
    ws.cell(row=row_num, column=10).alignment = align_text()
    ws.cell(row=row_num, column=11).alignment = align_text()

# Conditional format on Total Pagado
ws.conditional_formatting.add(f'H5:H{4+len(top_pagos)}',
    DataBarRule(start_type='min', end_type='max', color=ACCENT_POSITIVE, showValue=True))

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 5
ws.column_dimensions['C'].width = 9
ws.column_dimensions['D'].width = 12
ws.column_dimensions['E'].width = 10
ws.column_dimensions['F'].width = 7
ws.column_dimensions['G'].width = 16
ws.column_dimensions['H'].width = 14
ws.column_dimensions['I'].width = 9
ws.column_dimensions['J'].width = 9
ws.column_dimensions['K'].width = 12
ws.column_dimensions['L'].width = 32

print("Sheet 2 (Top Pagos) created")

# ============================================================
# SHEET 3: Pagos por Día / Mes / Trimestre
# ============================================================
ws = wb.create_sheet("Pagos por Período")

setup_sheet(ws, title="Análisis Temporal de Pagos — Patrones por Día, Mes, Trimestre y Semana", last_col=7)

row = 4

# Section: Por día de la semana
ws.cell(row=row, column=2, value="PAGOS POR DÍA DE LA SEMANA").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 24
row += 1

day_headers = ["Día", "Sorteos", "Total Pagado", "Promedio", "Máximo"]
for i, h in enumerate(day_headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=6)
row += 1

day_order = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
for dia in day_order:
    if dia in PATTERNS['pagos_por_dia']:
        s = PATTERNS['pagos_por_dia'][dia]
        if s['count'] > 0:
            ws.cell(row=row, column=2, value=dia.capitalize())
            ws.cell(row=row, column=3, value=s['count'])
            ws.cell(row=row, column=4, value=s['total']).number_format = '"$"#,##0.00'
            ws.cell(row=row, column=5, value=s['promedio']).number_format = '"$"#,##0.00'
            ws.cell(row=row, column=6, value=s['max']).number_format = '"$"#,##0.00'
            style_data_row(ws, row_num=row, col_start=2, col_end=6, row_index=row)
            ws.cell(row=row, column=2).alignment = align_text()
            for c in range(3, 7):
                ws.cell(row=row, column=c).alignment = align_number()
            row += 1

row += 2

# Section: Por mes
ws.cell(row=row, column=2, value="PAGOS POR MES DEL AÑO").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 24
row += 1

month_headers = ["Mes", "Sorteos", "Total Pagado", "Promedio", "Mediana"]
for i, h in enumerate(month_headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=6)
month_header_row = row
row += 1

for m in range(1, 13):
    ms = str(m)
    if ms in PATTERNS['pagos_por_mes']:
        s = PATTERNS['pagos_por_mes'][ms]
        if s['count'] > 0:
            ws.cell(row=row, column=2, value=MONTHS_SHORT[m-1])
            ws.cell(row=row, column=3, value=s['count'])
            ws.cell(row=row, column=4, value=s['total']).number_format = '"$"#,##0.00'
            ws.cell(row=row, column=5, value=s['promedio']).number_format = '"$"#,##0.00'
            ws.cell(row=row, column=6, value=s['mediana']).number_format = '"$"#,##0.00'
            style_data_row(ws, row_num=row, col_start=2, col_end=6, row_index=row)
            ws.cell(row=row, column=2).alignment = align_text()
            for c in range(3, 7):
                ws.cell(row=row, column=c).alignment = align_number()
            row += 1

# Color scale on promedio
ws.conditional_formatting.add(f'E{month_header_row+1}:E{row-1}',
    ColorScaleRule(start_type='min', start_color='F7F7F5',
                   mid_type='percentile', mid_value=50, mid_color='D6E4F0',
                   end_type='max', end_color=PRIMARY))

row += 2

# Section: Por trimestre
ws.cell(row=row, column=2, value="PAGOS POR TRIMESTRE").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 24
row += 1

q_headers = ["Trimestre", "Sorteos", "Total Pagado", "Promedio", "% del Total"]
for i, h in enumerate(q_headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=6)
row += 1

total_all = sum(s['total'] for s in PATTERNS['pagos_por_trimestre'].values())
for q in sorted(PATTERNS['pagos_por_trimestre'].keys(), key=lambda x: int(x)):
    s = PATTERNS['pagos_por_trimestre'][q]
    if s['count'] > 0:
        ws.cell(row=row, column=2, value=f"Q{q} ({MONTHS_SHORT[(int(q)-1)*3]}-{MONTHS_SHORT[(int(q)-1)*3+2]})")
        ws.cell(row=row, column=3, value=s['count'])
        ws.cell(row=row, column=4, value=s['total']).number_format = '"$"#,##0.00'
        ws.cell(row=row, column=5, value=s['promedio']).number_format = '"$"#,##0.00'
        ws.cell(row=row, column=6, value=s['total']/total_all if total_all else 0).number_format = '0.0%'
        style_data_row(ws, row_num=row, col_start=2, col_end=6, row_index=row)
        ws.cell(row=row, column=2).alignment = align_text()
        for c in range(3, 7):
            ws.cell(row=row, column=c).alignment = align_number()
        row += 1

row += 2

# Section: Por semana del mes
ws.cell(row=row, column=2, value="PAGOS POR SEMANA DEL MES").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 24
row += 1

w_headers = ["Semana del Mes", "Sorteos", "Total Pagado", "Promedio"]
for i, h in enumerate(w_headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=5)
row += 1

for w in sorted(PATTERNS['pagos_por_semana_mes'].keys(), key=lambda x: int(x)):
    s = PATTERNS['pagos_por_semana_mes'][w]
    if s['count'] > 0:
        ws.cell(row=row, column=2, value=f"Semana {w}")
        ws.cell(row=row, column=3, value=s['count'])
        ws.cell(row=row, column=4, value=s['total']).number_format = '"$"#,##0.00'
        ws.cell(row=row, column=5, value=s['promedio']).number_format = '"$"#,##0.00'
        style_data_row(ws, row_num=row, col_start=2, col_end=5, row_index=row)
        ws.cell(row=row, column=2).alignment = align_text()
        for c in range(3, 6):
            ws.cell(row=row, column=c).alignment = align_number()
        row += 1

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 24
ws.column_dimensions['C'].width = 12
ws.column_dimensions['D'].width = 18
ws.column_dimensions['E'].width = 18
ws.column_dimensions['F'].width = 18
ws.column_dimensions['G'].width = 12

print("Sheet 3 (Pagos por Período) created")

# ============================================================
# SHEET 4: Sumatoria de Números por Sorteo
# ============================================================
ws = wb.create_sheet("Sumatoria Números")

setup_sheet(ws, title="Sumatoria de Números por Sorteo — Análisis Estadístico", last_col=10)

# Top stats
row = 4
ws.cell(row=row, column=2, value="ESTADÍSTICAS GENERALES").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 24
row += 1

stats = PATTERNS['sumatoria_numeros']
stat_items = [
    ("Suma mínima", stats['min']),
    ("Suma máxima", stats['max']),
    ("Suma promedio", round(stats['promedio'], 2)),
    ("Suma mediana", stats['mediana']),
    ("Desviación estándar", round(stats['stdev'], 2)),
]
for label, value in stat_items:
    ws.cell(row=row, column=2, value=label).font = font_body()
    ws.cell(row=row, column=2).alignment = align_text()
    ws.cell(row=row, column=3, value=value).font = font_body()
    ws.cell(row=row, column=3).alignment = align_number()
    row += 1

row += 1

# Detailed table: Sorteo | Fecha | Día | Suma | Pares | Impares | Bajos | Medios | Altos | Números
ws.cell(row=row, column=2, value="DETALLE POR SORTEO").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 24
row += 1

headers = ["Sorteo #", "Fecha", "Día", "Suma", "Pares", "Impares", "Bajos (1-8)", "Medios (9-17)", "Altos (18-25)", "Números"]
for i, h in enumerate(headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=11)
sum_header_row = row
row += 1

for i, s in enumerate(stats['sorteos']):
    row_num = row + i
    ws.cell(row=row_num, column=2, value=s['sorteo'])
    if s['fecha']:
        try:
            dt = datetime.strptime(s['fecha'], '%Y-%m-%d')
            ws.cell(row=row_num, column=3, value=dt).number_format = 'YYYY-MM-DD'
        except:
            ws.cell(row=row_num, column=3, value=s['fecha'])
    ws.cell(row=row_num, column=4, value=s['dia'])
    ws.cell(row=row_num, column=5, value=s['suma'])
    ws.cell(row=row_num, column=6, value=s['pares'])
    ws.cell(row=row_num, column=7, value=s['impares'])
    ws.cell(row=row_num, column=8, value=s['bajos'])
    ws.cell(row=row_num, column=9, value=s['medios'])
    ws.cell(row=row_num, column=10, value=s['altos'])
    nums_str = ' '.join(f'{n:02d}' for n in s['numeros'])
    ws.cell(row=row_num, column=11, value=nums_str)
    style_data_row(ws, row_num=row_num, col_start=2, col_end=11, row_index=i)
    ws.cell(row=row_num, column=2).alignment = align_number()
    ws.cell(row=row_num, column=3).alignment = align_date()
    ws.cell(row=row_num, column=4).alignment = align_text()
    for c in range(5, 11):
        ws.cell(row=row_num, column=c).alignment = align_number()
    ws.cell(row=row_num, column=11).alignment = align_text()

# Conditional formatting on Suma column
sum_col_letter = get_column_letter(5)
ws.conditional_formatting.add(f'{sum_col_letter}{sum_header_row+1}:{sum_col_letter}{row+len(stats["sorteos"])-1}',
    ColorScaleRule(start_type='min', start_color='F8696B',
                   mid_type='percentile', mid_value=50, mid_color='FFEB84',
                   end_type='max', end_color='63BE7B'))

ws.freeze_panes = f'B{sum_header_row+1}'

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 9
ws.column_dimensions['C'].width = 12
ws.column_dimensions['D'].width = 10
ws.column_dimensions['E'].width = 8
ws.column_dimensions['F'].width = 8
ws.column_dimensions['G'].width = 10
ws.column_dimensions['H'].width = 12
ws.column_dimensions['I'].width = 14
ws.column_dimensions['J'].width = 12
ws.column_dimensions['K'].width = 32

print("Sheet 4 (Sumatoria) created")

# ============================================================
# SHEET 5: Rachas de Acumulación
# ============================================================
ws = wb.create_sheet("Rachas Acumulación")

setup_sheet(ws, title="Rachas de Acumulación — Sorteos Consecutivos sin Ganador de 11 Aciertos", last_col=7)

row = 4
ws.cell(row=row, column=2, value="RESUMEN DE RACHAS DETECTADAS").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 24
row += 1

rachas_headers = ["#", "Longitud (sorteos)", "Sorteo Inicio", "Sorteo Fin", "Fecha Inicio", "Fecha Fin", "Monto Máximo Acumulado"]
for i, h in enumerate(rachas_headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=8)
row += 1

for i, r in enumerate(PATTERNS['rachas_acumulacion']):
    ws.cell(row=row, column=2, value=i+1)
    ws.cell(row=row, column=3, value=r['longitud'])
    ws.cell(row=row, column=4, value=r['sorteo_inicio'])
    ws.cell(row=row, column=5, value=r['sorteo_fin'])
    if r['fecha_inicio']:
        try:
            dt = datetime.strptime(r['fecha_inicio'], '%Y-%m-%d')
            ws.cell(row=row, column=6, value=dt).number_format = 'YYYY-MM-DD'
        except:
            ws.cell(row=row, column=6, value=r['fecha_inicio'])
    if r['fecha_fin']:
        try:
            dt = datetime.strptime(r['fecha_fin'], '%Y-%m-%d')
            ws.cell(row=row, column=7, value=dt).number_format = 'YYYY-MM-DD'
        except:
            ws.cell(row=row, column=7, value=r['fecha_fin'])
    ws.cell(row=row, column=8, value=r['monto_max']).number_format = '"$"#,##0.00'
    style_data_row(ws, row_num=row, col_start=2, col_end=8, row_index=i)
    for c in range(2, 9):
        ws.cell(row=row, column=c).alignment = align_number() if c not in [6, 7] else align_date()
    row += 1

row += 2

# Detailed breakdown of the longest streak
ws.cell(row=row, column=2, value="DETALLE DE RACHA MÁS LARGA (Sorteos 951-957, oct-dic 2021)").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 24
row += 1

detail_headers = ["Sorteo #", "Fecha", "Día", "Monto Acumulado", "Incremento vs Anterior", "Mascota", "Números"]
for i, h in enumerate(detail_headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=8)
row += 1

# Get the longest streak sorteos
if PATTERNS['rachas_acumulacion']:
    longest = PATTERNS['rachas_acumulacion'][0]
    streak_sorteos = longest['sorteos']
    prev_monto = None
    for sn in streak_sorteos:
        # Find the record
        r = next((x for x in DATA if x['sorteo_num'] == sn), None)
        if r:
            p = r['premios']
            p11 = p.get(11, {})
            monto = p11.get('premio_indiv')
            ws.cell(row=row, column=2, value=r['sorteo_num'])
            if r['fecha']:
                try:
                    dt = datetime.strptime(r['fecha'], '%Y-%m-%d')
                    ws.cell(row=row, column=3, value=dt).number_format = 'YYYY-MM-DD'
                except:
                    ws.cell(row=row, column=3, value=r['fecha'])
            ws.cell(row=row, column=4, value=r.get('dia_semana', ''))
            ws.cell(row=row, column=5, value=monto).number_format = '"$"#,##0.00'
            if prev_monto and monto:
                inc = monto - prev_monto
                ws.cell(row=row, column=6, value=inc).number_format = '"$"#,##0.00'
            prev_monto = monto
            ws.cell(row=row, column=7, value=r.get('mascota', ''))
            nums_str = ' '.join(f'{n:02d}' for n in r['numeros'])
            ws.cell(row=row, column=8, value=nums_str)
            style_data_row(ws, row_num=row, col_start=2, col_end=8, row_index=row)
            ws.cell(row=row, column=2).alignment = align_number()
            ws.cell(row=row, column=3).alignment = align_date()
            ws.cell(row=row, column=4).alignment = align_text()
            for c in [5, 6]:
                ws.cell(row=row, column=c).alignment = align_number()
            ws.cell(row=row, column=7).alignment = align_text()
            ws.cell(row=row, column=8).alignment = align_text()
            row += 1

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 9
ws.column_dimensions['C'].width = 12
ws.column_dimensions['D'].width = 18
ws.column_dimensions['E'].width = 18
ws.column_dimensions['F'].width = 20
ws.column_dimensions['G'].width = 12
ws.column_dimensions['H'].width = 32

print("Sheet 5 (Rachas) created")

# ============================================================
# SHEET 6: Pares Co-ocurrentes (top combinations)
# ============================================================
ws = wb.create_sheet("Pares Co-ocurrentes")

setup_sheet(ws, title="Pares de Números que Más Salen Juntos — Coincidencias", last_col=6)

row = 4
ws.cell(row=row, column=2, value="TOP 15 PARES DE NÚMEROS MÁS CO-OCURRENTES").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 24
row += 1

# Note about expected frequency
ws.cell(row=row, column=2, value="Nota: La frecuencia esperada (si los números fueran independientes) es ~56 apariciones por par. Los pares calientes superan significativamente este valor.").font = font_caption()
ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=6)
ws.row_dimensions[row].height = 30
row += 1

headers = ["#", "Par", "N° 1", "N° 2", "Frecuencia", "% Aparición"]
for i, h in enumerate(headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=7)
row += 1

# Show top 25 (compute more)
from collections import Counter
pair_counter = Counter()
for r in DATA:
    if r['numeros']:
        unique_nums = sorted(set(r['numeros']))
        for i in range(len(unique_nums)):
            for j in range(i+1, len(unique_nums)):
                pair_counter[(unique_nums[i], unique_nums[j])] += 1

top_pairs = pair_counter.most_common(25)
for i, ((a, b), count) in enumerate(top_pairs):
    pct = count / len(DATA) * 100
    ws.cell(row=row, column=2, value=i+1)
    ws.cell(row=row, column=3, value=f"{a:02d} - {b:02d}")
    ws.cell(row=row, column=4, value=a).number_format = '00'
    ws.cell(row=row, column=5, value=b).number_format = '00'
    ws.cell(row=row, column=6, value=count)
    ws.cell(row=row, column=7, value=pct/100).number_format = '0.0%'
    style_data_row(ws, row_num=row, col_start=2, col_end=7, row_index=i)
    ws.cell(row=row, column=2).alignment = align_number()
    ws.cell(row=row, column=3).alignment = align_text()
    ws.cell(row=row, column=4).alignment = align_date()
    ws.cell(row=row, column=5).alignment = align_date()
    ws.cell(row=row, column=6).alignment = align_number()
    ws.cell(row=row, column=7).alignment = align_number()
    row += 1

# Data bar on frequency
ws.conditional_formatting.add(f'F5:F{4+25}',
    DataBarRule(start_type='min', end_type='max', color=PRIMARY, showValue=True))

# Add chart
chart = create_bar_chart(chart_type='bar', width=24, height=14)
data_ref = Reference(ws, min_col=6, min_row=4, max_col=6, max_row=4+25)
cats_ref = Reference(ws, min_col=3, min_row=5, max_col=3, max_row=4+25)
chart.add_data(data_ref, titles_from_data=True)
chart.set_categories(cats_ref)
setup_chart_titles(chart, title="Top 25 Pares de Números Más Co-ocurrentes", y_title="Par de números", x_title="Frecuencia")
apply_chart_colors(chart)
chart.legend = None
ws.add_chart(chart, "I4")

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 5
ws.column_dimensions['C'].width = 12
ws.column_dimensions['D'].width = 8
ws.column_dimensions['E'].width = 8
ws.column_dimensions['F'].width = 14
ws.column_dimensions['G'].width = 14

print("Sheet 6 (Pares Co-ocurrentes) created")

# ============================================================
# SHEET 7: Distribución Par/Impar y Rangos
# ============================================================
ws = wb.create_sheet("Distribuciones")

setup_sheet(ws, title="Distribución Estadística de los Números Ganadores", last_col=6)

row = 4

# Section: Distribución Par/Impar
ws.cell(row=row, column=2, value="DISTRIBUCIÓN PAR/IMPAR").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 24
row += 1

pi_headers = ["Pares", "Impares", "Cantidad de Sorteos", "% del Total"]
for i, h in enumerate(pi_headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=5)
row += 1

for item in PATTERNS['distribucion_par_impar']:
    ws.cell(row=row, column=2, value=item['pares'])
    ws.cell(row=row, column=3, value=item['impares'])
    ws.cell(row=row, column=4, value=item['count'])
    ws.cell(row=row, column=5, value=item['pct']/100).number_format = '0.0%'
    style_data_row(ws, row_num=row, col_start=2, col_end=5, row_index=row)
    for c in range(2, 6):
        ws.cell(row=row, column=c).alignment = align_number()
    row += 1

row += 2

# Section: Distribución por Rangos
ws.cell(row=row, column=2, value="DISTRIBUCIÓN POR RANGOS (1-8 / 9-17 / 18-25)").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 24
row += 1

r_headers = ["Bajos (1-8)", "Medios (9-17)", "Altos (18-25)", "Cantidad", "% del Total"]
for i, h in enumerate(r_headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=6)
row += 1

for item in PATTERNS['distribucion_rangos']:
    ws.cell(row=row, column=2, value=item['bajos'])
    ws.cell(row=row, column=3, value=item['medios'])
    ws.cell(row=row, column=4, value=item['altos'])
    ws.cell(row=row, column=5, value=item['count'])
    ws.cell(row=row, column=6, value=item['pct']/100).number_format = '0.0%'
    style_data_row(ws, row_num=row, col_start=2, col_end=6, row_index=row)
    for c in range(2, 7):
        ws.cell(row=row, column=c).alignment = align_number()
    row += 1

row += 2

# Section: Análisis por día - Suma promedio
ws.cell(row=row, column=2, value="SUMA PROMEDIO POR DÍA DE LA SEMANA").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 24
row += 1

sd_headers = ["Día", "Sorteos", "Suma Promedio", "Suma Mediana", "Suma Mínima", "Suma Máxima"]
for i, h in enumerate(sd_headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=7)
row += 1

# Recompute sums by day
from collections import defaultdict
from statistics import mean, median
sum_by_day = defaultdict(list)
for r in DATA:
    if r['numeros'] and r.get('dia_semana'):
        dia = r['dia_semana'].lower().strip()
        unique_nums = list(dict.fromkeys(r['numeros']))
        s = sum(unique_nums)
        sum_by_day[dia].append(s)

for dia in ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado']:
    if dia in sum_by_day and sum_by_day[dia]:
        vals = sum_by_day[dia]
        ws.cell(row=row, column=2, value=dia.capitalize())
        ws.cell(row=row, column=3, value=len(vals))
        ws.cell(row=row, column=4, value=round(mean(vals), 1))
        ws.cell(row=row, column=5, value=median(vals))
        ws.cell(row=row, column=6, value=min(vals))
        ws.cell(row=row, column=7, value=max(vals))
        style_data_row(ws, row_num=row, col_start=2, col_end=7, row_index=row)
        ws.cell(row=row, column=2).alignment = align_text()
        for c in range(3, 8):
            ws.cell(row=row, column=c).alignment = align_number()
        row += 1

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 16
ws.column_dimensions['C'].width = 16
ws.column_dimensions['D'].width = 16
ws.column_dimensions['E'].width = 16
ws.column_dimensions['F'].width = 16
ws.column_dimensions['G'].width = 16

print("Sheet 7 (Distribuciones) created")

# ============================================================
# SHEET 8: Número Frequency with Companions
# ============================================================
ws = wb.create_sheet("Acompañantes por Número")

setup_sheet(ws, title="Números 'Acompañantes' — Para cada número, cuáles salen más junto a él", last_col=8)

row = 4
ws.cell(row=row, column=2, value="Para cada número del 1 al 25, se muestran los 5 números que más veces salieron junto a él en el mismo sorteo.").font = font_caption()
ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=8)
ws.row_dimensions[row].height = 22
row += 1

headers = ["Número", "Frecuencia Total", "Top 1", "Top 2", "Top 3", "Top 4", "Top 5"]
for i, h in enumerate(headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=8)
row += 1

# Compute companion analysis for all numbers 1-25
single_with_other = defaultdict(Counter)
number_freq = Counter()
for r in DATA:
    if r['numeros']:
        unique_nums = sorted(set(r['numeros']))
        for n in unique_nums:
            number_freq[n] += 1
            others = [x for x in unique_nums if x != n]
            for o in others:
                single_with_other[n][o] += 1

for n in range(1, 26):
    freq = number_freq.get(n, 0)
    ws.cell(row=row, column=2, value=n).number_format = '00'
    ws.cell(row=row, column=3, value=freq)
    top_companions = single_with_other[n].most_common(5)
    for i, (comp, count) in enumerate(top_companions):
        ws.cell(row=row, column=4+i, value=f"{comp:02d} ({count}x)")
    style_data_row(ws, row_num=row, col_start=2, col_end=8, row_index=row)
    ws.cell(row=row, column=2).alignment = align_date()
    ws.cell(row=row, column=3).alignment = align_number()
    for c in range(4, 9):
        ws.cell(row=row, column=c).alignment = align_text()
    row += 1

# Data bar on Total frequency
ws.conditional_formatting.add(f'C5:C{4+25}',
    DataBarRule(start_type='min', end_type='max', color=PRIMARY, showValue=True))

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 10
ws.column_dimensions['C'].width = 18
ws.column_dimensions['D'].width = 14
ws.column_dimensions['E'].width = 14
ws.column_dimensions['F'].width = 14
ws.column_dimensions['G'].width = 14
ws.column_dimensions['H'].width = 14

print("Sheet 8 (Acompañantes) created")

# ============================================================
# Save
# ============================================================
wb.properties.creator = "Z.ai"
wb.properties.title = "Pozo Millonario - Análisis de Patrones"

output_path = '/home/z/my-project/download/Pozo_Millonario_Patrones.xlsx'
wb.save(output_path)

print(f"\n✓ Excel saved to: {output_path}")
print(f"  File size: {os.path.getsize(output_path):,} bytes")
print(f"  Sheets: {wb.sheetnames}")

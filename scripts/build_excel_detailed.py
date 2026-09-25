"""
Build the SUPER DETAILED Excel file with EVERY draw as a row.
Each row contains ALL information per draw:
- Sorteo #
- Fecha, día, año, mes
- Numbers N1-N11 (separadas)
- Suma de números, pares, impares
- Mascota
- Ganadores 11/10/9/8/7 y mascota
- Premios individuales por categoría
- Totales pagados por categoría
- Total pagado en el sorteo
- ¿Se acumuló el pozo? (Sí/No)
- Monto del pozo acumulado (premio_indiv de 11 aciertos)
- Pozo Revancha: #, números, mascota, ganadores, premios
- Próximo sorteo: fecha, día, monto estimado
- Fuente URL
"""
import sys
import os
import json
from collections import Counter, defaultdict
from datetime import datetime

# Add xlsx skill templates to path
sys.path.insert(0, '/home/z/my-project/skills/xlsx/templates')
sys.path.insert(0, '/home/z/my-project/skills/xlsx')

from base import (
    use_palette_explicit, setup_sheet, style_header_row, style_data_row,
    style_total_row, font_title, font_header, font_subheader, font_body,
    font_caption, font_kpi, font_kpi_label, fill_header, fill_total,
    fill_data_row, border_header, border_total, align_title, align_header,
    align_number, align_text, align_date, auto_fit_columns,
    PRIMARY, PRIMARY_LIGHT, SECONDARY, ACCENT_POSITIVE, ACCENT_NEGATIVE,
    ACCENT_WARNING, NEUTRAL_900, NEUTRAL_600, NEUTRAL_200, NEUTRAL_100,
    NEUTRAL_50, NEUTRAL_0, HEADER_TEXT, CHART_COLORS, FONT_NAME, HEADER_BOLD,
    FORMATS, ROW_HEIGHTS, COLUMN_WIDTHS, create_bar_chart, setup_chart_titles,
    apply_chart_colors,
)
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Border, Side, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule, CellIsRule, FormulaRule

# Use professional palette
use_palette_explicit("professional")

# Load data
with open('/home/z/my-project/data/pozo_data.json') as f:
    DATA = json.load(f)

# Normalize prize keys: convert string keys back to int
for r in DATA:
    new_premios = {}
    for k, v in r['premios'].items():
        if isinstance(k, str) and k.isdigit():
            new_premios[int(k)] = v
        else:
            new_premios[k] = v
    r['premios'] = new_premios
    if 'premios' in r['revancha']:
        new_rev = {}
        for k, v in r['revancha']['premios'].items():
            if isinstance(k, str) and k.isdigit():
                new_rev[int(k)] = v
            else:
                new_rev[k] = v
        r['revancha']['premios'] = new_rev

# Sort by sorteo_num ascending
DATA = sorted(DATA, key=lambda x: x['sorteo_num'])

print(f"Loaded {len(DATA)} sorteo records")
print(f"Date range: {min(r['fecha'] for r in DATA if r['fecha'])} to {max(r['fecha'] for r in DATA if r['fecha'])}")

# ============================================================
# Create workbook
# ============================================================
wb = Workbook()
wb.remove(wb.active)

# ============================================================
# SHEET 1: Tabla Detallada (MAIN - superdetallada)
# ============================================================
ws = wb.create_sheet("Tabla Detallada")

# Define ALL columns
headers = [
    # Identificación y fecha
    "Sorteo #",
    "Fecha",
    "Día Semana",
    "Año",
    "Mes",
    
    # Números ganadores Pozo Millonario
    "N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8", "N9", "N10", "N11",
    "Números (texto)",
    "Suma Números",
    "Pares",
    "Impares",
    "Mascota PM",
    
    # Detalle de Premios por Acierto
    "Gan 11 aciertos",
    "Premio indiv 11",
    "Total pagado 11",
    "Gan 10 aciertos",
    "Premio indiv 10",
    "Total pagado 10",
    "Gan 9 aciertos",
    "Premio indiv 9",
    "Total pagado 9",
    "Gan 8 aciertos",
    "Premio indiv 8",
    "Total pagado 8",
    "Gan 7 aciertos",
    "Premio indiv 7",
    "Total pagado 7",
    "Gan Mascota",
    "Premio indiv Mascota",
    "Total pagado Mascota",
    
    # Análisis del sorteo
    "Total Pagado Sorteo",
    "¿Pozo Acumulado?",
    "Monto Pozo Acumulado",
    "¿Hubo Ganador 11?",
    
    # Pozo Revancha
    "Revancha #",
    "R N1", "R N2", "R N3", "R N4", "R N5", "R N6", "R N7", "R N8", "R N9", "R N10", "R N11",
    "Mascota Revancha",
    "Gan R 11",
    "Gan R 10",
    "Gan R 9",
    "Gan R 8",
    "Total Pagado Revancha",
    
    # Próximo sorteo
    "Próx Sorteo #",
    "Próx Fecha",
    "Próx Día",
    "Monto Estimado Próx",
    
    # Metadata
    "URL Fuente",
]

last_col = len(headers) + 1  # +1 because we start at column B

setup_sheet(ws, title=f"Pozo Millonario Ecuador — Tabla Detallada por Sorteo ({len(DATA)} sorteos, oct-2021 a sep-2026)", last_col=last_col)

# Write headers at row 4
for i, h in enumerate(headers, 2):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, row_num=4, col_start=2, col_end=last_col)

# Map column indices for easier reference (1-indexed = column letter position)
COL = {
    'sorteo': 2, 'fecha': 3, 'dia': 4, 'año': 5, 'mes': 6,
    'n1': 7, 'n2': 8, 'n3': 9, 'n4': 10, 'n5': 11, 'n6': 12,
    'n7': 13, 'n8': 14, 'n9': 15, 'n10': 16, 'n11': 17,
    'nums_texto': 18, 'suma': 19, 'pares': 20, 'impares': 21, 'mascota_pm': 22,
    'g11': 23, 'p11': 24, 't11': 25,
    'g10': 26, 'p10': 27, 't10': 28,
    'g9': 29, 'p9': 30, 't9': 31,
    'g8': 32, 'p8': 33, 't8': 34,
    'g7': 35, 'p7': 36, 't7': 37,
    'gmasc': 38, 'pmasc': 39, 'tmasc': 40,
    'total_pagado': 41,
    'acumulado_flag': 42, 'acumulado_monto': 43, 'hubo_ganador_11': 44,
    'rev_num': 45,
    'r_n1': 46, 'r_n2': 47, 'r_n3': 48, 'r_n4': 49, 'r_n5': 50, 'r_n6': 51,
    'r_n7': 52, 'r_n8': 53, 'r_n9': 54, 'r_n10': 55, 'r_n11': 56,
    'mascota_rev': 57,
    'rg11': 58, 'rg10': 59, 'rg9': 60, 'rg8': 61, 'rtotal': 62,
    'prox_num': 63, 'prox_fecha': 64, 'prox_dia': 65, 'prox_monto': 66,
    'url': 67,
}

# Spanish month names
MONTHS_ES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

# Write data rows
for i, r in enumerate(DATA):
    row_num = 5 + i
    p = r['premios']
    rev = r['revancha']
    prox = r['proximo']
    
    # Sorteo #
    ws.cell(row=row_num, column=COL['sorteo'], value=r['sorteo_num'])
    
    # Fecha
    if r['fecha']:
        try:
            dt = datetime.strptime(r['fecha'], '%Y-%m-%d')
            ws.cell(row=row_num, column=COL['fecha'], value=dt).number_format = 'YYYY-MM-DD'
            ws.cell(row=row_num, column=COL['año'], value=dt.year)
            ws.cell(row=row_num, column=COL['mes'], value=MONTHS_ES.get(dt.month, ''))
        except:
            ws.cell(row=row_num, column=COL['fecha'], value=r['fecha'])
    
    # Día
    ws.cell(row=row_num, column=COL['dia'], value=r.get('dia_semana', ''))
    
    # Números
    nums = r['numeros']
    for j in range(11):
        if j < len(nums):
            ws.cell(row=row_num, column=COL['n1'] + j, value=nums[j]).number_format = '00'
    
    # Números como texto
    nums_str = ' '.join(f'{n:02d}' for n in nums)
    ws.cell(row=row_num, column=COL['nums_texto'], value=nums_str)
    
    # Suma, pares, impares
    if nums:
        ws.cell(row=row_num, column=COL['suma'], value=sum(nums))
        ws.cell(row=row_num, column=COL['pares'], value=sum(1 for n in nums if n % 2 == 0))
        ws.cell(row=row_num, column=COL['impares'], value=sum(1 for n in nums if n % 2 != 0))
    
    # Mascota PM
    ws.cell(row=row_num, column=COL['mascota_pm'], value=r.get('mascota', ''))
    
    # Premios por acierto
    def get_prize_data(premios_dict, acierto):
        d = premios_dict.get(acierto, {})
        return d.get('ganadores'), d.get('premio_indiv'), d.get('total')
    
    # 11
    g, p_ind, t = get_prize_data(p, 11)
    ws.cell(row=row_num, column=COL['g11'], value=g)
    ws.cell(row=row_num, column=COL['p11'], value=p_ind).number_format = '"$"#,##0.00'
    ws.cell(row=row_num, column=COL['t11'], value=t).number_format = '"$"#,##0.00'
    
    # 10
    g, p_ind, t = get_prize_data(p, 10)
    ws.cell(row=row_num, column=COL['g10'], value=g)
    ws.cell(row=row_num, column=COL['p10'], value=p_ind).number_format = '"$"#,##0.00'
    ws.cell(row=row_num, column=COL['t10'], value=t).number_format = '"$"#,##0.00'
    
    # 9
    g, p_ind, t = get_prize_data(p, 9)
    ws.cell(row=row_num, column=COL['g9'], value=g)
    ws.cell(row=row_num, column=COL['p9'], value=p_ind).number_format = '"$"#,##0.00'
    ws.cell(row=row_num, column=COL['t9'], value=t).number_format = '"$"#,##0.00'
    
    # 8
    g, p_ind, t = get_prize_data(p, 8)
    ws.cell(row=row_num, column=COL['g8'], value=g)
    ws.cell(row=row_num, column=COL['p8'], value=p_ind).number_format = '"$"#,##0.00'
    ws.cell(row=row_num, column=COL['t8'], value=t).number_format = '"$"#,##0.00'
    
    # 7
    g, p_ind, t = get_prize_data(p, 7)
    ws.cell(row=row_num, column=COL['g7'], value=g)
    ws.cell(row=row_num, column=COL['p7'], value=p_ind).number_format = '"$"#,##0.00'
    ws.cell(row=row_num, column=COL['t7'], value=t).number_format = '"$"#,##0.00'
    
    # Mascota
    pm = p.get('mascota', {})
    ws.cell(row=row_num, column=COL['gmasc'], value=pm.get('ganadores'))
    ws.cell(row=row_num, column=COL['pmasc'], value=pm.get('premio_indiv')).number_format = '"$"#,##0.00'
    ws.cell(row=row_num, column=COL['tmasc'], value=pm.get('total')).number_format = '"$"#,##0.00'
    
    # Total pagado en el sorteo (formula sumando totales 11, 10, 9, 8, 7, masc)
    # Get column letters for the totals
    t11_letter = get_column_letter(COL['t11'])
    t10_letter = get_column_letter(COL['t10'])
    t9_letter = get_column_letter(COL['t9'])
    t8_letter = get_column_letter(COL['t8'])
    t7_letter = get_column_letter(COL['t7'])
    tmasc_letter = get_column_letter(COL['tmasc'])
    ws.cell(row=row_num, column=COL['total_pagado'],
            value=f"=IFERROR(SUM({t11_letter}{row_num},{t10_letter}{row_num},{t9_letter}{row_num},{t8_letter}{row_num},{t7_letter}{row_num},{tmasc_letter}{row_num}),0)").number_format = '"$"#,##0.00'
    
    # ¿Pozo Acumulado? - si NO hay ganador de 11 y el monto acumulado es > $500 (base)
    p11_data = p.get(11, {})
    g11 = p11_data.get('ganadores')
    p11_ind = p11_data.get('premio_indiv')
    
    # Determinar si se acumuló (el pozo mayor no fue ganado)
    if g11 is not None and g11 > 0:
        # Hubo ganador de 11 aciertos
        acumulado = "NO"
        acumulado_monto = p11_ind  # monto ganado
        hubo_ganador = "SÍ"
    elif g11 == 0 and p11_ind is not None and p11_ind > 500:
        # No hubo ganador Y el monto supera el base de $500 → acumulado real
        acumulado = "SÍ"
        acumulado_monto = p11_ind
        hubo_ganador = "NO"
    elif g11 == 0:
        # No hubo ganador pero el monto es el base ($500) o no hay datos → probable acumulado sin datos
        acumulado = "SÍ (s/d monto)"
        acumulado_monto = None
        hubo_ganador = "NO"
    else:
        acumulado = "S/D"
        acumulado_monto = p11_ind
        hubo_ganador = "S/D"
    
    ws.cell(row=row_num, column=COL['acumulado_flag'], value=acumulado)
    ws.cell(row=row_num, column=COL['acumulado_monto'], value=acumulado_monto).number_format = '"$"#,##0.00'
    ws.cell(row=row_num, column=COL['hubo_ganador_11'], value=hubo_ganador)
    
    # Pozo Revancha
    rev_num = rev.get('sorteo_num')
    ws.cell(row=row_num, column=COL['rev_num'], value=rev_num)
    
    rev_nums = rev.get('numeros', [])
    for j in range(11):
        if j < len(rev_nums):
            try:
                n = int(rev_nums[j])
                ws.cell(row=row_num, column=COL['r_n1'] + j, value=n).number_format = '00'
            except:
                ws.cell(row=row_num, column=COL['r_n1'] + j, value=rev_nums[j])
    
    ws.cell(row=row_num, column=COL['mascota_rev'], value=rev.get('mascota', ''))
    
    # Revancha prize data
    rev_p = rev.get('premios', {})
    rg11, _, _ = get_prize_data(rev_p, 11)
    rg10, _, _ = get_prize_data(rev_p, 10)
    rg9, _, _ = get_prize_data(rev_p, 9)
    rg8, _, _ = get_prize_data(rev_p, 8)
    ws.cell(row=row_num, column=COL['rg11'], value=rg11)
    ws.cell(row=row_num, column=COL['rg10'], value=rg10)
    ws.cell(row=row_num, column=COL['rg9'], value=rg9)
    ws.cell(row=row_num, column=COL['rg8'], value=rg8)
    
    # Total pagado revancha (sum of totals where available)
    rev_totals = []
    for ac in [11, 10, 9, 8]:
        d = rev_p.get(ac, {})
        if d.get('total') is not None:
            rev_totals.append(d.get('total'))
    if rev_totals:
        ws.cell(row=row_num, column=COL['rtotal'], value=sum(rev_totals)).number_format = '"$"#,##0.00'
    
    # Próximo sorteo
    # The proximo data may have keys like proximo_sorteo, proximo_fecha, proximo_dia_semana, premio_estimado_proximo
    ws.cell(row=row_num, column=COL['prox_num'], value=prox.get('proximo_sorteo'))
    if prox.get('proximo_fecha'):
        try:
            dt = datetime.strptime(prox['proximo_fecha'], '%Y-%m-%d')
            ws.cell(row=row_num, column=COL['prox_fecha'], value=dt).number_format = 'YYYY-MM-DD'
        except:
            ws.cell(row=row_num, column=COL['prox_fecha'], value=prox.get('proximo_fecha'))
    ws.cell(row=row_num, column=COL['prox_dia'], value=prox.get('proximo_dia_semana', ''))
    ws.cell(row=row_num, column=COL['prox_monto'], value=prox.get('premio_estimado_proximo')).number_format = '"$"#,##0.00'
    
    # URL Fuente
    ws.cell(row=row_num, column=COL['url'],
            value=f"https://pozomillonario.info/pozo-millonario-sorteo-{r['sorteo_num']}")
    
    # Style data row
    style_data_row(ws, row_num=row_num, col_start=2, col_end=last_col, row_index=i)
    
    # Set alignment per column
    for col_idx in range(2, last_col + 1):
        cell = ws.cell(row=row_num, column=col_idx)
        if col_idx in [COL['sorteo'], COL['año']]:
            cell.alignment = align_number()
        elif col_idx in [COL['fecha'], COL['prox_fecha']]:
            cell.alignment = align_date()
        elif col_idx in [COL['dia'], COL['mes'], COL['prox_dia']]:
            cell.alignment = align_text()
        elif col_idx in [COL['n1'], COL['n2'], COL['n3'], COL['n4'], COL['n5'],
                         COL['n6'], COL['n7'], COL['n8'], COL['n9'], COL['n10'], COL['n11'],
                         COL['r_n1'], COL['r_n2'], COL['r_n3'], COL['r_n4'], COL['r_n5'],
                         COL['r_n6'], COL['r_n7'], COL['r_n8'], COL['r_n9'], COL['r_n10'], COL['r_n11']]:
            cell.alignment = align_date()
        elif col_idx in [COL['nums_texto'], COL['mascota_pm'], COL['mascota_rev'], COL['acumulado_flag'], COL['hubo_ganador_11']]:
            cell.alignment = align_text()
        elif col_idx == COL['url']:
            cell.font = Font(name=FONT_NAME, size=8, color=NEUTRAL_600)
            cell.alignment = align_text()
        else:
            cell.alignment = align_number()

# Conditional formatting for "¿Pozo Acumulado?" column
# SÍ → rojo (acumulado, no se ganó)
# NO → verde (se ganó)
# SÍ (s/d monto) → amarillo (probable acumulado, sin datos)
ws.conditional_formatting.add(
    f'{get_column_letter(COL["acumulado_flag"])}5:{get_column_letter(COL["acumulado_flag"])}{5 + len(DATA) - 1}',
    CellIsRule(operator='equal', formula=['"SÍ"'],
               fill=PatternFill('solid', fgColor='FDEDEC'),
               font=Font(name=FONT_NAME, color=ACCENT_NEGATIVE, bold=True)))
ws.conditional_formatting.add(
    f'{get_column_letter(COL["acumulado_flag"])}5:{get_column_letter(COL["acumulado_flag"])}{5 + len(DATA) - 1}',
    CellIsRule(operator='equal', formula=['"SÍ (s/d monto)"'],
               fill=PatternFill('solid', fgColor='FEF9E7'),
               font=Font(name=FONT_NAME, color=ACCENT_WARNING)))
ws.conditional_formatting.add(
    f'{get_column_letter(COL["acumulado_flag"])}5:{get_column_letter(COL["acumulado_flag"])}{5 + len(DATA) - 1}',
    CellIsRule(operator='equal', formula=['"NO"'],
               fill=PatternFill('solid', fgColor='E8F5E9'),
               font=Font(name=FONT_NAME, color=ACCENT_POSITIVE, bold=True)))

# Conditional formatting on Ganadores 11 (highlight > 0)
ws.conditional_formatting.add(
    f'{get_column_letter(COL["g11"])}5:{get_column_letter(COL["g11"])}{5 + len(DATA) - 1}',
    CellIsRule(operator='greaterThan', formula=['0'],
               fill=PatternFill('solid', fgColor='FEF9E7'),
               font=Font(name=FONT_NAME, color=ACCENT_WARNING, bold=True)))

# Freeze panes - keep sorteo # and fecha visible while scrolling
ws.freeze_panes = 'F5'

# Column widths
ws.column_dimensions['A'].width = 3  # margin
ws.column_dimensions[get_column_letter(COL['sorteo'])].width = 9
ws.column_dimensions[get_column_letter(COL['fecha'])].width = 12
ws.column_dimensions[get_column_letter(COL['dia'])].width = 10
ws.column_dimensions[get_column_letter(COL['año'])].width = 7
ws.column_dimensions[get_column_letter(COL['mes'])].width = 11
for c in range(COL['n1'], COL['n11'] + 1):
    ws.column_dimensions[get_column_letter(c)].width = 4.5
ws.column_dimensions[get_column_letter(COL['nums_texto'])].width = 28
ws.column_dimensions[get_column_letter(COL['suma'])].width = 7
ws.column_dimensions[get_column_letter(COL['pares'])].width = 6
ws.column_dimensions[get_column_letter(COL['impares'])].width = 7
ws.column_dimensions[get_column_letter(COL['mascota_pm'])].width = 11
# Prize columns
for c in [COL['g11'], COL['g10'], COL['g9'], COL['g8'], COL['g7'], COL['gmasc']]:
    ws.column_dimensions[get_column_letter(c)].width = 7
for c in [COL['p11'], COL['p10'], COL['p9'], COL['p8'], COL['p7'], COL['pmasc'],
          COL['t11'], COL['t10'], COL['t9'], COL['t8'], COL['t7'], COL['tmasc']]:
    ws.column_dimensions[get_column_letter(c)].width = 12
ws.column_dimensions[get_column_letter(COL['total_pagado'])].width = 14
ws.column_dimensions[get_column_letter(COL['acumulado_flag'])].width = 11
ws.column_dimensions[get_column_letter(COL['acumulado_monto'])].width = 16
ws.column_dimensions[get_column_letter(COL['hubo_ganador_11'])].width = 11
ws.column_dimensions[get_column_letter(COL['rev_num'])].width = 9
for c in range(COL['r_n1'], COL['r_n11'] + 1):
    ws.column_dimensions[get_column_letter(c)].width = 4.5
ws.column_dimensions[get_column_letter(COL['mascota_rev'])].width = 11
for c in [COL['rg11'], COL['rg10'], COL['rg9'], COL['rg8']]:
    ws.column_dimensions[get_column_letter(c)].width = 7
ws.column_dimensions[get_column_letter(COL['rtotal'])].width = 14
ws.column_dimensions[get_column_letter(COL['prox_num'])].width = 10
ws.column_dimensions[get_column_letter(COL['prox_fecha'])].width = 12
ws.column_dimensions[get_column_letter(COL['prox_dia'])].width = 10
ws.column_dimensions[get_column_letter(COL['prox_monto'])].width = 14
ws.column_dimensions[get_column_letter(COL['url'])].width = 35

print(f"Sheet 1 (Tabla Detallada) created with {len(DATA)} rows × {len(headers)} columns")

# ============================================================
# SHEET 2: Sorteos con Pozo Acumulado (filtered view)
# ============================================================
ws2 = wb.create_sheet("Pozos Acumulados")

# Filter records where pozo was accumulated (g11=0 and p11_ind > 500)
# Note: $500 is the base prize amount, anything higher indicates real accumulation
acumulados = [r for r in DATA if 11 in r['premios']
              and r['premios'][11].get('ganadores') == 0
              and r['premios'][11].get('premio_indiv') is not None
              and r['premios'][11]['premio_indiv'] > 500]

setup_sheet(ws2, title=f"Sorteos con Pozo Acumulado — Sin Ganador de 11 Aciertos ({len(acumulados)} sorteos)", last_col=10)

headers2 = ["Sorteo #", "Fecha", "Día", "Mascota", "Monto Pozo Acumulado", "Gan 10", "Total 10", "Gan 9", "Total 9", "Total Pagado Sorteo"]
for i, h in enumerate(headers2, 2):
    ws2.cell(row=4, column=i, value=h)
style_header_row(ws2, row_num=4, col_start=2, col_end=11)

for i, r in enumerate(acumulados):
    row_num = 5 + i
    p = r['premios']
    p11 = p.get(11, {})
    p10 = p.get(10, {})
    p9 = p.get(9, {})
    
    ws2.cell(row=row_num, column=2, value=r['sorteo_num'])
    if r['fecha']:
        try:
            dt = datetime.strptime(r['fecha'], '%Y-%m-%d')
            ws2.cell(row=row_num, column=3, value=dt).number_format = 'YYYY-MM-DD'
        except:
            ws2.cell(row=row_num, column=3, value=r['fecha'])
    ws2.cell(row=row_num, column=4, value=r.get('dia_semana', ''))
    ws2.cell(row=row_num, column=5, value=r.get('mascota', ''))
    ws2.cell(row=row_num, column=6, value=p11.get('premio_indiv')).number_format = '"$"#,##0.00'
    ws2.cell(row=row_num, column=7, value=p10.get('ganadores'))
    ws2.cell(row=row_num, column=8, value=p10.get('total')).number_format = '"$"#,##0.00'
    ws2.cell(row=row_num, column=9, value=p9.get('ganadores'))
    ws2.cell(row=row_num, column=10, value=p9.get('total')).number_format = '"$"#,##0.00'
    
    # Total pagado = total 10 + total 9 + total 8 + total 7 + total masc
    total = 0
    for ac in [10, 9, 8, 7]:
        if ac in p and p[ac].get('total'):
            total += p[ac]['total']
    if 'mascota' in p and p['mascota'].get('total'):
        total += p['mascota']['total']
    ws2.cell(row=row_num, column=11, value=total).number_format = '"$"#,##0.00'
    
    style_data_row(ws2, row_num=row_num, col_start=2, col_end=11, row_index=i)
    
    for col_idx in range(2, 12):
        cell = ws2.cell(row=row_num, column=col_idx)
        if col_idx in [2, 7, 9]:
            cell.alignment = align_number()
        elif col_idx in [3]:
            cell.alignment = align_date()
        elif col_idx in [4, 5]:
            cell.alignment = align_text()
        else:
            cell.alignment = align_number()

# Column widths
ws2.column_dimensions['A'].width = 3
ws2.column_dimensions['B'].width = 9
ws2.column_dimensions['C'].width = 12
ws2.column_dimensions['D'].width = 10
ws2.column_dimensions['E'].width = 12
ws2.column_dimensions['F'].width = 18
ws2.column_dimensions['G'].width = 9
ws2.column_dimensions['H'].width = 13
ws2.column_dimensions['I'].width = 9
ws2.column_dimensions['J'].width = 13
ws2.column_dimensions['K'].width = 16

print(f"Sheet 2 (Pozos Acumulados) created with {len(acumulados)} rows")

# ============================================================
# SHEET 3: Sorteos con Ganador 11 (jackpot winners)
# ============================================================
ws3 = wb.create_sheet("Ganadores 11 Aciertos")

ganadores_11 = [r for r in DATA if 11 in r['premios']
                and isinstance(r['premios'][11].get('ganadores'), int)
                and r['premios'][11]['ganadores'] > 0]

setup_sheet(ws3, title=f"Sorteos con Ganador de 11 Aciertos — ¡Pozo Mayor Ganado! ({len(ganadores_11)} sorteos)", last_col=10)

headers3 = ["Sorteo #", "Fecha", "Día", "Mascota", "Ganadores 11", "Premio por Ganador", "Total Pagado 11", "Números Ganadores", "Suma", "Pares/Impares"]
for i, h in enumerate(headers3, 2):
    ws3.cell(row=4, column=i, value=h)
style_header_row(ws3, row_num=4, col_start=2, col_end=11)

for i, r in enumerate(ganadores_11):
    row_num = 5 + i
    p = r['premios']
    p11 = p.get(11, {})
    
    ws3.cell(row=row_num, column=2, value=r['sorteo_num'])
    if r['fecha']:
        try:
            dt = datetime.strptime(r['fecha'], '%Y-%m-%d')
            ws3.cell(row=row_num, column=3, value=dt).number_format = 'YYYY-MM-DD'
        except:
            ws3.cell(row=row_num, column=3, value=r['fecha'])
    ws3.cell(row=row_num, column=4, value=r.get('dia_semana', ''))
    ws3.cell(row=row_num, column=5, value=r.get('mascota', ''))
    ws3.cell(row=row_num, column=6, value=p11.get('ganadores'))
    ws3.cell(row=row_num, column=7, value=p11.get('premio_indiv')).number_format = '"$"#,##0.00'
    ws3.cell(row=row_num, column=8, value=p11.get('total')).number_format = '"$"#,##0.00'
    nums_str = ' '.join(f'{n:02d}' for n in r['numeros'])
    ws3.cell(row=row_num, column=9, value=nums_str)
    ws3.cell(row=row_num, column=10, value=sum(r['numeros']))
    pares = sum(1 for n in r['numeros'] if n % 2 == 0)
    impares = sum(1 for n in r['numeros'] if n % 2 != 0)
    ws3.cell(row=row_num, column=11, value=f"{pares} par / {impares} impar")
    
    style_data_row(ws3, row_num=row_num, col_start=2, col_end=11, row_index=i)
    
    for col_idx in range(2, 12):
        cell = ws3.cell(row=row_num, column=col_idx)
        if col_idx in [2, 6, 10]:
            cell.alignment = align_number()
        elif col_idx == 3:
            cell.alignment = align_date()
        elif col_idx in [4, 5, 9, 11]:
            cell.alignment = align_text()
        else:
            cell.alignment = align_number()

ws3.column_dimensions['A'].width = 3
ws3.column_dimensions['B'].width = 9
ws3.column_dimensions['C'].width = 12
ws3.column_dimensions['D'].width = 10
ws3.column_dimensions['E'].width = 12
ws3.column_dimensions['F'].width = 13
ws3.column_dimensions['G'].width = 18
ws3.column_dimensions['H'].width = 18
ws3.column_dimensions['I'].width = 32
ws3.column_dimensions['J'].width = 7
ws3.column_dimensions['K'].width = 16

print(f"Sheet 3 (Ganadores 11) created with {len(ganadores_11)} rows")

# ============================================================
# SHEET 4: Frecuencia Números
# ============================================================
ws = wb.create_sheet("Frecuencia Números")

setup_sheet(ws, title="Análisis de Frecuencia — Números (1 al 25)", last_col=7)

number_counter = Counter()
last_appearance = {}
for r in DATA:
    for n in r['numeros']:
        number_counter[n] += 1
        last_appearance[n] = r['sorteo_num']

latest_sorteo = max(r['sorteo_num'] for r in DATA)

headers_freq = ["Número", "Frecuencia", "% Aparición", "Última Aparición", "Sorteos desde última", "Categoría"]
for i, h in enumerate(headers_freq, 2):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, row_num=4, col_start=2, col_end=7)

freq_data = []
for n in range(1, 26):
    freq = number_counter.get(n, 0)
    last_app = last_appearance.get(n)
    since_last = (latest_sorteo - last_app) if last_app else None
    pct = freq / len(DATA)
    freq_data.append((n, freq, pct, last_app, since_last))

for i, (n, freq, pct, last_app, since_last) in enumerate(freq_data):
    row_num = 5 + i
    if freq >= 130:
        category = "Caliente"
    elif freq <= 110:
        category = "Frio"
    else:
        category = "Moderado"
    ws.cell(row=row_num, column=2, value=n).number_format = '00'
    ws.cell(row=row_num, column=3, value=freq).number_format = FORMATS['integer']
    ws.cell(row=row_num, column=4, value=pct).number_format = FORMATS['percentage']
    ws.cell(row=row_num, column=5, value=last_app).number_format = FORMATS['integer']
    ws.cell(row=row_num, column=6, value=since_last).number_format = FORMATS['integer']
    ws.cell(row=row_num, column=7, value=category)
    style_data_row(ws, row_num=row_num, col_start=2, col_end=7, row_index=i)
    ws.cell(row=row_num, column=2).alignment = align_date()
    ws.cell(row=row_num, column=3).alignment = align_number()
    ws.cell(row=row_num, column=4).alignment = align_number()
    ws.cell(row=row_num, column=5).alignment = align_number()
    ws.cell(row=row_num, column=6).alignment = align_number()
    ws.cell(row=row_num, column=7).alignment = align_text()

ws.conditional_formatting.add(f'C5:C{4 + len(freq_data)}',
    ColorScaleRule(start_type='min', start_color='F8696B',
                   mid_type='percentile', mid_value=50, mid_color='FFEB84',
                   end_type='max', end_color='63BE7B'))
ws.conditional_formatting.add(f'D5:D{4 + len(freq_data)}',
    DataBarRule(start_type='min', end_type='max', color=PRIMARY, showValue=True))

# Chart
chart = create_bar_chart(width=24, height=12)
data_ref = Reference(ws, min_col=3, min_row=4, max_col=3, max_row=4 + len(freq_data))
cats_ref = Reference(ws, min_col=2, min_row=5, max_col=2, max_row=4 + len(freq_data))
chart.add_data(data_ref, titles_from_data=True)
chart.set_categories(cats_ref)
setup_chart_titles(chart, title="Frecuencia de Números (1-25)", y_title="Frecuencia", x_title="Número")
apply_chart_colors(chart)
chart.legend = None
ws.add_chart(chart, "I4")

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 10
ws.column_dimensions['C'].width = 14
ws.column_dimensions['D'].width = 14
ws.column_dimensions['E'].width = 18
ws.column_dimensions['F'].width = 18
ws.column_dimensions['G'].width = 14

print("Sheet 4 (Frecuencia Números) created")

# ============================================================
# SHEET 5: Frecuencia Mascotas
# ============================================================
ws = wb.create_sheet("Frecuencia Mascotas")

setup_sheet(ws, title="Análisis de Frecuencia — Mascotas", last_col=6)

mascot_counter = Counter()
for r in DATA:
    if r['mascota']:
        mascot_counter[r['mascota']] += 1

last_app_masc = {}
for r in DATA:
    if r['mascota']:
        last_app_masc[r['mascota']] = r['sorteo_num']

headers_masc = ["Mascota", "Frecuencia", "% Aparición", "Última Aparición", "Sorteos desde última"]
for i, h in enumerate(headers_masc, 2):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, row_num=4, col_start=2, col_end=6)

mascot_data = sorted(mascot_counter.items(), key=lambda x: -x[1])

for i, (mascot, freq) in enumerate(mascot_data):
    row_num = 5 + i
    last_app = last_app_masc.get(mascot)
    since_last = (latest_sorteo - last_app) if last_app else None
    pct = freq / len(DATA)
    ws.cell(row=row_num, column=2, value=mascot)
    ws.cell(row=row_num, column=3, value=freq).number_format = FORMATS['integer']
    ws.cell(row=row_num, column=4, value=pct).number_format = FORMATS['percentage']
    ws.cell(row=row_num, column=5, value=last_app).number_format = FORMATS['integer']
    ws.cell(row=row_num, column=6, value=since_last).number_format = FORMATS['integer']
    style_data_row(ws, row_num=row_num, col_start=2, col_end=6, row_index=i)
    ws.cell(row=row_num, column=2).alignment = align_text()
    ws.cell(row=row_num, column=3).alignment = align_number()
    ws.cell(row=row_num, column=4).alignment = align_number()
    ws.cell(row=row_num, column=5).alignment = align_number()
    ws.cell(row=row_num, column=6).alignment = align_number()

ws.conditional_formatting.add(f'C5:C{4 + len(mascot_data)}',
    ColorScaleRule(start_type='min', start_color='F8696B',
                   mid_type='percentile', mid_value=50, mid_color='FFEB84',
                   end_type='max', end_color='63BE7B'))
ws.conditional_formatting.add(f'D5:D{4 + len(mascot_data)}',
    DataBarRule(start_type='min', end_type='max', color=PRIMARY, showValue=True))

chart = create_bar_chart(chart_type='bar', width=24, height=14)
data_ref = Reference(ws, min_col=3, min_row=4, max_col=3, max_row=4 + len(mascot_data))
cats_ref = Reference(ws, min_col=2, min_row=5, max_col=2, max_row=4 + len(mascot_data))
chart.add_data(data_ref, titles_from_data=True)
chart.set_categories(cats_ref)
setup_chart_titles(chart, title="Frecuencia de Mascotas", y_title="Mascota", x_title="Frecuencia")
apply_chart_colors(chart)
chart.legend = None
ws.add_chart(chart, "H4")

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 16
ws.column_dimensions['C'].width = 14
ws.column_dimensions['D'].width = 14
ws.column_dimensions['E'].width = 18
ws.column_dimensions['F'].width = 18

print("Sheet 5 (Frecuencia Mascotas) created")

# ============================================================
# SHEET 6: Metodología y Fuentes
# ============================================================
ws = wb.create_sheet("Metodología")

setup_sheet(ws, title="Metodología y Fuentes de Datos", last_col=4)

row = 4
sections = [
    ("Cobertura de Datos", [
        ("Total de sorteos analizados", f"{len(DATA)} sorteos del Pozo Millonario"),
        ("Rango de sorteos", f"#{min(r['sorteo_num'] for r in DATA)} a #{max(r['sorteo_num'] for r in DATA)}"),
        ("Rango de fechas", f"{min(r['fecha'] for r in DATA if r['fecha'])} hasta {max(r['fecha'] for r in DATA if r['fecha'])}"),
        ("Años de historial", f"~5 años (octubre 2021 - septiembre 2026)"),
        ("Sorteos con Pozo Revancha", f"{sum(1 for r in DATA if r['revancha'].get('numeros'))} (desde enero 2023)"),
        ("Sorteos con datos completos de premios", f"{sum(1 for r in DATA if any(isinstance(v.get('ganadores'), int) for k, v in r['premios'].items() if k != 'mascota'))} de {len(DATA)}"),
    ]),
    ("Fuentes Consultadas", [
        ("Fuente principal - archivo histórico", "https://pozomillonario.info (sorteos 950 a 1257)"),
        ("Fuente oficial Lotería Nacional", "https://contenidos.loteria.com.ec/categoria/pozo/"),
        ("Fecha de extracción", datetime.now().strftime('%Y-%m-%d %H:%M')),
    ]),
    ("Estructura de la Tabla Detallada", [
        ("Total de columnas", "66 columnas con datos por sorteo"),
        ("Columnas de identificación", "Sorteo #, Fecha, Día, Año, Mes"),
        ("Columnas de números", "N1-N11 (números ganadores PM) + análisis (suma, pares, impares)"),
        ("Columnas de premios PM", "Ganadores, Premio individual y Total por cada nivel (11, 10, 9, 8, 7, mascota)"),
        ("Columnas de acumulación", "¿Pozo Acumulado? (SÍ/NO/S/D), Monto acumulado, ¿Hubo ganador 11?"),
        ("Columnas de Pozo Revancha", "Revancha #, N1-N11, Mascota, Ganadores por nivel"),
        ("Columnas de próximo sorteo", "Próximo #, fecha, día, monto estimado"),
        ("Columna URL fuente", "Enlace directo al sorteo en pozomillonario.info"),
    ]),
    ("Criterio de Acumulación", [
        ("¿Pozo Acumulado = SÍ", "Cuando NO hay ganador de 11 aciertos (ganadores=0) Y existe monto acumulado registrado"),
        ("¿Pozo Acumulado = NO", "Cuando SÍ hay ganador(es) de 11 aciertos (el pozo se repartió)"),
        ("¿Pozo Acumulado = S/D", "Sin datos suficientes para determinarlo (sorteo sin info de ganadores)"),
        ("Monto Pozo Acumulado", "Es el premio individual de 11 aciertos registrado en la fuente"),
    ]),
    ("Limitaciones y Notas", [
        ("Datos antiguos", "Algunos sorteos de 2021-2022 tienen solo datos de mascota, sin desglose completo de ganadores"),
        ("Sorteos recientes", "Los sorteos más recientes (post-2024) suelen mostrar solo montos fijos sin ganadores detallados"),
        ("Formato de números europeo", "Se convirtieron formatos como '953.551,00' → 953551.00"),
        ("Pozo Revancha", "Inició el 9 de enero de 2023 (sorteo PM #1014); no hay datos anteriores"),
        ("Errores en la fuente", "Algunos sorteos tienen números duplicados en la fuente (ej: sorteo 952 con dos veces el 25)"),
        ("Verificación", "Cruzamos datos entre pozomillonario.info y contenidos.loteria.com.ec (oficial)"),
    ]),
]

for section_title, items in sections:
    ws.cell(row=row, column=2, value=section_title).font = font_subheader()
    ws.cell(row=row, column=2).alignment = align_text()
    ws.row_dimensions[row].height = 24
    row += 1
    
    for label, value in items:
        ws.cell(row=row, column=2, value=label).font = font_body()
        ws.cell(row=row, column=2).alignment = align_text()
        ws.cell(row=row, column=3, value=value).font = font_body()
        ws.cell(row=row, column=3).alignment = align_text()
        ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=4)
        row += 1
    row += 1

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 38
ws.column_dimensions['C'].width = 35
ws.column_dimensions['D'].width = 35

print("Sheet 6 (Metodología) created")

# ============================================================
# Save workbook
# ============================================================
wb.properties.creator = "Z.ai"
wb.properties.title = "Pozo Millonario Ecuador - Tabla Detallada por Sorteo"

output_path = '/home/z/my-project/download/Pozo_Millonario_Tabla_Detallada.xlsx'
wb.save(output_path)

print(f"\n✓ Excel file saved to: {output_path}")
print(f"  File size: {os.path.getsize(output_path):,} bytes")
print(f"  Total sheets: {len(wb.sheetnames)}")
print(f"  Sheets: {wb.sheetnames}")

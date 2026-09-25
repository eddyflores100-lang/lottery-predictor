"""
Generate the comprehensive Excel file with all Pozo Millonario data.
Multiple sheets:
1. Resumen - Summary statistics
2. Sorteos PM - All Pozo Millonario draws
3. Sorteos Revancha - All Pozo Revancha draws
4. Frecuencia Números - Number frequency analysis
5. Frecuencia Mascotas - Mascot frequency analysis
6. Estadísticas - Additional statistics
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
from openpyxl.chart.label import DataLabelList
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule

# Use professional palette (deep blue - good for financial/data reports)
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
    # Same for revancha
    if 'premios' in r['revancha']:
        new_rev = {}
        for k, v in r['revancha']['premios'].items():
            if isinstance(k, str) and k.isdigit():
                new_rev[int(k)] = v
            else:
                new_rev[k] = v
        r['revancha']['premios'] = new_rev

# Sort by sorteo_num ascending (oldest first for table display)
DATA = sorted(DATA, key=lambda x: x['sorteo_num'])

print(f"Loaded {len(DATA)} sorteo records")
print(f"Date range: {min(r['fecha'] for r in DATA if r['fecha'])} to {max(r['fecha'] for r in DATA if r['fecha'])}")

# ============================================================
# Create workbook
# ============================================================
wb = Workbook()
wb.remove(wb.active)  # remove default sheet

# ============================================================
# Sheet 1: Resumen (Summary)
# ============================================================
ws = wb.create_sheet("Resumen")

# Compute summary stats
total_sorteos = len(DATA)
date_min = min(r['fecha'] for r in DATA if r['fecha'])
date_max = max(r['fecha'] for r in DATA if r['fecha'])
sorteo_min = min(r['sorteo_num'] for r in DATA)
sorteo_max = max(r['sorteo_num'] for r in DATA)

# Count records with revancha data
revancha_count = sum(1 for r in DATA if r['revancha'].get('numeros'))

# Count records with detailed prize data (numeric ganadores for any acierto, excluding mascot)
prize_data_count = 0
for r in DATA:
    p = r['premios']
    has_data = False
    for k, v in p.items():
        if k == 'mascota':
            continue
        if isinstance(v, dict) and isinstance(v.get('ganadores'), int):
            has_data = True
            break
    if has_data:
        prize_data_count += 1

# Year distribution
years = Counter()
for r in DATA:
    if r['fecha']:
        years[r['fecha'][:4]] += 1

# Mascot frequency
mascot_counter = Counter()
for r in DATA:
    if r['mascota']:
        mascot_counter[r['mascota']] += 1

# Number frequency
number_counter = Counter()
for r in DATA:
    for n in r['numeros']:
        number_counter[n] += 1

# Total ganadores by acierto (handle both int and string keys)
ganadores_by_acierto = defaultdict(int)
for r in DATA:
    p = r['premios']
    for k, v in p.items():
        # Normalize key to int if possible
        try:
            k_int = int(k) if isinstance(k, str) and k.isdigit() else (k if isinstance(k, int) else None)
        except (ValueError, TypeError):
            k_int = None
        if k_int is not None and isinstance(v, dict) and v.get('ganadores'):
            ganadores_by_acierto[k_int] += v['ganadores']

# Total monto pagado (where data available)
total_paid = 0
records_with_total = 0
for r in DATA:
    p = r['premios']
    row_total = 0
    has_data = False
    for k, v in p.items():
        if isinstance(v, dict) and v.get('total'):
            row_total += v['total']
            has_data = True
    if has_data:
        records_with_total += 1
        total_paid += row_total

# Build the summary sheet
last_col = 6  # B-G
setup_sheet(ws, title="Pozo Millonario — Resumen Ejecutivo", last_col=last_col)

# Row 4: Section "Información General"
ws.cell(row=4, column=2, value="Información General").font = font_subheader()
ws.cell(row=4, column=2).alignment = align_text()
ws.row_dimensions[4].height = 24

# KPI Cards (rows 5-8)
kpi_data = [
    ("Total de Sorteos Analizados", f"{total_sorteos:,}", "sorteos"),
    ("Rango de Sorteos", f"{sorteo_min} – {sorteo_max}", f"({sorteo_max - sorteo_min + 1} sorteos en el rango)"),
    ("Rango de Fechas", f"{date_min}", f"hasta {date_max}"),
    ("Años de Historial", f"{(datetime.strptime(date_max, '%Y-%m-%d') - datetime.strptime(date_min, '%Y-%m-%d')).days / 365.25:.2f}", "años"),
    ("Sorteos con Datos de Premios", f"{prize_data_count}", f"de {total_sorteos} ({prize_data_count/total_sorteos*100:.1f}%)"),
    ("Sorteos con Pozo Revancha", f"{revancha_count}", f"de {total_sorteos} ({revancha_count/total_sorteos*100:.1f}%)"),
]

row = 5
for label, value, sublabel in kpi_data:
    ws.cell(row=row, column=2, value=label).font = font_kpi_label()
    ws.cell(row=row, column=2).alignment = align_text()
    ws.cell(row=row, column=3, value=value).font = font_kpi()
    ws.cell(row=row, column=3).alignment = align_text()
    ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=last_col)
    ws.cell(row=row, column=4, value=sublabel).font = font_caption()
    ws.cell(row=row, column=4).alignment = align_text()
    ws.row_dimensions[row].height = 28
    row += 1

# Spacer
row += 1

# Section: Distribución por Año
ws.cell(row=row, column=2, value="Distribución por Año").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 24
row += 1

# Headers
year_headers = ["Año", "Sorteos", "% del Total", "Sorteos con Revancha"]
for i, h in enumerate(year_headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=2 + len(year_headers) - 1)
header_row_year = row
row += 1

# Data
for y in sorted(years.keys()):
    count = years[y]
    rev_count = sum(1 for r in DATA if r['fecha'] and r['fecha'][:4] == y and r['revancha'].get('numeros'))
    ws.cell(row=row, column=2, value=int(y)).alignment = align_date()
    ws.cell(row=row, column=3, value=count).alignment = align_number()
    ws.cell(row=row, column=3).number_format = FORMATS['integer']
    ws.cell(row=row, column=4, value=count/total_sorteos).alignment = align_number()
    ws.cell(row=row, column=4).number_format = FORMATS['percentage']
    ws.cell(row=row, column=5, value=rev_count).alignment = align_number()
    ws.cell(row=row, column=5).number_format = FORMATS['integer']
    style_data_row(ws, row_num=row, col_start=2, col_end=5, row_index=int(y) - 2020)
    row += 1

# Totals row
ws.cell(row=row, column=2, value="TOTAL").alignment = align_text()
ws.cell(row=row, column=3, value=f"=SUM(C{header_row_year+1}:C{row-1})").alignment = align_number()
ws.cell(row=row, column=3).number_format = FORMATS['integer']
ws.cell(row=row, column=4, value=f"=SUM(D{header_row_year+1}:D{row-1})").alignment = align_number()
ws.cell(row=row, column=4).number_format = FORMATS['percentage']
ws.cell(row=row, column=5, value=f"=SUM(E{header_row_year+1}:E{row-1})").alignment = align_number()
ws.cell(row=row, column=5).number_format = FORMATS['integer']
style_total_row(ws, row_num=row, col_start=2, col_end=5)
total_row_year = row
row += 2

# Section: Top 10 Números Más Frecuentes
ws.cell(row=row, column=2, value="Top 10 Números Más Frecuentes").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 24
row += 1

top_num_headers = ["Número", "Frecuencia", "% Aparición"]
for i, h in enumerate(top_num_headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=2 + len(top_num_headers) - 1)
row += 1

top_numbers = number_counter.most_common(10)
for i, (num, freq) in enumerate(top_numbers):
    ws.cell(row=row, column=2, value=num).alignment = align_date()
    ws.cell(row=row, column=2).number_format = '00'
    ws.cell(row=row, column=3, value=freq).alignment = align_number()
    ws.cell(row=row, column=3).number_format = FORMATS['integer']
    ws.cell(row=row, column=4, value=freq/total_sorteos).alignment = align_number()
    ws.cell(row=row, column=4).number_format = FORMATS['percentage']
    style_data_row(ws, row_num=row, col_start=2, col_end=4, row_index=i)
    row += 1

row += 1

# Section: Top 10 Mascotas Más Frecuentes
ws.cell(row=row, column=2, value="Top 10 Mascotas Más Frecuentes").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 24
row += 1

top_masc_headers = ["Mascota", "Frecuencia", "% Aparición"]
for i, h in enumerate(top_masc_headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=2 + len(top_masc_headers) - 1)
row += 1

top_mascots = mascot_counter.most_common(10)
for i, (mascot, freq) in enumerate(top_mascots):
    ws.cell(row=row, column=2, value=mascot).alignment = align_text()
    ws.cell(row=row, column=3, value=freq).alignment = align_number()
    ws.cell(row=row, column=3).number_format = FORMATS['integer']
    ws.cell(row=row, column=4, value=freq/total_sorteos).alignment = align_number()
    ws.cell(row=row, column=4).number_format = FORMATS['percentage']
    style_data_row(ws, row_num=row, col_start=2, col_end=4, row_index=i)
    row += 1

row += 2

# Notes/source
ws.cell(row=row, column=2, value="Fuente de datos:").font = font_caption()
ws.cell(row=row, column=3, value="Lotería Nacional del Ecuador (vía pozomillonario.info y contenidos.loteria.com.ec)").font = font_caption()
ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=last_col)
row += 1
ws.cell(row=row, column=2, value="Fecha de extracción:").font = font_caption()
ws.cell(row=row, column=3, value=datetime.now().strftime('%Y-%m-%d %H:%M')).font = font_caption()
ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=last_col)
row += 1
ws.cell(row=row, column=2, value="Nota:").font = font_caption()
ws.cell(row=row, column=3, value="Algunos sorteos antiguos no tienen datos detallados de ganadores/premios (placeholder).").font = font_caption()
ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=last_col)

# Column widths
ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 32
ws.column_dimensions['C'].width = 18
ws.column_dimensions['D'].width = 16
ws.column_dimensions['E'].width = 22
ws.column_dimensions['F'].width = 18
ws.column_dimensions['G'].width = 18

print("Sheet 1 (Resumen) created")

# ============================================================
# Sheet 2: Sorteos PM (All Pozo Millonario draws)
# ============================================================
ws = wb.create_sheet("Sorteos PM")

# Headers
headers_pm = [
    "Sorteo #", "Fecha", "Día", 
    "N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8", "N9", "N10", "N11",
    "Mascota",
    "Gan 11", "Premio 11", "Total 11",
    "Gan 10", "Premio 10", "Total 10",
    "Gan 9", "Premio 9", "Total 9",
    "Gan 8", "Premio 8", "Total 8",
    "Gan 7", "Premio 7", "Total 7",
    "Gan Masc", "Premio Masc", "Total Masc",
    "Total Pagado"
]
last_col = len(headers_pm) + 1  # +1 because we start at column B

setup_sheet(ws, title=f"Pozo Millonario — Histórico de Sorteos ({total_sorteos} sorteos, {date_min} a {date_max})", last_col=last_col)

# Write headers at row 4
for i, h in enumerate(headers_pm, 2):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, row_num=4, col_start=2, col_end=last_col)

# Write data
for i, r in enumerate(DATA):
    row_num = 5 + i
    p = r['premios']
    rev = r['revancha']
    
    # Sorteo number
    ws.cell(row=row_num, column=2, value=r['sorteo_num'])
    # Date
    if r['fecha']:
        try:
            dt = datetime.strptime(r['fecha'], '%Y-%m-%d')
            ws.cell(row=row_num, column=3, value=dt).number_format = 'YYYY-MM-DD'
        except:
            ws.cell(row=row_num, column=3, value=r['fecha'])
    # Day of week
    ws.cell(row=row_num, column=4, value=r.get('dia_semana', ''))
    # Numbers N1-N11
    nums = r['numeros']
    for j in range(11):
        if j < len(nums):
            ws.cell(row=row_num, column=5+j, value=nums[j]).number_format = '00'
    # Mascot
    ws.cell(row=row_num, column=16, value=r.get('mascota', ''))
    
    # Prize columns - acierto 11
    p11 = p.get(11, {})
    ws.cell(row=row_num, column=17, value=p11.get('ganadores'))
    ws.cell(row=row_num, column=18, value=p11.get('premio_indiv')).number_format = '"$"#,##0.00'
    ws.cell(row=row_num, column=19, value=p11.get('total')).number_format = '"$"#,##0.00'
    # acierto 10
    p10 = p.get(10, {})
    ws.cell(row=row_num, column=20, value=p10.get('ganadores'))
    ws.cell(row=row_num, column=21, value=p10.get('premio_indiv')).number_format = '"$"#,##0.00'
    ws.cell(row=row_num, column=22, value=p10.get('total')).number_format = '"$"#,##0.00'
    # acierto 9
    p9 = p.get(9, {})
    ws.cell(row=row_num, column=23, value=p9.get('ganadores'))
    ws.cell(row=row_num, column=24, value=p9.get('premio_indiv')).number_format = '"$"#,##0.00'
    ws.cell(row=row_num, column=25, value=p9.get('total')).number_format = '"$"#,##0.00'
    # acierto 8
    p8 = p.get(8, {})
    ws.cell(row=row_num, column=26, value=p8.get('ganadores'))
    ws.cell(row=row_num, column=27, value=p8.get('premio_indiv')).number_format = '"$"#,##0.00'
    ws.cell(row=row_num, column=28, value=p8.get('total')).number_format = '"$"#,##0.00'
    # acierto 7
    p7 = p.get(7, {})
    ws.cell(row=row_num, column=29, value=p7.get('ganadores'))
    ws.cell(row=row_num, column=30, value=p7.get('premio_indiv')).number_format = '"$"#,##0.00'
    ws.cell(row=row_num, column=31, value=p7.get('total')).number_format = '"$"#,##0.00'
    # Mascot prize
    pm = p.get('mascota', {})
    ws.cell(row=row_num, column=32, value=pm.get('ganadores'))
    ws.cell(row=row_num, column=33, value=pm.get('premio_indiv')).number_format = '"$"#,##0.00'
    ws.cell(row=row_num, column=34, value=pm.get('total')).number_format = '"$"#,##0.00'
    # Total paid (formula)
    ws.cell(row=row_num, column=35, value=f"=IFERROR(SUM(I{row_num},L{row_num},O{row_num},R{row_num},U{row_num},X{row_num}),0)").number_format = '"$"#,##0.00'
    # Wait - let me recompute column letters
    # Column 19 = S (11 total)
    # Column 22 = V (10 total)
    # Column 25 = Y (9 total)
    # Column 28 = AB (8 total)
    # Column 31 = AE (7 total)
    # Column 34 = AH (mascot total)
    # Total paid = sum of these
    ws.cell(row=row_num, column=35, value=f"=IFERROR(SUM(S{row_num},V{row_num},Y{row_num},AB{row_num},AE{row_num},AH{row_num}),0)").number_format = '"$"#,##0.00'
    
    # Style data row
    style_data_row(ws, row_num=row_num, col_start=2, col_end=last_col, row_index=i)
    
    # Set alignment for numeric columns
    for col in range(2, last_col + 1):
        cell = ws.cell(row=row_num, column=col)
        if col in [2, 3, 4]:  # sorteo, date, day
            cell.alignment = align_date() if col != 4 else align_text()
        elif col == 16:  # mascot
            cell.alignment = align_text()
        elif col in range(5, 16):  # N1-N11
            cell.alignment = align_date()
        else:  # prize columns
            cell.alignment = align_number()

# Freeze panes
ws.freeze_panes = 'E5'

# Column widths
ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 9  # sorteo
ws.column_dimensions['C'].width = 12  # fecha
ws.column_dimensions['D'].width = 10  # dia
for col in range(5, 16):  # N1-N11
    ws.column_dimensions[get_column_letter(col)].width = 5
ws.column_dimensions[get_column_letter(16)].width = 12  # mascot
for col in range(17, 35):  # prize cols
    ws.column_dimensions[get_column_letter(col)].width = 11
ws.column_dimensions[get_column_letter(35)].width = 14  # total paid

print(f"Sheet 2 (Sorteos PM) created with {len(DATA)} rows")

# ============================================================
# Sheet 3: Sorteos Revancha
# ============================================================
ws = wb.create_sheet("Sorteos Revancha")

# Filter records with revancha data
revancha_data = [r for r in DATA if r['revancha'].get('numeros')]
print(f"Revancha records: {len(revancha_data)}")

headers_rev = [
    "Sorteo PM #", "Fecha PM", "Día",
    "Sorteo Revancha #",
    "R N1", "R N2", "R N3", "R N4", "R N5", "R N6", "R N7", "R N8", "R N9", "R N10", "R N11",
    "Mascota Revancha",
    "Gan 11", "Premio 11", "Total 11",
    "Gan 10", "Premio 10", "Total 10",
    "Gan 9", "Premio 9", "Total 9",
    "Gan 8", "Premio 8", "Total 8",
    "Total Pagado"
]
last_col = len(headers_rev) + 1

setup_sheet(ws, title=f"Pozo Revancha — Histórico de Sorteos ({len(revancha_data)} sorteos con datos disponibles)", last_col=last_col)

for i, h in enumerate(headers_rev, 2):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, row_num=4, col_start=2, col_end=last_col)

for i, r in enumerate(revancha_data):
    row_num = 5 + i
    rev = r['revancha']
    
    ws.cell(row=row_num, column=2, value=r['sorteo_num'])
    if r['fecha']:
        try:
            dt = datetime.strptime(r['fecha'], '%Y-%m-%d')
            ws.cell(row=row_num, column=3, value=dt).number_format = 'YYYY-MM-DD'
        except:
            ws.cell(row=row_num, column=3, value=r['fecha'])
    ws.cell(row=row_num, column=4, value=r.get('dia_semana', ''))
    ws.cell(row=row_num, column=5, value=rev.get('sorteo_num'))
    
    # Revancha numbers (they're stored as strings)
    nums = rev.get('numeros', [])
    for j in range(11):
        if j < len(nums):
            try:
                n = int(nums[j])
                ws.cell(row=row_num, column=6+j, value=n).number_format = '00'
            except:
                ws.cell(row=row_num, column=6+j, value=nums[j])
    
    ws.cell(row=row_num, column=17, value=rev.get('mascota', ''))
    
    # Prize columns
    p = rev.get('premios', {})
    p11 = p.get(11, {})
    ws.cell(row=row_num, column=18, value=p11.get('ganadores'))
    ws.cell(row=row_num, column=19, value=p11.get('premio_indiv')).number_format = '"$"#,##0.00'
    ws.cell(row=row_num, column=20, value=p11.get('total')).number_format = '"$"#,##0.00'
    
    p10 = p.get(10, {})
    ws.cell(row=row_num, column=21, value=p10.get('ganadores'))
    ws.cell(row=row_num, column=22, value=p10.get('premio_indiv')).number_format = '"$"#,##0.00'
    ws.cell(row=row_num, column=23, value=p10.get('total')).number_format = '"$"#,##0.00'
    
    p9 = p.get(9, {})
    ws.cell(row=row_num, column=24, value=p9.get('ganadores'))
    ws.cell(row=row_num, column=25, value=p9.get('premio_indiv')).number_format = '"$"#,##0.00'
    ws.cell(row=row_num, column=26, value=p9.get('total')).number_format = '"$"#,##0.00'
    
    p8 = p.get(8, {})
    ws.cell(row=row_num, column=27, value=p8.get('ganadores'))
    ws.cell(row=row_num, column=28, value=p8.get('premio_indiv')).number_format = '"$"#,##0.00'
    ws.cell(row=row_num, column=29, value=p8.get('total')).number_format = '"$"#,##0.00'
    
    # Total pagado
    # T = col 20, W = col 23, Z = col 26, AC = col 29
    ws.cell(row=row_num, column=30, value=f"=IFERROR(SUM(T{row_num},W{row_num},Z{row_num},AC{row_num}),0)").number_format = '"$"#,##0.00'
    
    style_data_row(ws, row_num=row_num, col_start=2, col_end=last_col, row_index=i)
    
    # Alignment
    for col in range(2, last_col + 1):
        cell = ws.cell(row=row_num, column=col)
        if col in [2, 3, 4, 5]:
            cell.alignment = align_date() if col != 4 else align_text()
        elif col == 17:
            cell.alignment = align_text()
        elif col in range(6, 17):
            cell.alignment = align_date()
        else:
            cell.alignment = align_number()

ws.freeze_panes = 'F5'

# Column widths
ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 10
ws.column_dimensions['C'].width = 12
ws.column_dimensions['D'].width = 10
ws.column_dimensions['E'].width = 12
for col in range(6, 17):
    ws.column_dimensions[get_column_letter(col)].width = 5
ws.column_dimensions[get_column_letter(17)].width = 14
for col in range(18, 30):
    ws.column_dimensions[get_column_letter(col)].width = 11
ws.column_dimensions[get_column_letter(30)].width = 14

print(f"Sheet 3 (Sorteos Revancha) created with {len(revancha_data)} rows")

# ============================================================
# Sheet 4: Frecuencia Números
# ============================================================
ws = wb.create_sheet("Frecuencia Números")

setup_sheet(ws, title="Análisis de Frecuencia — Números (1 al 25)", last_col=6)

headers_freq = ["Número", "Frecuencia", "% Aparición", "Última Aparición", "Sorteos desde última", "Categoría"]
for i, h in enumerate(headers_freq, 2):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, row_num=4, col_start=2, col_end=7)

# Build last appearance map
last_appearance = {}
for r in DATA:
    for n in r['numeros']:
        last_appearance[n] = r['sorteo_num']  # Will get the latest one

latest_sorteo = max(r['sorteo_num'] for r in DATA)

# Compute frequency and write rows
freq_data = []
for n in range(1, 26):
    freq = number_counter.get(n, 0)
    last_app = last_appearance.get(n)
    since_last = (latest_sorteo - last_app) if last_app else None
    pct = freq / total_sorteos
    freq_data.append((n, freq, pct, last_app, since_last))

# Sort by frequency descending for the chart, but write sorted by number
for i, (n, freq, pct, last_app, since_last) in enumerate(freq_data):
    row_num = 5 + i
    
    # Determine category: hot (top 8), warm (mid 9), cold (bottom 8)
    if freq >= 130:
        category = "🔥 Caliente"
    elif freq <= 90:
        category = "❄️ Frío"
    else:
        category = "Moderado"
    
    ws.cell(row=row_num, column=2, value=n).number_format = '00'
    ws.cell(row=row_num, column=3, value=freq).number_format = FORMATS['integer']
    ws.cell(row=row_num, column=4, value=pct).number_format = FORMATS['percentage']
    ws.cell(row=row_num, column=5, value=last_app).number_format = FORMATS['integer']
    ws.cell(row=row_num, column=6, value=since_last).number_format = FORMATS['integer']
    ws.cell(row=row_num, column=7, value=category)
    
    style_data_row(ws, row_num=row_num, col_start=2, col_end=7, row_index=i)
    
    # Alignment
    ws.cell(row=row_num, column=2).alignment = align_date()
    ws.cell(row=row_num, column=3).alignment = align_number()
    ws.cell(row=row_num, column=4).alignment = align_number()
    ws.cell(row=row_num, column=5).alignment = align_number()
    ws.cell(row=row_num, column=6).alignment = align_number()
    ws.cell(row=row_num, column=7).alignment = align_text()

# Add color scale on frequency column
ws.conditional_formatting.add(f'C5:C{5 + len(freq_data) - 1}',
    ColorScaleRule(
        start_type='min', start_color='F8696B',
        mid_type='percentile', mid_value=50, mid_color='FFEB84',
        end_type='max', end_color='63BE7B'))

# Add data bar on percentage column
ws.conditional_formatting.add(f'D5:D{5 + len(freq_data) - 1}',
    DataBarRule(start_type='min', end_type='max', color=PRIMARY, showValue=True))

# Add chart
chart = create_bar_chart(width=24, height=12)
data_ref = Reference(ws, min_col=3, min_row=4, max_col=3, max_row=4 + len(freq_data))
cats_ref = Reference(ws, min_col=2, min_row=5, max_col=2, max_row=4 + len(freq_data))
chart.add_data(data_ref, titles_from_data=True)
chart.set_categories(cats_ref)
setup_chart_titles(chart, title="Frecuencia de Números (1-25)", y_title="Frecuencia", x_title="Número")
apply_chart_colors(chart)
chart.legend = None
ws.add_chart(chart, f"I4")

# Column widths
ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 10
ws.column_dimensions['C'].width = 14
ws.column_dimensions['D'].width = 14
ws.column_dimensions['E'].width = 18
ws.column_dimensions['F'].width = 18
ws.column_dimensions['G'].width = 14

print("Sheet 4 (Frecuencia Números) created")

# ============================================================
# Sheet 5: Frecuencia Mascotas
# ============================================================
ws = wb.create_sheet("Frecuencia Mascotas")

setup_sheet(ws, title="Análisis de Frecuencia — Mascotas", last_col=5)

headers_masc = ["Mascota", "Frecuencia", "% Aparición", "Última Aparición", "Sorteos desde última"]
for i, h in enumerate(headers_masc, 2):
    ws.cell(row=4, column=i, value=h)
style_header_row(ws, row_num=4, col_start=2, col_end=6)

# Build last appearance map for mascots
last_app_masc = {}
for r in DATA:
    if r['mascota']:
        last_app_masc[r['mascota']] = r['sorteo_num']

# Sort mascots by frequency desc
mascot_data = sorted(mascot_counter.items(), key=lambda x: -x[1])

for i, (mascot, freq) in enumerate(mascot_data):
    row_num = 5 + i
    last_app = last_app_masc.get(mascot)
    since_last = (latest_sorteo - last_app) if last_app else None
    pct = freq / total_sorteos
    
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

# Color scale
ws.conditional_formatting.add(f'C5:C{5 + len(mascot_data) - 1}',
    ColorScaleRule(
        start_type='min', start_color='F8696B',
        mid_type='percentile', mid_value=50, mid_color='FFEB84',
        end_type='max', end_color='63BE7B'))

ws.conditional_formatting.add(f'D5:D{5 + len(mascot_data) - 1}',
    DataBarRule(start_type='min', end_type='max', color=PRIMARY, showValue=True))

# Add chart
chart = create_bar_chart(chart_type='bar', width=24, height=14)
data_ref = Reference(ws, min_col=3, min_row=4, max_col=3, max_row=4 + len(mascot_data))
cats_ref = Reference(ws, min_col=2, min_row=5, max_col=2, max_row=4 + len(mascot_data))
chart.add_data(data_ref, titles_from_data=True)
chart.set_categories(cats_ref)
setup_chart_titles(chart, title="Frecuencia de Mascotas", y_title="Mascota", x_title="Frecuencia")
apply_chart_colors(chart)
chart.legend = None
ws.add_chart(chart, f"H4")

# Column widths
ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 16
ws.column_dimensions['C'].width = 14
ws.column_dimensions['D'].width = 14
ws.column_dimensions['E'].width = 18
ws.column_dimensions['F'].width = 18

print("Sheet 5 (Frecuencia Mascotas) created")

# ============================================================
# Sheet 6: Estadísticas
# ============================================================
ws = wb.create_sheet("Estadísticas")

setup_sheet(ws, title="Estadísticas Adicionales y Análisis", last_col=6)

row = 4

# Section: Estadísticas Generales
ws.cell(row=row, column=2, value="Estadísticas Generales").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 24
row += 1

# Headers
for i, h in enumerate(["Métrica", "Valor", "Comentario"], 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=4)
row += 1

stats_data = [
    ("Total de sorteos analizados", total_sorteos, "Datos desde sorteo 950 (Oct 2021) hasta sorteo 1257 (Sept 2026)"),
    ("Promedio de sorteos por año (últimos 3 años)", round(years.get('2024', 0) + years.get('2025', 0) + years.get('2026', 0)) // 3, "Aproximadamente 2 sorteos por semana (lunes y jueves)"),
    ("Número más frecuente", top_numbers[0][0] if top_numbers else None, f"Apareció {top_numbers[0][1]} veces ({top_numbers[0][1]/total_sorteos*100:.1f}%)" if top_numbers else ""),
    ("Número menos frecuente", number_counter.most_common()[-1][0] if number_counter else None, f"Apareció {number_counter.most_common()[-1][1]} veces ({number_counter.most_common()[-1][1]/total_sorteos*100:.1f}%)" if number_counter else ""),
    ("Mascota más frecuente", top_mascots[0][0] if top_mascots else None, f"Apareció {top_mascots[0][1]} veces ({top_mascots[0][1]/total_sorteos*100:.1f}%)" if top_mascots else ""),
    ("Mascota menos frecuente", mascot_counter.most_common()[-1][0] if mascot_counter else None, f"Apareció {mascot_counter.most_common()[-1][1]} veces" if mascot_counter else ""),
    ("Total ganadores 11 aciertos", ganadores_by_acierto.get(11, 0), "Pozo mayor acumulado (varía según sorteo)"),
    ("Total ganadores 10 aciertos", ganadores_by_acierto.get(10, 0), "Premio de consolación $500 USD c/u"),
    ("Total ganadores 9 aciertos", ganadores_by_acierto.get(9, 0), "Premio $10 USD c/u"),
    ("Total ganadores 8 aciertos", ganadores_by_acierto.get(8, 0), "Premio $2 USD c/u"),
    ("Total ganadores 7 aciertos", ganadores_by_acierto.get(7, 0), "Premio $1 USD c/u"),
]

for i, (metric, value, comment) in enumerate(stats_data):
    ws.cell(row=row, column=2, value=metric).alignment = align_text()
    ws.cell(row=row, column=3, value=value).alignment = align_number() if isinstance(value, (int, float)) else align_text()
    if isinstance(value, (int, float)):
        ws.cell(row=row, column=3).number_format = FORMATS['integer']
    ws.cell(row=row, column=4, value=comment).alignment = align_text()
    ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=6)
    style_data_row(ws, row_num=row, col_start=2, col_end=6, row_index=i)
    row += 1

row += 1

# Section: Análisis por Día de la Semana
ws.cell(row=row, column=2, value="Análisis por Día de la Semana").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 24
row += 1

for i, h in enumerate(["Día", "Sorteos", "% del Total", "Promedio Números Pares", "Promedio Números Impares"], 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=6)
row += 1

day_stats = defaultdict(lambda: {'count': 0, 'pares': 0, 'impares': 0})
for r in DATA:
    dia = r.get('dia_semana', '').lower()
    if dia:
        day_stats[dia]['count'] += 1
        for n in r['numeros']:
            if n % 2 == 0:
                day_stats[dia]['pares'] += 1
            else:
                day_stats[dia]['impares'] += 1

day_order = ['lunes', 'martes', 'miércoles', 'miercoles', 'jueves', 'viernes', 'sábado', 'sabado', 'domingo']
seen_days = set()
for i, dia in enumerate(day_order):
    if dia in day_stats and dia not in seen_days:
        stats = day_stats[dia]
        if stats['count'] == 0:
            continue
        avg_pares = stats['pares'] / stats['count']
        avg_impares = stats['impares'] / stats['count']
        # Normalize name
        if dia == 'miercoles':
            display = 'miércoles'
        elif dia == 'sabado':
            display = 'sábado'
        else:
            display = dia
        ws.cell(row=row, column=2, value=display.capitalize()).alignment = align_text()
        ws.cell(row=row, column=3, value=stats['count']).alignment = align_number()
        ws.cell(row=row, column=3).number_format = FORMATS['integer']
        ws.cell(row=row, column=4, value=stats['count']/total_sorteos).alignment = align_number()
        ws.cell(row=row, column=4).number_format = FORMATS['percentage']
        ws.cell(row=row, column=5, value=round(avg_pares, 2)).alignment = align_number()
        ws.cell(row=row, column=5).number_format = FORMATS['decimal_2']
        ws.cell(row=row, column=6, value=round(avg_impares, 2)).alignment = align_number()
        ws.cell(row=row, column=6).number_format = FORMATS['decimal_2']
        style_data_row(ws, row_num=row, col_start=2, col_end=6, row_index=i)
        seen_days.add(dia)
        row += 1

row += 1

# Section: Top 10 Sorteos con más ganadores de 11 aciertos
ws.cell(row=row, column=2, value="Top 10 Sorteos con más Ganadores de 11 Aciertos").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
ws.row_dimensions[row].height = 24
row += 1

for i, h in enumerate(["Sorteo #", "Fecha", "Ganadores 11", "Premio Individual", "Total Pagado 11"], 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=6)
row += 1

# Find top 10 by 11-acierto ganadores
top_11 = []
for r in DATA:
    p = r['premios']
    if 11 in p and p[11].get('ganadores') is not None and p[11]['ganadores'] > 0:
        top_11.append((r['sorteo_num'], r['fecha'], p[11]['ganadores'], p[11].get('premio_indiv'), p[11].get('total')))

top_11.sort(key=lambda x: -x[2])
for i, (sn, fecha, gan, prem, total) in enumerate(top_11[:10]):
    ws.cell(row=row, column=2, value=sn).alignment = align_number()
    ws.cell(row=row, column=2).number_format = FORMATS['integer']
    if fecha:
        try:
            dt = datetime.strptime(fecha, '%Y-%m-%d')
            ws.cell(row=row, column=3, value=dt).number_format = 'YYYY-MM-DD'
        except:
            ws.cell(row=row, column=3, value=fecha)
    ws.cell(row=row, column=3).alignment = align_date()
    ws.cell(row=row, column=4, value=gan).alignment = align_number()
    ws.cell(row=row, column=4).number_format = FORMATS['integer']
    ws.cell(row=row, column=5, value=prem).alignment = align_number()
    ws.cell(row=row, column=5).number_format = '"$"#,##0.00'
    ws.cell(row=row, column=6, value=total).alignment = align_number()
    ws.cell(row=row, column=6).number_format = '"$"#,##0.00'
    style_data_row(ws, row_num=row, col_start=2, col_end=6, row_index=i)
    row += 1

row += 2

# Notes
ws.cell(row=row, column=2, value="Metodología y Notas:").font = font_subheader()
ws.cell(row=row, column=2).alignment = align_text()
row += 1
notes = [
    "• Datos extraídos de pozomillonario.info (archivo histórico) y contenidos.loteria.com.ec (fuente oficial).",
    "• Se incluyeron todos los sorteos disponibles con números ganadores (excluyendo sorteos futuros no realizados).",
    "• Para sorteos antiguos (anteriores a 2024), algunos campos de ganadores/premios pueden estar vacíos porque la fuente no los registra.",
    "• Las frecuencias se calcularon sobre el total de sorteos analizados.",
    "• Las categorías 'Caliente/Frío' se basan en percentiles de frecuencia (top 30% = caliente, bottom 30% = frío).",
    "• El porcentaje de aparición se calcula como: (frecuencia / total sorteos) × 100.",
    "• El Pozo Revancha inició el 9 de enero de 2023 (sorteo PM 1014), por lo que no hay datos anteriores.",
    "• Para sorteos recientes (después de enero 2025), los datos de Pozo Revancha pueden no estar completos en la fuente.",
]
for note in notes:
    ws.cell(row=row, column=2, value=note).font = font_caption()
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=6)
    row += 1

# Column widths
ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 36
ws.column_dimensions['C'].width = 16
ws.column_dimensions['D'].width = 16
ws.column_dimensions['E'].width = 22
ws.column_dimensions['F'].width = 22
ws.column_dimensions['G'].width = 18

print("Sheet 6 (Estadísticas) created")

# ============================================================
# Save workbook
# ============================================================
wb.properties.creator = "Z.ai"
wb.properties.title = "Pozo Millonario - Análisis Histórico"

output_path = '/home/z/my-project/download/Pozo_Millonario_Historico.xlsx'
os.makedirs(os.path.dirname(output_path), exist_ok=True)
wb.save(output_path)

print(f"\n✓ Excel file saved to: {output_path}")
print(f"  File size: {os.path.getsize(output_path):,} bytes")
print(f"  Total sheets: {len(wb.sheetnames)}")
print(f"  Sheets: {wb.sheetnames}")

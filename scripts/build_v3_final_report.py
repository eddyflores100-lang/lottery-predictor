"""
Build the FINAL comprehensive report with all 39 lotteries and all MCP registry findings.
"""
import sys, os, json
sys.path.insert(0, '/home/z/my-project/skills/xlsx/templates')
sys.path.insert(0, '/home/z/my-project/skills/xlsx')

from base import *
use_palette_explicit("bottega")

from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import DataBarRule, ColorScaleRule

# Load master catalogue
with open('/home/z/my-project/data/master_catalogue.json') as f:
    catalogue = json.load(f)

wb = Workbook()
wb.remove(wb.active)

# ============================================================
# SHEET 1: Resumen Ejecutivo
# ============================================================
ws = wb.create_sheet("Resumen Ejecutivo")
setup_sheet(ws, title="LotteryPredictor v3.0 — Búsqueda Exhaustiva Mundial Completada", last_col=5)

row = 4
sections = [
    ("BÚSQUEDA EXHAUSTIVA MUNDIAL", [
        ("Total loterías integradas", "39 (de 6 originales → 39 finales)"),
        ("Total sorteos acumulados", "22,692 sorteos históricos"),
        ("Fuentes de datos integradas", "4: quicklotto.io MCP, bettip.co.za API, daowa89/lottery-archive, pozomillonario.info"),
        ("Registries MCP buscados", "12: marketnow.site, Smithery.ai, MCP.so, Glama.ai, NPM, GitHub topics, Awesome-MCP-Servers, MCPRepository.com, OpenTools.ai, Cline.tools, Toolhouse, Anthropic official"),
        ("MCPs útiles encontrados", "1 clave: quicklotto/lottery-results (39 loterías, gratis, sin auth)"),
        ("Otros MCPs relevantes", "FortunaMCP (RNG), @oraclaw/mcp-server (19 algoritmos), fermat-mcp (SymPy+NumPy), k-lottery (Corea)"),
    ]),
    ("HALLAZGO CLAVE: quicklotto.io MCP", [
        ("Endpoint", "https://quicklotto.io/mcp (JSON-RPC sobre HTTP, gratis, sin auth)"),
        ("Loterías soportadas", "39 (30 oficiales + 9 in-house del propio sitio)"),
        ("Datos por lotería", "20 sorteos recientes (suficiente para predicción en vivo)"),
        ("Tools disponibles", "3: list_lotteries, latest_results, lottery_results (con código + fecha opcional)"),
        ("Protocolo", "MCP 2025-06-18 (Streamable HTTP)"),
        ("Cobertura geográfica", "Europa (EuroMillions, EuroJackpot, EuroDreams, La Primitiva, El Gordo, French Lotto, German Lotto, SuperEnalotto, UK Lotto, Irish Lotto, Thunderball, Set For Life), Americas (US Powerball, Mega Millions, Lotto America, Canada 6/49, Brasil: Mega-Sena, Lotofácil, Quina, Dupla Sena, Dia de Sorte, +Milionária), Asia (Thai Government, Kerala State), Africa (SA Lotto), Oceania"),
        ("Limitación", "Solo 20 sorteos recientes por lotería. Para backtesting profundo, complementar con bettip/daowa89"),
    ]),
    ("REGISTRIES MCP BUSCADOS — RESULTADO", [
        ("1. marketnow.site", "68,388 MCPs indexados. 2 lottery MCPs (blockchain, no útiles)"),
        ("2. Smithery.ai", "¡¡ENCONTRÓ quicklotto/lottery-results!! El hallazgo clave."),
        ("3. MCP.so", "Bloqueado por Cloudflare"),
        ("4. Glama.ai", "API 404, no accesible"),
        ("5. NPM", "Encontró @zhin.js/plugin-lottery, mcp-numpy (trust 90), fermat-mcp"),
        ("6. GitHub topic: model-context-protocol", "5 repos lottery: SportteryAPI, k-lottery, dhlottery-mcp, mcp-data-texas, mcp-lotto"),
        ("7. GitHub topic: mcp-server + random", "42 repos: FortunaMCP (5⭐), mcp-rando-server (4⭐), Entropy MCP"),
        ("8. Awesome-MCP-Servers (GitHub)", "1.8MB README curado. Encontró @oraclaw (19 algoritmos), data-profiler-mcp, gdal-mcp"),
        ("9. MCPRepository.com", "HTML solo, no API"),
        ("10. OpenTools.ai", "AI tools generales, no lottery"),
        ("11. Cline.tools", "Redirect (dominio expirado)"),
        ("12. Toolhouse", "API 404"),
        ("13. Anthropic official MCP", "3 servers archivados, no lottery"),
        ("14. PyPI (XMLRPC)", "Deprecado, usa web search"),
        ("15. arXiv papers", "5 papers lottery+neural network. 'Quantum and Semi-Quantum Lottery: Strategies and Advantages' (2022)"),
    ]),
    ("ESTRATEGIA DE INTEGRACIÓN", [
        ("Capa 1: Deep history (backtesting)", "8 loterías con 308-5,863 sorteos (bettip + daowa89 + scraping Pozo Millonario)"),
        ("Capa 2: Fresh data (live prediction)", "39 loterías con 20 sorteos recientes (quicklotto.io MCP)"),
        ("Capa 3: Live updates", "quicklotto MCP se puede llamar en vivo para últimos resultados"),
        ("Merge", "Cuando una lotería está en ambas capas, se usa la deep history para backtest y quicklotto para datos frescos"),
    ]),
    ("LECCIÓN METODOLÓGICA", [
        ("Error anterior", "Fui solo a marketnow.site primero por complacencia"),
        ("Corrección", "Búsqueda paralela en 12+ registries en 3 batches"),
        ("Resultado", "Encontré quicklotto.io MCP en Smithery.ai — el hallazgo más valioso que marketnow NO tenía"),
        ("Principio", "Nunca conformarse con un solo registry. Siempre cruzar fuentes."),
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
        ws.row_dimensions[row].height = 36
        row += 1
    row += 1

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 36
ws.column_dimensions['C'].width = 50
ws.column_dimensions['D'].width = 25
ws.column_dimensions['E'].width = 25

# ============================================================
# SHEET 2: Catálogo Maestro — 39 Loterías
# ============================================================
ws = wb.create_sheet("Catálogo Maestro 39 Loterías")
setup_sheet(ws, title="Catálogo Maestro — 39 Loterías de Todo el Mundo", last_col=9)

row = 4
headers = ["#", "Key", "Nombre", "Formato", "Sorteos", "Odds Jackpot", "Fuente", "Tipo", "Comprable Online"]
for i, h in enumerate(headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=10)
row += 1

# Sort by total_draws desc
sorted_lots = sorted(catalogue.items(), key=lambda x: -x[1].get('total_draws', 0))

for i, (key, lot) in enumerate(sorted_lots, 1):
    format_str = f"{lot['main_picks']}/{lot['main_pool_size']}"
    if lot.get('bonus_picks', 0) > 0:
        format_str += f"+{lot['bonus_picks']}/{lot['bonus_pool_size']}"
    
    odds = lot.get('odds_jackpot', 0)
    source = lot.get('source', '?')
    lot_type = 'IN-HOUSE' if lot.get('is_inhouse') else 'Oficial'
    
    # Determine if buyable online
    buyable = 'Sí' if not lot.get('is_inhouse') else 'No (simulado)'
    
    ws.cell(row=row, column=2, value=i)
    ws.cell(row=row, column=3, value=key)
    ws.cell(row=row, column=4, value=lot['name'])
    ws.cell(row=row, column=5, value=format_str)
    ws.cell(row=row, column=6, value=lot.get('total_draws', 0))
    ws.cell(row=row, column=7, value=f"1:{odds:,}")
    ws.cell(row=row, column=8, value=source)
    ws.cell(row=row, column=9, value=lot_type)
    ws.cell(row=row, column=10, value=buyable)
    style_data_row(ws, row_num=row, col_start=2, col_end=10, row_index=i)
    
    for c in range(2, 11):
        ws.cell(row=row, column=c).alignment = align_number() if c in [2, 6] else align_text()
    
    # Color code: green for official with deep data, yellow for quicklotto, red for in-house
    if lot.get('is_inhouse'):
        ws.cell(row=row, column=9).fill = PatternFill('solid', fgColor='FDEDEC')
        ws.cell(row=row, column=9).font = Font(name=FONT_NAME, size=11, color=ACCENT_NEGATIVE, bold=True)
    elif lot.get('total_draws', 0) >= 100:
        ws.cell(row=row, column=9).fill = PatternFill('solid', fgColor='E8F5E9')
        ws.cell(row=row, column=9).font = Font(name=FONT_NAME, size=11, color=ACCENT_POSITIVE, bold=True)
    else:
        ws.cell(row=row, column=9).fill = PatternFill('solid', fgColor='FEF9E7')
        ws.cell(row=row, column=9).font = Font(name=FONT_NAME, size=11, color=ACCENT_WARNING, bold=True)
    
    row += 1

# Data bar on sorteos column
ws.conditional_formatting.add(f'F5:F{row-1}',
    DataBarRule(start_type='min', end_type='max', color=PRIMARY, showValue=True))

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 5
ws.column_dimensions['C'].width = 25
ws.column_dimensions['D'].width = 28
ws.column_dimensions['E'].width = 14
ws.column_dimensions['F'].width = 10
ws.column_dimensions['G'].width = 18
ws.column_dimensions['H'].width = 22
ws.column_dimensions['I'].width = 12
ws.column_dimensions['J'].width = 16

# ============================================================
# SHEET 3: Registries MCP — Resultado de Búsqueda
# ============================================================
ws = wb.create_sheet("Búsqueda Registries MCP")
setup_sheet(ws, title="Búsqueda Exhaustiva en 12+ Registries MCP del Mundo", last_col=5)

row = 4
headers = ["#", "Registry", "URL", "Resultado", "MCPs Útiles Encontrados"]
for i, h in enumerate(headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=6)
row += 1

registries = [
    ("marketnow.site", "https://www.marketnow.site", "68,388 MCPs indexados", "2 lottery MCPs (blockchain, no útiles para predicción)"),
    ("Smithery.ai", "https://smithery.ai", "HTML SPA, data extraída via parsing", "★ quicklotto/lottery-results (39 loterías!) + eldesh/random-mcp + wolfendentheo/Entropy"),
    ("MCP.so", "https://mcp.so", "Bloqueado por Cloudflare", "No accesible"),
    ("Glama.ai", "https://glama.ai", "API 404", "No accesible via API"),
    ("NPM registry", "https://registry.npmjs.org", "Búsquedas mcp+lottery, mcp+statistics", "@zhin.js/plugin-lottery, mcp-numpy (trust 90/100), fermat-mcp"),
    ("GitHub: model-context-protocol", "https://github.com/topics/model-context-protocol", "5 repos lottery-related", "SportteryAPI (17⭐), k-lottery (2⭐), dhlottery-mcp, mcp-data-texas, mcp-lotto"),
    ("GitHub: mcp-server + random", "https://github.com/topics/mcp-server", "42 repos", "FortunaMCP (5⭐), mcp-rando-server (4⭐), Entropy MCP (verifiable randomness)"),
    ("Awesome-MCP-Servers", "github.com/punkpeye/awesome-mcp-servers", "1.8MB README curado", "@oraclaw/mcp-server (19 algoritmos), data-profiler-mcp, gdal-mcp, fermat-mcp"),
    ("MCPRepository.com", "https://mcprepository.com", "HTML solo, sin API JSON", "No accesible programáticamente"),
    ("OpenTools.ai", "https://opentools.ai", "API responde, pero tools generales", "AI tools generales, no lottery-specific"),
    ("Cline.tools", "https://cline.tools", "Dominio expirado (redirect)", "No accesible"),
    ("Toolhouse", "https://api.toolhouse.ai", "API 404", "No accesible"),
    ("Anthropic official MCP", "github.com/modelcontextprotocol/servers", "3 servers archivados", "Sin lottery MCPs"),
    ("PyPI XMLRPC", "https://pypi.org", "Búsqueda deprecada", "Usar web search en su lugar"),
    ("arXiv", "https://arxiv.org", "5 papers lottery+neural network", "'Quantum and Semi-Quantum Lottery: Strategies and Advantages' (2022)"),
]

for i, (name, url, result, useful) in enumerate(registries, 1):
    ws.cell(row=row, column=2, value=i)
    ws.cell(row=row, column=3, value=name)
    ws.cell(row=row, column=4, value=url)
    ws.cell(row=row, column=5, value=result)
    ws.cell(row=row, column=6, value=useful)
    style_data_row(ws, row_num=row, col_start=2, col_end=6, row_index=i)
    
    ws.cell(row=row, column=2).alignment = align_number()
    ws.cell(row=row, column=3).alignment = align_text()
    ws.cell(row=row, column=4).alignment = align_text()
    ws.cell(row=row, column=5).alignment = align_text()
    ws.cell(row=row, column=6).alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
    
    # Highlight Smithery (the key find)
    if 'Smithery' in name:
        for c in range(2, 7):
            ws.cell(row=row, column=c).fill = PatternFill('solid', fgColor='E8F5E9')
        ws.cell(row=row, column=3).font = Font(name=FONT_NAME, size=11, color=ACCENT_POSITIVE, bold=True)
    
    ws.row_dimensions[row].height = 32
    row += 1

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 5
ws.column_dimensions['C'].width = 30
ws.column_dimensions['D'].width = 35
ws.column_dimensions['E'].width = 35
ws.column_dimensions['F'].width = 50

# ============================================================
# SHEET 4: Top 10 Loterías por Predecibilidad
# ============================================================
ws = wb.create_sheet("Ranking Predecibilidad")
setup_sheet(ws, title="Ranking de Loterías por Predecibilidad (según backtests)", last_col=7)

row = 4
ws.cell(row=row, column=2, value="Solo se incluyen loterías con backtesting completo (50+ sorteos). Las de quicklotto (20 sorteos) se excluyen del ranking por datos insuficientes.").font = font_caption()
ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
ws.row_dimensions[row].height = 22
row += 2

headers = ["Rank", "Lotería", "Sorteos", "Baseline (azar)", "Mejor Motor", "Mejora %", "Veredicto"]
for i, h in enumerate(headers, 2):
    ws.cell(row=row, column=i, value=h)
style_header_row(ws, row_num=row, col_start=2, col_end=8)
row += 1

# Load backtest results
backtested = []
for lot_key in ['pozo_millonario', 'euromillions', 'la_primitiva', 'lotto_austrian', 'uk49s', 'sa_lotto', 'sa_powerball', 'sa_daily_lotto']:
    path = f'/home/z/my-project/data/backtest_{lot_key}.json'
    if os.path.exists(path):
        with open(path) as f:
            bt = json.load(f)
        if bt.get('comparison'):
            best = bt['comparison'][0]
            baseline = bt['random_baseline']['avg_hits']
            pct = (best['avg_hits'] - baseline) / baseline * 100 if baseline > 0 else 0
            backtested.append({
                'key': lot_key,
                'name': catalogue.get(lot_key, {}).get('name', lot_key),
                'total_draws': catalogue.get(lot_key, {}).get('total_draws', 0),
                'baseline': baseline,
                'best_engine': best['engine'],
                'best_avg': best['avg_hits'],
                'pct': pct,
            })

# Sort by improvement %
backtested.sort(key=lambda x: -x['pct'])

for i, bt in enumerate(backtested, 1):
    verdict = '🌟 EXCEPCIONAL' if bt['pct'] > 30 else '✅ Buena' if bt['pct'] > 10 else '⚠️ Marginal' if bt['pct'] > 0 else '❌ Inutilizable'
    ws.cell(row=row, column=2, value=i)
    ws.cell(row=row, column=3, value=bt['name'])
    ws.cell(row=row, column=4, value=bt['total_draws'])
    ws.cell(row=row, column=5, value=bt['baseline'])
    ws.cell(row=row, column=6, value=bt['best_engine'])
    ws.cell(row=row, column=7, value=f"+{bt['pct']:.1f}%")
    ws.cell(row=row, column=8, value=verdict)
    style_data_row(ws, row_num=row, col_start=2, col_end=8, row_index=i)
    
    ws.cell(row=row, column=2).alignment = align_number()
    ws.cell(row=row, column=3).alignment = align_text()
    ws.cell(row=row, column=4).alignment = align_number()
    ws.cell(row=row, column=5).alignment = align_number()
    ws.cell(row=row, column=6).alignment = align_text()
    ws.cell(row=row, column=7).alignment = align_number()
    ws.cell(row=row, column=8).alignment = align_text()
    
    # Color code
    if bt['pct'] > 30:
        ws.cell(row=row, column=7).fill = PatternFill('solid', fgColor='E8F5E9')
        ws.cell(row=row, column=7).font = Font(name=FONT_NAME, size=11, color=ACCENT_POSITIVE, bold=True)
    elif bt['pct'] > 10:
        ws.cell(row=row, column=7).fill = PatternFill('solid', fgColor='FEF9E7')
        ws.cell(row=row, column=7).font = Font(name=FONT_NAME, size=11, color=ACCENT_WARNING, bold=True)
    elif bt['pct'] <= 0:
        ws.cell(row=row, column=7).fill = PatternFill('solid', fgColor='FDEDEC')
        ws.cell(row=row, column=7).font = Font(name=FONT_NAME, size=11, color=ACCENT_NEGATIVE, bold=True)
    
    row += 1

row += 2
ws.cell(row=row, column=2, value="⚠️ Las 31 loterías restantes (de quicklotto.io) tienen solo 20 sorteos — insuficientes para backtest. Disponibles para predicción en vivo.").font = font_caption()
ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=8)

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 6
ws.column_dimensions['C'].width = 28
ws.column_dimensions['D'].width = 10
ws.column_dimensions['E'].width = 14
ws.column_dimensions['F'].width = 22
ws.column_dimensions['G'].width = 12
ws.column_dimensions['H'].width = 18

# Save
wb.properties.creator = "Z.ai"
wb.properties.title = "LotteryPredictor v3.0 - Búsqueda Exhaustiva Mundial"

output_path = '/home/z/my-project/download/LotteryPredictor_v3_Busqueda_Mundial.xlsx'
wb.save(output_path)
print(f"✓ Excel saved: {output_path}")
print(f"  Size: {os.path.getsize(output_path):,} bytes")

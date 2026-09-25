"""
Parse all Pozo Millonario HTML files and extract structured data.
Output: /home/z/my-project/data/pozo_data.json
"""
import re
import os
import json
from pathlib import Path
from bs4 import BeautifulSoup

HTML_DIR = Path("/home/z/my-project/data/sorteos_html")
OUTPUT = Path("/home/z/my-project/data/pozo_data.json")

# Spanish month names
MONTHS_ES = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'setiembre': 9, 'octubre': 10,
    'noviembre': 11, 'diciembre': 12
}

def parse_date(text):
    """Parse Spanish date like 'lunes 18 de abril de 2022' or '18/04/2022' or '2022-04-18'."""
    # Try ISO format first
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # Try DD/MM/YYYY
    m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    # Try Spanish: "lunes 18 de abril de 2022"
    m = re.search(r'(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})', text, flags=re.I)
    if m:
        day = int(m.group(1))
        month_name = m.group(2).lower()
        year = int(m.group(3))
        month = MONTHS_ES.get(month_name)
        if month:
            return f"{year}-{month:02d}-{day:02d}"
    return None

def parse_day_of_week(text):
    """Extract day of week from text like 'lunes 18 de abril de 2022'."""
    days = ['lunes', 'martes', 'miércoles', 'miercoles', 'jueves', 'viernes', 'sábado', 'sabado', 'domingo']
    for d in days:
        if re.search(r'\b' + d + r'\b', text, flags=re.I):
            # Normalize
            if d == 'miercoles': return 'miércoles'
            if d == 'sabado': return 'sábado'
            return d
    return None

def extract_prize_table(soup, sorteo_num):
    """Extract prize table for a sorteo. Returns dict of acierto -> {ganadores, premio, total}."""
    # Find the section with "Premios del Pozo Millonario NNN"
    premios_section = None
    for div in soup.find_all(['div', 'section']):
        text = div.get_text(strip=True)
        if f'Premios del Pozo Millonario {sorteo_num}' in text and len(text) < 100:
            premios_section = div
            break
    
    if not premios_section:
        return {}
    
    # Find the parent container that has the prize rows
    container = premios_section.parent
    if not container:
        return {}
    
    prizes = {}
    # Find rows: each row has 4 cols (Aciertos, Ganadores, Premio, Total)
    rows = container.find_all('div', class_='filatipo3')
    for row in rows:
        cols = row.find_all('div', class_=re.compile(r'col[1-4]'))
        if len(cols) >= 4:
            acierto = cols[0].get_text(strip=True)
            ganadores = cols[1].get_text(strip=True)
            premio = cols[2].get_text(strip=True)
            total = cols[3].get_text(strip=True)
            
            # Skip placeholder rows where col2="Pozo" col3="Millonario" col4="Ecuador"
            # (these are old draws where the prize data wasn't digitized)
            if ganadores == 'Pozo' and (premio in ['Millonario', 'Revancha', 'Mil'] or premio.startswith('Mil')):
                continue
            # Also skip if col4 is "Ecuador" (placeholder)
            if total == 'Ecuador' and ganadores == 'Pozo':
                continue
            
            # Try to convert to numbers
            try:
                g_num = int(ganadores.replace('.', '').replace(',', '')) if ganadores else 0
            except (ValueError, AttributeError):
                try:
                    g_num = int(ganadores) if ganadores else 0
                except (ValueError, TypeError):
                    g_num = None
            
            # European number format: "953.551,00" = 953551.00
            def parse_eu_number(s):
                if not s:
                    return None
                s = s.strip()
                # Remove non-numeric chars except . and ,
                s = re.sub(r'[^\d.,\-]', '', s)
                if not s:
                    return None
                try:
                    # If both . and , present: . is thousands, , is decimal
                    if '.' in s and ',' in s:
                        # Find which comes last - that's the decimal separator
                        if s.rfind('.') < s.rfind(','):
                            # European: 1.234,56
                            s = s.replace('.', '').replace(',', '.')
                        else:
                            # US: 1,234.56
                            s = s.replace(',', '')
                    elif ',' in s:
                        # Could be decimal or thousands
                        # If only one comma and 1-2 digits after, likely decimal
                        parts = s.split(',')
                        if len(parts) == 2 and len(parts[1]) <= 2:
                            s = s.replace(',', '.')
                        else:
                            s = s.replace(',', '')
                    elif '.' in s:
                        # Could be decimal or thousands
                        parts = s.split('.')
                        if len(parts) == 2 and len(parts[1]) <= 2:
                            pass  # already decimal
                        else:
                            s = s.replace('.', '')
                    return float(s)
                except ValueError:
                    return None
            
            p_num = parse_eu_number(premio)
            t_num = parse_eu_number(total)
            
            # Determine if this is an acierto row (11, 10, 9, 8, 7) or mascot row
            if acierto.isdigit():
                prizes[int(acierto)] = {
                    'ganadores': g_num,
                    'premio_indiv': p_num,
                    'total': t_num,
                }
            else:
                # Mascot row
                prizes['mascota'] = {
                    'nombre': acierto,
                    'ganadores': g_num,
                    'premio_indiv': p_num,
                    'total': t_num,
                }
    
    return prizes

def extract_revancha_data(soup):
    """Extract Pozo Revancha data if present."""
    revancha = {}
    
    # Find "Resultados del Pozo Revancha sorteo NNN"
    text = soup.get_text(' ', strip=True)
    
    # Get revancha sorteo number
    m = re.search(r'Pozo Revancha\s+(?:sorteo\s+)?(\d+)', text)
    if m:
        revancha['sorteo_num'] = int(m.group(1))
    
    # Find revancha section
    revancha_section = None
    for div in soup.find_all(['div', 'section']):
        t = div.get_text(' ', strip=True)
        if 'Pozo Revancha' in t and re.search(r'\b\d+\b', t) and len(t) < 200:
            revancha_section = div
            break
    
    # Find revancha numbers - look for bola divs after "Pozo Revancha NNN"
    revancha_bolas = []
    # Find all bola divs
    all_bolas = soup.find_all('div', class_='bola')
    
    # Pozo Millonario has 11 (or 10) bolas, Pozo Revancha has 11 (or 10) bolas
    # Need to figure out which set belongs to which
    # Strategy: look for "Pozo Revancha NNN" label, then find the next bolas
    
    # Look for filabolacab containing "Pozo Revancha"
    revancha_cab = None
    for div in soup.find_all('div', class_='filabolacab'):
        t = div.get_text(' ', strip=True)
        if 'Pozo Revancha' in t:
            revancha_cab = div
            break
    
    if revancha_cab:
        # Find the next filabola sibling
        sibling = revancha_cab.find_next_sibling()
        while sibling and 'filabola' not in (sibling.get('class') or []):
            sibling = sibling.find_next_sibling()
        if sibling:
            bolas = sibling.find_all('div', class_='bola')
            for b in bolas:
                t = b.get_text(strip=True)
                if t:
                    revancha_bolas.append(t)
    
    revancha['numeros'] = revancha_bolas
    
    # Find revancha mascot
    # Look for "Mascota ganadora sorteo NNN" near "Pozo Revancha"
    revancha_mascot = None
    if revancha.get('sorteo_num'):
        # Try the pattern: "Mascota ganadora sorteo NNN MASCOT"
        rev_sorteo = revancha['sorteo_num']
        m = re.search(r'Mascota ganadora\s+(?:del\s+)?sorteo\s+' + str(rev_sorteo) + r'\s+([A-ZÁÉÍÓÚÑ]{3,20})\b', text)
        if m:
            candidate = m.group(1)
            if candidate not in ['Pronóstico', 'Premios', 'Resultados', 'Combinación', 'Aciertos', 'Redes', 'Sociales', 'Gráfico']:
                revancha_mascot = candidate
        if not revancha_mascot:
            # Find the second "Mascota ganadora" occurrence in the text (after Pozo Revancha)
            # Use regex to find all occurrences
            matches = list(re.finditer(r'Mascota ganadora\s+(?:del\s+)?sorteo\s+\d+\s*[:\s]*([A-ZÁÉÍÓÚÑ]{3,20})\b', text))
            if len(matches) >= 2:
                # Take the second one
                candidate = matches[1].group(1)
                if candidate not in ['Pronóstico', 'Premios', 'Resultados', 'Combinación', 'Aciertos', 'Redes', 'Sociales', 'Gráfico']:
                    revancha_mascot = candidate
    
    revancha['mascota'] = revancha_mascot
    
    # Find revancha prize table
    revancha_prizes = {}
    revancha_premios_label = None
    for div in soup.find_all('div', class_='filabolacab'):
        t = div.get_text(' ', strip=True)
        if 'Premios del Pozo Revancha' in t:
            revancha_premios_label = div
            break
    
    if revancha_premios_label:
        container = revancha_premios_label.parent
        if container:
            rows = container.find_all('div', class_='filatipo3')
            for row in rows:
                cols = row.find_all('div', class_=re.compile(r'col[1-4]'))
                if len(cols) >= 4:
                    acierto = cols[0].get_text(strip=True)
                    ganadores = cols[1].get_text(strip=True)
                    premio = cols[2].get_text(strip=True)
                    total = cols[3].get_text(strip=True)
                    
                    if ganadores == 'Pozo' and premio == 'Revancha':
                        continue
                    if total == 'Ecuador' and ganadores == 'Pozo':
                        continue

                    # European number format support
                    def _parse_eu(s):
                        if not s:
                            return None
                        s = s.strip()
                        s = re.sub(r'[^\d.,\-]', '', s)
                        if not s:
                            return None
                        try:
                            if '.' in s and ',' in s:
                                if s.rfind('.') < s.rfind(','):
                                    s = s.replace('.', '').replace(',', '.')
                                else:
                                    s = s.replace(',', '')
                            elif ',' in s:
                                parts = s.split(',')
                                if len(parts) == 2 and len(parts[1]) <= 2:
                                    s = s.replace(',', '.')
                                else:
                                    s = s.replace(',', '')
                            elif '.' in s:
                                parts = s.split('.')
                                if len(parts) == 2 and len(parts[1]) <= 2:
                                    pass
                                else:
                                    s = s.replace('.', '')
                            return float(s)
                        except ValueError:
                            return None

                    try:
                        g_num = int(ganadores.replace('.', '').replace(',', '')) if ganadores else 0
                    except (ValueError, AttributeError):
                        try:
                            g_num = int(ganadores) if ganadores else 0
                        except (ValueError, TypeError):
                            g_num = None
                    p_num = _parse_eu(premio)
                    t_num = _parse_eu(total)
                    
                    if acierto.isdigit():
                        revancha_prizes[int(acierto)] = {
                            'ganadores': g_num,
                            'premio_indiv': p_num,
                            'total': t_num,
                        }
                    elif acierto:
                        revancha_prizes['mascota'] = {
                            'nombre': acierto,
                            'ganadores': g_num,
                            'premio_indiv': p_num,
                            'total': t_num,
                        }
    
    revancha['premios'] = revancha_prizes
    
    return revancha

def extract_next_draw_info(soup):
    """Extract info about the next draw (estimated prize / acumulado)."""
    info = {}
    text = soup.get_text(' ', strip=True)
    
    # Look for "Próximo sorteo Pozo Millonario NNN"
    m = re.search(r'Pr[oó]ximo sorteo\s+(?:del\s+)?Pozo Millonario\s+(\d+)', text, flags=re.I)
    if m:
        info['proximo_sorteo'] = int(m.group(1))
    
    # Look for estimated prize: "El monto aproximado al ganador ... es USD XXX"
    m = re.search(r'monto aproximado.*?(?:USD|usd|d[oó]lares?)\s*([\d\.]+(?:,\d{2})?)', text, flags=re.I)
    if m:
        amount_str = m.group(1)
        # Convert "450.000,00" -> 450000.00
        try:
            # If has both . and , -> . is thousands, , is decimal
            if '.' in amount_str and ',' in amount_str:
                amount = float(amount_str.replace('.', '').replace(',', '.'))
            elif ',' in amount_str:
                amount = float(amount_str.replace(',', '.'))
            else:
                amount = float(amount_str)
            info['premio_estimado_proximo'] = amount
        except ValueError:
            pass
    
    # Look for date of next draw: "se realizará el día lunes 28 de septiembre de 2026"
    m = re.search(r'se realizar[aá].*?d[ií]a\s+(\w+)\s+(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})', text, flags=re.I)
    if m:
        day_name = m.group(1)
        day = int(m.group(2))
        month_name = m.group(3).lower()
        year = int(m.group(4))
        month = MONTHS_ES.get(month_name)
        if month:
            info['proximo_fecha'] = f"{year}-{month:02d}-{day:02d}"
            info['proximo_dia_semana'] = day_name
    
    return info

def parse_html_file(html_path):
    """Parse a single sorteo HTML file and return structured data."""
    with open(html_path, encoding='utf-8', errors='ignore') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Get sorteo number from filename
    fname = os.path.basename(html_path)
    sorteo_num = int(re.search(r'(\d+)', fname).group(1))
    
    text = soup.get_text(' ', strip=True)
    
    # Get title to confirm
    title_tag = soup.find('title')
    title = title_tag.get_text(strip=True) if title_tag else ''
    
    # Initialize result
    result = {
        'sorteo_num': sorteo_num,
        'titulo': title,
        'fecha': None,
        'dia_semana': None,
        'numeros': [],
        'mascota': None,
        'premios': {},
        'revancha': {},
        'proximo': {},
        'raw_text_preview': text[:500],
    }
    
    # Find the main sorteo date
    # Pattern: "realizado el día lunes 18 de abril de 2022"
    m = re.search(r'realizado\s+el\s+d[ií]a\s+(\w+)\s+(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})', text, flags=re.I)
    if m:
        result['dia_semana'] = m.group(1)
        day = int(m.group(2))
        month_name = m.group(3).lower()
        year = int(m.group(4))
        month = MONTHS_ES.get(month_name)
        if month:
            result['fecha'] = f"{year}-{month:02d}-{day:02d}"
    else:
        # Try other date patterns
        # "Pozo Millonario 976 2022-04-18"
        m = re.search(r'Pozo Millonario\s+' + str(sorteo_num) + r'\s+(\d{4})-(\d{2})-(\d{2})', text)
        if m:
            result['fecha'] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            # Also try to find day of week from text
            day_match = re.search(r'd[ií]a\s+(\w+)\s', text)
            if day_match:
                result['dia_semana'] = day_match.group(1)
    
    # Find winning numbers - look for the filabola section right after "Pozo Millonario NNN"
    # The first set of bolas belongs to Pozo Millonario
    pm_cab = None
    for div in soup.find_all('div', class_='filabolacab'):
        t = div.get_text(' ', strip=True)
        if f'Pozo Millonario {sorteo_num}' in t and 'Premios' not in t:
            pm_cab = div
            break
    
    if pm_cab:
        # Find next filabola
        sibling = pm_cab.find_next_sibling()
        while sibling and 'filabola' not in (sibling.get('class') or []):
            sibling = sibling.find_next_sibling()
        if sibling:
            bolas = sibling.find_all('div', class_='bola')
            for b in bolas:
                t = b.get_text(strip=True)
                if t and t.isdigit():
                    result['numeros'].append(int(t))
    
    # Find main mascot
    # Pattern: "Mascota ganadora sorteo NNN GALAPAGO"
    # Match a full uppercase word (3+ chars) that is a known mascot or any uppercase word
    KNOWN_MASCOTS = {
        'GALAPAGO', 'COCODRILO', 'VACA', 'LLAMA', 'GATO', 'PERRO', 'TUCAN', 'IGUANA',
        'BALLENA', 'CAMARON', 'CANGREJO', 'CONDOR', 'CONEJO', 'DELFIN', 'FOCA',
        'MONO', 'OSO', 'PAPAGAYO', 'TORO', 'PINGUINO', 'RANA', 'SERPIENTE',
        'TIBURON', 'TORTUGA', 'ZORRO', 'AGUILA', 'BÚHO', 'BUHO', 'CABALLO',
        'CERDO', 'CHIVO', 'CIGUEÑA', 'CIGUENA', 'COBRA', 'COLIBRI', 'ELEFANTE',
        'GALLINA', 'GAVILAN', 'JAGUAR', 'LEON', 'LOBO', 'MARIPosa', 'MURCIELAGO',
        'OSO', 'PALOMA', 'PATO', 'PEZ', 'PUMA', 'RATON', 'VENADO', 'ZORRO',
        'GUACAMAYO', 'GUANTA', 'GUATIN', 'NANDU', 'ÑANDU', 'PAVO', 'FAISAN',
        'HAMSTER', 'HORTON', 'CASTOR', 'CUMPLEAÑOS', 'TORTUGA', 'PIRAÑA',
        'GUABINA', 'BÚFALO', 'BUFALO', 'CAMELLO', 'CANGURO', 'JIRAFA', 'RINOCERONTE',
        'HIPOPOTAMO', 'MARIPOSA', 'MUSARAÑA', 'NUTRIA', 'ORANGUTAN', 'ORCA',
        'OSTRA', 'OCELOTE', 'PANDA', 'PEZESPADA', 'POLLITO', 'PULPO', 'PUMA',
        'RANA', 'RATON', 'RINOCERONTE', 'SALMON', 'SALTAMONTES', 'SERPIENTE',
        'TIBURON', 'TORTUGA', 'TOPO', 'TORO', 'TUCAN', 'VACA', 'VENADO', 'ZORRO'
    }
    m = re.search(r'Mascota ganadora\s+(?:del\s+)?sorteo\s+' + str(sorteo_num) + r'\s+([A-ZÁÉÍÓÚÑÜ]{3,20})\b', text)
    if m:
        candidate = m.group(1)
        # Filter out common false positives
        if candidate not in ['Pronóstico', 'Premios', 'Resultados', 'Combinación', 'Aciertos', 'Redes', 'Sociales']:
            result['mascota'] = candidate
    if not result['mascota']:
        # Try alternative: look for <strong>NAME</strong> after "Mascota ganadora"
        for strong in soup.find_all('strong'):
            t = strong.get_text(strip=True)
            if t and t.isupper() and len(t) > 2 and t != 'Pozo Millonario' and not t.isdigit():
                # Check context - must be near "Mascota ganadora"
                parent = strong.parent
                if parent:
                    ctx = parent.get_text(' ', strip=True)[:300]
                    if 'Mascota ganadora' in ctx and t not in ['Pronóstico', 'Premios', 'Resultados', 'Combinación', 'Aciertos', 'Redes', 'Sociales', 'Gráfico']:
                        result['mascota'] = t
                        break
    
    # Extract prize table
    result['premios'] = extract_prize_table(soup, sorteo_num)
    
    # Extract Pozo Revancha
    result['revancha'] = extract_revancha_data(soup)
    
    # Extract next draw info
    result['proximo'] = extract_next_draw_info(soup)
    
    return result

def main():
    all_results = []
    files = sorted(HTML_DIR.glob('sorteo_*.html'))
    print(f"Processing {len(files)} files...")
    
    for i, f in enumerate(files):
        if i % 50 == 0:
            print(f"[{i}/{len(files)}] Processing {f.name}...")
        try:
            data = parse_html_file(f)
            all_results.append(data)
        except Exception as e:
            print(f"  ERROR parsing {f.name}: {e}")
    
    # Sort by sorteo_num
    all_results.sort(key=lambda x: x['sorteo_num'])
    
    # Filter out future draws (no winning numbers)
    drawn_results = [r for r in all_results if r['numeros']]
    future_results = [r for r in all_results if not r['numeros']]
    
    print(f"\nDrawn: {len(drawn_results)}, Future (filtered out): {len(future_results)}")
    if future_results:
        print(f"Future sorteos removed: {[r['sorteo_num'] for r in future_results]}")
    
    # Save only drawn results
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(drawn_results, f, ensure_ascii=False, indent=2)
    
    print(f"\nDone! Saved {len(drawn_results)} records to {OUTPUT}")
    
    # Print summary
    print("\n--- Sample record ---")
    if drawn_results:
        sample = drawn_results[0]
        print(json.dumps(sample, ensure_ascii=False, indent=2)[:1500])
        
        print("\n--- Latest record ---")
        print(json.dumps(drawn_results[-1], ensure_ascii=False, indent=2)[:1500])
    
    # Stats
    print(f"\n--- Stats ---")
    print(f"Total records: {len(drawn_results)}")
    print(f"With date: {sum(1 for r in drawn_results if r['fecha'])}")
    print(f"With numbers: {sum(1 for r in drawn_results if r['numeros'])}")
    print(f"With mascot: {sum(1 for r in drawn_results if r['mascota'])}")
    print(f"With prizes: {sum(1 for r in drawn_results if r['premios'])}")
    print(f"With revancha numeros: {sum(1 for r in drawn_results if r['revancha'].get('numeros'))}")
    print(f"With revancha mascot: {sum(1 for r in drawn_results if r['revancha'].get('mascota'))}")
    print(f"Date range: {min(r['fecha'] for r in drawn_results if r['fecha'])} to {max(r['fecha'] for r in drawn_results if r['fecha'])}")

if __name__ == '__main__':
    main()

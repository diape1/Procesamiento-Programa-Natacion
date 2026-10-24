import re
import csv
import io
try:
    import pymupdf as fitz
except ImportError:
    import fitz
import pdfplumber
from datetime import datetime, timedelta
from collections import Counter

def parse_time_to_seconds(time_str):
    time_str = time_str.replace('L', '').replace('_', '').replace('Y', '').strip()
    if time_str == 'NT' or not time_str:
        return None
    try:
        parts = time_str.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 1:
            return float(parts[0])
    except:
        return None
    return None

def parse_event_desc(rest):
    m_dist = re.search(r'\b(4x\d+|\d+)\s*(?:CC|CL)?\s*(?:m\b|mts\.?|metros\b)', rest, re.IGNORECASE)
    if not m_dist:
        m_dist = re.search(r'(?<!-)\b(4x\d+|1500|1000|800|750|400|200|100|50|25)\b(?!-)', rest, re.IGNORECASE)
    dist = m_dist.group(1) if m_dist else '50'
    
    style_patterns = [
        (r'patada\s+de\s+crol', 'Patada de Crol'),
        (r'patada\s+de\s+dorso', 'Patada de Dorso'),
        (r'libre[s]?', 'Libre'),
        (r'dorso', 'Dorso'),
        (r'pecho', 'Pecho'),
        (r'mariposa', 'Mariposa'),
        (r'c\.?i\.?|combinado', 'Combinado'),
        (r'relevo', 'Relevo')
    ]
    style = 'Libre'
    for pat, st_name in style_patterns:
        if re.search(pat, rest, re.IGNORECASE):
            style = st_name
            break
            
    return dist, style

def clean_swimmer_name(name):
    name = re.sub(r'(\d+)', '', name)
    name = re.sub(r'\bOliv\s*e*r*\s*a\b', 'Olivera', name, flags=re.IGNORECASE)
    name = re.sub(r'\bMarti\s*nez\b', 'Martinez', name, flags=re.IGNORECASE)
    name = re.sub(r'\bGar\s*rido\b', 'Garrido', name, flags=re.IGNORECASE)
    name = re.sub(r'\bBarr\s*era\b', 'Barrera', name, flags=re.IGNORECASE)
    name = re.sub(r'\bGut\s*ierrez\b', 'Gutierrez', name, flags=re.IGNORECASE)
    name = re.sub(r'\bQu\s*intero\b', 'Quintero', name, flags=re.IGNORECASE)
    name = re.sub(r'\bSanch\s*ez\b', 'Sanchez', name, flags=re.IGNORECASE)
    name = re.sub(r'\bLo\s*renzo\b', 'Lorenzo', name, flags=re.IGNORECASE)
    name = re.sub(r'\bM\s*ejia\b', 'Mejia', name, flags=re.IGNORECASE)
    name = re.sub(r'\bN\s*ieto\b', 'Nieto', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+([a-zA-Z])\s+([a-zA-Z])(?:\s|$)', r'\1\2 ', name)
    name = re.sub(r'\s+([a-zA-Z])(?:\s|$)', r'\1 ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def matches_target_swimmer(targets, swimmer_name):
    def norm(s):
        return re.sub(r'[^a-zA-Z0-9]', '', s.lower())
    
    norm_sw = norm(swimmer_name)
    for t in targets:
        t_clean = t.strip()
        if not t_clean:
            continue
        norm_t = norm(t_clean)
        if norm_t in norm_sw:
            return True
        tokens = [norm(tok) for tok in t_clean.split() if len(tok) >= 3]
        if tokens and all(tok in norm_sw for tok in tokens):
            return True
        if 'reyes' in norm_t and 'olivera' in norm_t:
            if 'reyes' in norm_sw and ('olivera' in norm_sw or 'oliv' in norm_sw):
                return True
    return False

def matches_team_name(team_query, swimmer_team):
    sw_team = swimmer_team.lower().strip()
    target_teams = [t.strip().lower() for t in re.split(r'[;,]', team_query) if t.strip()]
    if not target_teams:
        target_teams = [team_query.strip().lower()]
    for q in target_teams:
        if not q:
            continue
        if q in sw_team or sw_team in q:
            return True
        # Equivalent aliases for Plan Sexenal / PLAN-CX / Plan
        if ('plan' in q or 'sexenal' in q) and ('plan' in sw_team or 'sexenal' in sw_team):
            return True
    return False

def parse_swimmer_line_justo_sierra(line):
    line = line.strip()
    m = re.match(r'^([1-9]|10)\s+(.*?)\s+(NT|\d+:\d+\.\d+|\d+\.\d+)\s*(?:_{2,})?$', line)
    if not m:
        return None

    lane, middle, time_str = m.groups()
    
    teams_pattern = r'(Plan Sexenal|JS Primaria|Sec JS Aragon|JS Jacarandas|JS Externos|JS San Mateo|Frances Hidalgo|Colegio Highland|Leones Conrad|Acuatica Veloz|UDM|Hydrion|Kima|Prepa Aragon|Independientes|2OCT-CX|CENSO-CX)'
    m_team = re.search(teams_pattern + r'\s*$', middle, re.IGNORECASE)
    if m_team:
        team = m_team.group(1).strip()
        before_team = middle[:m_team.start()].strip()
        m_age = re.search(r'\b(\d{1,2})\b\s*$', before_team)
        if m_age:
            age = m_age.group(1)
            raw_name = before_team[:m_age.start()].strip()
        else:
            m_dig = re.search(r'(\d{1,2})\s*$', before_team)
            if m_dig:
                age = m_dig.group(1)
                raw_name = before_team[:m_dig.start()].strip()
            else:
                age = ''
                raw_name = before_team
        return {
            'lane': lane.strip(),
            'name': clean_swimmer_name(raw_name),
            'age': age.strip(),
            'team': team,
            'time': time_str.strip()
        }
    else:
        parts = middle.split()
        if len(parts) >= 3 and parts[-2].isdigit():
            return {
                'lane': lane.strip(),
                'name': clean_swimmer_name(' '.join(parts[:-2])),
                'age': parts[-2],
                'team': parts[-1],
                'time': time_str.strip()
            }
        elif len(parts) >= 2:
            return {
                'lane': lane.strip(),
                'name': clean_swimmer_name(' '.join(parts[:-1])),
                'age': '',
                'team': parts[-1],
                'time': time_str.strip()
            }
    return None

def open_fitz_doc(pdf_input):
    if hasattr(pdf_input, 'read'):
        stream_bytes = pdf_input.read()
        if hasattr(pdf_input, 'seek'):
            pdf_input.seek(0)
        return fitz.open(stream=stream_bytes, filetype="pdf")
    elif isinstance(pdf_input, (bytes, bytearray)):
        return fitz.open(stream=pdf_input, filetype="pdf")
    else:
        return fitz.open(pdf_input)

def parse_justo_sierra_fitz(pdf_path):
    doc = open_fitz_doc(pdf_path)
    lines = [l.strip() for page in doc for l in page.get_text('text').splitlines() if l.strip()]
    doc.close()
    
    events = []
    current_event = None
    current_heat = None
    
    re_evento = re.compile(r'^Evento\s+(\d+)\s+(Mujer|Hombres|Muj|Hom|Niñas|Niños|Niñ[ao]s|Mixto)\s+(.*)$', re.IGNORECASE)
    re_heat = re.compile(r'^(?:Heat|Serie)\s+(\d+)\s*(?:of\s+(\d+))?\s*(?:Finales)?', re.IGNORECASE)

    completions = [
        (r'\bOliv$', 'Olivera'),
        (r'\bSanc$', 'Sanchez'),
        (r'\bMorale$', 'Morales'),
        (r'\bMart$', 'Martinez'),
        (r'\bAguila$', 'Aguilar'),
        (r'\bHernand$', 'Hernandez'),
        (r'\bGarc$', 'Garcia'),
        (r'\bCastill$', 'Castillo'),
        (r'\bRodrigu$', 'Rodriguez'),
        (r'\bGonzale$', 'Gonzalez'),
        (r'\bRonquill$', 'Ronquillo'),
        (r'\bCalzad$', 'Calzada'),
        (r'\bAlvar$', 'Alvarez'),
        (r'\bAlva$', 'Alvarez'),
        (r'\bJimene$', 'Jimenez'),
        (r'\bGutierre$', 'Gutierrez'),
        (r'\bVazq$', 'Vazquez'),
        (r'\bDavi$', 'Davila'),
        (r'\bContr$', 'Contreras'),
        (r'\bJuare$', 'Juarez'),
        (r'\bCarr$', 'Carrillo'),
        (r'\bFlo$', 'Flores'),
        (r'\bEsp$', 'Espinosa')
    ]
    def complete_name(n):
        for pat, repl in completions:
            if re.search(pat, n, re.IGNORECASE):
                n = re.sub(pat, repl, n, flags=re.IGNORECASE)
                break
        return n

    for i, line in enumerate(lines):
        m_ev = re_evento.match(line)
        if m_ev:
            num = m_ev.group(1)
            raw_g = m_ev.group(2)
            desc = m_ev.group(3)
            g_low = raw_g.lower()
            if 'mixt' in g_low: g = 'Mixto'
            elif 'muj' in g_low or 'niña' in g_low or 'fem' in g_low: g = 'Muj'
            else: g = 'Hom'
            
            dist, style = parse_event_desc(desc)
            clean_desc = re.sub(r'\bCC\s*(?:mts?\.?|metros|m)?\b', '', desc, flags=re.IGNORECASE)
            clean_desc = re.sub(r'\s*\.\s*', ' ', clean_desc)
            clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
            
            current_event = {
                'num': num,
                'name': line,
                'gender': g,
                'distance': dist,
                'style': style,
                'clean_name': f"Evento {num} {g} {clean_desc}",
                'heats': []
            }
            events.append(current_event)
            current_heat = None
            continue
            
        m_h = re_heat.match(line)
        if m_h:
            h_num = m_h.group(1)
            tot_h = m_h.group(2) or '?'
            current_heat = {'heat_num': h_num, 'total_heats': tot_h, 'swimmers': []}
            if current_event:
                current_event['heats'].append(current_heat)
            continue
            
        if line.startswith('____') and current_heat is not None:
            if i >= 5:
                team = lines[i-5]
                time_str = lines[i-4]
                age = lines[i-3]
                name = lines[i-2]
                lane = lines[i-1]
                
                if lane.isdigit():
                    sw_obj = {
                        'lane': lane,
                        'name': complete_name(name),
                        'age': age if age.isdigit() else '',
                        'team': team,
                        'time': time_str
                    }
                    current_heat['swimmers'].append(sw_obj)
                    
    valid_events = [e for e in events if len(e['heats']) > 0]
    return valid_events

def extract_competition_data(pdf_file):
    try:
        doc = open_fitz_doc(pdf_file)
        p0 = doc[0].get_text('text') if len(doc) > 0 else ''
        doc.close()
    except Exception:
        p0 = ''

    if 'Circuito Acu' in p0 or 'Justo Sierra' in p0 or ('Heat ' in p0 and 'T. de Insc' in p0):
        return parse_justo_sierra_fitz(pdf_file)

    if hasattr(pdf_file, 'seek'):
        pdf_file.seek(0)

    text_lines = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            left = page.crop((0, 0, page.width/2, page.height)).extract_text(layout=True)
            right = page.crop((page.width/2, 0, page.width, page.height)).extract_text(layout=True)
            if left: text_lines.extend([line.strip() for line in left.splitlines() if line.strip()])
            if right: text_lines.extend([line.strip() for line in right.splitlines() if line.strip()])

    events = []
    current_event_obj = None
    current_heat = None
    last_seen_evento = None
    current_total_heats = '?'
    distance_swimmers = []

    # Support traditional (Muj|Hom) and expanded formats (Mujer|Hombres|Niñas|Niños|Mixto)
    re_evento = re.compile(r'^Evento\s+(\d+)\s+(Mujer|Hombres|Muj|Hom|Niñas|Niños|Niñ[ao]s|Mixto)\s+(.*)$', re.IGNORECASE)
    re_standards = re.compile(r'(\d+-\d+|\d+\s*&\s*May)')
    # Support Serie and Heat headers
    re_serie = re.compile(r'^(?:Serie|Heat)\s+(\d+)\s*(?:of\s+(\d+))?\s*(?:Finales)?', re.IGNORECASE)
    
    # Traditional swimmer regex (strict time format, 0 or more spaces before team code):
    re_swimmer_lane = re.compile(r'^([0-9]|10)\s*(.*?)\s+(\d{1,2})\s*([A-Z0-9\-]+)\s+(NT|\d+:\d+\.\d+|\d+\.\d+)(?:\s+__+)?$')
    re_swimmer_rank = re.compile(r"^(\d+)\s*(.+?)\s+(\d{1,2})\s*([A-Z0-9\-]+)\s+(NT|[\d:\.]+)")
    re_rendimiento = re.compile(r'(R3A|R2A|R1A|O2A|O1A|D2A)')

    def flush_distance_swimmers():
        nonlocal distance_swimmers, current_event_obj
        if not current_event_obj or not distance_swimmers:
            distance_swimmers = []
            return
        
        lane_order = ['4', '5', '3', '6', '2', '7', '1', '8']
        num_swimmers = len(distance_swimmers)
        lanes_per_heat = 8
        
        chunks = [distance_swimmers[i:i + lanes_per_heat] for i in range(0, num_swimmers, lanes_per_heat)]
            
        for h_idx, heat_sws in enumerate(chunks):
            heat_num = str(h_idx + 1)
            h_obj = {'heat_num': heat_num, 'total_heats': str(len(chunks)), 'swimmers': []}
            for s_idx, sw in enumerate(heat_sws):
                sw_lane = lane_order[s_idx] if s_idx < len(lane_order) else str(s_idx + 1)
                h_obj['swimmers'].append({
                    'lane': sw_lane,
                    'name': sw['name'],
                    'age': sw['age'],
                    'team': sw['team'],
                    'time': sw['time']
                })
            current_event_obj['heats'].append(h_obj)
        distance_swimmers = []

    for line in text_lines:
        m_ev = re_evento.match(line)
        if m_ev:
            num = m_ev.group(1)
            gender_raw = m_ev.group(2)
            rest = m_ev.group(3).strip()

            g_low = gender_raw.lower()
            if 'mixt' in g_low:
                gender = 'Mixto'
            elif 'muj' in g_low or 'niña' in g_low or 'fem' in g_low:
                gender = 'Muj'
            elif 'hom' in g_low or 'niño' in g_low or 'var' in g_low:
                gender = 'Hom'
            else:
                gender = gender_raw

            dist, style = parse_event_desc(rest)

            # Build clean desc without redundant CC m / Mts
            clean_desc = rest
            clean_desc = re.sub(r'\bCC\s*(?:mts?\.?|metros|m)?\b', '', clean_desc, flags=re.IGNORECASE)
            clean_desc = re.sub(r'\s*\.\s*', ' ', clean_desc)
            clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()

            last_seen_evento = {
                'num': num,
                'gender': gender,
                'desc': clean_desc,
                'distance': dist,
                'style': style,
                'clean_name': f"Evento {num} {gender} {clean_desc}",
                'raw': line
            }

            # If this is the real overall event in traditional format (not category standards)
            if not re_standards.search(rest):
                flush_distance_swimmers()
                current_event_obj = {
                    'num': num,
                    'name': line,
                    'distance': last_seen_evento['distance'],
                    'style': last_seen_evento['style'],
                    'clean_name': f"Evento {num} {gender} {clean_desc}",
                    'heats': []
                }
                events.append(current_event_obj)
                current_heat = None
                current_total_heats = '?'
            continue

        if re_rendimiento.search(line) or "Equipo / Nombre" in line or "Carril / Nombre" in line or "Carril Nombre" in line:
            continue

        m_serie = re_serie.match(line)
        if m_serie:
            flush_distance_swimmers()
            if not current_event_obj or (last_seen_evento and current_event_obj['num'] != last_seen_evento['num']) or (last_seen_evento and len(current_event_obj['heats']) == 0 and current_event_obj['clean_name'] != last_seen_evento['clean_name']):
                if last_seen_evento:
                    if current_event_obj and current_event_obj['num'] == last_seen_evento['num'] and len(current_event_obj['heats']) == 0:
                        current_event_obj['name'] = last_seen_evento['raw']
                        current_event_obj['distance'] = last_seen_evento['distance']
                        current_event_obj['style'] = last_seen_evento['style']
                        current_event_obj['clean_name'] = last_seen_evento['clean_name']
                    else:
                        current_event_obj = {
                            'num': last_seen_evento['num'],
                            'name': last_seen_evento['raw'],
                            'distance': last_seen_evento['distance'],
                            'style': last_seen_evento['style'],
                            'clean_name': last_seen_evento['clean_name'],
                            'heats': []
                        }
                        events.append(current_event_obj)

            if m_serie.group(2):
                current_total_heats = m_serie.group(2)
            else:
                current_total_heats = '?'

            current_heat = {'heat_num': m_serie.group(1), 'total_heats': current_total_heats, 'swimmers': []}
            if current_event_obj:
                current_event_obj['heats'].append(current_heat)
            continue

        # If in heat with Serie/Heat
        if current_heat:
            # First try traditional Meet Manager format
            m_sw = re_swimmer_lane.match(line)
            if m_sw:
                lane, name, age, team, time_val = m_sw.groups()
                clean_time = time_val.replace('_', '').strip()
                current_heat['swimmers'].append({
                    'lane': lane.strip(),
                    'name': name.strip(),
                    'age': age.strip(),
                    'team': team.strip(),
                    'time': clean_time
                })
                continue

            # Second try Justo Sierra / Multi-word team format
            sw_js = parse_swimmer_line_justo_sierra(line)
            if sw_js:
                current_heat['swimmers'].append(sw_js)
                continue

        # If distance event without Serie headers (e.g. 800m Libre in traditional format)
        if current_event_obj and not current_heat:
            m_rank = re_swimmer_rank.match(line)
            if m_rank:
                rank, name, age, team, time_val = m_rank.groups()
                clean_time = time_val.replace('_', '').strip()
                distance_swimmers.append({
                    'rank': rank,
                    'name': name.strip(),
                    'age': age.strip(),
                    'team': team.strip(),
                    'time': clean_time
                })
                continue

    flush_distance_swimmers()
    valid_events = [e for e in events if len(e['heats']) > 0]
    return valid_events

def calculate_timeline(events, start_time_dt, delay_per_heat=None, delay_per_event=15, delay_style_change=20):
    current_time = start_time_dt
    last_style = None
    
    for ev in events:
        style = ev['style']
        if last_style is not None:
            if style != last_style:
                # Break for style change
                current_time += timedelta(seconds=delay_style_change)
            else:
                # Small break between same style events (men/women)
                current_time += timedelta(seconds=delay_per_event)
                
        last_style = style
        
        dist_str = str(ev.get('distance', '50'))
        if '4x25' in dist_str:
            dist_num = 100
        elif '4x50' in dist_str:
            dist_num = 200
        elif '4x100' in dist_str:
            dist_num = 400
        elif '4x200' in dist_str:
            dist_num = 800
        elif dist_str.isdigit():
            dist_num = int(dist_str)
        else:
            dist_num = 50
        
        for h in ev['heats']:
            # Ignore phantom heats with 0 swimmers (e.g. orphan headers across page breaks)
            if len(h['swimmers']) == 0:
                continue

            h['estimated_start'] = current_time
            
            max_time = 0
            for sw in h['swimmers']:
                t = parse_time_to_seconds(sw['time'])
                if t and t > max_time:
                    max_time = t
            
            if max_time == 0:
                max_time = (dist_num / 50.0) * 50.0 
                
            # Calibrated overhead based on empirical meet data:
            # - 50m (Libre, Pecho, Mariposa): 8s (over-the-top rapid start)
            # - 50m Dorso: 12s (in-water start and bar gripping)
            # - 100m (Todos): 15s (balanced lane clearance)
            # - 200m+ distances: 15s
            is_dorso = 'dorso' in style.lower()
            if dist_num <= 50:
                overhead = 12 if is_dorso else 8
            elif dist_num == 100:
                overhead = 15
            else:
                overhead = 15 
                
            current_time += timedelta(seconds=max_time + overhead)

def categorize_ages(swimmers):
    categories = {'7-8': 0, '9-10': 0, '11-12': 0, '13-14': 0, '15-16': 0, '17-18': 0, '19&May': 0, 'Otros': 0}
    for sw in swimmers:
        try:
            age = int(sw['age'])
            if 7 <= age <= 8: categories['7-8'] += 1
            elif 9 <= age <= 10: categories['9-10'] += 1
            elif 11 <= age <= 12: categories['11-12'] += 1
            elif 13 <= age <= 14: categories['13-14'] += 1
            elif 15 <= age <= 16: categories['15-16'] += 1
            elif 17 <= age <= 18: categories['17-18'] += 1
            elif age >= 19: categories['19&May'] += 1
            else: categories['Otros'] += 1
        except:
            categories['Otros'] += 1
    return {k: v for k, v in categories.items() if v > 0}

def format_swimmer_block(sw, targets, include_age=False):
    name_str = sw['name']
    if matches_target_swimmer(targets, name_str):
        name_str = f"_{name_str}_"
    if include_age and sw.get('age'):
        name_display = f"{name_str} ({sw['age']})"
    else:
        name_display = name_str
    block = f"     ▫️ *Carril {sw['lane']}:* {name_display}\n"
    block += f"     ▫️ ⏱️ Tiempo: {sw['time']}\n"
    return block
def generate_whatsapp_messages(events, team_name="PLAN-CX", targets=["Reyes Olivera"], show_all_predictions=False):
    msg1 = "*🏆 Resumen de Eventos*\n\n"
    last_combo = None
    
    for ev in events:
        combo = ev['distance'] + ev['style']
        if last_combo is not None and combo != last_combo:
            msg1 += "🌊🌊🌊🌊🌊 NUEVA PRUEBA 🌊🌊🌊🌊🌊\n\n" # Major separator
        elif last_combo is not None:
            msg1 += "➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖\n\n" # Minor separator
        last_combo = combo
        
        all_swimmers = []
        for h in ev['heats']:
            all_swimmers.extend(h['swimmers'])
            
        total_swimmers = len(all_swimmers)
        cat_stats = categorize_ages(all_swimmers)
        items = [f"{k}: {v}" for k, v in cat_stats.items()]
        
        if len(items) > 0:
            mid = (len(items) + 1) // 2
            line1 = " | ".join(items[:mid])
            line2 = " | ".join(items[mid:])
            if line2:
                cat_str = f"  {line1}\n  {line2}"
            else:
                cat_str = f"  {line1}"
        else:
            cat_str = "  N/A"
            
        heat_counts = Counter(len(h['swimmers']) for h in ev['heats'])
        parts = []
        for count, series_qty in sorted(heat_counts.items(), key=lambda x: -x[1]):
            if series_qty == 1:
                parts.append(f"1 serie de {count}")
            else:
                parts.append(f"{series_qty} series de {count}")
                
        if len(parts) == 1:
            series_summary = parts[0]
        elif len(parts) == 2:
            series_summary = f"{parts[0]} y {parts[1]}"
        else:
            series_summary = ", ".join(parts[:-1]) + f" y {parts[-1]}"
        
        msg1 += f"🔹 *{ev['clean_name']}*\n"
        msg1 += f"📊 Hits: {len(ev['heats'])} | Total: {total_swimmers} nadadores\n"
        msg1 += f"👥 Edades:\n{cat_str}\n"
        msg1 += f"  🔸 {series_summary}\n\n"

    msg2 = "*🎯 Competencias de TARGETS*\n\n"
    target_names_found = set()
    msg2_lines = []
    
    for ev in events:
        for h in ev['heats']:
            for sw in h['swimmers']:
                if matches_target_swimmer(targets, sw['name']):
                    horario = h['estimated_start'].strftime('%I:%M %p') if 'estimated_start' in h else 'N/A'
                    
                    block = f"🔹 *{ev['clean_name']}*\n\n"
                    block += f"  ▶️ *[ SERIE {h['heat_num']} de {h['total_heats']} ]* — ⏰ *{horario}*\n"
                    # Pass include_age=False for targets
                    block += format_swimmer_block(sw, targets, include_age=False)
                    block += "\n"
                    msg2_lines.append(block)
                    target_names_found.add(sw['name'])

    if target_names_found:
        msg2 = msg2.replace("TARGETS", " y ".join(target_names_found))
        for line in msg2_lines:
            msg2 += line
    else:
        msg2 = "*🎯 Competencias*\nNo se encontraron competencias para los nadadores buscados.\n"

    msg3 = f"*🌊 Nadadores del Equipo {team_name}*\n\n"
    last_combo_3 = None
    
    for ev in events:
        team_swimmers_in_ev = []
        for h in ev['heats']:
            swimmers_in_heat = [sw for sw in h['swimmers'] if matches_team_name(team_name, sw['team'])]
            if swimmers_in_heat:
                team_swimmers_in_ev.append((h['heat_num'], h['total_heats'], swimmers_in_heat, h.get('estimated_start', None)))
        
        if team_swimmers_in_ev:
            combo = ev['distance'] + ev['style']
            if last_combo_3 is not None and combo != last_combo_3:
                msg3 += "🌊🌊🌊🌊🌊 NUEVA PRUEBA 🌊🌊🌊🌊🌊\n\n"
            elif last_combo_3 is not None:
                msg3 += "➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖ ➖\n\n"
            last_combo_3 = combo

            msg3 += f"🔹 *{ev['clean_name']}*\n"
            for heat_num, total_heats, swimmers, est_start in team_swimmers_in_ev:
                has_target = any(matches_target_swimmer(targets, sw['name']) for sw in swimmers)
                
                if show_all_predictions or has_target:
                    horario = est_start.strftime('%I:%M %p') if est_start else 'N/A'
                    msg3 += f"  ▶️ *[ SERIE {heat_num} de {total_heats} ]* — ⏰ *{horario}*\n"
                else:
                    msg3 += f"  ▶️ *[ SERIE {heat_num} de {total_heats} ]*\n"
                    
                for sw in swimmers:
                    # Pass include_age=True for team list, but no team name anymore
                    msg3 += format_swimmer_block(sw, targets, include_age=True)
                msg3 += "\n"

    return msg1, msg2, msg3

def generate_csv(events):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Sesion', 'Evento', 'Distancia', 'Estilo', 'Serie', 'Carril', 'Nombre', 'Edad', 'Equipo', 'Tiempo'])
    for ev in events:
        for h in ev['heats']:
            for sw in h['swimmers']:
                writer.writerow(['1', ev['num'], ev['distance'], ev['style'], h['heat_num'], sw['lane'], sw['name'], sw['age'], sw['team'], sw['time']])
    return output.getvalue()

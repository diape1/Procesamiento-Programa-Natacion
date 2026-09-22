import re
import csv
import io
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

def extract_competition_data(pdf_file):
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

    re_evento = re.compile(r'^Evento\s+(\d+)\s+(Muj|Hom)\s+(.*)$')
    re_serie = re.compile(r'^Serie\s+(\d+)\s*(?:of\s+(\d+))?\s*Finales')
    re_swimmer = re.compile(r'^(\d)\s*(.*?)\s+(\d{1,2})\s*([A-Z0-9\-]+)\s+(.*)$')
    re_rendimiento = re.compile(r'(R3A|R2A|R1A|O2A|O1A|D2A)')

    for line in text_lines:
        m_ev = re_evento.match(line)
        if m_ev:
            desc = m_ev.group(3).replace('CC m ', '').strip()
            last_seen_evento = {
                'num': m_ev.group(1),
                'gender': m_ev.group(2),
                'desc': desc,
                'raw': line
            }
            parts = desc.split()
            dist = ''
            style = ''
            for i, p in enumerate(parts):
                if p.isdigit() and int(p) >= 25:
                    dist = p
                    style = ' '.join(parts[i+1:])
                    break
            last_seen_evento['distance'] = dist
            last_seen_evento['style'] = style
            continue
        
        if re_rendimiento.search(line):
            continue
        
        m_serie = re_serie.match(line)
        if m_serie:
            if not current_event_obj or current_event_obj['num'] != last_seen_evento['num']:
                current_event_obj = {
                    'num': last_seen_evento['num'],
                    'name': last_seen_evento['raw'],
                    'distance': last_seen_evento['distance'],
                    'style': last_seen_evento['style'],
                    'clean_name': f"Evento {last_seen_evento['num']} {last_seen_evento['gender']} {last_seen_evento['desc']}",
                    'heats': []
                }
                events.append(current_event_obj)
            
            if m_serie.group(2):
                current_total_heats = m_serie.group(2)

            current_heat = {'heat_num': m_serie.group(1), 'total_heats': current_total_heats, 'swimmers': []}
            current_event_obj['heats'].append(current_heat)
            continue
        
        m_sw = re_swimmer.match(line)
        if m_sw and current_heat:
            lane, name, age, team, time = m_sw.groups()
            
            clean_time = time.replace('_', '').strip()
            
            current_heat['swimmers'].append({
                'lane': lane.strip(),
                'name': name.strip(),
                'age': age.strip(),
                'team': team.strip(),
                'time': clean_time
            })

    return events

def calculate_timeline(events, start_time_dt, delay_per_heat=None, delay_per_event=15, delay_style_change=5):
    current_time = start_time_dt
    last_style = None
    
    for ev in events:
        style = ev['style']
        if last_style is not None:
            if style != last_style:
                # Break for style change
                current_time += timedelta(minutes=delay_style_change)
            else:
                # Small break between same style events (men/women)
                current_time += timedelta(seconds=delay_per_event)
                
        last_style = style
        
        dist_num = int(ev['distance']) if ev['distance'].isdigit() else 50
        
        for h in ev['heats']:
            h['estimated_start'] = current_time
            
            max_time = 0
            for sw in h['swimmers']:
                t = parse_time_to_seconds(sw['time'])
                if t and t > max_time:
                    max_time = t
            
            if max_time == 0:
                max_time = (dist_num / 50.0) * 60.0 
                
            # Dynamic overhead based on distance to prevent accumulation error
            if dist_num <= 50:
                overhead = 30 
            elif dist_num == 100:
                overhead = 20
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
    if any(t.lower() in name_str.lower() for t in targets):
        name_str = f"_{name_str}_" # Italics for targets
    
    block = f"  🏊‍♂️ *Carril {sw['lane']}*\n"
    if include_age:
        # We only show the age, removed the team name because it's redundant
        block += f"  👤 {name_str} ({sw['age']})\n"
    else:
        block += f"  👤 {name_str}\n"
    block += f"  ⏱️ Tiempo: {sw['time']}\n"
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
                if any(t.lower() in sw['name'].lower() for t in targets):
                    horario = h['estimated_start'].strftime('%I:%M %p') if 'estimated_start' in h else 'N/A'
                    
                    block = f"🔹 *{ev['clean_name']}*\n"
                    block += f"🔸 _Serie {h['heat_num']} de {h['total_heats']}_ - ⏰ *{horario}*\n"
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
            swimmers_in_heat = [sw for sw in h['swimmers'] if sw['team'] == team_name]
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
                has_target = any(any(t.lower() in sw['name'].lower() for t in targets) for sw in swimmers)
                
                if show_all_predictions or has_target:
                    horario = est_start.strftime('%I:%M %p') if est_start else 'N/A'
                    msg3 += f"🔸 _Serie {heat_num} de {total_heats}_ - ⏰ *{horario}*\n"
                else:
                    msg3 += f"🔸 _Serie {heat_num} de {total_heats}_\n"
                    
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

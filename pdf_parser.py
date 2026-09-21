import re
import csv
import io
import pdfplumber

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
            current_heat['swimmers'].append({
                'lane': lane.strip(),
                'name': name.strip(),
                'age': age.strip(),
                'team': team.strip(),
                'time': time.strip()
            })

    return events

def generate_whatsapp_messages(events, team_name="PLAN-CX", targets=["Reyes Olivera"]):
    msg1 = "*Resumen de Eventos*\n"
    for ev in events:
        total_swimmers = sum(len(h['swimmers']) for h in ev['heats'])
        msg1 += f"_{ev['clean_name']}_\n"
        msg1 += f"  Hits: {len(ev['heats'])} | Total competidores: {total_swimmers}\n"
        for h in ev['heats']:
             msg1 += f"  - Serie {h['heat_num']} de {h['total_heats']}: {len(h['swimmers'])} competidores\n"
        msg1 += "\n"

    msg2 = "*Competencias de TARGETS*\n"
    target_names_found = set()
    msg2_lines = []
    
    for ev in events:
        for h in ev['heats']:
            for sw in h['swimmers']:
                if any(t.lower() in sw['name'].lower() for t in targets):
                    msg2_lines.append(f"Evento {ev['num']} ({ev['style']} {ev['distance']}m) - Carril: {sw['lane']} - Tiempo: {sw['time']} - Nadador: {sw['name']}\n")
                    target_names_found.add(sw['name'])

    if target_names_found:
        msg2 = msg2.replace("TARGETS", " y ".join(target_names_found))
        for line in msg2_lines:
            msg2 += line
    else:
        msg2 = "*Competencias*\nNo se encontraron competencias para los nadadores buscados en esta sesión.\n"

    msg3 = f"*Nadadores del Equipo {team_name}*\n"
    for ev in events:
        team_swimmers_in_ev = []
        for h in ev['heats']:
            swimmers_in_heat = [sw for sw in h['swimmers'] if sw['team'] == team_name]
            if swimmers_in_heat:
                team_swimmers_in_ev.append((h['heat_num'], h['total_heats'], swimmers_in_heat))
        
        if team_swimmers_in_ev:
            msg3 += f"*{ev['clean_name']}*\n"
            for heat_num, total_heats, swimmers in team_swimmers_in_ev:
                msg3 += f"Serie {heat_num} de {total_heats}:\n"
                for sw in swimmers:
                    name_str = sw['name']
                    if any(t.lower() in name_str.lower() for t in targets):
                        name_str = f"_{name_str}_"
                    msg3 += f"  Carril {sw['lane']}. {name_str} {sw['age']}. {sw['team']}. {sw['time']}\n"
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

if __name__ == '__main__':
    events = extract_competition_data('Procesados/Sesion 1 - WM.pdf')
    m1, m2, m3 = generate_whatsapp_messages(events)
    print("M2 Sample:")
    print(m2)

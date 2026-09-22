import re
import os
import csv
import pdfplumber
import shutil

pdf_path = 'Sesion 1 - WM.pdf'
processed_dir = 'Procesados'
if not os.path.exists(processed_dir):
    os.makedirs(processed_dir)

# Extract sequential text
text_lines = []
with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        left = page.crop((0, 0, page.width/2, page.height)).extract_text(layout=True)
        right = page.crop((page.width/2, 0, page.width, page.height)).extract_text(layout=True)
        if left: text_lines.extend([line.strip() for line in left.splitlines() if line.strip()])
        if right: text_lines.extend([line.strip() for line in right.splitlines() if line.strip()])

events = [] # list of dicts: {'name': '...', 'num': '...', 'distance': '...', 'style': '...', 'heats': []}
current_event_header = None
current_event_obj = None
current_heat = None

# Regexes
re_evento = re.compile(r'^Evento\s+(\d+)\s+(Muj|Hom)\s+(.*)$')
re_serie = re.compile(r'^Serie\s+(\d+).*Finales')
re_swimmer = re.compile(r'^(\d)\s*(.*?)\s+(\d{1,2})\s*([A-Z0-9\-]+)\s+(.*)$')
re_rendimiento = re.compile(r'(R3A|R2A|R1A|O2A|O1A|D2A)')

# Some events have age category in header, some don't. We'll just grab the latest Evento header that isn't a qualification.
# Wait, qualifications also start with Evento. How to distinguish?
# A true event header for heats is followed by 'Carril /Nombre' or 'Serie' soon after, NOT by 'R3A'.
# Let's track the last seen Evento. If we hit 'Serie', we lock it in if not already.

last_seen_evento = None

for line in text_lines:
    m_ev = re_evento.match(line)
    if m_ev:
        last_seen_evento = {
            'num': m_ev.group(1),
            'gender': m_ev.group(2),
            'desc': m_ev.group(3).replace('CC m ', '').strip(),
            'raw': line
        }
        # Try to extract distance and style
        # desc is like '11-12 400 Libre' or '400 Libre'
        parts = last_seen_evento['desc'].split()
        # Find first number which is distance
        dist = ''
        style = ''
        for i, p in enumerate(parts):
            if p.isdigit() and int(p) >= 25: # 25, 50, 100, 200, 400...
                dist = p
                style = ' '.join(parts[i+1:])
                break
        last_seen_evento['distance'] = dist
        last_seen_evento['style'] = style
        continue
    
    if re_rendimiento.search(line):
        # This means the last_seen_evento was a qualification header. That's fine, we just ignore these lines.
        continue
    
    m_serie = re_serie.match(line)
    if m_serie:
        # Check if we need to start a new event
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
        
        current_heat = {'heat_num': m_serie.group(1), 'swimmers': []}
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

# Now process the data as requested.
msg1 = "*Resumen de Eventos*\n"
for ev in events:
    total_swimmers = sum(len(h['swimmers']) for h in ev['heats'])
    msg1 += f"_{ev['clean_name']}_\n"
    msg1 += f"  Hits: {len(ev['heats'])} | Total competidores: {total_swimmers}\n"
    for h in ev['heats']:
         msg1 += f"  - Serie {h['heat_num']}: {len(h['swimmers'])} competidores\n"
    msg1 += "\n"

msg2 = "*Competencias de Ian / Iker*\n"
ian_found = False
for ev in events:
    for h in ev['heats']:
        for sw in h['swimmers']:
            if 'Reyes Olivera' in sw['name'] or 'Ian' in sw['name'] or 'Iker' in sw['name']: # Broaden search just in case
                if 'Reyes Olivera' in sw['name']:
                    msg2 += f"Evento {ev['num']} ({ev['style']} {ev['distance']}m) - Carril: {sw['lane']} - Tiempo: {sw['time']}\n"
                    ian_found = True

if not ian_found:
    msg2 += "No se encontraron competencias para Ian/Iker en esta sesión.\n"

msg3 = "*Nadadores del Equipo PLAN-CX*\n"
for ev in events:
    team_swimmers_in_ev = []
    for h in ev['heats']:
        swimmers_in_heat = [sw for sw in h['swimmers'] if sw['team'] == 'PLAN-CX']
        if swimmers_in_heat:
            team_swimmers_in_ev.append((h['heat_num'], swimmers_in_heat))
    
    if team_swimmers_in_ev:
        msg3 += f"*{ev['clean_name']}*\n"
        for heat_num, swimmers in team_swimmers_in_ev:
            msg3 += f"Serie {heat_num}:\n"
            for sw in swimmers:
                name_str = sw['name']
                if 'Reyes Olivera' in name_str:
                    name_str = f"_{name_str}_"
                msg3 += f"  Carril {sw['lane']}. {name_str} {sw['age']}. {sw['team']}. {sw['time']}\n"
        msg3 += "\n"

with open('whatsapp_output.txt', 'w', encoding='utf-8') as f:
    f.write(msg1 + '\n\n' + msg2 + '\n\n' + msg3)

# Create CSV
csv_filename = os.path.join(processed_dir, 'Sesion_1_datos.csv')
with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['Sesion', 'Evento', 'Distancia', 'Estilo', 'Serie', 'Carril', 'Nombre', 'Edad', 'Equipo', 'Tiempo'])
    for ev in events:
        for h in ev['heats']:
            for sw in h['swimmers']:
                writer.writerow(['1', ev['num'], ev['distance'], ev['style'], h['heat_num'], sw['lane'], sw['name'], sw['age'], sw['team'], sw['time']])

# Move PDF
shutil.move(pdf_path, os.path.join(processed_dir, pdf_path))
print("Done processing!")

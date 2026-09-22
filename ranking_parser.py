import pdfplumber
import re
import csv
import io

def extract_ranking_pdf(pdf_file):
    events_data = []
    current_date = "Desconocida"
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if not text:
                continue
                
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            
            # This is a very robust skeleton for parsing the Ranking PDF.
            # Real regexes will need to be adjusted once the user uploads the actual PDF format.
            current_rama = "Varonil"
            current_categoria = "11-12"
            current_distancia = "50"
            current_estilo = "Libre"
            
            for line in lines:
                # Basic heuristic to find date in headers
                if "202" in line and current_date == "Desconocida":
                    parts = line.split()
                    for p in parts:
                        if "202" in p:
                            current_date = line
                            break
                            
                # Fallback Regex to catch swimmer rows
                # Example: "1 0:32.36 500 Juan Perez 12 PLAN-CX 12/05/2023 Merida"
                m_rank = re.match(r'^(\d+)\s+([\d:.]+)\s+(\d+)\s+([A-Za-z\s,]+?)\s+(\d+)\s+([A-Za-z0-9\s]+?)\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(.*)$', line)
                if m_rank:
                    pos, tiempo, puntos, nombre, edad, equipo, fecha, lugar = m_rank.groups()
                    events_data.append({
                        'Fecha_Ranking': current_date,
                        'Rama': current_rama,
                        'Categoria': current_categoria,
                        'Distancia': current_distancia,
                        'Estilo': current_estilo,
                        'Posicion': pos,
                        'Tiempo': tiempo,
                        'Puntos': puntos,
                        'Nombre': nombre.strip(),
                        'Edad': edad,
                        'Equipo': equipo.strip(),
                        'Fecha_Logro': fecha,
                        'Lugar': lugar.strip()
                    })
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Fecha_Ranking', 'Rama', 'Categoria', 'Distancia', 'Estilo', 'Posicion', 'Tiempo', 'Puntos', 'Nombre', 'Edad', 'Equipo', 'Fecha_Logro', 'Lugar'])
    for row in events_data:
        writer.writerow([row[k] for k in row.keys()])
        
    return output.getvalue()

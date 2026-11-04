import pdfplumber
import re
import csv
import io
import os
import pandas as pd
import sys

def extract_ranking_pdf(pdf_file):
    events_data = []
    current_date = "Desconocida"
    
    with pdfplumber.open(pdf_file) as pdf:
        # Intentar extraer la fecha del ranking de la primera pgina
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if not text: continue
            for line in text.splitlines():
                if "Ranking ANCM - (" in line:
                    # Extraer fecha
                    m = re.search(r'Ranking ANCM - \((.*?)\)', line)
                    if m:
                        current_date = m.group(1)
                        break
            if current_date != "Desconocida":
                break
                
        current_rama = ""
        current_categoria = ""
        current_distancia = ""
        current_estilo = ""
        
        pattern = re.compile(
            r'^(\d+)\*?\s+x?([\d:.]+)(?:\s+([A-Z0-9]{1,4}))?\s+([A-Za-z0-9\u00C0-\u017F\s\.\'\-]+,\s*[A-Za-z0-9\u00C0-\u017F\s\.\'\-]+?)\s+(\d{1,2})\s+([A-Za-z0-9\.\-\/\s]+?)\s+(\d{2}/\d{2}/\d{4})\s+(.*)$'
        )
        
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if not text: continue
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            
            for line in lines:
                # Buscar encabezado de categoria (Ej. Femenil 7-8 50 Libre o Varonil 11-12 100 Mariposa)
                m_cat = re.match(r'^(Femenil|Varonil)\s+(.*?)\s+(\d+)\s+(.*?)$', line)
                if m_cat:
                    current_rama, current_categoria, current_distancia, current_estilo = m_cat.groups()
                    continue
                    
                # Buscar fila de nadador
                m_rank = pattern.match(line)
                if m_rank:
                    pos, tiempo, premio, nombre, edad, equipo, fecha, lugar = m_rank.groups()
                    # Eliminar basurilla del OCR en el nombre y equipo
                    nombre = re.sub(r'\s{2,}', ' ', nombre).strip()
                    nombre = re.sub(r'^5([a-z])', r'S\1', nombre)
                    equipo = re.sub(r'\s+', '', equipo).strip()
                    lugar = re.sub(r'\s{2,}', ' ', lugar).strip()
                    
                    events_data.append({
                        'Fecha_Ranking': current_date,
                        'Rama': current_rama,
                        'Categoria': current_categoria,
                        'Distancia': current_distancia,
                        'Estilo': current_estilo,
                        'Posicion': pos,
                        'Tiempo': tiempo,
                        'Puntos': '0', # El PDF a veces no trae puntos de forma clara
                        'Nombre': nombre,
                        'Edad': edad,
                        'Equipo': equipo,
                        'Fecha_Logro': fecha,
                        'Lugar': lugar
                    })

    return events_data, current_date

if __name__ == "__main__":
    print("=== Actualizador de Ranking Historico ===")
    
    # Check if a file was provided as an argument
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1].strip()
    else:
        pdf_file = input("Ingresa el nombre del archivo PDF del ranking (ej. Ranking ANCM - 2026Mayo.pdf): ").strip()
    
    if not os.path.exists(pdf_file):
        print(f"Error: No se encontro el archivo '{pdf_file}'")
    else:
        print(f"Procesando {pdf_file}...")
        try:
            new_data, ranking_date = extract_ranking_pdf(pdf_file)
            print(f"Fecha del Ranking extraida: {ranking_date}")
            print(f"Se encontraron {len(new_data)} registros.")
            
            df_new = pd.DataFrame(new_data)
            
            csv_path = "ranking_historico.csv"
            if not os.path.exists(csv_path):
                alt_path = os.path.join(os.path.dirname(__file__), "ranking_historico.csv")
                if os.path.exists(alt_path):
                    csv_path = alt_path
                    
            if os.path.exists(csv_path):
                df_old = pd.read_csv(csv_path)
                # Eliminar registros con la misma Fecha_Ranking para evitar duplicados
                df_old = df_old[df_old['Fecha_Ranking'] != ranking_date]
                df_final = pd.concat([df_old, df_new], ignore_index=True)
            else:
                df_final = df_new
                
            df_final.to_csv(csv_path, index=False)
            print(f"{csv_path} actualizado exitosamente!")
        except Exception as e:
            print(f"Ocurrio un error: {e}")

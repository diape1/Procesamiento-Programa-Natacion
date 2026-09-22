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
                # Ej: 1     39.57 L     Castaeda Rivera, Frida Paulina 8 CDMX 17/04/2026 CAMPEONATO REGIONAL CL 2026
                # Ej: 18    41.46 L     Gonzalez Urbina, Nadia  10 MOCT-D F 16/05/2026 2QdRoO T orneo
                # Puntos podria no estar, o el equipo podria tener espacios
                m_rank = re.match(r'^(\d+)\s+([\d:.]+)\s+[LS]\s+(.*?)\s+(\d+)\s+([A-Z0-9-]+\s?[A-Z]*)\s+(\d{2}/\d{2}/\d{4})\s+(.*)$', line)
                if m_rank:
                    pos, tiempo, nombre, edad, equipo, fecha, lugar = m_rank.groups()
                    # Eliminar basurilla del OCR en el nombre y equipo
                    nombre = re.sub(r'\s{2,}', ' ', nombre).strip()
                    equipo = equipo.replace(' ', '').strip() # MOCT-D F -> MOCT-DF
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
            
            if os.path.exists("ranking_historico.csv"):
                df_old = pd.read_csv("ranking_historico.csv")
                # Eliminar registros con la misma Fecha_Ranking para evitar duplicados
                df_old = df_old[df_old['Fecha_Ranking'] != ranking_date]
                df_final = pd.concat([df_old, df_new], ignore_index=True)
            else:
                df_final = df_new
                
            df_final.to_csv("ranking_historico.csv", index=False)
            print("ranking_historico.csv actualizado exitosamente!")
        except Exception as e:
            print(f"Ocurrio un error: {e}")

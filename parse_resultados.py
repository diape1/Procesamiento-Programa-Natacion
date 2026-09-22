import pandas as pd
import warnings
import re
import datetime
import shutil

warnings.filterwarnings('ignore')

file_path = "Tiempos Natación.xlsx"
tmp_path = "Tiempos_tmp_auto.xlsx"
try:
    xls = pd.ExcelFile(file_path)
    using_tmp = False
except PermissionError:
    print(f"[{file_path}] abierto en otro lado. Usando copia temporal...")
    import subprocess
    subprocess.run(["powershell", "-Command", f"Copy-Item '{file_path}' '{tmp_path}'"], check=False)
    xls = pd.ExcelFile(tmp_path)
    using_tmp = True

all_results = []

def parse_time_to_seconds(time_str):
    if pd.isna(time_str) or time_str == "-":
        return None
    time_str = str(time_str).strip()
    try:
        if ':' in time_str:
            parts = time_str.split(':')
            return int(parts[0]) * 60 + float(parts[1])
        elif time_str.count('.') == 2:
            parts = time_str.split('.')
            return int(parts[0]) * 60 + float(f"{parts[1]}.{parts[2]}")
        else:
            return float(time_str)
    except:
        return None

for sheet_name in xls.sheet_names:
    sheet = sheet_name.strip()
    is_official = False
    swimmer = None
    year = None
    
    if sheet.startswith("Sexenal Ian "):
        is_official = True
        swimmer = "Ian"
        year = sheet.replace("Sexenal Ian ", "").strip()
    elif sheet.startswith("Sexenal Iker "):
        is_official = True
        swimmer = "Iker"
        year = sheet.replace("Sexenal Iker ", "").strip()
    elif sheet.startswith("Ian "):
        swimmer = "Ian"
        year = sheet.replace("Ian ", "").strip()
    elif sheet.startswith("Iker "):
        swimmer = "Iker"
        year = sheet.replace("Iker ", "").strip()
    else:
        continue

    if year and len(year) == 2:
        year = "20" + year

    print(f"Processing sheet: '{sheet}'")

    df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
    
    if len(df) < 3:
        continue

    # Identify structure
    header_str_1 = " ".join([str(x).lower() for x in df.iloc[1].values])
    header_str_2 = " ".join([str(x).lower() for x in df.iloc[2].values]) if len(df) > 2 else ""
    
    if "tiempo" in header_str_1:
        structure = "A"
        header_row_idx = 1
        data_start_idx = 2
    elif "tiempo" in header_str_2:
        structure = "B"
        header_row_idx = 2
        data_start_idx = 3
    else:
        print(f"  [!] Unknown structure in sheet {sheet}")
        continue

    # Forward fill to handle merged cells
    df.iloc[0] = df.iloc[0].ffill()
    if structure == "B":
        df.iloc[1] = df.iloc[1].ffill()

    num_cols = len(df.columns)
    
    for c in range(1, num_cols):
        h_val = str(df.iloc[header_row_idx, c]).strip().lower()
        if h_val.startswith("pos"):
            c_pos = c
            c_time = c + 1
            c_parts = c + 2
            
            if c_parts >= num_cols:
                break
                
            event_name = str(df.iloc[0, c_pos]).strip()
            if event_name == "nan" or not event_name:
                continue
                
            course = "CC" if not is_official else ""
            if " CC" in event_name or event_name.endswith("CC"):
                course = "CC"
            elif " CL" in event_name or event_name.endswith("CL"):
                course = "CL"

            # Quitar CC, CL y el año del nombre del evento
            event_name = re.sub(r'\bCC\b|\bCL\b', '', event_name, flags=re.IGNORECASE)
            yr_full = year
            if yr_full and len(yr_full) == 2:
                yr_full = "20" + yr_full
            elif not yr_full:
                yr_full = "2024" # fallback
                
            if year:
                yr_2 = year[-2:]
                event_name = re.sub(rf'\b20{yr_2}\b|\b{yr_2}\b', '', event_name, flags=re.IGNORECASE)
            
            event_date_text = ""
            if structure == "B":
                date_val = str(df.iloc[1, c_pos]).strip()
                if date_val != "nan" and date_val:
                    if isinstance(df.iloc[1, c_pos], datetime.datetime):
                        event_date_text = df.iloc[1, c_pos].strftime("%Y-%m-%d")
                    else:
                        event_date_text = date_val
                        if "eliminatoria" in date_val.lower() or "final" in date_val.lower():
                            event_name = f"{event_name} ({date_val})"
                            event_date_text = ""
            
            full_text = event_name + " " + event_date_text
            
            fecha_inicio = ""
            fecha_fin = ""
            match_str = ""
            
            m1 = re.search(r'\b(Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic)\s*(\d+)?(?:\s*y\s*(\d+))?\b', full_text, re.IGNORECASE)
            m2 = re.search(r'\b(\d+)(?:\s*,\s*\d+)*(?:\s*y\s*(\d+))?\s+(Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic)\b', full_text, re.IGNORECASE)
            
            if event_date_text and re.match(r'^\d{4}-\d{2}-\d{2}$', event_date_text):
                fecha_inicio = event_date_text
                fecha_fin = event_date_text
            elif m2:
                start_day = m2.group(1)
                end_day = m2.group(2) if m2.group(2) else start_day
                month = m2.group(3)
                match_str = m2.group(0)
            elif m1:
                month = m1.group(1)
                start_day = m1.group(2) if m1.group(2) else "1"
                end_day = m1.group(3) if m1.group(3) else start_day
                match_str = m1.group(0)
            else:
                month = None
                
            mm = ""
            if month:
                # Remove the date string from event name
                event_name = event_name.replace(match_str, "")
                month_map = {'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 'may': '05', 'jun': '06', 'jul': '07', 'ago': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12'}
                mm = month_map.get(month.lower()[:3], "01")
                fecha_inicio = f"{yr_full}-{mm}-{start_day.zfill(2)}"
                fecha_fin = f"{yr_full}-{mm}-{end_day.zfill(2)}"
                
            # Limpiar event_name
            event_name = re.sub(r'\s+', ' ', event_name).strip("- ")
            
            # Ajustar curso (CL/CC) para oficiales si no se sabe
            if not course and is_official:
                if mm:
                    if int(mm) <= 6:
                        course = "CL"
                    else:
                        course = "CC"
                else:
                    course = "CL" # default si no hay mes
                    
            original_event_name_check = str(df.iloc[0, c_pos]).strip().lower()
            
            # Las Estacas overwrite
            is_estacas = "estacas" in event_name.lower() or "estacas" in original_event_name_check
            if is_estacas:
                course = "AA"
                
            # Fabrica del deporte overwrite
            is_fabrica = "fabrica del deporte" in event_name.lower() or "fábrica del deporte" in original_event_name_check
            if is_fabrica:
                fecha_inicio = "2024-04-29"
                fecha_fin = "2024-04-29"
                
            # Alma Mater overwrite
            is_almamater = "alma mater" in event_name.lower() or "alma mater" in original_event_name_check
            if is_almamater:
                fecha_inicio = "2025-04-08"
                fecha_fin = "2025-04-09"

            for r in range(data_start_idx, len(df)):
                prueba = str(df.iloc[r, 0]).strip()
                if prueba == "nan" or not prueba:
                    continue
                    
                # Separar estilo y distancia
                dist_match = re.search(r'(\d+)', prueba)
                if dist_match:
                    distancia = dist_match.group(1)
                    estilo = prueba.replace(distancia, "").replace("m", "").strip()
                else:
                    distancia = ""
                    estilo = prueba
                    
                if estilo.lower() == "crol":
                    estilo = "Libre"
                    
                if is_estacas:
                    estilo = "Libre Contra Corriente"
                    distancia = "1000"
                    
                pos = str(df.iloc[r, c_pos]).strip()
                time_str = str(df.iloc[r, c_time]).strip()
                parts = str(df.iloc[r, c_parts]).strip()
                
                if time_str == "nan" or not time_str or time_str == "-":
                    continue
                    
                sec = parse_time_to_seconds(time_str)
                if sec is None:
                    continue
                    
                pos = "" if pos == "nan" else pos
                pos = pos.replace('er', '').replace('do', '').replace('ro', '').replace('to', '').replace('mo', '').replace('vo', '').replace('no', '')
                pos = ''.join(filter(str.isdigit, pos))
                
                parts = "" if parts == "nan" else parts

                all_results.append({
                    "Nombre": swimmer,
                    "Tipo": "Oficial" if is_official else "Recreativa",
                    "Año": year,
                    "Evento": event_name,
                    "Fecha Inicio": fecha_inicio,
                    "Fecha Fin": fecha_fin,
                    "Curso": course,
                    "Estilo": estilo,
                    "Distancia": distancia,
                    "Posicion": pos,
                    "Tiempo": time_str,
                    "Segundos": sec,
                    "Participantes": parts
                })

df_res = pd.DataFrame(all_results)
df_res = df_res.sort_values(by=["Fecha Inicio", "Evento", "Nombre"], ascending=[False, True, True])
df_res.to_csv("resultados_historicos.csv", index=False, encoding="utf-8-sig")
print("Saved to resultados_historicos.csv")
print(f"Total rows: {len(df_res)}")

if using_tmp:
    import os
    try:
        os.remove(tmp_path)
    except:
        pass

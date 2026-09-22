import streamlit as st
import tempfile
import os
import pandas as pd
import altair as alt
import unicodedata
from datetime import datetime, time

# App modules
from pdf_parser import extract_competition_data, calculate_timeline, generate_whatsapp_messages, generate_csv

def remove_accents(input_str):
    if pd.isna(input_str):
        return ""
    nfkd_form = unicodedata.normalize('NFKD', str(input_str))
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

st.set_page_config(page_title="Gestor de Natación", layout="wide")
st.title("Gestor Integral de Natación")

with st.sidebar:
    with st.expander("ℹ️ Ayuda / Mantenimiento"):
        st.markdown('''
        **¿Cómo actualizar la base de datos?**
        
        **1. Historial de Resultados (Tab 2, 4 y 6)**
        * El archivo maestro es `Tiempos Natación.xlsx`.
        * Si agregas tiempos manualmente en Excel, abre una terminal en esta carpeta y ejecuta:
          `python parse_resultados.py`
        * Esto actualizará el archivo `resultados_historicos.csv`.
        * *Nota: Si usas la Tab 6 (Registrar Resultado), asegúrate de descargar el CSV actualizado y reemplazar `resultados_historicos.csv`.*
        
        **2. Ranking CDMX (Tab 3)**
        * Pon los nuevos PDFs de ranking en la carpeta.
        * Ejecuta `python ranking_parser.py` para extraerlos y actualizar `ranking_historico.csv`.
        
        **3. Campeonato Nacional (Tab 5)**
        * Para actualizar los Tiempos Tope, simplemente edita o reemplaza el archivo `tiempos_tope.csv` respetando el formato de columnas.
        
        **4. Subir a la Nube (GitHub)**
        * Después de realizar cualquier cambio local (ej. reemplazar CSVs), siempre debes hacer `git add .`, `git commit -m "Actualización"` y `git push` para que los cambios se reflejen en Streamlit.
        ''')

tab_evento, tab_resultados, tab_analitica, tab_registro, tab_ranking, tab_tope = st.tabs([
    "🏊 Programa de Competencia", 
    "🏅 Resultados Personales", 
    "📈 Analítica", 
    "➕ Registrar Resultado", 
    "🏆 Ranking CDMX",
    "⏱️ Campeonato Nacional"
])

# ----------------- TAB 1: EVENTOS -----------------
with tab_evento:
    st.write("Sube el archivo PDF de la sesión para calcular horarios y generar el WhatsApp.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.header("Configuración")
        start_time = st.time_input("Hora de inicio de la sesión", value=time(9, 0))
        team_name = st.text_input("Equipo a buscar", value="PLAN-CX")
        targets_input = st.text_input("Nadador(es) a buscar (separados por ; )", value="Reyes Olivera")
        targets = [t.strip() for t in targets_input.split(';') if t.strip()]
        st.markdown("---")
        show_pred = st.checkbox("Mostrar predicciones de horario a todo el equipo", value=False)
        
    with col2:
        uploaded_file = st.file_uploader("Sube el PDF del Programa", type=["pdf"])
        if uploaded_file is not None and st.button("Procesar Programa"):
            with st.spinner("Procesando documento..."):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name

                    events = extract_competition_data(tmp_path)
                    start_dt = datetime.combine(datetime.today(), start_time)
                    calculate_timeline(events, start_dt)
                    m1, m2, m3 = generate_whatsapp_messages(events, team_name=team_name, targets=targets, show_all_predictions=show_pred)
                    csv_data = generate_csv(events)

                    st.success("¡Programa procesado con éxito!")
                    
                    st.subheader("1. Resumen de Eventos")
                    with st.container(height=400): st.code(m1, language="markdown")

                    st.subheader("2. Competencias de los Nadadores")
                    with st.container(height=400): st.code(m2, language="markdown")

                    st.subheader("3. Nadadores del Equipo")
                    with st.container(height=400): st.code(m3, language="markdown")

                    st.download_button("Descargar CSV de la Sesión", data=csv_data, file_name="sesion_procesada.csv", mime="text/csv")
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    if 'tmp_path' in locals() and os.path.exists(tmp_path): os.remove(tmp_path)

# ----------------- TAB 5: CAMPEONATO NACIONAL -----------------
with tab_tope:
    st.write("Consulta la tabla de Tiempos Tope para el Campeonato Nacional.")
    
    if os.path.exists("tiempos_tope.csv"):
        df_tope = pd.read_csv("tiempos_tope.csv")
        
        st.subheader("Búsqueda Rápida")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: f_curso = st.selectbox("Curso", ["Todos"] + list(df_tope["Curso"].dropna().unique()))
        with c2: f_rama = st.selectbox("Rama", ["Todas"] + list(df_tope["Rama"].dropna().unique()))
        with c3: f_cat = st.selectbox("Categoría", ["Todas"] + list(df_tope["Categoria"].dropna().unique()))
        with c4: f_estilo = st.selectbox("Estilo", ["Todos"] + list(df_tope["Estilo"].dropna().unique()))
        with c5: f_dist = st.selectbox("Distancia", ["Todas"] + list(df_tope["Distancia"].dropna().astype(str).unique()))
        
        filtered = df_tope.copy()
        if f_curso != "Todos": filtered = filtered[filtered["Curso"] == f_curso]
        if f_rama != "Todas": filtered = filtered[filtered["Rama"] == f_rama]
        if f_cat != "Todas": filtered = filtered[filtered["Categoria"] == f_cat]
        if f_estilo != "Todos": filtered = filtered[filtered["Estilo"] == f_estilo]
        if f_dist != "Todas": filtered = filtered[filtered["Distancia"].astype(str) == f_dist]
        
        st.dataframe(filtered, use_container_width=True, hide_index=True)
    else:
        st.warning("No se encontró el archivo \	iempos_tope.csv\ en el servidor.")

# ----------------- TAB 3: RANKING CDMX -----------------
with tab_ranking:
    st.write("Consulta el Ranking CDMX Histórico de tus nadadores.")
    
    if os.path.exists("ranking_historico.csv"):
        df_rank = pd.read_csv("ranking_historico.csv").dropna(subset=['Nombre'])
        
        # Calcular el total de participantes por ranking, rama, categoría, distancia y estilo
        total_counts = df_rank.groupby(['Fecha_Ranking', 'Rama', 'Categoria', 'Distancia', 'Estilo']).size().reset_index(name='Total')
        df_rank = pd.merge(df_rank, total_counts, on=['Fecha_Ranking', 'Rama', 'Categoria', 'Distancia', 'Estilo'], how='left')
        
        # Formatear la columna Posicion como X/Y
        pos_str = pd.to_numeric(df_rank['Posicion'], errors='coerce').fillna(-1).astype(int).astype(str).replace('-1', '-')
        df_rank['Posicion'] = pos_str + "/" + df_rank['Total'].astype(str)
        
        c1, c2 = st.columns([2, 1])
        with c1:
            search_name = st.text_input("Nombre del Nadador (búsqueda inteligente)")
        
        if search_name:
            search_norm = remove_accents(search_name).lower()
            df_rank['Nombre_Norm'] = df_rank['Nombre'].apply(remove_accents).str.lower()
            
            # Filtro inicial por nombre
            filtered_rank = df_rank[df_rank['Nombre_Norm'].str.contains(search_norm, na=False)].copy()
            filtered_rank = filtered_rank.drop(columns=['Nombre_Norm'])
            
            if len(filtered_rank) > 0:
                # Mostrar todos los nombres encontrados
                nombres_encontrados = list(filtered_rank['Nombre'].unique())
                msg = "Resultados para:\\n" + "\\n".join([f"- **{n}**" for n in nombres_encontrados])
                st.success(msg)
                
                # Filtros adicionales
                fechas_unicas = list(filtered_rank["Fecha_Ranking"].dropna().unique())
                try:
                    fechas_unicas.sort(key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
                except:
                    fechas_unicas.sort(reverse=True)
                
                opciones_fecha = fechas_unicas + ["Todas"]
                
                f1, f2, f3 = st.columns(3)
                with f1: filter_fecha = st.selectbox("Ranking", opciones_fecha)
                with f2: filter_estilo = st.selectbox("Filtrar Estilo", ["Todos"] + list(filtered_rank["Estilo"].dropna().unique()))
                with f3: filter_dist = st.selectbox("Filtrar Distancia", ["Todas"] + list(filtered_rank["Distancia"].astype(str).dropna().unique()))
                
                # Aplicar filtros adicionales
                if filter_fecha != "Todas": filtered_rank = filtered_rank[filtered_rank["Fecha_Ranking"] == filter_fecha]
                if filter_estilo != "Todos": filtered_rank = filtered_rank[filtered_rank["Estilo"] == filter_estilo]
                if filter_dist != "Todas": filtered_rank = filtered_rank[filtered_rank["Distancia"].astype(str) == filter_dist]
                
                # Renombrar columnas
                filtered_display = filtered_rank.rename(columns={
                    "Fecha_Ranking": "Ranking",
                    "Fecha_Logro": "Fecha",
                    "Posicion": "Posición"
                })
                
                # Seleccionar y ordenar columnas (agregando Nombre al inicio)
                columnas_deseadas = ['Ranking', 'Distancia', 'Estilo', 'Posición', 'Tiempo', 'Edad', 'Nombre', 'Fecha', 'Lugar']
                columnas_finales = [col for col in columnas_deseadas if col in filtered_display.columns]
                filtered_display = filtered_display[columnas_finales]
                
                # Ordenar por Nombre (para hacer bloques) y luego por fecha (Ranking) si es posible
                if 'Nombre' in filtered_display.columns:
                    filtered_display = filtered_display.sort_values(by=['Nombre', 'Ranking'], ascending=[True, False])
                
                def color_rows(row):
                    try:
                        if 'Nombre' in row:
                            idx = nombres_encontrados.index(row['Nombre'])
                            if idx % 2 == 0:
                                return ['background-color: rgba(60, 60, 60, 0.2)'] * len(row)
                            else:
                                return ['background-color: rgba(120, 120, 120, 0.2)'] * len(row)
                        return [''] * len(row)
                    except:
                        return [''] * len(row)
                        
                st.dataframe(filtered_display.style.apply(color_rows, axis=1), use_container_width=True, hide_index=True)
            else:
                st.warning(f"No se encontró a nadie llamado '{search_name}'. Verifica la ortografía.")
    else:
        st.warning("No hay base de datos de ranking. Se agregará próximamente.")


# ----------------- TAB 4: RESULTADOS PERSONALES -----------------
        st.warning("No hay base de datos de ranking. Se agregará próximamente.")


# ----------------- TAB 4: RESULTADOS PERSONALES -----------------
with tab_resultados:
    st.write("Consulta el histórico de competencias de Ian e Iker.")
    
    if os.path.exists("resultados_historicos.csv"):
        df_res = pd.read_csv("resultados_historicos.csv")
        
        # Filtros
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: f_nombre = st.selectbox("Nadador", ["Ambos"] + list(df_res["Nombre"].dropna().unique()), key="res_nombre")
        with c2: f_tipo = st.selectbox("Tipo de Evento", ["Todos"] + list(df_res["Tipo"].dropna().unique()), key="res_tipo")
        with c3: f_anio = st.selectbox("Año", ["Todos"] + list(df_res["Año"].astype(str).dropna().unique()), key="res_anio")
        with c4: f_estilo = st.selectbox("Estilo", ["Todos"] + list(df_res["Estilo"].dropna().unique()), key="res_estilo")
        with c5: f_dist = st.selectbox("Distancia", ["Todas"] + list(df_res["Distancia"].astype(str).dropna().unique()), key="res_dist")
        
        filtered_res = df_res.copy()
        if f_nombre != "Ambos": filtered_res = filtered_res[filtered_res["Nombre"] == f_nombre]
        if f_tipo != "Todos": filtered_res = filtered_res[filtered_res["Tipo"] == f_tipo]
        if f_anio != "Todos": filtered_res = filtered_res[filtered_res["Año"].astype(str) == f_anio]
        if f_estilo != "Todos": filtered_res = filtered_res[filtered_res["Estilo"] == f_estilo]
        if f_dist != "Todas": filtered_res = filtered_res[filtered_res["Distancia"].astype(str) == f_dist]
        
        cols_to_show = ["Nombre", "Año", "Tipo", "Evento", "Fecha Inicio", "Fecha Fin", "Curso", "Estilo", "Distancia", "Posicion", "Tiempo", "Participantes"]
        cols_final = [c for c in cols_to_show if c in filtered_res.columns]
        
        # Ordenar tabla por Fecha Inicio (más reciente primero), luego Evento y Nombre
        filtered_res = filtered_res.sort_values(by=["Fecha Inicio", "Evento", "Nombre"], ascending=[False, True, True])
        
        st.dataframe(filtered_res[cols_final], use_container_width=True, hide_index=True)
    else:
        st.warning("No se encontró el archivo resultados_historicos.csv. Asegúrate de ejecutar el script de procesamiento primero.")


# ----------------- TAB 5: ANALÍTICA -----------------
with tab_analitica:
    st.write("Analiza el progreso y evolución de los tiempos.")
    if os.path.exists("resultados_historicos.csv"):
        df_an = pd.read_csv("resultados_historicos.csv").dropna(subset=["Segundos", "Fecha Inicio"])
        
        col1, col2, col3 = st.columns(3)
        with col1: a_nombre = st.selectbox("Nadador", ["Ambos"] + list(df_an["Nombre"].dropna().unique()), key="an_nombre")
        with col2: a_estilo = st.selectbox("Estilo", list(df_an["Estilo"].dropna().unique()), key="an_estilo")
        with col3: a_dist = st.selectbox("Distancia", list(df_an["Distancia"].astype(str).dropna().unique()), key="an_dist")
        
        an_filtered = df_an[(df_an["Estilo"] == a_estilo) & (df_an["Distancia"].astype(str) == a_dist)]
        if a_nombre != "Ambos":
            an_filtered = an_filtered[an_filtered["Nombre"] == a_nombre]
            
        if not an_filtered.empty:
            st.subheader(f"Evolución en {a_estilo} {a_dist}m")
            
            # Ordenar cronológicamente
            an_filtered = an_filtered.sort_values(by="Fecha Inicio", ascending=True)
            
            # Formatear el DataFrame para usar Altair y mostrar tooltip con Evento y Fecha (dd mmm aaaa)
            # Primero convertir a datetime
            an_filtered["Fecha_Obj"] = pd.to_datetime(an_filtered["Fecha Inicio"])
            # Diccionario de meses en español para manual formatting
            meses = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dic'}
            an_filtered["Fecha Fmt"] = an_filtered["Fecha_Obj"].apply(lambda x: f"{x.day:02d} {meses.get(x.month, '')} {x.year}")
            
            # Tomar el mejor tiempo si un nadador tiene múltiples hits en el mismo evento (para evitar líneas duplicadas confusas)
            an_filtered = an_filtered.loc[an_filtered.groupby(["Nombre", "Fecha Inicio"])["Segundos"].idxmin()]
            
            chart = alt.Chart(an_filtered).mark_line(point=True).encode(
                x=alt.X('Fecha Inicio:T', title='Fecha'),
                y=alt.Y('Segundos:Q', title='Segundos', scale=alt.Scale(zero=False)),
                color='Nombre:N',
                tooltip=[
                    alt.Tooltip('Nombre:N', title='Nadador'),
                    alt.Tooltip('Fecha Fmt:N', title='Fecha'),
                    alt.Tooltip('Evento:N', title='Evento'),
                    alt.Tooltip('Tiempo:N', title='Tiempo')
                ]
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)
            st.caption("Eje X: Fecha de Competencia | Eje Y: Tiempo (Segundos). Un tiempo menor es mejor.")
            
            st.markdown("### Estadísticas")
            stats_cols = st.columns(len(an_filtered["Nombre"].unique()))
            for idx, n in enumerate(an_filtered["Nombre"].unique()):
                swimmer_data = an_filtered[an_filtered["Nombre"] == n]
                if not swimmer_data.empty:
                    mejor_tiempo = swimmer_data["Segundos"].min()
                    mejor_tiempo_str = swimmer_data[swimmer_data["Segundos"] == mejor_tiempo]["Tiempo"].iloc[0]
                    primer_tiempo = swimmer_data["Segundos"].iloc[0]
                    ultimo_tiempo = swimmer_data["Segundos"].iloc[-1]
                    ultimo_tiempo_str = swimmer_data["Tiempo"].iloc[-1]
                    
                    mejora = primer_tiempo - ultimo_tiempo
                    mejora_str = f"{mejora:.2f} s" if mejora > 0 else f"{mejora:.2f} s (sin mejora)"
                    
                    with stats_cols[idx]:
                        st.info(f"**{n}**")
                        st.write(f"Mejor tiempo histórico: **{mejor_tiempo_str}**")
                        st.write(f"Último tiempo: **{ultimo_tiempo_str}**")
                        st.write(f"Mejora total (1ra vs Última): **{mejora_str}**")
                        st.write(f"Competencias registradas: **{len(swimmer_data)}**")
        else:
            st.info("No hay datos para esta combinación de filtros.")
    else:
        st.warning("No hay base de datos de resultados.")


# ----------------- TAB 6: REGISTRAR RESULTADO -----------------
with tab_registro:
    st.write("Agrega manualmente nuevos resultados de competencias. Al finalizar, recuerda **descargar** el archivo CSV para guardarlo en tu computadora o GitHub.")
    
    if os.path.exists("resultados_historicos.csv"):
        df_base = pd.read_csv("resultados_historicos.csv")
        
        # Obtener catálogos únicos
        cat_eventos = list(df_base["Evento"].dropna().unique())
        cat_estilos = list(df_base["Estilo"].dropna().unique())
        cat_distancias = list(df_base["Distancia"].dropna().astype(str).unique())
        
        with st.form("form_registro"):
            st.subheader("Datos de la Competencia")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                sel_evento = st.selectbox("Evento", ["➕ Agregar Nuevo Evento"] + cat_eventos)
                if sel_evento == "➕ Agregar Nuevo Evento":
                    nuevo_evento = st.text_input("Nombre del Nuevo Evento")
                else:
                    nuevo_evento = sel_evento
            with c2:
                fecha_inicio = st.date_input("Fecha de Inicio")
            with c3:
                fecha_fin = st.date_input("Fecha de Fin")
            with c4:
                tipo = st.selectbox("Tipo", ["Oficial", "Recreativa"])
                
            st.subheader("Datos del Nado")
            c5, c6, c7, c8 = st.columns(4)
            with c5:
                nadador = st.selectbox("Nadador", ["Ian", "Iker"])
                curso = st.selectbox("Curso", ["CC", "CL", "AA"])
            with c6:
                sel_estilo = st.selectbox("Estilo", ["➕ Agregar Nuevo Estilo"] + cat_estilos)
                if sel_estilo == "➕ Agregar Nuevo Estilo":
                    nuevo_estilo = st.text_input("Nombre del Nuevo Estilo (ej. Libre)")
                else:
                    nuevo_estilo = sel_estilo
            with c7:
                sel_distancia = st.selectbox("Distancia", ["➕ Agregar Nueva Distancia"] + cat_distancias)
                if sel_distancia == "➕ Agregar Nueva Distancia":
                    nueva_distancia = st.text_input("Nueva Distancia (ej. 200)")
                else:
                    nueva_distancia = sel_distancia
            with c8:
                tiempo_str = st.text_input("Tiempo (ej. 45.23 o 1:05.40)")
                posicion = st.number_input("Posición", min_value=1, step=1)
                participantes = st.number_input("Participantes", min_value=1, step=1)
                
            submitted = st.form_submit_button("Guardar Resultado")
            
            if submitted:
                # Validaciones
                evento_final = nuevo_evento.strip() if sel_evento == "➕ Agregar Nuevo Evento" else sel_evento
                estilo_final = nuevo_estilo.strip() if sel_estilo == "➕ Agregar Nuevo Estilo" else sel_estilo
                distancia_final = nueva_distancia.strip() if sel_distancia == "➕ Agregar Nueva Distancia" else sel_distancia
                
                if not evento_final or not estilo_final or not distancia_final or not tiempo_str:
                    st.error("Por favor completa todos los campos requeridos (Evento, Estilo, Distancia y Tiempo).")
                else:
                    # Parsear tiempo a segundos
                    def parse_t(t_str):
                        try:
                            if ':' in t_str:
                                p = t_str.split(':')
                                return int(p[0]) * 60 + float(p[1])
                            else:
                                return float(t_str)
                        except:
                            return None
                            
                    segundos = parse_t(tiempo_str)
                    
                    if segundos is None:
                        st.error("El formato del tiempo es incorrecto. Usa formato SS.MM o MM:SS.MM (ej. 45.23 o 1:05.20)")
                    else:
                        año_str = str(fecha_inicio.year)
                        
                        nuevo_registro = {
                            "Nombre": nadador,
                            "Año": año_str,
                            "Tipo": tipo,
                            "Evento": evento_final,
                            "Fecha Inicio": fecha_inicio.strftime("%Y-%m-%d"),
                            "Fecha Fin": fecha_fin.strftime("%Y-%m-%d"),
                            "Curso": curso,
                            "Estilo": estilo_final,
                            "Distancia": distancia_final,
                            "Posicion": str(posicion),
                            "Tiempo": tiempo_str,
                            "Segundos": segundos,
                            "Participantes": str(participantes)
                        }
                        
                        df_base = pd.concat([df_base, pd.DataFrame([nuevo_registro])], ignore_index=True)
                        
                        # Ordenar: Fecha Inicio desc, Evento asc, Nombre asc
                        df_base = df_base.sort_values(by=["Fecha Inicio", "Evento", "Nombre"], ascending=[False, True, True])
                        
                        # Guardar localmente
                        df_base.to_csv("resultados_historicos.csv", index=False, encoding="utf-8-sig")
                        
                        st.success(f"¡Resultado de {nadador} guardado con éxito!")
                        st.session_state["csv_updated"] = True

        if st.session_state.get("csv_updated", False):
            st.info("⚠️ **IMPORTANTE:** Si usas Streamlit Cloud, el archivo se borrará al suspenderse la app. **Descarga el archivo ahora** y súbelo a tu GitHub para hacerlo permanente.")
            
            with open("resultados_historicos.csv", "rb") as file:
                st.download_button(
                    label="⬇️ Descargar Base de Datos Actualizada (CSV)",
                    data=file,
                    file_name="resultados_historicos.csv",
                    mime="text/csv",
                )
    else:
        st.warning("No hay base de datos de resultados.")

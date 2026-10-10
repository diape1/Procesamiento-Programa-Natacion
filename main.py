import flet as ft

def time_to_seconds(t_str):
    if not t_str or t_str == '-': return 0.0
    try:
        if ':' in t_str:
            m, s = t_str.split(':')
            return int(m) * 60 + float(s)
        else:
            return float(t_str)
    except:
        return 0.0

def seconds_to_time(sec):
    m = int(sec // 60)
    s = sec % 60
    if m > 0:
        return f"{m}:{s:05.2f}"
    return f"{s:.2f}"


import database as db

def main(page: ft.Page):

    # Calendario para la fecha
    import datetime
    def on_date_ini_change(e):
        if e.control.value:
            form_fecha_ini.value = e.control.value.strftime('%d/%m/%Y')
            page.update()
            
    def on_date_fin_change(e):
        if e.control.value:
            form_fecha_fin.value = e.control.value.strftime('%d/%m/%Y')
            page.update()

    date_picker_ini = ft.DatePicker(first_date=datetime.datetime(2020, 1, 1), last_date=datetime.datetime(2030, 12, 31), on_change=on_date_ini_change)
    date_picker_fin = ft.DatePicker(first_date=datetime.datetime(2020, 1, 1), last_date=datetime.datetime(2030, 12, 31), on_change=on_date_fin_change)
    page.overlay.extend([date_picker_ini, date_picker_fin])

    page.title = "Natación Tracker - Ian & Iker"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 800
    page.padding = 20
    
    # Inicializar Base de Datos
    db.init_db()
    
    # Obtener nadadores
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT id, nombre FROM nadadores")
    nadadores = c.fetchall()
    conn.close()

    # ==========================================
    # PESTAÑA 1: VISUALIZACIÓN (HISTORIAL)
    # ==========================================
    
    # Contenedor con scroll para la lista de resultados
    resultados_view = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)
    
    def actualizar_historial(e=None):
        resultados_view.controls.clear()
        
        if not dropdown_nadador_ver.value:
            return
            
        nadador_id = int(dropdown_nadador_ver.value)
        
        conn = db.get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT id, competencia_nombre, categoria, fecha_ini, fecha_fin, distancia, estilo, tiempo, posicion, no_participantes 
            FROM resultados 
            WHERE nadador_id = ? 
            ORDER BY id DESC
        ''', (nadador_id,))
        registros = c.fetchall()
        conn.close()
        
        if not registros:
            resultados_view.controls.append(
                ft.Container(
                    content=ft.Text("No hay resultados registrados aún. Ve a 'Registrar' para agregar uno.", italic=True, color=ft.Colors.GREY_500),
                    padding=20
                )
            )
        else:
            def delete_record(e):
                record_id = e.control.data
                conn = db.get_connection()
                c = conn.cursor()
                c.execute("DELETE FROM resultados WHERE id = ?", (record_id,))
                conn.commit()
                conn.close()
                actualizar_historial()
                # También actualizar estadísticas por si acaso
                load_stats_pruebas(None)
                page.update()

            for reg in registros:
                r_id, comp_nombre, categoria, fecha_ini, fecha_fin, dist, est, tiempo, pos, part = reg
                
                card = ft.Card(
                    elevation=3,
                    content=ft.Container(
                        padding=15,
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"{comp_nombre} ({categoria})", weight=ft.FontWeight.BOLD, size=16),
                                ft.Text(f"Prueba: {dist} - {est}", color=ft.Colors.BLUE_700, weight=ft.FontWeight.W_500),
                                ft.Row([
                                    ft.Row([ft.Icon(ft.Icons.TIMER, size=16, color=ft.Colors.ORANGE_700), ft.Text(f"{tiempo}", weight=ft.FontWeight.BOLD)]),
                                    ft.Row([ft.Icon(ft.Icons.EMOJI_EVENTS, size=16, color=ft.Colors.AMBER_500), ft.Text(f"Pos: {pos}")]),
                                ], alignment=ft.MainAxisAlignment.START, spacing=20)
                            ], expand=True),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color=ft.Colors.RED_400,
                                tooltip="Eliminar este resultado",
                                data=r_id,
                                on_click=delete_record
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    )
                )
                resultados_view.controls.append(card)
        
        page.update()

    
    dropdown_nadador_ver = ft.Dropdown(
        label="Seleccionar Nadador",
        options=[ft.dropdown.Option(key=str(n[0]), text=n[1]) for n in nadadores],
        width=300,
        border=ft.OutlineInputBorder(border_radius=10),
        on_select=actualizar_historial
    )
    
    dashboard_content = ft.Column([
        ft.Text("Historial Deportivo", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
        dropdown_nadador_ver,
        ft.Divider(),
        resultados_view
    ], expand=True)

    # ==========================================
    # PESTAÑA 2: CARGA DE DATOS
    # ==========================================
    
    form_nadador = ft.Dropdown(
        label="Nadador", 
        options=[ft.dropdown.Option(key=str(n[0]), text=n[1]) for n in nadadores],
        border=ft.OutlineInputBorder(border_radius=10)
    )
    
    form_tipo = ft.Dropdown(
        label="Tipo de Competencia",
        options=[ft.dropdown.Option("Oficial"), ft.dropdown.Option("Recreativa")],
        value="Oficial",
        border=ft.OutlineInputBorder(border_radius=10),
        expand=True
    )
    form_categoria = ft.Dropdown(
        label="Categoría",
        options=[
            ft.dropdown.Option("7 y 8 años"),
            ft.dropdown.Option("9 y 10 años"),
            ft.dropdown.Option("11 y 12 años"),
            ft.dropdown.Option("13 y 14 años"),
            ft.dropdown.Option("15 y mayores")
        ],
        border=ft.OutlineInputBorder(border_radius=10)
    )
    
    # --- CATÁLOGOS DINÁMICOS ---
    def load_catalogs():
        conn = db.get_connection()
        c = conn.cursor()
        
        c.execute("SELECT DISTINCT competencia_nombre FROM resultados ORDER BY competencia_nombre")
        comps = [row[0] for row in c.fetchall() if row[0]]
        
        c.execute("SELECT DISTINCT estilo FROM resultados ORDER BY estilo")
        estilos = [row[0] for row in c.fetchall() if row[0]]
        
        c.execute("SELECT DISTINCT distancia FROM resultados ORDER BY distancia")
        distancias = [row[0] for row in c.fetchall() if row[0]]
        
        conn.close()
        
        form_competencia.options = [ft.dropdown.Option(x) for x in comps]
        form_estilo.options = [ft.dropdown.Option(x) for x in estilos]
        form_distancia.options = [ft.dropdown.Option(x) for x in distancias]

    form_competencia = ft.Dropdown(label="Competencia", border=ft.OutlineInputBorder(border_radius=10), expand=True)
    form_estilo = ft.Dropdown(label="Estilo", border=ft.OutlineInputBorder(border_radius=10), expand=True)
    form_distancia = ft.Dropdown(label="Distancia", border=ft.OutlineInputBorder(border_radius=10), expand=True)

    def open_add_dialog(campo_tipo):
        def close_dlg(e):
            dialog.open = False
            page.update()
            
        def add_item(e):
            nuevo_valor = txt_nuevo.value.strip()
            if nuevo_valor:
                if campo_tipo == "comp":
                    form_competencia.options.append(ft.dropdown.Option(nuevo_valor))
                    form_competencia.value = nuevo_valor
                elif campo_tipo == "estilo":
                    form_estilo.options.append(ft.dropdown.Option(nuevo_valor))
                    form_estilo.value = nuevo_valor
                elif campo_tipo == "distancia":
                    form_distancia.options.append(ft.dropdown.Option(nuevo_valor))
                    form_distancia.value = nuevo_valor
                
                dialog.open = False
                page.update()

        txt_nuevo = ft.TextField(label="Nuevo valor")
        dialog = ft.AlertDialog(
            title=ft.Text(f"Agregar nuevo catálogo"),
            content=txt_nuevo,
            actions=[
                ft.TextButton("Cancelar", on_click=close_dlg),
                ft.FilledButton("Agregar", on_click=add_item)
            ]
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    row_comp = ft.Row([
        form_competencia,
        ft.IconButton(icon=ft.Icons.ADD_CIRCLE, icon_color=ft.Colors.BLUE_700, icon_size=35, on_click=lambda _: open_add_dialog("comp"))
    ])
    
    col_distancia = ft.Column([
        ft.Row([
            form_distancia,
            ft.IconButton(icon=ft.Icons.ADD_CIRCLE, icon_color=ft.Colors.BLUE_700, icon_size=35, on_click=lambda _: open_add_dialog("distancia"))
        ])
    ], expand=True)

    col_estilo = ft.Column([
        ft.Row([
            form_estilo,
            ft.IconButton(icon=ft.Icons.ADD_CIRCLE, icon_color=ft.Colors.BLUE_700, icon_size=35, on_click=lambda _: open_add_dialog("estilo"))
        ])
    ], expand=True)

    form_fecha_ini = ft.TextField(label="Fecha Inicio", border=ft.OutlineInputBorder(border_radius=10), read_only=True, on_click=lambda _: date_picker_ini.pick_date(), expand=True)
    form_fecha_fin = ft.TextField(label="Fecha Fin", border=ft.OutlineInputBorder(border_radius=10), read_only=True, on_click=lambda _: date_picker_fin.pick_date(), expand=True)
    row_fechas = ft.Row([form_fecha_ini, form_fecha_fin])
    
    
    form_tiempo = ft.TextField(label="Tiempo (ej. 1:12.78)", border=ft.OutlineInputBorder(border_radius=10))
    
    row_pos_par = ft.Row([
        ft.TextField(label="Posición", width=120, border=ft.OutlineInputBorder(border_radius=10), keyboard_type=ft.KeyboardType.NUMBER),
        ft.TextField(label="Participantes", width=150, border=ft.OutlineInputBorder(border_radius=10), keyboard_type=ft.KeyboardType.NUMBER)
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    
    def guardar_click(e):
        if not all([form_nadador.value, form_competencia.value, form_categoria.value, form_distancia.value, form_estilo.value, form_tiempo.value]):
            page.snack_bar = ft.SnackBar(ft.Text("Por favor completa los campos principales."))
            page.snack_bar.open = True
            page.update()
            return
            
        db.guardar_resultado(
            int(form_nadador.value),
            form_competencia.value,
            form_categoria.value,
            form_fecha_ini.value,
            form_fecha_fin.value,
            form_distancia.value,
            form_estilo.value,
            form_tiempo.value,
            row_pos_par.controls[0].value,
            row_pos_par.controls[1].value
        )
        
        # Limpiar campos y avisar
        form_competencia.value = ""
        form_categoria.value = None
        form_fecha_ini.value = ""
        form_fecha_fin.value = ""
        form_tiempo.value = ""
        row_pos_par.controls[0].value = ""
        row_pos_par.controls[1].value = ""
        page.snack_bar = ft.SnackBar(ft.Text("¡Resultado guardado exitosamente!", color="green"))
        page.snack_bar.open = True
        
        # Actualizar historial en tiempo real si el mismo nadador está seleccionado
        if dropdown_nadador_ver.value == form_nadador.value:
            actualizar_historial(None)
            
        page.update()

    btn_guardar = ft.FilledButton(
        content="Guardar Resultado", 
        icon=ft.Icons.SAVE,
        on_click=guardar_click,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
            padding=20,
            shape=ft.RoundedRectangleBorder(radius=10)
        ),
        width=350
    )
    
    carga_content = ft.Column([
        ft.Text("Registrar Tiempo", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
        form_nadador,
        row_comp,
        form_categoria,
        row_fechas,
        ft.Row([col_distancia, col_estilo], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        form_tiempo,
        row_pos_par,
        ft.Container(height=20),
        btn_guardar
    ], scroll=ft.ScrollMode.AUTO, spacing=15, expand=True)

    # ==========================================
    # BARRA DE NAVEGACIÓN INFERIOR
    # ==========================================
    
    def on_nav_change(e):
        idx = e.control.selected_index
        dashboard_content.visible = (idx == 0)
        carga_content.visible = (idx == 1)
        ranking_content.visible = (idx == 2)
        estadisticas_content.visible = (idx == 3)
        tiempos_tope_content.visible = (idx == 4)
        page.update()

    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.INSERT_CHART_OUTLINED, label="Historial"),
            ft.NavigationBarDestination(icon=ft.Icons.ADD_CIRCLE_OUTLINE, label="Registrar"),
            ft.NavigationBarDestination(icon=ft.Icons.STAR, label="Ranking"),
            ft.NavigationBarDestination(icon=ft.Icons.SSID_CHART, label="Estadísticas"),
            ft.NavigationBarDestination(icon=ft.Icons.TIMER_OUTLINED, label="T. Tope")
        ],
        on_change=on_nav_change,
        selected_index=0
    )
    
    dashboard_content.visible = True
    carga_content.visible = False    
    
    # --- MÓDULO RANKING ---
    def procesar_pdf_ranking(e: ft.FilePickerResultEvent):
        if not e.files:
            return
            
        # Mostrar barra de progreso
        ranking_progress.visible = True
        ranking_status.value = "Procesando documento... (puede tardar un momento)"
        page.update()
        
        pdf_path = e.files[0].path
        
        # Ejecutar el procesamiento en un hilo (o async) para no congelar la UI
        import threading
        def worker():
            try:
                import PyPDF2
                import os
                import re
                from datetime import datetime
                
                header_pattern = re.compile(r'^(Femenil|Varonil)\s+(.*?)\s+(\d+k?m?)\s+(.*?)$', re.IGNORECASE)
                
                current_event = None
                event_buffer = []
                event_has_target = False
                target_results = []
                eventos_a_guardar = []
                
                reader = PyPDF2.PdfReader(pdf_path)
                fecha_hoy = datetime.now().strftime('%d/%m/%Y')
                
                def flush_event():
                    if current_event and event_has_target:
                        eventos_a_guardar.append({
                            'evento': current_event.copy(),
                            'tiempos': event_buffer.copy()
                        })

                for page_obj in reader.pages:
                    text = page_obj.extract_text()
                    if not text: continue
                    
                    for line in text.split('\n'):
                        line = line.strip()
                        if not line: continue
                        
                        m_header = header_pattern.match(line)
                        if m_header:
                            flush_event()
                            current_event = {
                                'rama': m_header.group(1).strip(),
                                'categoria': m_header.group(2).strip(),
                                'distancia': m_header.group(3).strip(),
                                'estilo': m_header.group(4).strip()
                            }
                            event_buffer = []
                            event_has_target = False
                            continue
                        
                        if current_event:
                            # Robust regex from the end
                            m_end = re.search(r'\s+([A-Za-zñÑáéíóúÁÉÍÓÚ\s,\-]+?)\s+(\d+)\s+(DQ|NS|[\d:.]+)\s+(\d+)\s*$', line)
                            if not m_end:
                                continue
                                
                            nombre_equipo = m_end.group(1).strip()
                            edad = m_end.group(2)
                            tiempo = m_end.group(3)
                            
                            rest = line[:m_end.start()].strip()
                            m_start = re.match(r'^([-\d*]+(?:\s+\d+)?)\s+', rest)
                            pos = m_start.group(1).strip() if m_start else "-"
                            
                            # check if it is Ian or Iker
                            is_target = False
                            nadador_limpio = ""
                            n_id = 0
                            if 'reyes olvera, ian' in nombre_equipo.lower():
                                is_target = True
                                nadador_limpio = "Ian Alejandro"
                                n_id = 1
                            elif 'reyes olvera, iker' in nombre_equipo.lower() or ('reyes' in nombre_equipo.lower() and 'iker' in nombre_equipo.lower()):
                                is_target = True
                                nadador_limpio = "Iker Rodrigo"
                                n_id = 2
                                
                            event_buffer.append({
                                'posicion': pos,
                                'nombre': nombre_equipo,
                                'tiempo': tiempo,
                                'is_target': is_target
                            })
                            
                            if is_target:
                                event_has_target = True
                                # Find date if possible
                                m_date = re.search(r'\d{2}-[A-Za-z]{3}-\d{2}', rest)
                                fecha_norm = "-"
                                if m_date:
                                    fecha_cruda = m_date.group(0)
                                    meses = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06','Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
                                    parts = fecha_cruda.split('-')
                                    if len(parts) == 3:
                                        fecha_norm = f"{parts[0]}/{meses.get(parts[1], '01')}/20{parts[2]}"
                                    else:
                                        fecha_norm = fecha_cruda
                                        
                                # Find competition name
                                comp_name = rest[m_start.end() if m_start else 0 : m_date.start() if m_date else len(rest)].strip()
                                if not comp_name: comp_name = "Ranking ANCM"
                                
                                target_results.append({
                                    'nadador_id': n_id,
                                    'Nadador': nadador_limpio,
                                    'Rama': current_event['rama'],
                                    'Categoría': current_event['categoria'],
                                    'Distancia': current_event['distancia'],
                                    'Estilo': current_event['estilo'],
                                    'Posición': pos,
                                    'Tiempo': tiempo,
                                    'Fecha': fecha_norm,
                                    'Lugar': comp_name
                                })
                flush_event()
                
                if target_results:
                    conn = db.get_connection()
                    c = conn.cursor()
                    nuevos = 0
                    # 1. Guardar target_results en `resultados`
                    for r in target_results:
                        c.execute("SELECT id FROM resultados WHERE nadador_id = ? AND estilo = ? AND distancia = ? AND tiempo = ?",
                                  (r['nadador_id'], r['Estilo'], r['Distancia'], r['Tiempo']))
                        if not c.fetchone():
                            c.execute('''INSERT INTO resultados 
                                         (nadador_id, competencia_nombre, categoria, fecha_ini, fecha_fin, distancia, estilo, tiempo, posicion, no_participantes, tipo) 
                                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                                      (r['nadador_id'], r['Lugar'], r['Categoría'], r['Fecha'], r['Fecha'], r['Distancia'], r['Estilo'], r['Tiempo'], r['Posición'], "", "Oficial"))
                            nuevos += 1
                            
                    # 2. Guardar eventos completos en `ranking_eventos` y `ranking_tiempos`
                    for ev_data in eventos_a_guardar:
                        ev = ev_data['evento']
                        # Check if event already exists
                        c.execute("SELECT id FROM ranking_eventos WHERE fecha_archivo = ? AND categoria = ? AND distancia = ? AND estilo = ?",
                                  (fecha_hoy, ev['categoria'], ev['distancia'], ev['estilo']))
                        row = c.fetchone()
                        if not row:
                            c.execute("INSERT INTO ranking_eventos (fecha_archivo, rama, categoria, distancia, estilo) VALUES (?, ?, ?, ?, ?)",
                                      (fecha_hoy, ev['rama'], ev['categoria'], ev['distancia'], ev['estilo']))
                            evento_id = c.lastrowid
                            for t in ev_data['tiempos']:
                                c.execute("INSERT INTO ranking_tiempos (evento_id, posicion, tiempo, nombre, equipo) VALUES (?, ?, ?, ?, ?)",
                                          (evento_id, t['posicion'], t['tiempo'], t['nombre'], ""))
                    conn.commit()
                    conn.close()

                    ranking_status.value = f"¡Éxito! Se detectaron {len(target_results)} marcas ({nuevos} nuevas en Historial) y se guardó el ranking completo de {len(eventos_a_guardar)} pruebas."
                    ranking_status.color = ft.Colors.GREEN_700
                    
                    # Mostrar ranking completo en la UI
                    res_col.controls.clear()
                    for ev_data in eventos_a_guardar:
                        ev = ev_data['evento']
                        tiles = []
                        for t in ev_data['tiempos']:
                            bg_color = ft.Colors.BLUE_50 if t['is_target'] else None
                            weight = "bold" if t['is_target'] else "normal"
                            tiles.append(
                                ft.ListTile(
                                    bgcolor=bg_color,
                                    title=ft.Text(f"{t['posicion']} - {t['nombre']}", weight=weight),
                                    trailing=ft.Text(t['tiempo'], weight=weight, color=ft.Colors.BLUE_900)
                                )
                            )
                        res_col.controls.append(
                            ft.ExpansionTile(
                                title=ft.Text(f"{ev['distancia']} {ev['estilo']} ({ev['categoria']})", weight="bold", size=18, color=ft.Colors.BLUE_900),
                                subtitle=ft.Text(f"{len(ev_data['tiempos'])} nadadores rankeados"),
                                expanded=False,
                                controls=tiles
                            )
                        )
                else:
                    ranking_status.value = "Análisis completo. No se encontraron marcas de Ian o Iker."
                    ranking_status.color = ft.Colors.ORANGE_700
                    res_col.controls.clear()
            except Exception as ex:
                ranking_status.value = f"Error al procesar: {ex}"
                ranking_status.color = ft.Colors.RED_700

            ranking_progress.visible = False
            page.update()
            
        threading.Thread(target=worker).start()

    file_picker = ft.FilePicker(on_result=procesar_pdf_ranking)
    page.services.append(file_picker)

    btn_cargar_pdf = ft.FilledButton(
        "Cargar PDF de Ranking",
        icon=ft.Icons.UPLOAD_FILE,
        action=ft.PickFiles(file_picker=file_picker, allowed_extensions=["pdf"])
    )
    
    ranking_status = ft.Text("Selecciona un PDF para procesar.", italic=True)
    ranking_progress = ft.ProgressBar(width=400, visible=False)
    res_col = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    ranking_content = ft.Column([
        ft.Text("Extractor de Rankings", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
        ft.Text("Extrae automáticamente las marcas de Ian e Iker desde los PDFs oficiales."),
        btn_cargar_pdf,
        ranking_progress,
        ranking_status,
        ft.Divider(),
        res_col
    ], visible=False, expand=True)


    # --- MÓDULO ESTADÍSTICAS ---
    stats_nadador = ft.Dropdown(
        label="Nadador",
        options=[ft.dropdown.Option("1", "Ian Alejandro"), ft.dropdown.Option("2", "Iker Rodrigo")],
        value="1",
        border=ft.OutlineInputBorder(border_radius=10),
        expand=True
    )
    stats_prueba = ft.Dropdown(
        label="Prueba (Estilo y Distancia)",
        border=ft.OutlineInputBorder(border_radius=10),
        expand=True
    )
    
    stats_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Fecha", weight="bold")),
            ft.DataColumn(ft.Text("Competencia", weight="bold")),
            ft.DataColumn(ft.Text("Tiempo", weight="bold")),
        ],
        rows=[],
        heading_row_color=ft.Colors.BLUE_50,
        expand=True
    )
    
    chart_container = ft.Container(content=ft.Column([stats_table], scroll=ft.ScrollMode.AUTO), height=350, padding=10)
    stats_message = ft.Text("", color=ft.Colors.RED)

    def load_stats_pruebas(e):
        n_id = stats_nadador.value
        if not n_id: return
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("SELECT DISTINCT estilo, distancia FROM resultados WHERE nadador_id = ? ORDER BY estilo, distancia", (n_id,))
        rows = c.fetchall()
        conn.close()
        
        stats_prueba.options = [ft.dropdown.Option(f"{r[0]} {r[1]}") for r in rows]
        if stats_prueba.options:
            stats_prueba.value = stats_prueba.options[0].key
        
        # Safe update
        try:
            stats_prueba.update()
        except:
            pass
        update_chart(None)

    def update_chart(e):
        n_id = stats_nadador.value
        prueba = stats_prueba.value
        if not n_id or not prueba: return
        
        import re
        dist_match = re.search(r'\d+\s*(?:m|km)', prueba, re.IGNORECASE)
        if dist_match:
            dist = dist_match.group(0)
            est = prueba.replace(dist, '').strip()
        else:
            dist = ''
            est = prueba

        conn = db.get_connection()
        c = conn.cursor()
        c.execute("SELECT fecha_ini, tiempo, competencia_nombre, tipo FROM resultados WHERE nadador_id = ? AND estilo = ? AND distancia = ? ORDER BY id", (n_id, est, dist))
        rows = c.fetchall()
        conn.close()
        
        stats_table.rows.clear()
        
        if not rows:
            stats_message.value = "No hay tiempos registrados."
        else:
            best_oficial_sec = 999999.0
            best_oficial_row = None
            best_recreativa_sec = 999999.0
            best_recreativa_row = None
            
            parsed_rows = []
            for row in rows:
                if len(row) == 4:
                    fecha_ini, tiempo, comp, tipo = row
                else:
                    fecha_ini, tiempo, comp = row[:3]
                    tipo = "Oficial"
                    
                if not tipo: tipo = "Oficial"
                    
                sec = time_to_seconds(tiempo)
                parsed_rows.append((fecha_ini, tiempo, comp, sec, tipo))
                if sec > 0:
                    if tipo.lower() == 'recreativa':
                        if sec < best_recreativa_sec:
                            best_recreativa_sec = sec
                            best_recreativa_row = (fecha_ini, tiempo, comp)
                    else:
                        if sec < best_oficial_sec:
                            best_oficial_sec = sec
                            best_oficial_row = (fecha_ini, tiempo, comp)
            
            parsed_rows.reverse()
            
            msg = []
            if best_oficial_row:
                b_fecha, b_tiempo, b_comp = best_oficial_row
                msg.append(f"🥇 PB Oficial: {b_tiempo} ({b_comp})")
                
            if best_recreativa_row and (best_recreativa_sec < best_oficial_sec):
                b_fecha, b_tiempo, b_comp = best_recreativa_row
                msg.append(f"⭐ PB Recreativa: {b_tiempo} ({b_comp})")
                
            if not msg:
                if best_recreativa_row:
                    b_fecha, b_tiempo, b_comp = best_recreativa_row
                    msg.append(f"🥇 PB Recreativa: {b_tiempo} ({b_comp})")
                    
            if msg:
                stats_message.value = "\n".join(msg)
                stats_message.color = ft.Colors.GREEN_700
                stats_message.weight = "bold"
                stats_message.size = 16
            else:
                stats_message.value = f"Mostrando {len(rows)} resultados."
                stats_message.color = ft.Colors.BLUE_700
                stats_message.weight = "normal"
                stats_message.size = 14
            
            for (fecha_ini, tiempo, comp, sec, tipo) in parsed_rows:
                is_best_oficial = (sec == best_oficial_sec and sec > 0 and tipo.lower() != 'recreativa')
                is_best_recreativa = (sec == best_recreativa_sec and sec > 0 and tipo.lower() == 'recreativa' and best_recreativa_sec < best_oficial_sec)
                
                is_best = is_best_oficial or is_best_recreativa
                row_color = ft.Colors.GREEN_50 if is_best else None
                
                icon_star = ""
                if is_best_oficial: icon_star = "🥇 "
                elif is_best_recreativa: icon_star = "⭐ "
                
                stats_table.rows.append(
                    ft.DataRow(
                        color=row_color,
                        cells=[
                            ft.DataCell(ft.Text(fecha_ini if fecha_ini else "-", weight="bold" if is_best else "normal")),
                            ft.DataCell(ft.Text(comp + (" (Rec)" if tipo.lower()=='recreativa' else ""), weight="bold" if is_best else "normal")),
                            ft.DataCell(ft.Text(f"{icon_star}{tiempo}", color=ft.Colors.GREEN_900 if is_best else ft.Colors.BLUE_700, weight="bold")),
                        ]
                    )
                )

        try:
            stats_table.update()
            stats_message.update()
        except:
            pass


    stats_nadador.on_change = load_stats_pruebas
    stats_prueba.on_change = update_chart
    
    # We add an explicit button to update
    btn_actualizar_stats = ft.FilledButton("Actualizar Tabla", icon=ft.Icons.REFRESH, on_click=update_chart)

    estadisticas_content = ft.Column([
        ft.Text("Historial de Tiempos", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
        ft.Row([stats_nadador, stats_prueba]),
        btn_actualizar_stats,
        stats_message,
        chart_container,
    ], visible=False)


    # --- MÓDULO TIEMPOS TOPE ---
    import json
    import os
    
    tope_rama = ft.Dropdown(label="Rama", options=[ft.dropdown.Option("Femenil"), ft.dropdown.Option("Varonil")], value="Varonil", border_radius=10, expand=True)
    tope_categoria = ft.Dropdown(label="Categoría", options=[
        ft.dropdown.Option("12"), ft.dropdown.Option("13-14"), 
        ft.dropdown.Option("15-16"), ft.dropdown.Option("17-21")
    ], value="12", border_radius=10, expand=True)
    
    tope_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Prueba")),
            ft.DataColumn(ft.Text("CC")),
            ft.DataColumn(ft.Text("CL"))
        ],
        rows=[],
        expand=True
    )
    
    def update_tope_table(e):
        try:
            if not os.path.exists("tiempos_nacionales_2026.json"):
                return
            with open("tiempos_nacionales_2026.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            
            rama = tope_rama.value.lower()
            cat = tope_categoria.value
            
            tope_table.rows.clear()
            if rama in data and cat in data[rama]:
                pruebas = data[rama][cat]
                for p_name, t_vals in pruebas.items():
                    tope_table.rows.append(
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text(p_name, weight="bold")),
                            ft.DataCell(ft.Text(t_vals.get("CC", "-"), color=ft.Colors.BLUE_700)),
                            ft.DataCell(ft.Text(t_vals.get("CL", "-"), color=ft.Colors.ORANGE_700))
                        ])
                    )
            
            try:
                tope_table.update()
                page.update()
            except:
                pass
        except Exception as ex:
            print("Error cargando Tiempos Tope:", ex)
            
    tope_rama.on_change = update_tope_table
    tope_categoria.on_change = update_tope_table
    
    tiempos_tope_content = ft.Container(
        visible=False,
        expand=True,
        padding=20,
        content=ft.Column([
            ft.Text("Tiempos Tope Nacionales", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
            ft.Row([tope_rama, tope_categoria]),
            ft.ListView(controls=[tope_table], expand=True)
        ], expand=True)
    )
    
    # Call it initially to load data if it exists
    update_tope_table(None)

    # Contenedor principal centrado simulando un celular
    main_container = ft.Container(
        content=ft.Column([dashboard_content, carga_content, ranking_content, estadisticas_content, tiempos_tope_content], expand=True),
        width=450,
        alignment=ft.Alignment.CENTER
    )

    load_stats_pruebas(None)
    load_catalogs()
    page.add(
        ft.Row([main_container], alignment=ft.MainAxisAlignment.CENTER, expand=True)
    )

if __name__ == "__main__":
    ft.run(main)

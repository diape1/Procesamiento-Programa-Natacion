import streamlit as st
import tempfile
import os
from pdf_parser import extract_competition_data, generate_whatsapp_messages, generate_csv

st.set_page_config(page_title="Procesador de Competencias", layout="wide")

st.title("Procesador de PDF de Competencias de Natación")
st.write("Sube el archivo PDF de la sesión para extraer la información y darle formato de WhatsApp.")

with st.sidebar:
    st.header("Configuración")
    team_name = st.text_input("Equipo a buscar", value="PLAN-CX")
    targets_input = st.text_input("Nadador(es) a buscar (separados por coma)", value="Reyes Olivera")
    targets = [t.strip() for t in targets_input.split(',')]

uploaded_file = st.file_uploader("Sube el PDF del Programa", type=["pdf"])

if uploaded_file is not None:
    if st.button("Procesar PDF"):
        with st.spinner("Procesando documento... esto puede tardar unos segundos."):
            try:
                # Save uploaded file to a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                events = extract_competition_data(tmp_path)
                m1, m2, m3 = generate_whatsapp_messages(events, team_name=team_name, targets=targets)
                csv_data = generate_csv(events)

                st.success("¡Documento procesado con éxito!")

                st.subheader("1. Resumen de Eventos")
                st.code(m1, language="markdown")

                st.subheader("2. Competencias de los Nadadores")
                st.code(m2, language="markdown")

                st.subheader("3. Nadadores del Equipo")
                st.code(m3, language="markdown")

                st.download_button(
                    label="Descargar CSV de la Sesión",
                    data=csv_data,
                    file_name="sesion_procesada.csv",
                    mime="text/csv"
                )

            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")
            finally:
                if 'tmp_path' in locals() and os.path.exists(tmp_path):
                    os.remove(tmp_path)

import google.generativeai as genai
import io
import csv

def extract_tiempos_tope(image_bytes, api_key):
    genai.configure(api_key=api_key)
    
    generation_config = {
        "temperature": 0.0,
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
    )
    
    prompt = """
    Analiza la imagen adjunta que contiene tiempos tope de natacion.
    Extrae todos los datos y devuelvelos en formato CSV estricto (sin formato markdown, solo texto crudo separado por comas).
    Las columnas deben ser exactamente:
    Curso,Rama,Categoria,Estilo,Distancia,Tiempo
    
    Reglas:
    - Curso: "Largo" o "Corto" (Identificalo del titulo superior de cada bloque).
    - Rama: "Femenil" (Damas) o "Varonil" (Varones).
    - Categoria: "11-12", "13-14", "15-16", "17 & May".
    - Estilo: "Libre", "Dorso", "Pecho", "Mariposa", "C. Ind" (C. Ind Marip es C. Ind).
    - Distancia: El numero (50, 100, 200, 400, 800, 1500).
    - Tiempo: El tiempo exacto en la celda correspondiente (ej. 0:32.36). Si la celda esta vacia o en blanco, NO crees esa fila.
    
    Recuerda extraer los datos de todas las columnas (tanto Damas como Varones) y de todos los estilos y distancias.
    La primera linea debe ser el encabezado: Curso,Rama,Categoria,Estilo,Distancia,Tiempo
    """
    
    image_parts = [
        {
            "mime_type": "image/jpeg",
            "data": image_bytes
        }
    ]
    
    response = model.generate_content([prompt, image_parts[0]])
    
    csv_text = response.text.strip()
    if csv_text.startswith("```csv"):
        csv_text = csv_text.split("```csv")[1].split("```")[0].strip()
    elif csv_text.startswith("```"):
        csv_text = csv_text.split("```")[1].split("```")[0].strip()
        
    return csv_text

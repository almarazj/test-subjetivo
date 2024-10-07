import streamlit as st
import random
import string
from pathlib import Path
import pandas as pd
from streamlit_gsheets import GSheetsConnection


# Configuración básica
st.set_page_config(page_title="Test Subjetivo", layout="centered")

# Conectar o crear la base de datos SQLite
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read()

# Función para generar un ID alfanumérico aleatorio
def generar_id_aleatorio():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=4))

# Función para guardar los resultados en Google Sheets
def guardar_resultados():
    # Crear una fila con los datos del participante
    nueva_fila = [
        id_participante,  # ID generado
        edad,             # Edad
        genero,           # Género
        experiencia,      # Experiencia de escucha
    ] + resultados  # Puntajes de las comparaciones

    # Añadir la fila a la Google Sheet
    conn.append_row(nueva_fila)
    st.success("Resultados guardados correctamente en Google Sheets")

# Inicialización de session_state
if "comparacion_actual" not in st.session_state:
    st.session_state["comparacion_actual"] = 0
    st.session_state["resultados"] = []
    st.session_state["datos_sujeto"] = {}

# Parámetros
total_comparaciones = 16
sistemas = {"wavmark": "wm", "audioseal": "as", "silentcipher": "sc"}

# Selección de los audios
audio_folder = Path("data/audio_samples/")
audios_originales = list((audio_folder / "original").glob("*.wav"))

# Función para reproducir audios
def play_audio(audio_path):
    st.audio(str(audio_path))

def start_test():
    st.session_state["datos_sujeto"] = {
        "edad": edad,
        "experiencia": experiencia,
        "genero": genero,
        "id_participante": id_participante
    }
    # Limpiar los inputs del formulario
    st.session_state["comparacion_actual"] += 1
    
def next_comparison():
    st.session_state["resultados"].append(dmos_score)
    st.session_state["comparacion_actual"] += 1
    
def prev_comparison():
    st.session_state["comparacion_actual"] -= 1
    st.session_state["resultados"].pop()  # Eliminar el último resultado guardado si se vuelve atrás

def end_test():
    # Guardamos el resultado de esta comparación
    guardar_resultados()
    # Avanzamos a la pantalla de agradecimiento
    st.session_state["comparacion_actual"] += 1

def new_test():
    st.session_state["comparacion_actual"] = 0
    st.session_state["resultados"] = []
    st.session_state["datos_sujeto"] = {}

# Título de la aplicación
st.title("Test de Calidad de Audio - DMOS")

# Datos del sujeto
if st.session_state["comparacion_actual"] == 0:
    with st.form(key="datos_sujeto_form"):
        edad = st.number_input("Edad:", min_value=0, max_value=120)
        experiencia = st.selectbox("Experiencia de escucha:", ["Escucho música regularmente", "Trabajo en algo relacionado con la música", "No suelo escuchar música"])
        genero = st.selectbox("Género:", ["Masculino", "Femenino", "Otro"])
        id_participante = generar_id_aleatorio()
        
        submitted = st.form_submit_button("Comenzar test", on_click=start_test)


# Si el usuario está en la primera comparación o en cualquier comparación posterior
if st.session_state["comparacion_actual"] > 0:
    comparacion_actual = st.session_state["comparacion_actual"]

    if comparacion_actual <= total_comparaciones:
        # Seleccionamos un audio y un sistema aleatorio
        audio_prueba = random.choice(audios_originales)
        sistema, abreviatura = random.choice(list(sistemas.items()))

        # Iniciamos el formulario de comparación
        with st.form(key="dmos_form"):
            st.write(f"Comparación {comparacion_actual} de {total_comparaciones}")
            st.write("Audio A")
            play_audio(audio_prueba)

            # Audio procesado por un sistema (AB)
            audio_degradado = audio_folder / sistema / f"{abreviatura}_{audio_prueba.name}"
            st.write("Audio B")
            play_audio(audio_degradado)
            
            st.write(f"¿Cómo describirías la degradación percibida en el audio B con respecto al audio A?")
            # Opciones de puntaje DMOS con radio buttons
            opciones = {
                5: "Degradación inaudible",
                4: "Degradación audible, pero no molesta",
                3: "Degradación ligeramente molesta",
                2: "Degradación molesta",
                1: "Degradación muy molesta"
            }

            dmos_score = st.radio("Calidad percibida", list(opciones.keys()), format_func=lambda x: opciones[x], key=f"dmos_{comparacion_actual}")

            # Botones "Volver atrás" y "Siguiente" o "Finalizar" en la última comparación
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("Atrás", on_click=prev_comparison)
            with col2:
                if comparacion_actual <= total_comparaciones:
                    submitted = st.form_submit_button("Siguiente", on_click=next_comparison)
                else:
                    submitted = st.form_submit_button("Finalizar", on_click=end_test)
            
    else:
        resultados = st.session_state["resultados"]
        st.write("¡Prueba finalizada! Gracias por participar.")

        # Limpiar el estado para una nueva sesión (opcional)
        submitted = st.button("Comenzar una nueva prueba", on_click=new_test)

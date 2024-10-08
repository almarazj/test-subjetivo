import streamlit as st
import random
import string
from pathlib import Path
from pymongo import MongoClient

MONGO_URI = f"mongodb+srv://{st.secrets['db_username']}:{st.secrets['db_pswd']}@{st.secrets['cluster_name']}.j8rqe.mongodb.net/?retryWrites=true&w=majority&appName=test-subjetivo"
client = MongoClient(MONGO_URI)


db = client["results_db"]
collection = db["results_collection"]

def generar_id_participante():
    # Genera un string aleatorio de 4 caracteres alfanuméricos
    return ''.join(random.choices(string.ascii_letters + string.digits, k=4))

# Configuración básica
st.set_page_config(page_title="Test Subjetivo", layout="centered")

# Función para guardar los resultados en Google Sheets
def guardar_resultados():
    id_participante = generar_id_participante()
    edad = st.session_state.age
    genero = st.session_state.gender
    experiencia = st.session_state.exp
    resultados = st.session_state.resultados  # Puntajes de las comparaciones
    
    nuevo_documento = {
        "id_participante": generar_id_participante(),  # ID generado
        "edad": st.session_state.age,             # Edad
        "genero": st.session_state.gender,           # Género
        "experiencia": st.session_state.exp,      # Experiencia de escucha
        "resultados": st.session_state.resultados
    } # Puntajes de las comparaciones

    collection.insert_one(nuevo_documento)
    st.success("Resultados guardados correctamente en la base de datos.")


# Inicialización de session_state
if "comparacion_actual" not in st.session_state:
    st.session_state["comparacion_actual"] = 0
    st.session_state["resultados"] = []

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

# Título de la aplicación
st.title("Test de Calidad de Audio - DMOS")

# Datos del sujeto
if st.session_state["comparacion_actual"] == 0:
    with st.form(key="datos_sujeto_form"):
        st.session_state.age = st.number_input("Edad:", min_value=0, max_value=120)
        st.session_state.exp = st.selectbox("Experiencia de escucha:", ["Escucho música regularmente", "Trabajo en algo relacionado con la música", "No suelo escuchar música"])
        st.session_state.gender = st.selectbox("Género:", ["Masculino", "Femenino", "Otro"])
        
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
                if comparacion_actual <= total_comparaciones-1:
                    submitted = st.form_submit_button("Siguiente", on_click=next_comparison)
                else:
                    submitted = st.form_submit_button("Finalizar", on_click=end_test)
            
    else:
        resultados = st.session_state["resultados"]
        st.write("¡Prueba finalizada! Gracias por participar.")

        # Limpiar el estado para una nueva sesión (opcional)
        submitted = st.button("Comenzar una nueva prueba", on_click=new_test)

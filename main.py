import streamlit as st
import random
import string
from pathlib import Path
from pymongo import MongoClient

MONGO_URI = f"mongodb+srv://{st.secrets['db_username']}:{st.secrets['db_pswd']}@{st.secrets['cluster_name']}.j8rqe.mongodb.net/?retryWrites=true&w=majority&appName=test-subjetivo"
client = MongoClient(MONGO_URI)

db = client["results_db"]
collection = db["results_collection"]

# Parámetros
total_comparaciones = 16

# Configuración básica
st.set_page_config(page_title="Test Subjetivo", layout="centered")
# Inicialización de session_state
if "comparacion_actual" not in st.session_state:
    st.session_state["comparacion_actual"] = 0
    st.session_state["resultados"] = [None] * total_comparaciones
    st.session_state["disabled"] = True
    
    # Generar una lista con las comparaciones a realizar en orden aleatorio
    audio_folder = Path("data/audio_samples/")
    audios_originales = list((audio_folder / "original").glob("*.wav"))
    
    # Carpetas con los sistemas de procesamiento
    sistemas = {
        "as": audio_folder / "audioseal",
        "sc": audio_folder / "silentcipher",
        "wm": audio_folder / "wavmark"
    }
    
    # Lista de pares de comparación
    comparaciones = []
    # Generar comparaciones entre los originales y los procesados
    for audio_original in audios_originales:
        # Obtener el ID del archivo (e.g., F1, F2, M1, M2)
        audio_id = audio_original.stem.split('_')[0]
        # Comparar audios originales entre sí
        comparaciones.append((audio_original, audio_original))
        # Comparar con los audios en las otras carpetas
        for sistema, carpeta in sistemas.items():
            archivo_procesado = carpeta / f"{audio_id}_{sistema}.wav"
            if archivo_procesado.exists():
                comparaciones.append((audio_original, archivo_procesado))
                
    random.shuffle(comparaciones)            
    st.session_state["comparaciones"] = comparaciones

# Función para reproducir audios
def play_audio(audio_path):
    st.audio(str(audio_path))

# Título de la aplicación
st.title("Test de Calidad de Audio - DMOS")

# Datos del sujeto
if st.session_state["comparacion_actual"] == 0:
    with st.form(key="datos_sujeto_form"):
        age = st.number_input("Edad:", min_value=0, max_value=120)
        exp = st.selectbox("Experiencia de escucha:", ["Escucho música regularmente", "Trabajo en algo relacionado con la música", "No suelo escuchar música"])
        gender = st.selectbox("Género:", ["Masculino", "Femenino", "Otro"])
        
        submitted = st.form_submit_button("Comenzar test")
        if submitted:
            st.session_state.age = age
            st.session_state.exp = exp
            st.session_state.gender = gender
            st.session_state["comparacion_actual"] += 1
            st.rerun()
            
# Si el usuario está en la primera comparación o en cualquier comparación posterior
if st.session_state["comparacion_actual"] > 0:
    comparacion_actual = st.session_state["comparacion_actual"]

    if comparacion_actual <= total_comparaciones:
        # Seleccionamos un audio y un sistema aleatorio
        audio_a, audio_b = st.session_state["comparaciones"][comparacion_actual - 1]

        # Iniciamos el formulario de comparación
        with st.form(key="dmos_form"):
            st.write(f"Comparación {comparacion_actual} de {total_comparaciones}")
            
            st.write("Audio A")
            play_audio(audio_a)

            st.write("Audio B")
            play_audio(audio_b)
            
            st.write(f"¿Cómo describirías la degradación percibida en el audio B con respecto al audio A?")
            # Opciones de puntaje DMOS con radio buttons
            opciones = {
                5: "Degradación inaudible",
                4: "Degradación audible, pero no molesta",
                3: "Degradación ligeramente molesta",
                2: "Degradación molesta",
                1: "Degradación muy molesta"
            }

            # Actualización del puntaje de la comparación
            st.session_state["resultados"][comparacion_actual - 1] = st.radio(
                "Calidad percibida", 
                list(opciones.keys()), 
                format_func=lambda x: opciones[x], 
                key=f"dmos_{comparacion_actual}",
                index=st.session_state["resultados"][comparacion_actual - 1]
            )
            
            # Botones "Volver atrás" y "Siguiente" o "Finalizar" en la última comparación
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("Atrás")
                if submitted:
                    st.session_state["comparacion_actual"] -= 1
                    st.rerun()
            with col2:
                if comparacion_actual <= total_comparaciones-1:
                    submitted = st.form_submit_button("Siguiente")
                    if submitted:
                        st.session_state["comparacion_actual"] += 1
                        st.rerun()
                else:
                    submitted = st.form_submit_button("Finalizar")
                    if submitted:
                        nuevo_documento = {
                            "id_participante": ''.join(random.choices(string.ascii_letters + string.digits, k=4)),   # ID generado
                            "edad": st.session_state.age,                   # Edad
                            "genero": st.session_state.gender,              # Género
                            "experiencia": st.session_state.exp,            # Experiencia de escucha
                            "resultados": st.session_state.resultados       # Resultados
                        } 
                        collection.insert_one(nuevo_documento)
                        st.success("Resultados guardados correctamente en la base de datos.")
                        # Avanzamos a la pantalla de agradecimiento
                        st.session_state["comparacion_actual"] += 1
                        st.rerun()
                        
    else:
        st.success("Resultados guardados correctamente en la base de datos.")
        st.write("¡Prueba finalizada! Gracias por participar.")
        # Limpiar el estado para una nueva sesión (opcional)
        submitted = st.button("Comenzar una nueva prueba")
        if submitted:
            st.session_state["comparacion_actual"] = 0
            st.session_state["resultados"] = [None] * total_comparaciones
            st.rerun()

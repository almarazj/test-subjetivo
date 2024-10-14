import streamlit as st
import random
import string
from pathlib import Path
from pymongo import MongoClient

# Database using mongodb
MONGO_URI = f"mongodb+srv://{st.secrets['db_username']}:{st.secrets['db_pswd']}@{st.secrets['cluster_name']}.j8rqe.mongodb.net/?retryWrites=true&w=majority&appName=test-subjetivo"
client = MongoClient(MONGO_URI)

db = client["results_db"]
collection = db["results_collection"]

# Parámetros
total_comparaciones = 16

# Checkbox for mobile users
if "center" not in st.session_state:
    layout = "centered"
else:
    layout = "wide" if st.session_state.center else "centered"

st.set_page_config(page_title="Test Subjetivo", page_icon=":loud_sound:", layout=layout)

st.checkbox(
    "¿Estás usando un teléfono?", key="center", value=st.session_state.get("center", False), help="Chequeá la casilla si el contenido se ve muy angosto en tu pantalla."
)


# Inicialización de session_state
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "registro"
    st.session_state["resultados"] = [None] * total_comparaciones
    
    # Generar una lista con las comparaciones a realizar en orden aleatorio
    audio_folder = Path("data/audio_samples/")
    audios_originales = list((audio_folder / "original").glob("*.wav"))
    cal_file = Path("data/audio_samples/calibration/cal.wav")
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
    st.session_state.cal = cal_file

# Función para reproducir audios
def play_audio(audio_path):
    st.audio(str(audio_path))

# Título de la aplicación
st.title("Test de degradación de la calidad de audio")

# Datos del sujeto
if st.session_state["pagina_actual"] == "registro":
    st.header("Bienvenido/a :wave:")
    st.write(
    """
    ¡Hola! Antes que nada muchas gracias por participar. A continuación se encuentra una prueba subjetiva con una duración estimada de 6 minutos. 
    Tendrás que realizar comparaciones entre dos audios: el primero será el original y el segundo un audio procesado. 
    Tu tarea será indicar qué tan degradado te parece el segundo audio con respecto al original, utilizando la escala presentada.

    Por favor, ubicate en un lugar tranquilo y usá auriculares de ser posible. 
    El test es completamente anónimo, sólo te pido algunos datos para el análisis estadístico de los resultados.
    """
    )
    with st.form(key="datos_sujeto_form"):
        age = st.number_input("Edad:", min_value=10, max_value=90, value=None, placeholder="Ingresá tu edad")
        gender = st.selectbox("Género:",
                        ["Masculino", "Femenino", "Otro"],
                        index=None,
                        placeholder="Seleccioná tu género")
        exp = st.selectbox("Experiencia de escucha:",
                           ["Trabajo/estudio relacionado a la música", "Escucho música regularmente", "No suelo escuchar música"],
                           index=None,
                           placeholder="Seleccioná la opción con la que te identifiques")
        sist = st.selectbox("Sistema de escucha:",
                            ["Auriculares in-ear [Recomendado]", "Auriculares over-ear [Recomendado]", "Altoparlantes (PC, laptop o smartphone)"],
                            index=None,
                            placeholder="Seleccioná tu sistema de escucha")
        
        submitted = st.form_submit_button("Continuar")
        if submitted:
            if None not in (age, exp, sist, gender):
                st.session_state.age = age
                st.session_state.exp = exp
                st.session_state.sist = sist
                st.session_state.gender = gender
                st.session_state["pagina_actual"] = "calibracion"
                st.rerun()
            else:
                st.error("Falta algún dato del formulario")

if st.session_state["pagina_actual"] == "calibracion":
    
    with st.form(key="cal_form"):
        st.subheader("Calibración", divider=True)
        st.write("Antes de continuar, reproducí el siguiente audio y ajustá el volumen de tu dispositivo según tu preferencia, de manera que puedas escuchar cómodamente. Al finalizar presioná el boton 'Comenzar Test' y no modifiques el volumen hasta finalizar la prueba.")
        play_audio(st.session_state.cal)    
        submitted = st.form_submit_button("Comenzar Test")
        if submitted:
            st.session_state["pagina_actual"] = "comparaciones"
            st.rerun()

# Comienzo del test
if st.session_state["pagina_actual"] == "comparaciones":
    st.write("Todo listo! Por favor escuchá una única vez cada audio y elegí una respuesta en base a las diferencias que percibiste. Si no notas diferencia alguna podes indicar que la degradación es inaudible.")
    # Iniciamos el formulario de comparación
    with st.form(key="dmos_form"):
        for i in range(total_comparaciones):
            
            st.subheader(f"Comparación {i+1} de {total_comparaciones}", divider=True)
            
            audio_a, audio_b = st.session_state["comparaciones"][i]
            
            st.write("Audio A")
            play_audio(audio_a)

            st.write("Audio B")
            play_audio(audio_b)
        
            # Opciones de puntaje DMOS con radio buttons
            opciones = {
                5: "Degradación inaudible",
                4: "Degradación audible, pero no molesta",
                3: "Degradación ligeramente molesta",
                2: "Degradación molesta",
                1: "Degradación muy molesta"
            }
            
            st.write("¿Cómo describirías la degradación percibida en el audio B con respecto al audio A?")
            # Actualización del puntaje de la comparación
            st.session_state["resultados"][i] = {
                "audio": audio_b.stem,
                "puntaje": st.radio(
                    label="opciones",
                    options=list(opciones.keys()), 
                    format_func=lambda x: opciones[x], 
                    key=f"dmos_{i}",
                    index=None,
                    label_visibility="collapsed"
                )
            }
            
            # O puedes añadir un poco más de espacio
            st.write("\n\n")
        # Finalizar test
        submitted = st.form_submit_button("Finalizar")
        if submitted:
            resultados_dict = {}
            for resultado in st.session_state["resultados"]:
                audio_b_name = resultado["audio"]  # Nombre del archivo audio_b
                puntaje = resultado["puntaje"]  # Puntaje seleccionado
                resultados_dict[audio_b_name] = puntaje
            
            if None in resultados_dict.values():
                st.error("Por favor completá todas las comparaciones.")
            else:
                nuevo_documento = {
                    "id_participante": ''.join(random.choices(string.ascii_letters + string.digits, k=4)),   # ID generado
                    "edad": st.session_state.age,                   # Edad
                    "genero": st.session_state.gender,              # Género
                    "sistema": st.session_state.sist,               # Sistema de escucha
                    "experiencia": st.session_state.exp,            # Experiencia de escucha
                    "resultados": resultados_dict       # Resultados
                } 
                collection.insert_one(nuevo_documento)
                # Avanzamos a la pantalla de agradecimiento
                st.session_state["pagina_actual"] = "final"
                st.rerun()
             
if st.session_state["pagina_actual"] == "final":
    st.success("Resultados guardados correctamente en la base de datos.")
    st.write("¡Prueba finalizada! Gracias por participar.")
    # Limpiar el estado para una nueva sesión (opcional)
    submitted = st.button("Comenzar una nueva prueba")
    if submitted:
        st.session_state["pagina_actual"] = "registro"
        st.session_state["resultados"] = [None] * total_comparaciones
        st.rerun()

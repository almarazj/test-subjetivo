import streamlit as st
import csv
import random
import os
from pathlib import Path
from utils import play_audio

# Configuración básica
st.set_page_config(page_title="Audio AB Test", layout="centered")

# Datos del usuario
st.title("Test Subjetivo de Audio - DMOS")
st.write("Por favor, ingresa tus datos antes de comenzar el test.")

# Preguntas
edad = st.slider("Edad", 18, 80, 25)
experiencia = st.selectbox("Experiencia de escucha", ["Escucho música regularmente", "Trabajo en algo relacionado con la música", "No suelo escuchar música"])
genero = st.selectbox("Género", ["Masculino", "Femenino", "Otro", "Prefiero no decir"])
sistema_audio = st.selectbox("¿Cómo estás escuchando el test?", ["Auriculares", "Parlantes", "Celular"])

# Guardar las respuestas en un CSV
def guardar_respuesta(edad, experiencia, genero, sistema_audio, dmos_score, audio_id, sistema):
    filepath = Path("results/results.csv")
    filepath.parent.mkdir(exist_ok=True, parents=True)
    
    with open(filepath, mode="a", newline='') as file:
        writer = csv.writer(file)
        writer.writerow([edad, experiencia, genero, sistema_audio, dmos_score, audio_id, sistema])

# Iniciar el test
st.header("Evaluación de los audios")
st.write("A continuación, escucharás pares de audios degradados por diferentes sistemas. Evalúa la calidad percibida.")

# Selección de los audios
audio_folder = Path("data/audio_samples/")
audios_originales = list((audio_folder / "original").glob("*.wav"))

# Test AB
if st.button("Comenzar test"):
    audio_prueba = random.choice(audios_originales)
    
    st.write(f"Audio de referencia: {audio_prueba.name}")
    play_audio(audio_prueba)
    
    sistemas = ["wavmark", "audioseal", "silentcipher"]
    random.shuffle(sistemas)
    
    for sistema in sistemas:
        st.write(f"Sistema {sistema}")
        audio_degradado = audio_folder / sistema / audio_prueba.name.replace(".wav", f"_{sistema[:2]}.wav")
        play_audio(audio_degradado)
        
        dmos_score = st.slider(f"Calidad percibida para {sistema}", 1, 5, 3)
        
        if st.button(f"Guardar resultado para {sistema}"):
            guardar_respuesta(edad, experiencia, genero, sistema_audio, dmos_score, audio_prueba.name, sistema)
            st.success(f"Guardado el resultado para {sistema} correctamente.")

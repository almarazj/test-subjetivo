import streamlit as st

def play_audio(audio_path):
    """Función para reproducir un archivo de audio en la app Streamlit."""
    audio_file = open(audio_path, 'rb')
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/wav')

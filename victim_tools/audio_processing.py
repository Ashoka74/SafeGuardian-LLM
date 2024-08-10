# audio_processing.py

from faster_whisper import WhisperModel
import io
import numpy as np
import logging
import requests
import os
import streamlit as st
import base64

logger = logging.getLogger(__name__)

MODEL_SIZE = "large-v2"
model = None

def load_model():
    global model
    if model is None:
        try:
            model = WhisperModel(MODEL_SIZE, device="cuda", compute_type="float16")
            logger.info(f"Loaded Whisper model: {MODEL_SIZE}")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="float16")
            logger.info(f"Loaded Whisper model on CPU: {MODEL_SIZE}")
    return model

def process_audio(audio):
    if audio is not None:
        try:
            audio_buffer = io.BytesIO()
            audio.export(audio_buffer, format="wav", parameters=["-ar", str(16000)])
            audio_array = np.frombuffer(audio_buffer.getvalue()[44:], dtype=np.int16).astype(np.float32) / 32768.0

            model = load_model()
            segments, _ = model.transcribe(audio_array)
            text = ' '.join([segment.text for segment in segments])
            logger.info(f"Transcribed audio: {text[:50]}...")
            return text
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return None
    else:
        return None
    


def text_to_speech_elevenlabs(text):
    text = ''.join(text)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
    elevenlab_api = os.getenv('elevenlabs_api')
    headers = {
    "accept": "audio/mpeg",
    "xi-api-key": elevenlab_api,
    "Content-Type": "application/json",
    }

    data = {"text": text}
    response = requests.post(url, headers = headers, json=data)

    if response.status_code == 200:
        print(response.status_code)
        return response.content
    else:
        print(f"Error: {response.status_code}, {response.content}")
        return None
    
def play_audio(text):
    try:
        if '```' in text:
            text = text.split('```')[-1]
        print(text)
        audio_content = text_to_speech_elevenlabs(text)
        # audio_content = text_to_speech_openai(text)

        if audio_content is not None:
            audio_content = io.BytesIO(audio_content)
            audio_content.seek(0) 
            audio_base_64 = base64.b64encode(audio_content.read()).decode("utf-8")
            st.audio(audio_content, format='audio/mpeg', autoplay=True)
    except Exception as e:
        print(f'Error :{e}')

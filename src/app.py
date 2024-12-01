import subprocess
from flask import Flask, request, jsonify
from PIL import Image
import base64
import numpy as np
import imageio_ffmpeg as ffmpeg
from transformers import pipeline

app = Flask(__name__)
whisper_model = pipeline("automatic-speech-recognition", model="openai/whisper-small")

# Funzione per leggere e preprocessare l'audio con ffmpeg tramite subprocess
def load_audio_with_ffmpeg(file_path, target_sr=16000):
    # Ottieni il percorso dell'eseguibile ffmpeg
    ffmpeg_exe = ffmpeg.get_ffmpeg_exe()
    
    # Comando ffmpeg per convertire l'audio
    ffmpeg_cmd = [
        ffmpeg_exe,
        "-i", file_path,         # Input file
        "-f", "wav",             # Output formato WAV
        "-ar", str(target_sr),   # Campionamento a 16 kHz
        "-ac", "1",              # Mono
        "pipe:1"                 # Output come stream binario
    ]
    
    # Esegui il comando e cattura l'output
    process = subprocess.run(
        ffmpeg_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True
    )
    
    # Converte il risultato binario in array NumPy
    wav_data = process.stdout
    audio = np.frombuffer(wav_data, dtype=np.int16)
    return audio


@app.route('/upload', methods=['POST'])
def upload():
    data = request.get_json()
    if not data:
      return jsonify({'error': 'Data required'}), 400
    
    has_image = 'image' in data
    has_audio = 'audio' in data

    text = ''
    
    if has_image:
      image_b64 = data['image']

      try:
        image_data = base64.b64decode(image_b64)
      except Exception as _:
        return jsonify({'error': 'Invalid image file'}), 400
    
    if has_audio:
      audio_b64 = data['audio']
      try:
        audio_data = base64.b64decode(audio_b64)

        # write the audio data to a file
        with open('audio.wav', 'wb') as audio_file:
            audio_file.write(audio_data)

        audio_final = load_audio_with_ffmpeg('audio.wav')

        # Use Whisper's `transcribe` method with the buffer
        result = whisper_model(audio_final)

        text = result['text']
        #text = 'test'
      except Exception as e:
        return jsonify({'error': f'Error occurred while processing audio file: {str(e)}'}), 500
    else:
      text = data['text']

    return jsonify({'OK': 'Data uploaded', 'trascription': text}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

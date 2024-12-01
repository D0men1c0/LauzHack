from io import BytesIO
import io
from flask import Flask, request, jsonify
from PIL import Image
import base64
from transformers import pipeline
import os
import numpy as np
from pydub import AudioSegment
from scipy.io import wavfile

app = Flask(__name__)
whisper_model = pipeline("automatic-speech-recognition", model="openai/whisper-small")

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

        # Create a byte buffer
        audio_buffer = io.BytesIO(audio_data)

        # Use Whisper's `transcribe` method with the buffer
        result = whisper_model(audio_buffer)

        text = result['text']
        text = 'test'
      except Exception as e:
        return jsonify({'error': f'Error occurred while processing audio file: {str(e)}'}), 500
    else:
      text = data['text']

    return jsonify({'OK': 'Data uploaded', 'trascription': text}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

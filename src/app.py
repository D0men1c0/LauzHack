from flask import Flask, request, jsonify
from PIL import Image
import base64
import os

app = Flask(__name__)
#whisper_model = pipeline("automatic-speech-recognition", model="openai/whisper-small")

@app.route('/upload', methods=['POST'])
def upload():
    data = request.get_json()
    if not data:
      return jsonify({'error': 'Data required'}), 400
    
    has_image = 'image' in data
    has_audio = 'audio' in data

    text = ''
    
    if has_image:
      image_b64 = request.files['image']

      try:
        image_data = base64.b64encode(image_b64)
      except Exception as _:
        return jsonify({'error': 'Invalid image file'}), 400
    
    if has_audio:
      audio_b64 = request.files['audio']
      try:
        audio_data = base64.b64encode(audio_b64)
        
        #result = whisper_model(audio_path)
        #text = result['text']
        text = 'test'
      except Exception as e:
        return jsonify({'error': 'Error occurred while processing audio file'}), 500
    else:
      text = data['text']

    return jsonify({'OK': 'Data uploaded', 'trascription': text}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

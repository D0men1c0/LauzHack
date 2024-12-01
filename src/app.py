import subprocess
from flask import Flask, request, jsonify
import base64
import numpy as np
import imageio_ffmpeg as ffmpeg
from transformers import pipeline

app = Flask(__name__)
whisper_model = pipeline("automatic-speech-recognition", model="openai/whisper-small")


# Function to read and preprocess the audio with ffmpeg via subprocess
def load_audio_with_ffmpeg(file_path, target_sr=16000):
    # Get the path of the ffmpeg executable
    ffmpeg_exe = ffmpeg.get_ffmpeg_exe()

    # ffmpeg command to convert the audio
    ffmpeg_cmd = [
        ffmpeg_exe,
        "-i", file_path,         # Input file
        "-f", "wav",             # Output format WAV
        "-ar", str(target_sr),   # Resample to 16 kHz
        "-ac", "1",              # Mono
        "pipe:1"                 # Output as binary stream
    ]

    # Run the command and capture output
    try:
        process = subprocess.run(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        # Convert the binary result to a NumPy array
        wav_data = process.stdout
        audio = np.frombuffer(wav_data, dtype=np.int16)
        return audio
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error with ffmpeg: {e.stderr.decode()}")


@app.route('/upload', methods=['POST'])
def upload():
    try:
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
                # Process image if needed
            except Exception:
                return jsonify({'error': 'Invalid image file'}), 400

        if has_audio:
            audio_b64 = data['audio']
            try:
                audio_data = base64.b64decode(audio_b64)

                # Write the audio data to a file
                with open('audio.wav', 'wb') as audio_file:
                    audio_file.write(audio_data)

                # Preprocess the audio file
                audio_final = load_audio_with_ffmpeg('audio.wav')

                # Use Whisper to transcribe
                result = whisper_model(audio_final)
                text = result['text']
            except Exception as e:
                return jsonify({'error': f'Error occurred while processing audio file: {str(e)}'}), 500
        else:
            if 'text' in data:
                text = data['text']
            else:
                return jsonify({'error': 'No audio or text provided'}), 400

        return jsonify({'OK': 'Data uploaded', 'transcription': text}), 200
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)

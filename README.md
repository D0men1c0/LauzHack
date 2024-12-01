# VisionAI Assistant

VisionAI Assistant is a mobile application designed to analyze and interpret visual content using advanced AI technologies. Users can upload photos and interact with the app by submitting questions through text or voice recordings. The system processes these inputs to provide detailed insights into the image.

The backend is built with a Python Flask server that integrates OpenAI's APIs and Meta's segmentation algorithms, allowing precise analysis of the uploaded images. Speech-to-text conversion is handled by OpenAI's Whisper model, enabling accurate transcription of voice commands. The frontend, developed in Flutter, ensures a responsive and consistent user interface across platforms.

## Features

- **Image Analysis:** Supports natural language queries about images, such as counting objects or identifying specific attributes (e.g., "How many cars are in this image?" or "Are there any red houses?").
- **Multimodal Input:** Allows users to interact via text or voice, adapting to different preferences.
- **Dynamic Output:** Results include visual highlights, such as bounding boxes or annotations directly on the image.
- **Re-querying:** Users can ask additional questions about the same image without re-uploading it.
- **Cross-Platform Support:** Flutter ensures compatibility with many devices.


## Getting Started

To run the VisionAI Assistant locally, follow these steps:

### 1. Set up the Backend

Navigate to the `src` directory where the Flask server is located and start the server with the following command:

```bash
python app.py
```

Ensure you have all the required dependencies installed (see the `requirements.txt` file for details).

### 2. Set up the Frontend

The graphical user interface for VisionAI Assistant is built with Flutter. To run it:

1. Ensure you have Flutter installed on your machine. Follow the [official Flutter installation guide](https://docs.flutter.dev/get-started/install) if needed.
2. Connect your smartphone to your computer via USB if you wish to run the app on your mobile device. Make sure USB debugging is enabled.
3. Navigate to the Flutter project directory and start the app with the following command:

```bash
flutter run
```

If your device is connected, the app will be deployed and launched on your smartphone.


## Notes

- Ensure the Flask server is running before starting the Flutter frontend.
- Both components must communicate over the same network. If running on different devices, ensure network compatibility and configure the API endpoint in the Flutter project accordingly.


## Contributing

Feel free to contribute to VisionAI Assistant by submitting pull requests or raising issues in this repository.


## License

This project is licensed under the [MIT License](LICENSE).
import 'dart:io';
import 'dart:convert';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_sound/flutter_sound.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:path_provider/path_provider.dart';
import 'package:http/http.dart' as http;
import 'second_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Vitol Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blueAccent,
          brightness: Brightness.light,
        ),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _textController = TextEditingController();
  final ImagePicker _picker = ImagePicker();

  File? _photo;
  File? _video;
  String? _text;
  File? _voiceFile;
  FlutterSoundRecorder? _audioRecorder;
  FlutterSoundPlayer? _audioPlayer;
  bool _isRecording = false;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _audioRecorder = FlutterSoundRecorder();
    _audioPlayer = FlutterSoundPlayer();
    _initRecorder();
    _initPlayer();
  }

  @override
  void dispose() {
    _audioRecorder?.closeRecorder();
    _audioPlayer?.closePlayer();
    super.dispose();
  }

  Future<void> _initRecorder() async {
    final status = await Permission.microphone.request();
    if (status != PermissionStatus.granted) {
      throw 'Microphone permission not granted';
    }
    await _audioRecorder?.openRecorder();
  }

  Future<void> _initPlayer() async {
    await _audioPlayer?.openPlayer();
  }

  Future<void> _startRecording() async {
    final directory = await getTemporaryDirectory();
    final filePath =
        '${directory.path}/audio_${DateTime.now().millisecondsSinceEpoch}.wav';

    await _audioRecorder?.startRecorder(
      toFile: filePath,
      codec: Codec.pcm16WAV,
    );

    setState(() {
      _isRecording = true;
    });
  }

  Future<void> _stopRecording() async {
    final path = await _audioRecorder?.stopRecorder();
    setState(() {
      _isRecording = false;
      if (path != null) {
        _voiceFile = File(path);
        print('Saved WAV file: $path');
      }
    });
  }

  void _addText() {
    final text = _textController.text.trim();
    if (text.isNotEmpty) {
      setState(() {
        _text = text;
        _voiceFile = null;
        _textController.clear();
      });
    }
  }

  Future<void> _pickPhoto(ImageSource source) async {
    final XFile? photo = await _picker.pickImage(source: source);
    if (photo != null) {
      setState(() {
        _photo = File(photo.path);
      });
    }
  }

  Future<void> _pickVideo(ImageSource source) async {
    final XFile? video = await _picker.pickVideo(source: source);
    if (video != null) {
      setState(() {
        _video = File(video.path);
      });
    }
  }

  Future<void> _submitContent() async {
    if (_text == null && _voiceFile == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text(
                'Please add either text or a voice recording before submitting.')),
      );
      return;
    }

    setState(() {
      _isSubmitting = true;
    });

    // Prepare the payload
    Map<String, dynamic> payload = {};

    try {
      if (_photo != null) {
        // Encode image as base64
        final imageBytes = await _photo!.readAsBytes();
        payload['image'] = base64Encode(imageBytes);
      }

      if (_voiceFile != null) {
        // Encode audio as base64
        final audioBytes = await _voiceFile!.readAsBytes();
        payload['audio'] = base64Encode(audioBytes);
      }

      if (_text != null) {
        // Include text if provided
        payload['text'] = _text;
      }

      // Send the POST request
      final response = await http.post(
        Uri.parse(
            'http://ec2-44-243-95-41.us-west-2.compute.amazonaws.com/upload'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => SecondScreen(initialData: responseData),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Server Error: ${response.body}')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      setState(() {
        _isSubmitting = false;
      });
    }
  }

  void _removePhoto() => setState(() => _photo = null);
  void _removeVideo() => setState(() => _video = null);
  void _removeText() => setState(() => _text = null);
  void _removeVoice() => setState(() => _voiceFile = null);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Vitol Demo'),
        centerTitle: true,
      ),
      body: Column(
        children: [
          const Spacer(),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Container(
              width: double.infinity,
              height: MediaQuery.of(context).size.height * 0.4,
              decoration: BoxDecoration(
                color: Colors.grey[200],
                borderRadius: BorderRadius.circular(15),
                border: Border.all(color: Colors.grey.shade400, width: 2),
                boxShadow: [
                  BoxShadow(
                    color: Colors.grey.withOpacity(0.5),
                    blurRadius: 10,
                    offset: const Offset(0, 5),
                  ),
                ],
              ),
              child: Wrap(
                alignment: WrapAlignment.start,
                spacing: 10,
                runSpacing: 10,
                children: [
                  if (_photo != null)
                    _buildPreview(
                      label: "Photo",
                      onRemove: _removePhoto,
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(10),
                        child: Image.file(
                          _photo!,
                          fit: BoxFit.cover,
                        ),
                      ),
                    ),
                  if (_video != null)
                    _buildPreview(
                      label: "Video",
                      onRemove: _removeVideo,
                      child: const Icon(Icons.videocam,
                          size: 50, color: Colors.orange),
                    ),
                  if (_text != null)
                    _buildPreview(
                      label: "Text",
                      onRemove: _removeText,
                      child: Center(
                        child: Text(
                          _text!,
                          overflow: TextOverflow.ellipsis,
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                              fontSize: 14, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ),
                  if (_voiceFile != null)
                    _buildPreview(
                      label: "Voice",
                      onRemove: _removeVoice,
                      child: IconButton(
                        icon: Icon(
                          _audioPlayer?.isPlaying == true
                              ? Icons.pause
                              : Icons.play_arrow,
                        ),
                        onPressed: () async {
                          if (_audioPlayer?.isPlaying == true) {
                            await _audioPlayer?.stopPlayer();
                          } else if (_voiceFile != null) {
                            await _audioPlayer?.startPlayer(
                              fromURI: _voiceFile!.path,
                              codec: Codec.pcm16WAV,
                              whenFinished: () {
                                setState(() {});
                              },
                            );
                          }
                          setState(() {});
                        },
                      ),
                    ),
                ],
              ),
            ),
          ),
          if (_photo != null ||
              _video != null ||
              _text != null ||
              _voiceFile != null)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 16.0),
              child: ElevatedButton(
                onPressed:
                    (_isSubmitting || (_text == null && _voiceFile == null))
                        ? null
                        : _submitContent,
                style: ElevatedButton.styleFrom(
                  padding:
                      const EdgeInsets.symmetric(vertical: 12, horizontal: 24),
                  backgroundColor:
                      (_isSubmitting || (_text == null && _voiceFile == null))
                          ? Colors.grey
                          : Colors.blueAccent,
                ),
                child: _isSubmitting
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2.5,
                          valueColor:
                              AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      )
                    : const Text('Submit'),
              ),
            ),
          const Spacer(),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(
              children: [
                FloatingActionButton(
                  onPressed: () => _pickPhoto(ImageSource.gallery),
                  mini: true,
                  heroTag: 'photoButton',
                  tooltip: "Add Photo",
                  child: const Icon(Icons.photo),
                ),
                const SizedBox(width: 10),
                FloatingActionButton(
                  onPressed: () => _pickVideo(ImageSource.gallery),
                  mini: true,
                  heroTag: 'videoButton',
                  tooltip: "Add Video",
                  child: const Icon(Icons.video_library),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: TextField(
                    controller: _textController,
                    decoration: InputDecoration(
                      hintText: "Add text...",
                      filled: true,
                      fillColor: Colors.grey[200],
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(30),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                          vertical: 10, horizontal: 20),
                    ),
                    onSubmitted: (_) => _addText(),
                  ),
                ),
                const SizedBox(width: 10),
                FloatingActionButton(
                  onPressed: _isRecording ? _stopRecording : _startRecording,
                  mini: true,
                  heroTag: 'recordButton',
                  tooltip: _isRecording ? "Stop Recording" : "Record Voice",
                  child: Icon(_isRecording ? Icons.stop : Icons.mic),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPreview({
    required String label,
    required VoidCallback onRemove,
    required Widget child,
  }) {
    return Stack(
      children: [
        Container(
          width: 100,
          height: 100,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: Colors.blueGrey, width: 2),
            boxShadow: [
              BoxShadow(
                color: Colors.grey.withOpacity(0.5),
                blurRadius: 5,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: child,
        ),
        Positioned(
          top: 4,
          right: 4,
          child: GestureDetector(
            onTap: onRemove,
            child: const CircleAvatar(
              radius: 12,
              backgroundColor: Colors.red,
              child: Icon(Icons.close, color: Colors.white, size: 16),
            ),
          ),
        ),
      ],
    );
  }
}

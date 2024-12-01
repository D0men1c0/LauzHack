import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:image/image.dart' as img;
import 'package:http/http.dart' as http;

class SecondScreen extends StatefulWidget {
  final Map<String, dynamic> initialData;

  const SecondScreen({super.key, required this.initialData});

  @override
  State<SecondScreen> createState() => _SecondScreenState();
}

class _SecondScreenState extends State<SecondScreen> {
  int _currentIndex = 0;
  final List<Map<String, dynamic>> _outputs = [];
  late FlutterTts _flutterTts;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _flutterTts = FlutterTts();

    if (widget.initialData.isNotEmpty) {
      _outputs.add(widget.initialData);
    }
  }

  @override
  void dispose() {
    _flutterTts.stop();
    super.dispose();
  }

  Future<void> _resendData() async {
    final currentInput = _outputs[_currentIndex];
    setState(() {
      _isLoading = true;
    });

    try {
      Map<String, dynamic> payload = {};

      if (currentInput.containsKey("image") && currentInput["image"] != null) {
        payload["image"] = currentInput["image"];
      }
      if (currentInput.containsKey("audio") && currentInput["audio"] != null) {
        payload["audio"] = currentInput["audio"];
      }
      if (currentInput.containsKey("text") && currentInput["text"] != null) {
        payload["text"] = currentInput["text"];
      }

      final response = await http.post(
        Uri.parse(
            'http://ec2-44-243-95-41.us-west-2.compute.amazonaws.com/upload'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        setState(() {
          _outputs.add(responseData);
          _currentIndex = _outputs.length - 1;
        });
      } else {
        throw Exception(
            'Failed to resend data. Server responded with ${response.body}');
      }
    } catch (e) {
      print("Error during re-sending: $e");
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error during re-sending: $e")),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Uint8List? _correctImageOrientation(Uint8List imageBytes) {
    try {
      final image = img.decodeImage(imageBytes);
      if (image == null) return imageBytes;
      final orientedImage = img.bakeOrientation(image);
      return Uint8List.fromList(img.encodeJpg(orientedImage));
    } catch (e) {
      print("Error correcting image orientation: $e");
      return imageBytes;
    }
  }

  @override
  Widget build(BuildContext context) {
    final currentOutput = _outputs.isNotEmpty ? _outputs[_currentIndex] : null;

    return Scaffold(
      appBar: AppBar(
        title: const Text('LauzHack 2024 - Demo'),
        centerTitle: true,
      ),
      body: Column(
        children: [
          const Spacer(),
          Expanded(
            flex: 6,
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Container(
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
                child: currentOutput != null
                    ? SingleChildScrollView(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            if (currentOutput.containsKey("image") &&
                                currentOutput["image"] != null)
                              Stack(
                                children: [
                                  Container(
                                    width: double.infinity,
                                    height: MediaQuery.of(context).size.height *
                                        0.3,
                                    decoration: BoxDecoration(
                                      borderRadius: const BorderRadius.vertical(
                                          top: Radius.circular(15)),
                                    ),
                                    child: _buildImageFromBase64(
                                        currentOutput["image"]),
                                  ),
                                ],
                              )
                            else
                              const Padding(
                                padding: EdgeInsets.all(16.0),
                                child: Center(
                                  child: Text(
                                    "No image available.",
                                    style: TextStyle(
                                      fontSize: 16,
                                      color: Colors.grey,
                                    ),
                                  ),
                                ),
                              ),
                            if (currentOutput.containsKey("text") &&
                                currentOutput["text"] != null)
                              Padding(
                                padding: const EdgeInsets.all(16.0),
                                child: Column(
                                  children: [
                                    FloatingActionButton(
                                      onPressed: () => _speak(
                                          currentOutput["text"] ?? "No text"),
                                      mini: true,
                                      child: const Icon(Icons.volume_up),
                                      tooltip: "Read Aloud",
                                    ),
                                    const SizedBox(height: 16),
                                    Text(
                                      currentOutput["text"],
                                      textAlign: TextAlign.center,
                                      style: const TextStyle(
                                        fontSize: 18,
                                        fontWeight: FontWeight.w500,
                                        color: Colors.black87,
                                      ),
                                    ),
                                  ],
                                ),
                              )
                            else
                              const Padding(
                                padding: EdgeInsets.all(16.0),
                                child: Center(
                                  child: Text(
                                    "No text available.",
                                    style: TextStyle(
                                      fontSize: 16,
                                      color: Colors.grey,
                                    ),
                                  ),
                                ),
                              ),
                          ],
                        ),
                      )
                    : const Center(
                        child: Text(
                          "No response available. Re-send to get output.",
                          textAlign: TextAlign.center,
                          style: TextStyle(fontSize: 16, color: Colors.black54),
                        ),
                      ),
              ),
            ),
          ),
          const Spacer(),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              IconButton(
                icon: const Icon(Icons.arrow_back),
                onPressed: _outputs.isNotEmpty && _currentIndex > 0
                    ? () {
                        setState(() {
                          _currentIndex--;
                        });
                      }
                    : null,
              ),
              ElevatedButton(
                onPressed: _isLoading ? null : _resendData,
                style: ElevatedButton.styleFrom(
                  padding:
                      const EdgeInsets.symmetric(vertical: 12, horizontal: 24),
                ),
                child: _isLoading
                    ? const CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      )
                    : const Text('Re-send for New Response'),
              ),
              IconButton(
                icon: const Icon(Icons.arrow_forward),
                onPressed:
                    _outputs.isNotEmpty && _currentIndex < _outputs.length - 1
                        ? () {
                            setState(() {
                              _currentIndex++;
                            });
                          }
                        : null,
              ),
            ],
          ),
          const Spacer(),
        ],
      ),
    );
  }

  Widget _buildImageFromBase64(String base64String) {
    try {
      Uint8List imageBytes = base64Decode(base64String);
      imageBytes = _correctImageOrientation(imageBytes) ?? imageBytes;
      return Image.memory(
        imageBytes,
        fit: BoxFit.cover,
        errorBuilder: (context, error, stackTrace) {
          return const Center(
            child: Text(
              "Failed to load image.",
              style: TextStyle(color: Colors.red),
            ),
          );
        },
      );
    } catch (e) {
      return const Center(
        child: Text(
          "Invalid image data.",
          style: TextStyle(color: Colors.red),
        ),
      );
    }
  }

  Future<void> _speak(String text) async {
    try {
      await _flutterTts.setLanguage("en-US");
      await _flutterTts.setPitch(1.0);
      await _flutterTts.speak(text);
    } catch (e) {
      print("Error during text-to-speech: $e");
    }
  }
}

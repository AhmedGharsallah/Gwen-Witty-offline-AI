# Gwen: Witty Offline AI Bestie 💅✨

Gwen is a fully offline, voice-interfaced AI companion. She uses **Ollama (Llama 3.2)** for her "brain," **SpeechRecognition** to hear you, and **Piper** for high-quality, neural text-to-speech.

## 🚀 Features
- **100% Offline:** No data leaves your machine.
- **Neural TTS:** Uses Piper for natural, non-robotic female speech.
- **Low Latency:** Real-time audio streaming (no temporary files).
- **Personality:** Custom "Witty Bestie" persona for fun banter.

## 🛠️ Prerequisites
1. **Ollama:** Download and install [Ollama](https://ollama.com/).
   - Pull the model: `ollama pull llama3.2:3b`
2. **Python 3.9+**
3. **Voice Models:** Download `en_US-amy-medium.onnx` and `en_US-amy-medium.onnx.json` from [Piper Voices](https://github.com/rhasspy/piper#voices) and place them in the project root.

## 📥 Installation

1. Clone the repo:
   ```bash
   git clone [https://github.com/AhmedGharsallah/Gwen-Witty-offline-AI.git](https://github.com/AhmedGharsallah/Gwen-Witty-offline-AI.git)
   cd YOUR_REPO_NAME

2. Install dependencies:
            pip install -r requirements.txt

3. Run the AI
            python chat.py

## 🎮 Commands
Speak naturally to chat.

Say "stop listening" to pause the mic.

Say "exit" or "bye" to quit.
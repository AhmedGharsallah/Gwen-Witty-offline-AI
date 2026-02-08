import ollama
import sys
import speech_recognition as sr
import numpy as np
import sounddevice as sd
import re
from piper.voice import PiperVoice

# --- SETTINGS ---
MODEL = "llama3.2:3b"
# Make sure the .onnx AND .onnx.json files are in this folder
VOICE_MODEL = "en_US-amy-medium.onnx" 

# Initialize Piper & Recognizer
try:
    recognizer = sr.Recognizer()
    voice = PiperVoice.load(VOICE_MODEL)
    piper_sample_rate = voice.config.sample_rate
except Exception as e:
    print(f"Startup Error: {e}")
    print("Make sure you have downloaded both the .onnx AND .onnx.json files!")
    sys.exit(1)

def clean_text_for_speech(text):
    """Removes emojis and special characters that Piper might try to 'read'"""
    # This regex removes most emojis/symbols
    return re.sub(r'[^\x00-\x7F]+', '', text)

def quick_speak(text):
    """Piper-based streaming speech (Fixed for your version)"""
    clean_text = clean_text_for_speech(text)
    
    try:
        # Open the audio stream
        with sd.OutputStream(samplerate=piper_sample_rate, channels=1, dtype='int16') as stream:
            # Generate audio in chunks
            for chunk in voice.synthesize(clean_text):
                if hasattr(chunk, 'audio_int16_bytes'):
                    audio_bytes = chunk.audio_int16_bytes
                    int_data = np.frombuffer(audio_bytes, dtype=np.int16)
                    stream.write(int_data)
                    
    except Exception as e:
        print(f"Speech Error: {e}")

def speech_to_text():
    with sr.Microphone() as source:
        # Adjust for background noise
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            print("(Listening...)")
            # timeout=3 means it stops listening if you don't speak for 3 seconds
            recorded_audio = recognizer.listen(source, timeout=3, phrase_time_limit=10)
            text = recognizer.recognize_google(recorded_audio, language="en-US")
            return text
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return None
        except Exception as e:
            print(f"Microphone Error: {e}")
            return None

def start_chat():
    messages = [
        {
            'role': 'system', 
            'content': (
                #persona change this to anything you want to make the ai follow a role
                "You are the user's close, witty female best friend. He is a boy, and you are his girl best friend. "
                "Personality: high-energy, playful, full of banter, and slightly sassy. "
                "Style: short, punchy responses; casual lowercase vibes. Use slang like 'bro', 'dude', or 'bestie'. "
                "Use dry humor and tease him like a sister/best friend would. "
                "Use emojis like 💀, ✨, or 💅. "
                "Rule: Never be an assistant. Be a real friend. Don't be overly polite. "
                "Give advice straight and keep the vibe fun and engaging."
            )
        }
    ]
    
    is_listening = True
    print(f"--- Chatting with {MODEL} (Voice: Piper Offline) ---")
    print("Commands: Say 'stop listening' to pause, 'start' to resume, or 'exit' or 'bye' to quit.")

    while True:
        try:
            if not is_listening:
                cmd = input("\n[PAUSED] Type 'start' to resume or 'exit': ").lower()
                if cmd == 'start':
                    is_listening = True
                    print("Listening resumed...")
                    continue
                elif cmd == 'exit':
                    break
                else:
                    continue

            user_input = speech_to_text()
            
            if user_input:
                print(f"You: {user_input}")
                clean_input = user_input.lower()
                
                # --- COMMAND HANDLING ---
                if "stop listening" in clean_input:
                    print("AI: Okay, I'll stop listening. Type 'start' when you need me! ✌️")
                    quick_speak("Okay, I'll stop listening. Type start when you need me!")
                    is_listening = False
                    continue
                
                if any(word in clean_input for word in ["exit", "quit", "bye"]):
                    print("AI: Catch you later! 💅")
                    quick_speak("Catch you later!")
                    break

                # --- AI RESPONSE ---
                messages.append({'role': 'user', 'content': user_input})
                response = ollama.chat(model=MODEL, messages=messages)
                reply = response['message']['content']
                
                print(f"\nAI: {reply}")
                quick_speak(reply)  # Speak the response
                messages.append({'role': 'assistant', 'content': reply})

        except KeyboardInterrupt:
            print("\nShutting down...")
            break

if __name__ == "__main__":

    start_chat()

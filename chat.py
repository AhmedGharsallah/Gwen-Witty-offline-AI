import ollama
import sys
import speech_recognition as sr
import numpy as np
import sounddevice as sd
import re
import random
import json
import os
from piper.voice import PiperVoice

# --- SETTINGS ---
MODEL = "llama3.2:3b"
VOICE_MODEL = "en_US-amy-medium.onnx" 
MEMORY_FILE = "memory.json"

# --- MOOD OPTIONS ---
MOODS = {
    "hyper": "You are extremely high-energy, using lots of exclamation marks and 'OMG'. You're excited about everything.",
    "grumpy": "You're a bit annoyed today. You use dry sarcasm and tease him for being 'annoying'.",
    "chill": "You're very relaxed and low-key. Casual, cool, and effortless vibes only.",
    "chaotic": "You're unpredictable and slightly unhinged. You love saying wild things just for the plot."
}

# --- MEMORY UTILITIES ---
def load_memory():
    """Loads user data. Defaults to 'bestie' if no name is known."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"user_name": "bestie", "facts": []}

def save_memory(data):
    """Saves user data to disk."""
    with open(MEMORY_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- AUDIO UTILITIES ---
try:
    recognizer = sr.Recognizer()
    voice = PiperVoice.load(VOICE_MODEL)
    piper_sample_rate = voice.config.sample_rate
except Exception as e:
    print(f"Startup Error: {e}")
    sys.exit(1)

def clean_text_for_speech(text):
    """Removes technical tags and emojis before sending to Piper."""
    # Remove hidden tags
    clean = re.sub(r'SAVE_FACT:.*', '', text)
    clean = re.sub(r'SET_NAME:.*', '', clean)
    # Remove non-ASCII (emojis)
    return re.sub(r'[^\x00-\x7F]+', '', clean).strip()

def quick_speak(text):
    """Handles the TTS output."""
    clean_text = clean_text_for_speech(text)
    if not clean_text:
        return
        
    try:
        with sd.OutputStream(samplerate=piper_sample_rate, channels=1, dtype='int16') as stream:
            for chunk in voice.synthesize(clean_text):
                if hasattr(chunk, 'audio_int16_bytes'):
                    audio_bytes = chunk.audio_int16_bytes
                    int_data = np.frombuffer(audio_bytes, dtype=np.int16)
                    stream.write(int_data)
    except Exception as e:
        print(f"Speech Error: {e}")

def speech_to_text():
    """Handles the Microphone input."""
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            print("(Listening...)")
            recorded_audio = recognizer.listen(source, timeout=3, phrase_time_limit=10)
            text = recognizer.recognize_google(recorded_audio, language="en-US")
            return text
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return None
        except Exception as e:
            print(f"Microphone Error: {e}")
            return None

# --- MAIN CHAT ENGINE ---
def start_chat():
    user_memory = load_memory()
    current_mood_name = random.choice(list(MOODS.keys()))
    mood_description = MOODS[current_mood_name]
    
    # Initialization UI
    print(f"✨ Vibe Check: She's feeling {current_mood_name.upper()} today. ✨")
    print(f"Current friend on record: {user_memory['user_name']}")
    print("-" * 30)
    print("1. Texting (Keyboard)")
    print("2. Chatting (Voice)")
    
    choice = input("Select 1 or 2: ").strip()
    current_mode = "voice" if choice == "2" else "text"
    speak_during_text = False

    if current_mode == "text":
        voice_choice = input("Should I speak back? (y/n): ").lower().strip()
        speak_during_text = (voice_choice == 'y')

    print(f"\n--- Starting in {current_mode} mode ---")

    # Construct the personalized System Prompt
    known_facts = ", ".join(user_memory['facts']) if user_memory['facts'] else "You don't know any specific facts yet."
    
    messages = [
        {
            'role': 'system', 
            'content': (
                f"You are the user's close, witty female best friend. He is a boy, and you are his girl best friend. {mood_description} "
                f"Your friend's name is {user_memory['user_name']}. "
                f"Facts you remember: {known_facts}. "
                "Personality: high-energy, playful, full of banter, and slightly sassy. "
                "Style: short, punchy responses; casual lowercase vibes. Use slang like 'bro', 'dude', or 'bestie'. "
                "Use dry humor and tease him like a sister/best friend would. "
                "Use emojis like 💀, ✨, or 💅. "
                "Rule: Never be an assistant. Be a real friend. Don't be overly polite. "
                "Give advice straight and keep the vibe fun and engaging. "
                "LEARNING RULES: \n"
                "1. If the user tells you their name for the first time or changes it, "
                "add 'SET_NAME: [name]' to the end of your response.\n"
                "2. If they share a new fact about their life, add 'SAVE_FACT: [short fact]' to the end.\n"
                "Example: 'Got it, Alex! SAVE_FACT: plays guitar SET_NAME: Alex'"
            )
        }
    ]
    
    while True:
        try:
            user_input = None
            if current_mode == "voice":
                user_input = speech_to_text()
            else:
                user_input = input("\nYou: ")

            if user_input:
                clean_input = user_input.lower().strip()
                
                # Handle Exit (Respecting Silence)
                if any(word in clean_input for word in ["exit", "quit", "bye"]):
                    farewell = "Later! 💅"
                    print(f"AI: {farewell}")
                    if current_mode == "voice" or (current_mode == "text" and speak_during_text):
                        quick_speak(farewell)
                    break

                if current_mode == "voice":
                    print(f"You: {user_input}")

                # AI Generation
                messages.append({'role': 'user', 'content': user_input})
                response = ollama.chat(model=MODEL, messages=messages)
                full_reply = response['message']['content']
                
                # --- MEMORY PROCESSING ---
                # Check for Name Updates
                if "SET_NAME:" in full_reply:
                    name_match = re.search(r'SET_NAME:\s*(\w+)', full_reply)
                    if name_match:
                        user_memory['user_name'] = name_match.group(1)
                
                # Check for Fact Updates
                if "SAVE_FACT:" in full_reply:
                    fact_match = re.search(r'SAVE_FACT:\s*([^S\n]+)', full_reply)
                    if fact_match:
                        new_fact = fact_match.group(1).strip()
                        if new_fact not in user_memory['facts']:
                            user_memory['facts'].append(new_fact)
                
                # Save changes to JSON if tags were found
                if "SET_NAME:" in full_reply or "SAVE_FACT:" in full_reply:
                    save_memory(user_memory)

                # Strip tags for display and speech
                actual_reply = re.sub(r'(SET_NAME|SAVE_FACT):.*', '', full_reply).strip()

                print(f"\nAI: {actual_reply}")
                
                if current_mode == "voice" or (current_mode == "text" and speak_during_text):
                    quick_speak(actual_reply) 
                
                messages.append({'role': 'assistant', 'content': full_reply})

        except KeyboardInterrupt:
            print("\nShutting down...")
            break

if __name__ == "__main__":
    start_chat()

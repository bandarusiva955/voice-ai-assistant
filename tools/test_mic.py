"""Run this first if Jarvis can't hear you:  python tools/test_mic.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import speech_recognition as sr
from jarvis.mic import SDMicrophone, get_microphone

print("Microphones found:")
try:
    devs = SDMicrophone.list_devices()
except Exception as e:
    devs = []
    print("  sounddevice error:", e, "-> run: pip install sounddevice")
for i, n in devs:
    print(f"  [{i}] {n}")

idx = input("\nMic number to test (Enter = default): ").strip()
idx = int(idx) if idx else None
r = sr.Recognizer()
with get_microphone(idx) as src:
    r.adjust_for_ambient_noise(src, duration=1)
    print("Speak now...")
    audio = r.listen(src, timeout=8, phrase_time_limit=6)
print("Heard:", r.recognize_google(audio, language="en-IN"))
print("\nWorks! To use this mic permanently, set \"mic_index\" in C:\\Users\\<you>\\.openjarvis\\config.json")

"""
jarvis_voice.py - Live speech loop. Answers to the name set in config.py.
Works on Windows, macOS and Linux.
"""
import re
import subprocess
import sys
import time

import speech_recognition as sr

from . import config
from . import brain as jarvis_brain
from .mic import get_microphone
from .hud import state as hud_state
from .hud import server as hud_server

CFG = config.first_run_setup(force="--rename" in sys.argv)
NAME = CFG["name"]
WAKE = config.wake_words(CFG)

_tts = None


def speak(text):
    if not text:
        return
    print(f"\n[{NAME.upper()}]: {text}\n")
    hud_state.add_chat("jarvis", text)
    hud_state.set_state("speaking")
    if sys.platform == "darwin":
        subprocess.run(["say", "-v", "Samantha", text])
        hud_state.set_state("listening")
        return
    global _tts
    try:
        import pyttsx3
        if _tts is None:
            _tts = pyttsx3.init()
        _tts.say(text)
        _tts.runAndWait()
    except Exception as e:
        print(f"[speech output unavailable: {e}]")
    hud_state.set_state("listening")


def strip_wake(query):
    """Returns (heard_name, remaining_command)."""
    q = query.lower()
    for w in WAKE:
        if re.search(r"\b" + re.escape(w) + r"\b", q):
            rest = re.sub(r"\b" + re.escape(w) + r"\b", " ", q)
            return True, rest.strip(" ,.!?")
    return False, q.strip(" ,.!?")


def text_mode():
    if "--no-hud" not in sys.argv:
        hud_server.start()
    print("Typing mode (mic not available). Type commands:")
    while True:
        try:
            s = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if s:
            _, cmd = strip_wake(s)
            hud_state.add_chat("you", s)
            run_command(cmd or s)


def run_command(cmd):
    """Run one command through the brain and update the HUD."""
    t0 = time.time()
    hud_state.set_state("thinking")
    hud_state.update(tool_active=True)
    reply = jarvis_brain.think(cmd)
    hud_state.update(tool_active=False, t_think=time.time() - t0)
    hud_state.count_tool(cmd[:28].title())
    low = cmd.lower()
    if reply and any(k in low for k in ("stock", "market", "nifty", "sensex", "crypto", "bitcoin")):
        hud_state.add_card("MARKET BRIEFING", reply)
    elif reply and any(k in low for k in ("mail", "email", "inbox")):
        hud_state.add_card("INBOX BRIEFING", reply)
    speak(reply)


def listen_loop():
    if "--no-hud" not in sys.argv:
        hud_server.start()
    r = sr.Recognizer()
    r.dynamic_energy_threshold = True
    r.pause_threshold = 0.8

    try:
        mic = get_microphone(CFG.get("mic_index"))
    except Exception as e:
        print("\n[!] MICROPHONE ERROR:", e)
        print("    Fix: pip install sounddevice  |  Windows Settings > Privacy > Microphone > allow apps")
        print("    Run python test_mic.py to pick the right mic.\n")
        text_mode()
        return

    with mic as source:
        print("\n" + "=" * 52)
        print(f"  {NAME.upper()} IS LISTENING - say '{NAME}, open chrome'")
        print("=" * 52)
        r.adjust_for_ambient_noise(source, duration=1.0)

    awake_until = 0.0
    hud_state.set_state("listening")
    speak(f"Hello. I am ready. Call me {NAME}.")

    while True:
        try:
            with mic as source:
                print("Listening... ", end="", flush=True)
                hud_state.set_state("listening")
                audio = r.listen(source, timeout=10, phrase_time_limit=8)
            hud_state.set_state("recognizing")
            t0 = time.time()
            query = r.recognize_google(audio, language=CFG["language"]).strip()
            print(f'\nYou said: "{query}"')
            hud_state.update(t_rec=time.time() - t0)

            heard, cmd = strip_wake(query)
            now = time.time()
            if heard:
                awake_until = now + 20   # follow-up commands allowed for 20s
            elif CFG["require_wake_word"] and now > awake_until:
                print(f"(ignored - say '{NAME}' first)")
                hud_state.set_state("listening")
                continue

            hud_state.add_chat("you", query)
            if not cmd:
                speak("Yes?")
                continue
            run_command(cmd)

        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            print(f"\n[Speech service error - check internet]: {e}")
            time.sleep(2)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\n[Notice]: {e}")
            time.sleep(0.5)


if __name__ == "__main__":
    listen_loop()

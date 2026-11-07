"""
config.py - Assistant name / wake word settings.
Change the name any time:  python jarvis_voice.py --rename
"""
import json
import os
import sys

CONFIG_DIR = os.path.expanduser("~/.openjarvis")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULTS = {
    "name": "Jarvis",          # the name YOU want to call the assistant by
    "aliases": [],             # other ways the mic may hear it (e.g. "ravi", "ravee")
    "require_wake_word": True, # only act when the name is heard
    "language": "en-IN",       # en-IN suits Indian accents; use en-US if you prefer
    "mic_index": None,         # run test_mic.py to find the right number
}


def load():
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    return cfg


def save(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def first_run_setup(force=False):
    """Ask for the name once and remember it."""
    cfg = load()
    if os.path.exists(CONFIG_FILE) and not force:
        return cfg
    if not sys.stdin or not sys.stdin.isatty():
        return cfg
    print("\nWhat name should I answer to? (press Enter to keep '%s')" % cfg["name"])
    name = input("Name: ").strip()
    if name:
        cfg["name"] = name
    print("Other spellings the mic might hear for this name? (comma separated, or Enter to skip)")
    alts = input("Aliases: ").strip()
    if alts:
        cfg["aliases"] = [a.strip().lower() for a in alts.split(",") if a.strip()]
    save(cfg)
    print("Saved. I will answer to '%s'.\n" % cfg["name"])
    return cfg


def wake_words(cfg=None):
    cfg = cfg or load()
    words = [cfg["name"].lower().strip()] + [a.lower() for a in cfg.get("aliases", [])]
    return [w for w in dict.fromkeys(words) if w]

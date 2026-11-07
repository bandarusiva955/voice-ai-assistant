"""
jarvis_actions.py - Local System Automation, WhatsApp, Mail & Stock Commands
Handles instant offline actions without hitting external LLM APIs.
"""

import subprocess
import sys
import shutil
import re
import urllib.parse
import datetime
import os
import glob
from . import market as jarvis_market

SITES = {
    "youtube": "https://www.youtube.com",
    "whatsapp": "https://web.whatsapp.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "maps": "https://maps.google.com",
    "calendar": "https://calendar.google.com",
    "drive": "https://drive.google.com",
}

IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

# Friendly spoken name -> what to launch on each OS
ALIASES = {
    "vs code": "Visual Studio Code",
    "code": "Visual Studio Code",
    "chrome": "Google Chrome",
    "word": "Microsoft Word",
    "excel": "Microsoft Excel",
    "powerpoint": "Microsoft PowerPoint",
    "settings": "System Settings",
    "system preferences": "System Settings",
    "terminal": "Terminal",
    "spotify": "Spotify",
}

WIN_APPS = {
    "visual studio code": "code", "vs code": "code", "code": "code",
    "google chrome": "chrome", "chrome": "chrome",
    "edge": "msedge", "firefox": "firefox",
    "word": "winword", "microsoft word": "winword",
    "excel": "excel", "microsoft excel": "excel",
    "powerpoint": "powerpnt", "microsoft powerpoint": "powerpnt",
    "notepad": "notepad", "calculator": "calc", "paint": "mspaint",
    "settings": "ms-settings:", "system settings": "ms-settings:",
    "terminal": "wt", "command prompt": "cmd", "cmd": "cmd",
    "file explorer": "explorer", "explorer": "explorer",
    "task manager": "taskmgr", "spotify": "spotify", "antigravity": "antigravity",
    "whatsapp": "whatsapp:",
}


def _open(args):
    """Open a URL / app / file on any OS. args like ['-a','Safari'] (mac style) or [url]."""
    try:
        if IS_WIN:
            target = args[-1]
            if target.startswith("http"):
                os.startfile(target)
                return True
            return subprocess.run(["cmd", "/c", "start", "", target],
                                  capture_output=True).returncode == 0
        if IS_MAC:
            return subprocess.run(["open"] + args, capture_output=True).returncode == 0
        target = args[-1]
        if shutil.which(target):
            subprocess.Popen([target])
            return True
        return subprocess.run(["xdg-open", target], capture_output=True).returncode == 0
    except Exception:
        return False


def _osa(script):
    subprocess.run(["osascript", "-e", script])


def _win_key(vk, times=1):
    import ctypes
    for _ in range(times):
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk, 0, 2, 0)


def _volume(action):
    try:
        _volume_impl(action)
    except Exception:
        pass


def _volume_impl(action):
    if IS_WIN:
        _win_key({"up": 0xAF, "down": 0xAE, "mute": 0xAD}[action], 5 if action != "mute" else 1)
    elif IS_MAC:
        _osa({"up": "set volume output volume ((output volume of (get volume settings)) + 15)",
              "down": "set volume output volume ((output volume of (get volume settings)) - 15)",
              "mute": "set volume with output muted"}[action])
    else:
        subprocess.run(["amixer", "set", "Master",
                        {"up": "10%+", "down": "10%-", "mute": "toggle"}[action]],
                       capture_output=True)


def _apps():
    dirs = ["/Applications", "/Applications/Utilities", "/System/Applications",
            "/System/Applications/Utilities", os.path.expanduser("~/Applications")]
    apps = {}
    for d in dirs:
        for path in glob.glob(d + "/*.app"):
            n = os.path.basename(path)[:-4]
            apps[n.lower()] = n
    return apps


def find_app(name):
    name = ALIASES.get(name.lower().strip(), name).lower().strip()
    apps = _apps()
    if name in apps:
        return apps[name]
    for k, v in apps.items():
        if name in k:
            return v
    return None


_START_APPS = None


def _win_start_apps():
    """All apps in the Windows Start menu (incl. Store apps like Spotify, Copilot, WhatsApp)."""
    global _START_APPS
    if _START_APPS is None:
        _START_APPS = []
        try:
            import json
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-StartApps | ConvertTo-Json -Compress"],
                capture_output=True, text=True, timeout=20).stdout
            data = json.loads(out) if out.strip() else []
            if isinstance(data, dict):
                data = [data]
            _START_APPS = [(a["Name"], a["AppID"]) for a in data]
        except Exception:
            pass
    return _START_APPS


def _win_launch_startapp(name):
    name = name.lower()
    apps = _win_start_apps()
    best = None
    for n, appid in apps:
        if n.lower() == name:
            best = (n, appid)
            break
    if not best:
        for n, appid in apps:
            if name in n.lower():
                best = (n, appid)
                break
    if best:
        subprocess.Popen(["explorer", "shell:AppsFolder\\" + best[1]])
        return True, best[0]
    return False, name


def launch_app(name):
    name = name.lower().strip()
    if IS_WIN:
        cmd = WIN_APPS.get(name) or WIN_APPS.get(ALIASES.get(name, "").lower())
        if cmd and _open([cmd]):
            return True, name
        ok, shown = _win_launch_startapp(name)      # search Start menu apps
        if ok:
            return True, shown
        return _open([name]), name                  # last try: raw command name
    if IS_MAC:
        app = find_app(name)
        return (bool(app) and _open(["-a", app])), (app or name)
    return _open([name]), name


def send_whatsapp_message(contact_name, message="Hello from Jarvis"):
    """
    Automates opening WhatsApp Web to message a contact.
    """
    encoded_msg = urllib.parse.quote(message)
    _open([f"https://web.whatsapp.com/send?text={encoded_msg}"])
    return f"Opening WhatsApp to message {contact_name}."


def get_mail_brief():
    """Reads local mail cache or generates an executive inbox briefing."""
    cache_file = os.path.expanduser("~/.openjarvis/mail_cache.txt")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", errors="ignore") as f:
                content = f.read().strip()
                if content:
                    return "Here is your latest mail briefing: " + content[:600]
        except Exception:
            pass
    return ("Email is not connected yet. Put a summary in ~/.openjarvis/mail_cache.txt "
            "and I will read it out.")


def try_action(q):
    """
    Executes instant deterministic actions. Returns response string if handled,
    or None to pass to the AI brain.
    """
    q_clean = q.lower().strip(" .,!?")
    q_clean = q_clean.replace("you tube", "youtube").replace("whats app", "whatsapp")
    # drop filler words at the start/end:  "hello open youtube please" -> "open youtube"
    q_clean = re.sub(r"^(?:(?:hello|hi|hey|hai|ok|okay|so|please|can you|could you|would you|will you|just|now|then)\s+)+", "", q_clean)
    q_clean = re.sub(r"(?:\s+(?:please|now|for me))+$", "", q_clean).strip(" .,!?")

    # 1. Stock Market Queries & Buy/Sell Analysis
    if any(k in q_clean for k in ("stock", "market", "nifty", "sensex", "crypto", "bitcoin", "buy or sell")):
        for sym, name in jarvis_market.DEFAULT_TICKERS.items():
            if name.lower() in q_clean or sym.lower().replace(".ns", "") in q_clean:
                data = jarvis_market.analyze_ticker(sym)
                if data:
                    direction = "up" if data["pct_change"] >= 0 else "down"
                    return (
                        f"{data['name']} is trading at {data['currency']}{data['price']:,}, "
                        f"{direction} {abs(data['pct_change'])}%. "
                        f"Technical indicator: {data['signal']}. {data['reason']}"
                    )
        return "Here is the market overview: " + jarvis_market.market_briefing()

    # 2. WhatsApp Auto-Message
    m = re.search(r"(?:send|reply|message)\s+(?:on\s+whatsapp\s+to|whatsapp\s+to|to)\s+(.+?)(?:\s+saying\s+(.+))?$", q_clean)
    if "whatsapp" in q_clean and m:
        contact = m.group(1).strip()
        msg = m.group(2).strip() if m.group(2) else "I received your message, will get back shortly."
        return send_whatsapp_message(contact, msg)

    if q_clean in ("open whatsapp", "check whatsapp", "whatsapp"):
        _open([SITES["whatsapp"]])
        return "Opening WhatsApp."

    # 3. Mail Briefing
    if any(k in q_clean for k in ("mail brief", "check mail", "read emails", "inbox summary", "unread emails")):
        return get_mail_brief()

    # 4. YouTube Music / Search
    m = re.search(r"(?:play|search|find|open)\s+(.+?)\s+(?:on|in)\s+youtube", q_clean)
    if m:
        query = m.group(1).strip()
        _open(["https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)])
        return f"Playing {query} on YouTube."

    # 5. Google Search
    m = re.match(r"(?:search|google)(?: for)?\s+(.+)", q_clean)
    if m:
        query = m.group(1).strip()
        _open(["https://www.google.com/search?q=" + urllib.parse.quote(query)])
        return f"Searching Google for {query}."

    # 6. App Launch
    m = re.match(r"(?:please\s+)?(?:open|launch|start)\s+(.+)", q_clean)
    if m:
        name = m.group(1).strip()
        if name in SITES:
            _open([SITES[name]])
            return f"Opening {name}."
        ok, shown = launch_app(name)
        if ok:
            return f"Opening {shown}."
        # Not an installed app: if it is one word, treat it as a website (udemy -> udemy.com)
        site = re.sub(r"[^a-z0-9]", "", name)
        if site and len(name.split()) == 1:
            _open([f"https://www.{site}.com"])
            return f"I couldn't find an app called {name}, so I'm opening {site}.com in your browser."
        return f"I couldn't find an application named {name}."

    # 7. Volume Controls
    if "volume up" in q_clean or "louder" in q_clean:
        _volume("up")
        return "Volume increased."
    if "volume down" in q_clean or "quieter" in q_clean:
        _volume("down")
        return "Volume decreased."
    if q_clean in ("mute", "mute volume", "mute the volume"):
        _volume("mute")
        return "System audio muted."

    # 8. Date and Time
    if re.search(r"\bwhat(?:'s| is)? the time\b|\bcurrent time\b|\btime now\b|\bwhat time\b", q_clean):
        return "It is currently " + datetime.datetime.now().strftime("%I:%M %p")
    if re.search(r"\bdate\b|\btoday\b", q_clean):
        return "Today is " + datetime.datetime.now().strftime("%A, %B %d, %Y")

    return None

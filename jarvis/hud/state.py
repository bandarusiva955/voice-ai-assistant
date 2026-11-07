"""hud_state.py - shared live state that the holographic HUD (jarvis_workplace.html) reads."""
import collections
import os
import shutil
import threading
import time

_lock = threading.Lock()
_state = {
    "state": "starting", "note": "Ready", "mode": "Hybrid",
    "model": "Groq / Llama-3.3 + Local", "last_you": "", "last_tool": "App Launcher",
    "tools": 0, "facts": 0, "mail_age": None, "tool_active": False,
    "t_rec": 0.0, "t_think": 0.0,
}
_chat, _cards, _stocks = [], [], []
_levels = collections.deque(maxlen=400)
_level_total = 0
_seq = 0


def _now():
    return time.strftime("%H:%M:%S")


def set_state(st, note=None):
    with _lock:
        _state["state"] = st
        if note is not None:
            _state["note"] = note


def update(**kw):
    with _lock:
        _state.update(kw)


def add_chat(kind, text):
    """kind: 'you' | 'jarvis' | 'sys'"""
    global _seq
    with _lock:
        _seq += 1
        _chat.append({"i": _seq, "k": kind, "x": text, "t": _now()})
        del _chat[:-80]
        if kind == "you":
            _state["last_you"] = text


def add_card(title, body):
    global _seq
    with _lock:
        _seq += 1
        _cards.insert(0, {"i": _seq, "title": title, "t": _now(), "body": body})
        del _cards[6:]


def push_level(v):
    global _level_total
    with _lock:
        _levels.append(max(0.0, min(1.0, v)))
        _level_total += 1


def count_tool(name):
    with _lock:
        _state["tools"] += 1
        _state["last_tool"] = name


def _sys_stats():
    out = {}
    try:
        import psutil
        out["cpu"] = psutil.cpu_percent(interval=None)
        out["ram"] = psutil.virtual_memory().percent
        d = shutil.disk_usage(os.path.abspath(os.sep))
        out["disk"] = d.used / d.total * 100
        out["free"] = round(d.free / 1e9)
        b = psutil.sensors_battery()
        if b:
            out["bat"] = round(b.percent)
            out["plug"] = bool(b.power_plugged)
        out["up"] = int(time.time() - psutil.boot_time())
    except Exception:
        pass
    return out


def snapshot(lv=0):
    with _lock:
        n = _level_total
        if lv > n:
            lv = n
        new = list(_levels)[-min(n - lv, 40):] if n > lv else []
        snap = dict(_state)
        snap["chat"] = list(_chat)
        snap["cards"] = list(_cards)
        snap["stocks"] = list(_stocks)
        snap["mic"] = {"n": n, "a": new}
    snap["sys"] = _sys_stats()
    return snap


def _refresh_stocks():
    from .. import market as m
    while True:
        rows = []
        for sym, name in m.DEFAULT_TICKERS.items():
            try:
                chart = m._fetch_chart(sym, "5d", "15m")
                meta = chart.get("meta", {})
                closes = [c for c in chart["indicators"]["quote"][0]["close"] if c is not None]
                price = meta.get("regularMarketPrice") or closes[-1]
                prev = meta.get("chartPreviousClose") or meta.get("previousClose") or price
                sma5 = sum(closes[-5:]) / len(closes[-5:])
                rows.append({
                    "sym": sym, "name": name, "price": price,
                    "pct": (price - prev) / prev * 100 if prev else 0,
                    "spark": closes[-40:], "above": price > sma5,
                    "mom": round((price / closes[0] - 1) * 100, 2) if closes else 0,
                })
            except Exception:
                rows.append({"sym": sym, "name": name, "err": True})
        with _lock:
            _stocks[:] = rows
        time.sleep(90)


def start_background():
    threading.Thread(target=_refresh_stocks, daemon=True).start()

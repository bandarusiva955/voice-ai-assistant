# Voice AI Assistant with a Holographic HUD

A voice-controlled desktop assistant you can name yourself. Say its name, give a command, and it
opens apps, plays YouTube, searches Google, shows live market data, controls volume, and answers
questions. A sci-fi dashboard (HUD) in your browser shows what it is doing in real time.

<!-- Add your screenshot or demo GIF here:  ![Demo](docs/demo.png) -->

## Features

- **Your own wake word.** Name it anything (`Shiva`, `Friday`, ...). Set it once, change it any time.
- **Voice commands** that work on Windows, macOS and Linux.
- **Live HUD** (`http://127.0.0.1:8765`): listening / thinking / speaking states, mic oscilloscope,
  chat log, CPU / RAM / battery, and live market tickers with Buy / Hold / Sell signals.
- **Smart app launching on Windows.** Finds Store and desktop apps from the Start menu (Spotify, Copilot, ...).
- **Hybrid brain.** Local commands run instantly and offline. Free-form questions go to an LLM
  (Groq, free tier) with automatic rate-limit cooldown and local fallback.

## Quick start

Requires Python 3.10+ and a microphone.

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python tools/test_mic.py        # optional: check your microphone
python main.py
```

On first run it asks what name it should answer to. Windows users can also double-click `scripts/install.bat`.

| Flag | What it does |
| --- | --- |
| `--rename` | Change the assistant's name / spelling aliases |
| `--no-hud` | Run without the browser dashboard |

## Example commands

Say your assistant's name first (it keeps listening for 20 seconds after that).

| Say | Result |
| --- | --- |
| "Shiva, open Chrome" | Launches the app |
| "Open Udemy" | Opens the site if no app with that name exists |
| "Play lofi on YouTube" | YouTube search for lofi |
| "Search best python projects" | Google search |
| "Volume up" / "Mute" | System volume |
| "Stock market report" / "Analyze Nifty" | Live prices with a Buy / Hold / Sell signal |
| "What time is it" | Current time |

## Optional: enable open-ended chat

Get a free key from <https://console.groq.com/keys>, then either set the `GROQ_API_KEY`
environment variable or save the key to `~/.openjarvis/free.key`. The key never lives in this repo.

## Project structure

```
.
├── main.py                  # entry point
├── jarvis/
│   ├── voice.py             # microphone loop, wake word, speech output
│   ├── brain.py             # local commands first, then LLM with failover
│   ├── actions.py           # open apps / sites, volume, search, YouTube
│   ├── market.py            # live market data + signals (Yahoo Finance)
│   ├── mic.py               # PyAudio-free microphone (sounddevice)
│   ├── config.py            # name, aliases, language
│   └── hud/                 # local server + dashboard (jarvis_workplace.html)
├── tools/test_mic.py        # microphone checker
└── scripts/                 # one-click installers
```

## Known limitations

- Commands are pattern based, so phrasing matters ("open X", "play X on YouTube"). Free-form
  sentences need the optional Groq key, and even then actions stay rule based.
- Speech recognition uses Google's free web service, so it needs internet.
- WhatsApp opens WhatsApp Web with your message but does not pick the contact for you.
- Email briefing is a placeholder: it reads `~/.openjarvis/mail_cache.txt` if present. It is not connected to Gmail.
- Market signals are a simple moving-average heuristic. **Not financial advice.**

## Roadmap

- LLM tool-calling so natural sentences trigger actions
- Gmail / Calendar integration
- Offline speech recognition

## License

MIT. See [LICENSE](LICENSE).

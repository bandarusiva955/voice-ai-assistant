"""
mic.py - Microphone for SpeechRecognition using `sounddevice` (no PyAudio needed).
Works on new Python versions (3.13 / 3.14) where PyAudio cannot be installed.
"""
import speech_recognition as sr


class _Stream:
    def __init__(self, raw):
        self.raw = raw

    def read(self, size):
        data, _overflow = self.raw.read(size)
        b = bytes(data)
        try:
            import array
            from .hud import state as hud_state
            a = array.array("h", b)
            rms = (sum(x * x for x in a) / max(1, len(a))) ** 0.5
            hud_state.push_level(rms / 4000.0)
        except Exception:
            pass
        return b


class SDMicrophone(sr.AudioSource):
    def __init__(self, device_index=None, sample_rate=16000, chunk_size=1024):
        import sounddevice as sd
        self.sd = sd
        self.device_index = device_index
        self.SAMPLE_RATE = sample_rate
        self.CHUNK = chunk_size
        self.SAMPLE_WIDTH = 2  # int16
        self.stream = None

    def __enter__(self):
        raw = self.sd.RawInputStream(samplerate=self.SAMPLE_RATE, blocksize=self.CHUNK,
                                     device=self.device_index, channels=1, dtype="int16")
        raw.start()
        self._raw = raw
        self.stream = _Stream(raw)
        return self

    def __exit__(self, *exc):
        try:
            self._raw.stop()
            self._raw.close()
        finally:
            self.stream = None

    @staticmethod
    def list_devices():
        import sounddevice as sd
        out = []
        for i, d in enumerate(sd.query_devices()):
            if d["max_input_channels"] > 0:
                out.append((i, d["name"]))
        return out


def get_microphone(device_index=None):
    """Try PyAudio first, then sounddevice."""
    try:
        return sr.Microphone(device_index=device_index)
    except Exception:
        return SDMicrophone(device_index=device_index)

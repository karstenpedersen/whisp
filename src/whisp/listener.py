import collections
import queue
import time

import numpy as np
import sounddevice as sd
import typer
from faster_whisper import WhisperModel
from faster_whisper.vad import get_vad_model

from whisp.config import BLOCK, BLOCK_MS, SAMPLE_RATE, WINDOW_BLOCKS
from whisp.commands import COMMANDS


class Listener:
    """Reads the mic and uses Silero VAD to cut out one spoken command."""

    def __init__(self, device, vad_threshold, gain, silence_s, max_s):
        self.q = queue.Queue()
        self.vad = get_vad_model()  # Silero VAD bundled with faster-whisper
        self.on_thresh = vad_threshold
        self.off_thresh = max(vad_threshold - 0.15, 0.1)  # hysteresis
        self.gain = gain
        self.silence_blocks = int(silence_s * 1000 / BLOCK_MS)
        self.max_blocks = int(max_s * 1000 / BLOCK_MS)
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=BLOCK,
            device=device,
            callback=self._callback,
        )

    def _callback(self, indata, frames, time_info, status):
        self.q.put(indata[:, 0].copy())

    def flush(self):
        while not self.q.empty():
            self.q.get_nowait()

    def _speech_prob(self, history) -> float:
        """Speech probability for the most recent ~100 ms."""
        window = np.concatenate(history)
        # Silero was trained on normal-volume speech, so lift quiet input first.
        window = np.clip(window * self.gain, -1.0, 1.0)
        probs = self.vad(window)  # one probability per 512-sample chunk
        return float(np.mean(probs[-3:]))

    def capture(self, wait_timeout=None):
        """Block until one utterance is captured. Returns float32 audio or None."""
        history = collections.deque(maxlen=WINDOW_BLOCKS)
        audio = []
        speaking = False
        quiet = 0
        started = time.time()

        while True:
            try:
                block = self.q.get(timeout=0.5)
            except queue.Empty:
                block = None
            if block is None:
                if (
                    wait_timeout
                    and not speaking
                    and time.time() - started > wait_timeout
                ):
                    return None
                continue

            history.append(block)
            if len(history) < 8:  # need ~250 ms of context first
                continue

            prob = self._speech_prob(history)

            if not speaking:
                if prob > self.on_thresh:
                    speaking = True
                    audio = list(history)[-12:]  # ~400 ms of lead-in
                    quiet = 0
                elif wait_timeout and time.time() - started > wait_timeout:
                    return None
            else:
                audio.append(block)
                quiet = quiet + 1 if prob < self.off_thresh else 0
                if quiet >= self.silence_blocks or len(audio) >= self.max_blocks:
                    break

        keep = max(len(audio) - max(quiet - 6, 0), 1)  # trim trailing silence
        audio = np.concatenate(audio[:keep])
        if len(audio) < SAMPLE_RATE * 0.25:
            return None
        return audio


def boost(audio: np.ndarray, target_peak=0.9, max_gain=60.0) -> np.ndarray:
    """Amplify quiet speech so the recogniser gets a healthy signal."""
    peak = float(np.max(np.abs(audio)))
    if peak < 1e-6:
        return audio
    gain = min(target_peak / peak, max_gain)
    return np.clip(audio * gain, -1.0, 1.0).astype(np.float32)


def transcribe(model, audio):
    prompt = "Voice commands: " + ", ".join(COMMANDS) + "."
    segments, _ = model.transcribe(
        audio,
        language="en",
        beam_size=5,
        initial_prompt=prompt,  # nudges Whisper toward your vocabulary
        condition_on_previous_text=False,
        vad_filter=False,  # our own detector already trimmed it
        temperature=0.0,
    )
    return " ".join(s.text for s in segments).strip()

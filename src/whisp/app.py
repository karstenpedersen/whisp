import wave
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional
from dotenv import load_dotenv

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
import typer
from whisp.commands import COMMANDS, PHRASES, match_command
from whisp.config import SAMPLE_RATE
from whisp.listener import Listener, boost, transcribe
from whisp.log import log, setup_logging
from whisp.telegram import get_bot_id

load_dotenv()

app = typer.Typer(name="whisp", no_args_is_help=True)


def save_wav(audio: np.ndarray, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{datetime.now():%Y%m%d-%H%M%S-%f}.wav"
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(pcm.tobytes())
    return path


@app.command(help="List avaiable audio devices")
def devices() -> None:
    print(sd.query_devices())


@app.command(help="Get Telegram bot id")
def bot_info():
    print(get_bot_id())


@app.command(help="Listen for commands")
def listen(
    model: Annotated[str, typer.Option(help="Model")] = "small.en",
    device: Annotated[Optional[str], typer.Option(help="Model")] = None,
    vad_threshold: Annotated[
        float,
        typer.Option(
            min=0.05,
            max=0.95,
            help="Speech probability needed to start a command. Lower = more sensitive.",
        ),
    ] = 0.4,
    gain: Annotated[
        float,
        typer.Option(
            help="Volume boost applied before voice detection. Raise for very faint voices."
        ),
    ] = 8.0,
    silence: Annotated[
        float, typer.Option(help="Seconds of silence that end a command.")
    ] = 0.9,
    max_seconds: Annotated[
        float, typer.Option(help="Maximum length of a single command.")
    ] = 8.0,
    match_cutoff: Annotated[
        float,
        typer.Option(
            min=0.0,
            max=1.0,
            help="How closely speech must match a command (lower = more forgiving).",
        ),
    ] = 0.6,
    save_audio: Annotated[
        bool,
        typer.Option(
            "--save-audio",
            help="Save each captured command as a WAV file.",
        ),
    ] = False,
    audio_dir: Annotated[
        Path,
        typer.Option(help="Folder for saved audio files (used with --save-audio)."),
    ] = Path("recordings"),
    save_log: Annotated[
        bool,
        typer.Option(
            "--save-log",
            help="Also write log output to a file.",
        ),
    ] = False,
    log_file: Annotated[
        Path,
        typer.Option(help="Log file path (used with --save-log)."),
    ] = Path("whisper.log"),
) -> None:
    device_number = int(device) if device and device.isdigit() else device

    setup_logging(log_file=log_file if save_log else None)

    log.info("Audio input device: %s", device_number)
    log.info("Model: '%s'", model)

    log.info("Loading model...")
    whisper = WhisperModel(model, device="cpu", compute_type="int8")

    listener = Listener(device_number, vad_threshold, gain, silence, max_seconds)

    with listener.stream:
        log.info(f"Available commands: {', '.join(PHRASES)}")
        log.info("Ready to listen for commands. Press Ctrl+C to quit")

        try:
            while True:
                audio = listener.capture()
                if audio is None:
                    continue

                audio = boost(audio)
                heard = transcribe(whisper, audio)
                log.info(f"Heard: '{heard}'")
                if save_audio:
                    path = save_wav(audio, audio_dir)
                    log.info(f"Saved: {path}")

                command = match_command(heard, match_cutoff)
                if not command:
                    log.info("Found no matching command")
                else:
                    log.info(f"Matched phrase to command: {command}")
                    COMMANDS[command]()
        except KeyboardInterrupt:
            log.info("Stopping...")


if __name__ == "__main__":
    app()

import difflib
import re

from httpx import HTTPStatusError
from whisp.log import log
from whisp.telegram import send_message


def help_command():
    log.info("Sending message...")
    try:
        send_message("help command activated")
    except HTTPStatusError as e:
        log.error(f"Failed to send message: {e}")

    log.info("Send message")


COMMANDS = {"help": help_command}

PHRASES = list(COMMANDS)


def normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def match_command(heard: str, cutoff: float):
    heard = normalise(heard)
    if not heard:
        return None

    for phrase in PHRASES:
        if phrase in heard:
            return phrase

    close = difflib.get_close_matches(heard, PHRASES, n=1, cutoff=cutoff)
    if not close:
        return None

    return close[0]

"""Генератор уникальных trax_id для трекинг-ссылок."""
import secrets
import string

_ALPHABET = string.ascii_lowercase + string.digits
_LENGTH = 8


def generate_trax_id() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(_LENGTH))


def build_tracking_url(trax_id: str, base_url: str = "https://t.attribly.io") -> str:
    return f"{base_url}/t/{trax_id}"

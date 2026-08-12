import json
import os
import re
from datetime import datetime, timezone
from threading import Lock

from config import ENABLE_QUERY_LOGGING, QUERY_LOG_PATH, MASK_LOG_SENSITIVE


_WRITE_LOCK = Lock()

_IP_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_HOST_PATTERN = re.compile(r"\b(?:rc|lm)-\d+-\d+-\d+-s\d+\b", re.IGNORECASE)


def _mask_text(value):
    masked = _IP_PATTERN.sub("<masked_ip>", value)
    masked = _HOST_PATTERN.sub("<masked_host>", masked)
    return masked


def _sanitize(value):
    if isinstance(value, str):
        return _mask_text(value) if MASK_LOG_SENSITIVE else value

    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}

    if isinstance(value, list):
        return [_sanitize(v) for v in value]

    return value


def _utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def log_interaction(payload):
    """
    Append one interaction record to a JSONL log file.

    Each line is a JSON object so logs are easy to parse later
    for quality analysis and failure clustering.
    """

    if not ENABLE_QUERY_LOGGING:
        return

    record = {
        "timestamp_utc": _utc_now_iso(),
        **(payload or {}),
    }

    record = _sanitize(record)

    directory = os.path.dirname(QUERY_LOG_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)

    line = json.dumps(record, ensure_ascii=True, default=str)

    with _WRITE_LOCK:
        with open(QUERY_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")

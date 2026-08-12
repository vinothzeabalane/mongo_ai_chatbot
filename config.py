import os


# ============================================================
# MongoDB
# ============================================================

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://10.74.135.199:27018"
)

DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "openstack"
)

COLLECTION_NAME = os.getenv(
    "COLLECTION_NAME",
    "dashboard"
)


# ============================================================
# Ollama
# ============================================================

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://127.0.0.1:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.1:8b"
)

OLLAMA_TIMEOUT = int(
    os.getenv(
        "OLLAMA_TIMEOUT",
        "60"
    )
)


# ============================================================
# Interaction Logging
# ============================================================

ENABLE_QUERY_LOGGING = os.getenv(
    "ENABLE_QUERY_LOGGING",
    "1",
) == "1"

QUERY_LOG_PATH = os.getenv(
    "QUERY_LOG_PATH",
    "logs/chatbot_interactions.jsonl",
)

MASK_LOG_SENSITIVE = os.getenv(
    "MASK_LOG_SENSITIVE",
    "1",
) == "1"

ADMIN_LOG_TAIL_LINES = int(
    os.getenv(
        "ADMIN_LOG_TAIL_LINES",
        "100",
    )
)

# Max size per log file before rotation (bytes); default 5 MB
LOG_MAX_BYTES = int(
    os.getenv(
        "LOG_MAX_BYTES",
        str(5 * 1024 * 1024),
    )
)

# Number of rotated backup files to keep
LOG_BACKUP_COUNT = int(
    os.getenv(
        "LOG_BACKUP_COUNT",
        "5",
    )
)
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
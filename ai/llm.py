import requests

from config import OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_TIMEOUT

_SYSTEM_CONTEXT = (
    "You are a helpful assistant embedded in a boot-profile dashboard. "
    "Answer the user's question clearly and concisely. "
    "If the question is about boot metrics, hosts, or performance data, "
    "remind the user they can ask directly in dashboard language."
)


def ask_llm(question: str) -> str:
    url = OLLAMA_HOST.rstrip("/") + "/api/generate"

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{_SYSTEM_CONTEXT}\n\nUser: {question}\nAssistant:",
        "stream": False,
    }

    response = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
    response.raise_for_status()

    return response.json().get("response", "").strip()

import requests

from config import (
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
)


def ask_llm(prompt):

    url = (
        OLLAMA_HOST.rstrip("/")
        + "/api/generate"
    )

    payload = {

        "model":
            OLLAMA_MODEL,

        "prompt":
            prompt,

        "stream":
            False,
    }

    response = requests.post(
        url,
        json=payload,
        timeout=OLLAMA_TIMEOUT
    )

    if response.status_code != 200:

        raise RuntimeError(
            "Ollama request failed: {} {}".format(
                response.status_code,
                response.text
            )
        )

    return response.json().get(
        "response",
        ""
    ).strip()
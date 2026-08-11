
import json
import re
import requests

from config import (
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
)


SYSTEM_PROMPT = """
You are the query-understanding assistant for a boot performance
dashboard.

Your job is NOT to answer the user's question.

Your job is to convert the user's natural-language question into
a structured JSON query.

The database contains boot performance information.

Available fields:

- hostname
- sku
- bootType
- date
- metric

Known boot types:
- EB0
- SPI

Known metrics include:

SBL:
SBL_SPI_INIT
SBL_FCONFIG_LOAD
SBL_CRYPTO_INIT
SBL_CRITICAL_BOOT_LOAD
SBL_UFH_LOAD_AND_VERIFY
SBL_DIGEST_COMPUTE
SBL_LOAD_TBL_IMAGE
SBL_RIOT
SBL_TOTAL

TBL:
TBL_PRETOTAL
TBL_SPI_INIT
TBL_FCONFIG_LOAD
TBL_PCIE_INIT
TBL_LOAD_PBL_IMAGE
TBL_RIOT
TBL_TOTAL

PBL:
PBL_SPI_INIT
PBL_PARSE_FCONFIG
PBL_PMIC_INIT
PBL_DRAM_INIT
PBL_SCRUB_MAINFW_DRAM
PBL_CRYPTO_INIT
PBL_NAND_INIT
PBL_LOAD_MAIN_FW
PBL_RIOT
PBL_WAKE_CORES_JUMP
PBL_TOTAL

MAINFW:
MAINFW_BSS_INIT
MAINFW_PCM_BSS_INIT
MAINFW_SPI_SEC_INIT
MAINFW_ENABLE_ADDR_PARITY_CHECKING
MAINFW_UART_INIT
MAINFW_GPIO_INIT_LOCKS
MAINFW_GPIO_INIT_DCSU
MAINFW_BL_SPINLOCK_SETUP
MAINFW_LLOG_INIT
MAINFW_MGR_REG_INIT
MAINFW_MEM_PRINT_INIT
MAINFW_PRE_PMU_INIT
MAINFW_GIC_LOCK_INIT
MAINFW_APP_TIMER_LOCK_INIT
MAINFW_ULOG_INIT
MAINFW_PMU_INIT
MAINFW_SMBUS_INIT
MAINFW_INT_INIT
MAINFW_RNG_INIT
MAINFW_KERNEL_INIT_EARLY
MAINFW_PS_INIT_0
MAINFW_PS_INIT_1
MAINFW_PS_INIT_2
MAINFW_DRAM_SCRUB_WAIT
MAINFW_DRAM_SCRUB_3
MAINFW_DRIVER_SUB_INIT
MAINFW_TASK_CREATE
MAINFW_SAVE_AND_CLEAR_BRAM
MAINFW_CORESIGHT_INIT

Totals:
BOOTLOADERS_TOTAL
OVERALL_TOTAL

Operations:

- list
- metric
- lowest
- highest
- average
- count
- chart

Rules:

"lowest", "fastest", "minimum", "smallest"
    -> lowest

"highest", "slowest", "maximum", "largest", "worst"
    -> highest

"average", "avg", "mean"
    -> average

"count", "how many", "number of"
    -> count

"plot", "graph", "chart", "trend"
    -> chart

"show", "display", "list", "give"
    -> list or metric

If a specific metric is mentioned, put it in "metric".

If the user says "boot time", "overall time", or "overall",
use OVERALL_TOTAL.

If the user says "pbl", use PBL_TOTAL when the question is
clearly asking for total PBL boot time.

Return ONLY valid JSON.

The JSON must have exactly these fields:

{
  "operation": "list",
  "metric": null,
  "hostname": null,
  "sku": null,
  "bootType": null,
  "date_from": null,
  "date_to": null,
  "group_by": null,
  "limit": 100
}

Never return MongoDB syntax.
Never return Python.
Never return an explanation.
"""


def _extract_json(text):
    """
    Extract JSON from an Ollama response.

    Handles cases where the model accidentally adds
    markdown fences or surrounding text.
    """

    text = text.strip()

    # Remove markdown code fences.
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = text.strip()

    # Direct JSON.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find the first JSON object.
    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL,
    )

    if not match:
        raise ValueError(
            "Ollama did not return a JSON query."
        )

    return json.loads(match.group(0))


def ask_llm(question: str) -> dict:
    """
    Convert natural language into a structured query.
    """

    url = (
        OLLAMA_HOST.rstrip("/")
        + "/api/generate"
    )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": (
            SYSTEM_PROMPT
            + "\n\nUSER QUESTION:\n"
            + question
            + "\n\nJSON:"
        ),
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
        },
    }

    response = requests.post(
        url,
        json=payload,
        timeout=OLLAMA_TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    raw = data.get("response", "")

    if not raw:
        raise ValueError(
            "Ollama returned an empty response."
        )

    result = _extract_json(raw)

    if not isinstance(result, dict):
        raise ValueError(
            "LLM response is not a JSON object."
        )

    return result


_PLAIN_CONTEXT = (
    "You are a helpful assistant embedded in a boot-profile dashboard. "
    "Answer the user's question clearly and concisely."
)


def ask_llm_plain(question: str) -> str:
    """Plain-text answer for off-topic questions."""
    url = OLLAMA_HOST.rstrip("/") + "/api/generate"

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{_PLAIN_CONTEXT}\n\nUser: {question}\nAssistant:",
        "stream": False,
    }

    response = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
    response.raise_for_status()

    return response.json().get("response", "").strip()

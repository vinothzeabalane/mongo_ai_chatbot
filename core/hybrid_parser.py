
from core.parser import (
    parse_question,
    is_dashboard_question,
    is_simple_dashboard_question,
)

from core.query_validator import (
    validate_llm_query,
)

from ai.llm import ask_llm


class OffTopicResponse(Exception):
    """Raised to signal a plain-text answer should be shown instead of a table."""

    def __init__(self, answer: str):
        self.answer = answer


OUT_OF_SCOPE_MESSAGE = (
    "I can only answer questions about the Bootloader profile dashboard "
    "(boot metrics, hosts, SKUs, dates, etc.). That question is outside my scope."
)


def parse_hybrid(question: str):
    """
    Three-way routing:
      1. Off-topic           → fixed out-of-scope message (no LLM call)
      2. Simple dashboard    → deterministic parser
      3. Complex dashboard   → LLM JSON parser
    """

    if not isinstance(question, str):
        raise TypeError("Question must be a string.")

    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    # Gate 1: off-topic — no dashboard keywords and no metric pattern.
    # Never delegate to the LLM here; it must not answer general-knowledge questions.
    if not is_dashboard_question(question):
        raise OffTopicResponse(OUT_OF_SCOPE_MESSAGE)

    # Gate 2: simple dashboard — deterministic parser is reliable.
    if is_simple_dashboard_question(question):
        query = parse_question(question)
        return query, {"path": "deterministic", "llm_used": False}

    # Gate 3: complex dashboard — use LLM JSON parser.
    llm_data = ask_llm(question)
    query = validate_llm_query(llm_data, question)
    return query, {"path": "llm", "llm_used": True, "llm_query": llm_data}

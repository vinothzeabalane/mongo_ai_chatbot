
from core.parser import (
    parse_question,
    is_dashboard_question,
    is_simple_dashboard_question,
)

from core.query_validator import (
    validate_llm_query,
)

from ai.llm import ask_llm, ask_llm_plain


class OffTopicResponse(Exception):
    """Raised to signal a plain-text answer should be shown instead of a table."""

    def __init__(self, answer: str):
        self.answer = answer


def parse_hybrid(question: str):
    """
    Three-way routing:
      1. Off-topic           → ask_llm_plain → raise OffTopicResponse
      2. Simple dashboard    → deterministic parser
      3. Complex dashboard   → LLM JSON parser
    """

    if not isinstance(question, str):
        raise TypeError("Question must be a string.")

    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    # Gate 1: off-topic — no dashboard keywords and no metric pattern.
    if not is_dashboard_question(question):
        answer = ask_llm_plain(question)
        raise OffTopicResponse(answer)

    # Gate 2: simple dashboard — deterministic parser is reliable.
    if is_simple_dashboard_question(question):
        query = parse_question(question)
        return query, {"path": "deterministic", "llm_used": False}

    # Gate 3: complex dashboard — use LLM JSON parser.
    llm_data = ask_llm(question)
    query = validate_llm_query(llm_data, question)
    return query, {"path": "llm", "llm_used": True, "llm_query": llm_data}

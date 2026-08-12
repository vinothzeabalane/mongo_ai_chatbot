import unittest

from core.parser import parse_question
from core.query_engine import execute
from core.hybrid_parser import parse_hybrid


PARSER_CASES = [
    (
        "list all hosts",
        {"operation": "list", "metric": None, "hostname": None, "bootType": None},
    ),
    (
        "show OVERALL_TOTAL for rc136-031-19-s3",
        {"operation": "metric", "metric": "OVERALL_TOTAL", "hostname": "rc136-031-19-s3"},
    ),
    (
        "show OVERALL_TOTAL for rc136-031-19-s3 SPI",
        {"operation": "metric", "metric": "OVERALL_TOTAL", "hostname": "rc136-031-19-s3", "bootType": "SPI"},
    ),
    (
        "show performance of rc136-031-19-s3 SPI",
        {"operation": "list", "hostname": "rc136-031-19-s3", "bootType": "SPI"},
    ),
    (
        "count records for SPI",
        {"operation": "count", "bootType": "SPI"},
    ),
    (
        "show SBL_TOTAL on 2026-07-31",
        {"operation": "metric", "metric": "SBL_TOTAL", "date_from": "2026-07-31", "date_to": "2026-07-31"},
    ),
    (
        "plot SBL_TOTAL for rc136-031-19-s3",
        {"operation": "chart", "metric": "SBL_TOTAL", "hostname": "rc136-031-19-s3"},
    ),
    (
        "list all tbl total value",
        {"operation": "metric", "metric": "TBL_TOTAL"},
    ),
    (
        "show SBL_TOTAL for EB0",
        {"operation": "metric", "metric": "SBL_TOTAL", "bootType": "EB0"},
    ),
    (
        "find the highest SBL_TOTAL",
        {"operation": "highest", "metric": "SBL_TOTAL", "value_field": "max"},
    ),
    (
        "find the lowest SBL_TOTAL",
        {"operation": "lowest", "metric": "SBL_TOTAL"},
    ),
    (
        "find the fastest host based on SBL_TOTAL for EB0",
        {"operation": "lowest", "metric": "SBL_TOTAL", "bootType": "EB0", "value_field": "max"},
    ),
    (
        "find the slowest host based on SBL_TOTAL for EB0",
        {"operation": "highest", "metric": "SBL_TOTAL", "bootType": "EB0", "value_field": "max"},
    ),
    (
        "average SBL_TOTAL for EB0",
        {"operation": "average", "metric": "SBL_TOTAL", "bootType": "EB0"},
    ),
    (
        "plot SBL_TOTAL over time",
        {"operation": "chart", "metric": "SBL_TOTAL"},
    ),
]


class ParserSmokeTests(unittest.TestCase):
    def test_parser_cases(self):
        for question, expected in PARSER_CASES:
            with self.subTest(question=question):
                parsed = parse_question(question)
                for key, value in expected.items():
                    self.assertEqual(
                        getattr(parsed, key),
                        value,
                        msg=f"q={question!r} field={key}",
                    )


class IntegrationSmokeTests(unittest.TestCase):
    def test_execute_returns_result_shape(self):
        for question, _expected in PARSER_CASES:
            with self.subTest(question=question):
                query = parse_question(question)
                result = execute(query)
                self.assertIsInstance(result, dict)
                self.assertIn("query", result)
                self.assertIn("record_count", result)
                self.assertIn("pipeline", result)
                self.assertIn("records", result)
                self.assertIsInstance(result["record_count"], int)
                self.assertGreaterEqual(result["record_count"], 0)
                self.assertIsInstance(result["pipeline"], list)
                self.assertIsInstance(result["records"], list)

    def test_count_query_returns_count_document_when_present(self):
        query = parse_question("count records for SPI")
        result = execute(query)
        if result["records"]:
            self.assertIn("count", result["records"][0])

    def test_fastest_uses_max_value_field(self):
        query = parse_question("find the fastest host based on SBL_TOTAL")
        self.assertEqual(query.value_field, "max")
        self.assertEqual(query.operation, "lowest")

    def test_slowest_uses_max_value_field(self):
        query = parse_question("find the slowest host based on SBL_TOTAL")
        self.assertEqual(query.value_field, "max")
        self.assertEqual(query.operation, "highest")

    def test_validator_rejects_forbidden_operator(self):
        from core.query_validator import validate_llm_query
        with self.assertRaises(ValueError):
            validate_llm_query(
                {"operation": "list", "$where": "1==1"},
                "test",
            )

    def test_validator_rejects_unknown_metric(self):
        from core.query_validator import validate_llm_query
        with self.assertRaises(ValueError):
            validate_llm_query(
                {"operation": "metric", "metric": "SBL_UNKNOWN"},
                "test",
            )

    def test_validator_accepts_valid_value_field(self):
        from core.query_validator import validate_llm_query
        q = validate_llm_query(
            {"operation": "lowest", "metric": "SBL_TOTAL", "value_field": "max"},
            "fastest host SBL_TOTAL",
        )
        self.assertEqual(q.value_field, "max")

    def test_validator_rejects_invalid_value_field(self):
        from core.query_validator import validate_llm_query
        q = validate_llm_query(
            {"operation": "lowest", "metric": "SBL_TOTAL", "value_field": "median"},
            "test",
        )
        self.assertIsNone(q.value_field)

    def test_hybrid_unique_hostname_details_routes_deterministic(self):
        query, meta = parse_hybrid("list all unique hostname details")
        self.assertEqual(meta["path"], "deterministic")
        self.assertEqual(query.operation, "list")
        self.assertIsNone(query.hostname)

    def test_validator_sanitizes_generic_hostname(self):
        from core.query_validator import validate_llm_query
        q = validate_llm_query(
            {"operation": "list", "hostname": "unique"},
            "list all unique hostname details",
        )
        self.assertIsNone(q.hostname)



if __name__ == "__main__":
    unittest.main(verbosity=2)
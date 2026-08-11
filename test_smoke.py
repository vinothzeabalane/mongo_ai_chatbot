import unittest

from parser import parse_question
from query_engine import execute


PARSER_CASES = [
    (
        "list all hosts",
        {
            "operation": "list",
            "metric": None,
            "hostname": None,
            "bootType": None,
        },
    ),
    (
        "show OVERALL_TOTAL for rc136-031-19-s3",
        {
            "operation": "metric",
            "metric": "OVERALL_TOTAL",
            "hostname": "rc136-031-19-s3",
        },
    ),
    (
        "show performance of rc136-031-19-s3 SPI",
        {
            "operation": "list",
            "hostname": "rc136-031-19-s3",
            "bootType": "SPI",
        },
    ),
    (
        "count records for SPI",
        {
            "operation": "count",
            "bootType": "SPI",
        },
    ),
    (
        "show SBL_TOTAL on 2026-07-31",
        {
            "operation": "metric",
            "metric": "SBL_TOTAL",
            "date_from": "2026-07-31",
            "date_to": "2026-07-31",
        },
    ),
    (
        "plot SBL_TOTAL for rc136-031-19-s3",
        {
            "operation": "chart",
            "metric": "SBL_TOTAL",
            "hostname": "rc136-031-19-s3",
        },
    ),
]


class ParserSmokeTests(unittest.TestCase):
    def test_parser_cases(self):
        for question, expected in PARSER_CASES:
            with self.subTest(question=question):
                parsed = parse_question(question)

                for key, value in expected.items():
                    self.assertEqual(getattr(parsed, key), value)


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
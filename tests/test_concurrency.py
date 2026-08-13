import json
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.mongo import get_collection
from core.parser import parse_question
from core.query_engine import execute
from core import interaction_logger


class MongoClientSingletonTests(unittest.TestCase):
    def test_concurrent_get_collection_returns_same_instance(self):
        # Simulate many Streamlit sessions hitting a cold start at once.
        with ThreadPoolExecutor(max_workers=20) as pool:
            futures = [pool.submit(get_collection) for _ in range(20)]
            collections = [f.result() for f in as_completed(futures)]

        first = collections[0]
        for collection in collections:
            self.assertIs(collection, first)


class ConcurrentQueryTests(unittest.TestCase):
    def test_concurrent_execute_no_errors(self):
        questions = [
            "list all hosts",
            "count records for SPI",
            "find the highest SBL_TOTAL",
            "find the lowest SBL_TOTAL",
            "show SBL_TOTAL for EB0",
        ] * 4  # 20 concurrent queries, mixed operations

        def run(question):
            query = parse_question(question)
            return execute(query)

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(run, q) for q in questions]
            for future in as_completed(futures):
                result = future.result()  # raises if the worker threw
                self.assertIn("records", result)
                self.assertIn("pipeline", result)


class ConcurrentLoggingTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        )
        self._tmp.close()
        self._orig_path = interaction_logger.QUERY_LOG_PATH
        self._orig_enabled = interaction_logger.ENABLE_QUERY_LOGGING
        interaction_logger.QUERY_LOG_PATH = self._tmp.name
        interaction_logger.ENABLE_QUERY_LOGGING = True

    def tearDown(self):
        interaction_logger.QUERY_LOG_PATH = self._orig_path
        interaction_logger.ENABLE_QUERY_LOGGING = self._orig_enabled
        os.unlink(self._tmp.name)

    def test_concurrent_writes_produce_valid_jsonl(self):
        def write(i):
            interaction_logger.log_interaction(
                {"event": "query_success", "question": f"q{i}"}
            )

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(write, i) for i in range(50)]
            for future in as_completed(futures):
                future.result()

        with open(self._tmp.name, "r") as fh:
            lines = [line for line in fh.read().splitlines() if line]

        self.assertEqual(len(lines), 50)
        for line in lines:
            json.loads(line)  # raises if a line got interleaved/corrupted


if __name__ == "__main__":
    unittest.main()

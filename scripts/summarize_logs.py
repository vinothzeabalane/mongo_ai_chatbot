import argparse
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import QUERY_LOG_PATH


def _read_jsonl(path):
    records = []
    if not path.exists():
        return records

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return records


def _is_dashboard_like(question):
    q = (question or "").lower()
    keywords = [
        "host", "hostname", "sku", "boot", "eb0", "spi", "metric",
        "sbl", "tbl", "pbl", "overall", "plot", "graph", "trend",
        "count", "date", "record",
    ]
    return any(word in q for word in keywords)


def summarize(records, top_n):
    failures = Counter()
    offtopic = Counter()
    offtopic_misroutes = Counter()

    for rec in records:
        event = rec.get("event")
        question = rec.get("question", "")

        if event == "query_error":
            failures[question] += 1

        if event == "query_offtopic":
            offtopic[question] += 1
            if _is_dashboard_like(question):
                offtopic_misroutes[question] += 1

    return {
        "total_records": len(records),
        "total_failures": sum(failures.values()),
        "total_offtopic": sum(offtopic.values()),
        "top_failed_questions": failures.most_common(top_n),
        "top_offtopic_questions": offtopic.most_common(top_n),
        "top_offtopic_misroutes": offtopic_misroutes.most_common(top_n),
    }


def main():
    parser = argparse.ArgumentParser(description="Summarize chatbot interaction logs.")
    parser.add_argument("--path", default=QUERY_LOG_PATH, help="Path to JSONL interaction log file")
    parser.add_argument("--top", type=int, default=10, help="Top N questions to show")
    args = parser.parse_args()

    path = Path(args.path)
    records = _read_jsonl(path)
    report = summarize(records, max(1, args.top))

    print(f"Log file: {path}")
    print(f"Records: {report['total_records']}")
    print(f"Failures: {report['total_failures']}")
    print(f"Off-topic: {report['total_offtopic']}")
    print("\nTop Failed Questions")
    for q, count in report["top_failed_questions"]:
        print(f"- {count}x | {q}")

    print("\nTop Off-topic Questions")
    for q, count in report["top_offtopic_questions"]:
        print(f"- {count}x | {q}")

    print("\nTop Off-topic Misroutes (dashboard-like)")
    for q, count in report["top_offtopic_misroutes"]:
        print(f"- {count}x | {q}")


if __name__ == "__main__":
    main()

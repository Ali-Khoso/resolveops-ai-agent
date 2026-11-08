"""Live smoke evaluation: requires RAG_TEST_JWT and demo policy files to be ingested."""
import json
import os
from pathlib import Path
import httpx

CASES = Path(__file__).resolve().parents[1] / "evals" / "policy_cases.jsonl"

def evaluate(base_url: str, token: str) -> int:
    results=[]
    with httpx.Client(timeout=90) as client:
        for line in CASES.read_text(encoding="utf-8").splitlines():
            item=json.loads(line)
            response=client.post(
                f"{base_url.rstrip('/')}/api/v1/workspace/knowledge/ask",
                headers={"Authorization":f"Bearer {token}"},
                json={"question":item["question"]},
            )
            response.raise_for_status()
            answer=response.json()
            text=answer["answer"].lower()
            if item["should_abstain"]:
                passed=not answer["grounded"]
            else:
                passed=(answer["grounded"] and bool(answer["sources"])
                    and all(term.lower() in text for term in item["expected_terms"])
                    and any(s["filename"]==item["policy"] for s in answer["sources"]))
            results.append(passed)
            print(("PASS" if passed else "FAIL"),item["question"])
    print(f"Passed {sum(results)}/{len(results)} reference checks")
    return 0 if all(results) else 1

if __name__=="__main__":
    token=os.getenv("RAG_TEST_JWT","")
    if not token:
        raise SystemExit("Set RAG_TEST_JWT in your local environment; never commit your token")
    raise SystemExit(evaluate(os.getenv("RAG_TEST_API","http://127.0.0.1:8000"),token))

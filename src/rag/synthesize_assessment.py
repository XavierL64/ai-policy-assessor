"""
Step 5 CLI: synthesize final assessment from retrieved chunks for each bank.

Run from project root:
    python src/rag/synthesize_assessment.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG — edit BANK_IDS to control which banks get synthesis runs
# ---------------------------------------------------------------------------
BANK_IDS = ["ABN", "HSBC", "BBVA", "Barclays"]
COMMITMENT_ID = "CP.1"
SYNTHESIS_MODEL = "gpt-4.1"
DATA_DIR = "data/rag"
CRITERIA_CSV = "criteria/criteria.csv"
EXCEPTIONS_CSV = "exceptions/exceptions.csv"
EXCEPTIONS_CRITERIA_CSV = "exceptions/exceptions_criteria.csv"
# ---------------------------------------------------------------------------

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rag.synthesis import synthesize_assessment_from_retrieval  # noqa: E402


def main() -> None:
    data_dir = Path(DATA_DIR)

    for bank_id in BANK_IDS:
        # Input: retrieval JSON from Step 4
        retrieval_path = data_dir / f"retrieval_{bank_id.lower()}_cp1.json"
        if not retrieval_path.exists():
            print(f"  Skipping {bank_id}: {retrieval_path} not found")
            continue

        with retrieval_path.open("r", encoding="utf-8") as f:
            retrieval_payload = json.load(f)

        raw_model_output, assessment, total_tokens = synthesize_assessment_from_retrieval(
            retrieval_payload=retrieval_payload,
            model_name=SYNTHESIS_MODEL,
            criteria_csv_path=CRITERIA_CSV,
            exceptions_csv_path=EXCEPTIONS_CSV,
            exceptions_criteria_csv_path=EXCEPTIONS_CRITERIA_CSV,
        )

        output_payload = {
            "commitment_id": retrieval_payload.get("commitment_id"),
            "query_embedding_model": retrieval_payload.get("query_embedding_model"),
            "synthesis_model": SYNTHESIS_MODEL,
            "retrieval": retrieval_payload.get("retrieval", {}),
            "assessment_model_output": raw_model_output,
            "assessment": assessment,
            "synthesis_tokens_used": total_tokens,
        }

        output_path = data_dir / f"final_assessment_{bank_id.lower()}_cp1.json"
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(output_payload, f, ensure_ascii=True, indent=2)

        retrieved_count = output_payload["retrieval"].get("retrieved_count", 0)
        print(f"  {bank_id}: {retrieved_count} chunks, {total_tokens} tokens -> {output_path}")

    print(f"\nSynthesis complete for {len(BANK_IDS)} banks.")


if __name__ == "__main__":
    main()

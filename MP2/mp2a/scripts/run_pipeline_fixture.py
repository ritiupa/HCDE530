"""Run full LENS pipeline on fixture sessions (no media, no API keys required)."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from export import save_markdown
from query_engine import answer_query
from report_multimodal import generate_multimodal_report
from session_builder import session_from_fixture
from synthesis import cluster_sessions


def main() -> None:
    fixtures = sorted((ROOT / "fixtures").glob("*.json"))
    sessions = [session_from_fixture(json.loads(p.read_text(encoding="utf-8"))) for p in fixtures]
    print(f"Loaded {len(sessions)} fixture session(s)")
    for s in sessions:
        print(f"  {s.participant_id}: {s.capabilities.summary()} -> confidence {s.overall_confidence.value}")

    clusters = cluster_sessions(sessions)
    print(f"Clusters: {len(clusters)}")

    report = generate_multimodal_report(sessions, clusters, use_mistral=False)
    out = ROOT / "outputs" / "lens_report.md"
    save_markdown(report, out)
    print(f"Wrote {out}")

    ans = answer_query(
        "What would a text-only tool have missed?",
        report,
        sessions,
        use_mistral=False,
    )
    print(f"Sample query ({ans['source']}): {ans['answer'][:200]}...")


if __name__ == "__main__":
    main()

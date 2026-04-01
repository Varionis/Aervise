from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import get_settings
from pipeline.enrichment.service import EnrichmentService
from pipeline.intent.parser import InteractionService
from pipeline.orchestrator import PipelineOrchestrator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Aervise canonical decision input payload.")
    parser.add_argument("--environment", type=Path, required=True, help="Path to a normalized environment snapshot JSON file.")
    parser.add_argument("--interaction-file", type=Path, help="Path to a JSON file containing the Stage 0 request payload.")
    parser.add_argument("--interaction-json", help="Inline JSON containing the Stage 0 request payload.")
    parser.add_argument("--output", type=Path, help="Optional output file path.")
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    if not args.interaction_file and not args.interaction_json:
        raise ValueError("Either --interaction-file or --interaction-json must be provided")

    settings = get_settings()
    environment_snapshot = _load_json(args.environment)
    interaction_request = _load_json(args.interaction_file) if args.interaction_file else json.loads(args.interaction_json)

    interaction = InteractionService(settings=settings).preview(interaction_request)
    environment_state = EnrichmentService(settings=settings).snapshot_to_environment_state(environment_snapshot)
    decision_input = PipelineOrchestrator().build_decision_input(
        entry_point=interaction["entry_point"],
        intent_recognition=interaction["intent_recognition"],
        environment_state=environment_state,
    )

    rendered = json.dumps(decision_input, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

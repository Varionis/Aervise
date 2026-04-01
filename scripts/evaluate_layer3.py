from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core import DecisionLayer2Evaluator, DecisionLayer3Policy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Aervise decision engine layer 3 policy output.")
    parser.add_argument("--decision-input", type=Path, required=True, help="Path to a canonical decision input JSON file.")
    parser.add_argument("--output", type=Path, help="Optional output file path.")
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    decision_input = _load_json(args.decision_input)
    layer2 = DecisionLayer2Evaluator().evaluate(decision_input)
    layer3 = DecisionLayer3Policy().evaluate(layer2)

    rendered = json.dumps(layer3, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

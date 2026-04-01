from __future__ import annotations

import unittest

from core.modes.common import ModeEvaluationHelper


class ModeSelectionTests(unittest.TestCase):
    def test_select_best_evaluated_candidate_prefers_full_score_over_temperature(self) -> None:
        colder_candidate = {"time": "2026-04-01T01:00:00+00:00", "temperature_c": 6.0, "humidity": 95, "wind_speed": 0.5}
        milder_candidate = {"time": "2026-04-01T02:00:00+00:00", "temperature_c": 8.0, "humidity": 60, "wind_speed": 2.5}
        evaluated = [
            (colder_candidate, {"decision": {"score": 0.42, "confidence": 0.8}}),
            (milder_candidate, {"decision": {"score": 0.21, "confidence": 0.8}}),
        ]

        selected_candidate, selected_result = ModeEvaluationHelper.select_best_evaluated_candidate(evaluated)

        self.assertEqual(selected_candidate["time"], milder_candidate["time"])
        self.assertEqual(selected_result["decision"]["score"], 0.21)


if __name__ == "__main__":
    unittest.main()

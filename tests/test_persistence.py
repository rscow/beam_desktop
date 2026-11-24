import json
import tempfile
import unittest
from pathlib import Path

from beam_designer.analysis import AnalysisInput, AxialLoad, PointLoad, UniformLoad
from beam_designer.catalog import CATALOG
from beam_designer.persistence import SavedDesign, open_design, save_design


STEEL = CATALOG["Steel W-shapes"][1]


class PersistenceTests(unittest.TestCase):
    def sample_design(self) -> SavedDesign:
        inputs = AnalysisInput(
            support="cantilever",
            span_ft=18.5,
            member=STEEL,
            point_loads=(PointLoad(4.5, 12.25),),
            uniform_load=UniformLoad(.75, 2, 14),
            axial_loads=(AxialLoad(8, 7, True, 1.25, -2.5),),
            include_self_weight=False,
            deflection_limit_ratio=240,
        )
        return SavedDesign.from_analysis(inputs, "Steel W-shapes", 8.75)

    def test_round_trip_preserves_complete_design(self) -> None:
        expected = self.sample_design()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.beam.json"
            save_design(path, expected)
            actual = open_design(path)
        self.assertEqual(actual, expected)
        self.assertEqual(actual.analysis_input().member, STEEL)

    def test_saved_file_is_readable_versioned_json(self) -> None:
        design = self.sample_design()
        payload = design.to_dict()
        self.assertEqual(payload["format"], "beam-designer")
        self.assertEqual(payload["version"], 1)
        self.assertEqual(payload["beam"]["member_section"], "W14x22")
        self.assertEqual(payload["beam"]["deflection_limit_ratio"], 240)
        self.assertEqual(len(payload["loads"]["axial"]), 1)

    def test_invalid_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.beam.json"
            path.write_text(json.dumps({"format": "beam-designer", "version": 99}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                open_design(path)

    def test_load_outside_span_is_rejected_before_open(self) -> None:
        payload = self.sample_design().to_dict()
        payload["loads"]["point"][0]["position_ft"] = 99
        with self.assertRaisesRegex(ValueError, "located on the beam"):
            SavedDesign.from_dict(payload)


if __name__ == "__main__":
    unittest.main()

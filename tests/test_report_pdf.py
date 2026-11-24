import tempfile
import unittest
from pathlib import Path

from beam_designer.analysis import AnalysisInput, AxialLoad, PointLoad, UniformLoad, analyze
from beam_designer.catalog import CATALOG
from beam_designer.report_pdf import create_calculation_sheet


class CalculationSheetTests(unittest.TestCase):
    def test_pdf_contains_inputs_checks_and_all_diagrams(self) -> None:
        inputs = AnalysisInput(
            support="simple",
            span_ft=20,
            member=CATALOG["Steel W-shapes"][0],
            point_loads=(PointLoad(3, 6), PointLoad(2, 14)),
            uniform_load=UniformLoad(.5, 2, 18),
            axial_loads=(AxialLoad(5, 10, False, 1, -2),),
            include_self_weight=True,
            deflection_limit_ratio=360,
            sample_count=101,
        )
        result = analyze(inputs)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calculation-sheet.pdf"
            create_calculation_sheet(path, inputs, result, "Steel W-shapes", 10)
            data = path.read_bytes()

        self.assertTrue(data.startswith(b"%PDF-1.4"))
        self.assertTrue(data.endswith(b"%%EOF\n"))
        self.assertEqual(data.count(b"/Type /Page /Parent"), 2)
        for expected_text in (
            b"DESIGN INPUTS",
            b"Section: W12x26",
            b"Point loads",
            b"Axial loads",
            b"GOVERNING RESULTS AND CHECKS",
            b"BENDING:",
            b"Shear diagram",
            b"Moment diagram",
            b"Deflection diagram",
            b"CROSS-SECTION STRESSES",
            b"Educational analysis only",
        ):
            self.assertIn(expected_text, data)

    def test_pdf_xref_points_to_valid_object_offsets(self) -> None:
        inputs = AnalysisInput(
            support="cantilever",
            span_ft=10,
            member=CATALOG["Douglas Fir-Larch lumber"][0],
            point_loads=(PointLoad(1, 10),),
            include_self_weight=False,
            sample_count=101,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calculation-sheet.pdf"
            create_calculation_sheet(path, inputs, analyze(inputs), "Douglas Fir-Larch lumber", 5)
            data = path.read_bytes()

        xref_offset = int(data.rsplit(b"startxref\n", 1)[1].splitlines()[0])
        self.assertEqual(data[xref_offset:xref_offset + 4], b"xref")
        xref_lines = data[xref_offset:].splitlines()
        object_count = int(xref_lines[1].split()[1])
        for object_id, line in enumerate(xref_lines[3:3 + object_count - 1], 1):
            offset = int(line.split()[0])
            self.assertTrue(data[offset:].startswith(f"{object_id} 0 obj".encode("ascii")))


if __name__ == "__main__":
    unittest.main()

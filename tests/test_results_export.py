import csv
import tempfile
import unittest
from pathlib import Path

from beam_designer.analysis import AnalysisInput, UniformLoad, analyze
from beam_designer.catalog import CATALOG
from beam_designer.results_export import CSV_HEADERS, export_results_csv


class ResultsExportTests(unittest.TestCase):
    def test_csv_contains_headers_and_every_analysis_station(self) -> None:
        result = analyze(AnalysisInput(
            support="simple",
            span_ft=20,
            member=CATALOG["Steel W-shapes"][0],
            uniform_load=UniformLoad(1, 0, 20),
            include_self_weight=False,
            sample_count=101,
        ))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.csv"
            export_results_csv(path, result)
            with path.open(encoding="utf-8-sig", newline="") as source:
                rows = list(csv.reader(source))

        self.assertEqual(tuple(rows[0]), CSV_HEADERS)
        self.assertEqual(len(rows), 102)
        self.assertEqual([float(value) for value in rows[1]], [0.0, 10.0, 0.0, 0.0])
        self.assertAlmostEqual(float(rows[51][0]), 10.0)
        self.assertAlmostEqual(float(rows[51][2]), 50.0)
        self.assertAlmostEqual(float(rows[-1][0]), 20.0)

    def test_csv_has_excel_friendly_utf8_bom_and_crlf_rows(self) -> None:
        result = analyze(AnalysisInput(
            support="simple",
            span_ft=10,
            member=CATALOG["Steel W-shapes"][0],
            include_self_weight=False,
            sample_count=101,
        ))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.csv"
            export_results_csv(path, result)
            data = path.read_bytes()

        self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
        self.assertIn(b"\r\n", data)


if __name__ == "__main__":
    unittest.main()

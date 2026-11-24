"""Export calculated beam results in spreadsheet-friendly formats."""

from __future__ import annotations

import csv
from pathlib import Path

from .analysis import AnalysisResult


CSV_HEADERS = ("x (ft)", "V (kip)", "M (kip-ft)", "deflection (in)")


def export_results_csv(path: str | Path, result: AnalysisResult) -> None:
    """Write every calculated station to an Excel-compatible UTF-8 CSV file."""
    row_count = len(result.x_ft)
    if not all(len(values) == row_count for values in (result.shear_kip, result.moment_kip_ft, result.deflection_in)):
        raise ValueError("Result columns must have the same number of stations.")
    with Path(path).open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.writer(output, lineterminator="\r\n")
        writer.writerow(CSV_HEADERS)
        for row in zip(result.x_ft, result.shear_kip, result.moment_kip_ft, result.deflection_in):
            writer.writerow(f"{value:.10g}" for value in row)

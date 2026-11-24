"""Generate a dependency-free PDF calculation sheet for a beam analysis."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .analysis import AnalysisInput, AnalysisResult


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
NAVY = (0.09, 0.20, 0.30)
BLUE = (0.16, 0.45, 0.65)
RED = (0.71, 0.14, 0.09)
GREEN = (0.12, 0.48, 0.30)
GOLD = (0.54, 0.36, 0.00)
PURPLE = (0.42, 0.24, 0.60)
GRAY = (0.40, 0.47, 0.51)
LIGHT = (0.80, 0.84, 0.87)


class PdfPage:
    """Small top-origin vector drawing surface backed by PDF commands."""

    def __init__(self) -> None:
        self.commands: list[str] = []
        self.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=(1, 1, 1), fill=(1, 1, 1), line_width=0)

    @staticmethod
    def _y(y: float) -> float:
        return PAGE_HEIGHT - y

    @staticmethod
    def _color(color: tuple[float, float, float]) -> str:
        return " ".join(f"{part:.3f}" for part in color)

    def text(
        self,
        x: float,
        y: float,
        value: str,
        size: float = 9,
        bold: bool = False,
        color: tuple[float, float, float] = NAVY,
    ) -> None:
        escaped = value.encode("latin-1", "replace").decode("latin-1").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        font = "F2" if bold else "F1"
        self.commands.append(
            f"BT /{font} {size:.2f} Tf {self._color(color)} rg 1 0 0 1 {x:.2f} {self._y(y):.2f} Tm ({escaped}) Tj ET"
        )

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        color: tuple[float, float, float] = NAVY,
        width: float = 1,
        dash: str | None = None,
    ) -> None:
        dash_command = f"[{dash}] 0 d" if dash else "[] 0 d"
        self.commands.append(
            f"{self._color(color)} RG {width:.2f} w {dash_command} {x1:.2f} {self._y(y1):.2f} m {x2:.2f} {self._y(y2):.2f} l S"
        )

    def rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        stroke: tuple[float, float, float] = LIGHT,
        fill: tuple[float, float, float] | None = None,
        line_width: float = 1,
    ) -> None:
        operator = "B" if fill else "S"
        fill_command = f"{self._color(fill)} rg " if fill else ""
        self.commands.append(
            f"{self._color(stroke)} RG {fill_command}{line_width:.2f} w {x:.2f} {self._y(y + height):.2f} {width:.2f} {height:.2f} re {operator}"
        )

    def polyline(
        self,
        points: list[tuple[float, float]],
        color: tuple[float, float, float],
        width: float = 1.2,
    ) -> None:
        if len(points) < 2:
            return
        commands = [f"{points[0][0]:.2f} {self._y(points[0][1]):.2f} m"]
        commands.extend(f"{x:.2f} {self._y(y):.2f} l" for x, y in points[1:])
        self.commands.append(f"{self._color(color)} RG {width:.2f} w [] 0 d " + " ".join(commands) + " S")

    def content(self) -> bytes:
        return ("\n".join(self.commands) + "\n").encode("latin-1", "replace")


def _draw_header(page: PdfPage, page_number: int) -> None:
    page.rect(0, 0, PAGE_WIDTH, 46, stroke=NAVY, fill=NAVY, line_width=0)
    page.text(30, 27, "BEAM DESIGNER - CALCULATION SHEET", 16, True, (1, 1, 1))
    page.text(492, 26, f"Page {page_number} of 2", 9, False, (1, 1, 1))


def _draw_section_title(page: PdfPage, y: float, title: str) -> None:
    page.text(30, y, title.upper(), 10, True, NAVY)
    page.line(30, y + 5, 582, y + 5, LIGHT, .8)


def _draw_chart(
    page: PdfPage,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    xs: tuple[float, ...],
    values: tuple[float, ...],
    units: str,
    color: tuple[float, float, float],
) -> None:
    page.rect(x, y, width, height, LIGHT)
    page.text(x + 8, y + 14, f"{title} ({units})", 9, True)
    left, right, top, bottom = x + 47, x + width - 12, y + 24, y + height - 20
    minimum, maximum = min(min(values), 0), max(max(values), 0)
    if abs(maximum - minimum) < 1e-12:
        minimum, maximum = -1, 1
    span = xs[-1] - xs[0]
    map_x = lambda value: left + (value - xs[0]) / span * (right - left)
    map_y = lambda value: top + (maximum - value) / (maximum - minimum) * (bottom - top)
    zero = map_y(0)
    page.line(left, zero, right, zero, GRAY, .6)
    page.line(left, top, left, bottom, LIGHT, .6)
    points = [(map_x(x_value), map_y(value)) for x_value, value in zip(xs, values)]
    page.polyline(points, color, 1.25)
    page.text(left - 5, map_y(maximum) + 3, f"{maximum:.3g}", 7, False, GRAY)
    page.text(left - 5, map_y(minimum) + 3, f"{minimum:.3g}", 7, False, GRAY)
    page.text(left, y + height - 6, "0 ft", 7, False, GRAY)
    page.text(right - 24, y + height - 6, f"{xs[-1]:.2f} ft", 7, False, GRAY)


def _draw_beam(page: PdfPage, y: float, inputs: AnalysisInput) -> None:
    x1, x2, beam_y = 58, 558, y + 53
    map_x = lambda position: x1 + position / inputs.span_ft * (x2 - x1)
    page.rect(30, y, 552, 95, LIGHT)
    page.text(38, y + 15, "Beam and applied loads", 9, True)
    page.line(x1, beam_y, x2, beam_y, NAVY, 5)
    if inputs.support == "simple":
        for support_x in (x1, x2):
            page.line(support_x, beam_y + 3, support_x - 8, beam_y + 15, GRAY, 1.4)
            page.line(support_x - 8, beam_y + 15, support_x + 8, beam_y + 15, GRAY, 1.4)
            page.line(support_x + 8, beam_y + 15, support_x, beam_y + 3, GRAY, 1.4)
    else:
        page.line(x1, beam_y - 15, x1, beam_y + 15, GRAY, 5)
    uniform = inputs.uniform_load
    uniform_end = inputs.span_ft if uniform.end_ft is None else uniform.end_ft
    if uniform.magnitude_kip_ft:
        ux1, ux2 = map_x(uniform.start_ft), map_x(uniform_end)
        page.line(ux1, beam_y - 34, ux2, beam_y - 34, BLUE, 2)
        for index in range(11):
            arrow_x = ux1 + index * (ux2 - ux1) / 10
            page.line(arrow_x, beam_y - 33, arrow_x, beam_y - 7, BLUE, .7)
        page.text(ux1, beam_y - 40, f"w = {uniform.magnitude_kip_ft:g} kip/ft", 7, False, BLUE)
    for load in inputs.point_loads:
        load_x = map_x(load.position_ft)
        page.line(load_x, beam_y - 35, load_x, beam_y - 6, RED, 1.4)
        page.text(load_x - 15, beam_y - 40, f"{load.magnitude_kip:g} kip", 7, False, RED)
    for load in inputs.axial_loads:
        load_x = map_x(load.position_ft)
        page.text(load_x - 12, beam_y + 31, f"{'T' if load.tension else 'C'} {load.magnitude_kip:g} kip", 7, True, GREEN if load.tension else RED)
        page.line(load_x - 15, beam_y + 22, load_x + 15, beam_y + 22, GREEN if load.tension else RED, 1.5)
    page.text(x1, y + 86, "0 ft", 7, False, GRAY)
    page.text(x2 - 25, y + 86, f"{inputs.span_ft:g} ft", 7, False, GRAY)


def _draw_inputs(page: PdfPage, inputs: AnalysisInput, material_table: str, section_location_ft: float) -> None:
    _draw_section_title(page, 65, "Design inputs")
    uniform = inputs.uniform_load
    uniform_end = inputs.span_ft if uniform.end_ft is None else uniform.end_ft
    left = (
        f"Support: {'Simply supported' if inputs.support == 'simple' else 'Cantilever, fixed left'}",
        f"Span: {inputs.span_ft:g} ft",
        f"Member table: {material_table}",
        f"Section: {inputs.member.name}",
        f"Deflection limit: L/{inputs.deflection_limit_ratio:g}",
        f"Section view location: {section_location_ft:g} ft",
        f"Self-weight: {'Included' if inputs.include_self_weight else 'Excluded'} ({inputs.member.weight:g} lb/ft)",
        f"Uniform load: {uniform.magnitude_kip_ft:g} kip/ft, {uniform.start_ft:g} to {uniform_end:g} ft",
    )
    for index, value in enumerate(left):
        page.text(38, 83 + index * 13, value, 8)
    page.text(315, 83, "Point loads", 8, True)
    if inputs.point_loads:
        for index, load in enumerate(inputs.point_loads, 1):
            page.text(315, 83 + index * 13, f"{index}. {load.magnitude_kip:g} kip at {load.position_ft:g} ft", 8)
    else:
        page.text(315, 96, "None", 8, False, GRAY)
    axial_start = 92 + max(1, len(inputs.point_loads)) * 12
    page.text(315, axial_start, "Axial loads", 8, True)
    if inputs.axial_loads:
        for index, load in enumerate(inputs.axial_loads, 1):
            direction = "T" if load.tension else "C"
            page.text(315, axial_start + index * 12, f"{index}. {direction} {load.magnitude_kip:g} kip at {load.position_ft:g} ft; ex={load.horizontal_offset_in:g}, ey={load.vertical_offset_in:g} in", 7.5)
    else:
        page.text(315, axial_start + 13, "None", 8, False, GRAY)


def _draw_checks(page: PdfPage, y: float, inputs: AnalysisInput, result: AnalysisResult) -> None:
    _draw_section_title(page, y, "Governing results and checks")
    page.text(38, y + 22, f"Maximum shear: {result.max_shear_kip:.3f} kip at x = {result.max_shear_location_ft:.3f} ft", 8)
    page.text(38, y + 36, f"Maximum moment: {result.max_moment_kip_ft:.3f} kip-ft at x = {result.max_moment_location_ft:.3f} ft", 8)
    page.text(38, y + 50, f"Maximum deflection: {result.max_deflection_in:.4f} in at x = {result.max_deflection_location_ft:.3f} ft", 8)
    bending_color = GREEN if result.bending_passes else RED
    deflection_color = GREEN if result.deflection_passes else RED
    page.text(315, y + 22, f"BENDING: {'PASS' if result.bending_passes else 'FAIL'}", 9, True, bending_color)
    page.text(315, y + 36, f"Combined stress {result.combined_stress_ksi:.3f} ksi / allowable {inputs.member.allowable_bending / 1000:.3f} ksi ({result.bending_utilization:.1%})", 7.5)
    page.text(315, y + 50, f"DEFLECTION L/{inputs.deflection_limit_ratio:g}: {'PASS' if result.deflection_passes else 'FAIL'}", 9, True, deflection_color)
    page.text(315, y + 64, f"{result.max_deflection_in:.4f} in / {result.deflection_limit_in:.4f} in ({result.deflection_utilization:.1%})", 7.5)


def _draw_cross_section(page: PdfPage, y: float, inputs: AnalysisInput, result: AnalysisResult, location: float) -> None:
    _draw_section_title(page, y, "Cross-section stresses")
    member = inputs.member
    index = result.nearest_index(location)
    moment = result.moment_kip_ft[index]
    shear = result.shear_kip[index]
    bending = moment * 12 / member.sx
    shear_area = member.depth * member.web_thickness if member.material == "steel" and member.web_thickness else member.area
    average_shear = shear / shear_area
    cx, cy, section_height = 145, y + 112, 150
    scale = section_height / member.depth
    section_width = max(25, member.width * scale)
    if member.material == "steel":
        flange_height = max(5, (member.flange_thickness or 0) * scale)
        web_width = max(5, (member.web_thickness or 0) * scale)
        page.rect(cx - section_width / 2, cy - section_height / 2, section_width, flange_height, NAVY, (0.86, 0.91, 0.95), 1)
        page.rect(cx - web_width / 2, cy - section_height / 2 + flange_height, web_width, section_height - 2 * flange_height, NAVY, (0.66, 0.78, 0.87), 1)
        page.rect(cx - section_width / 2, cy + section_height / 2 - flange_height, section_width, flange_height, NAVY, (0.86, 0.91, 0.95), 1)
    else:
        page.rect(cx - section_width / 2, cy - section_height / 2, section_width, section_height, NAVY, (0.85, 0.79, 0.65), 1)
    page.line(cx - section_width / 2 - 12, cy, cx + section_width / 2 + 12, cy, GRAY, .6, "3 3")
    text_x = 260
    lines = (
        f"Selected location: x = {location:.3f} ft",
        f"Local moment M = {moment:+.3f} kip-ft",
        f"Local shear V = {shear:+.3f} kip",
        f"Edge bending stress fb = M/Sx = {bending:+.3f} ksi",
        f"Average educational shear stress = {average_shear:+.3f} ksi",
        f"Governing combined stress = {result.combined_stress_ksi:.3f} ksi",
        "Positive moment: top compression / bottom tension.",
    )
    for index, line in enumerate(lines):
        page.text(text_x, y + 35 + index * 18, line, 8, index == 5)


def _draw_basis(page: PdfPage, y: float, inputs: AnalysisInput) -> None:
    _draw_section_title(page, y, "Calculation basis and limitations")
    notes = (
        "Reactions, shear, and moment are determined from static equilibrium.",
        "Elastic deflection is obtained by integrating M/(EI); axial deformation and P-delta effects are excluded.",
        "Bending stress: fb = M/Sx. Deflection utilization: maximum deflection / (span / selected ratio).",
        "No shear strength check is reported. Displayed shear stress is an educational average approximation only.",
        f"Member properties: {inputs.member.source}. {inputs.member.assumptions}",
        "Sign convention: downward loads are positive; positive moment produces top compression and bottom tension.",
        "Educational analysis only - not for final structural design.",
    )
    for index, note in enumerate(notes):
        page.text(38, y + 22 + index * 18, note, 7.7, index == len(notes) - 1, RED if index == len(notes) - 1 else NAVY)


def create_calculation_sheet(
    path: str | Path,
    inputs: AnalysisInput,
    result: AnalysisResult,
    material_table: str,
    section_location_ft: float,
) -> None:
    """Write a two-page, vector PDF calculation sheet for the current design."""
    page1, page2 = PdfPage(), PdfPage()
    _draw_header(page1, 1)
    _draw_inputs(page1, inputs, material_table, section_location_ft)
    _draw_checks(page1, 225, inputs, result)
    _draw_beam(page1, 310, inputs)
    _draw_chart(page1, 30, 415, 552, 135, "Shear diagram", result.x_ft, result.shear_kip, "kip", BLUE)
    _draw_chart(page1, 30, 565, 552, 135, "Moment diagram", result.x_ft, result.moment_kip_ft, "kip-ft", GOLD)
    page1.text(30, 752, f"Generated {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}", 7, False, GRAY)

    _draw_header(page2, 2)
    _draw_chart(page2, 30, 68, 552, 155, "Deflection diagram", result.x_ft, result.deflection_in, "in", PURPLE)
    _draw_cross_section(page2, 250, inputs, result, section_location_ft)
    _draw_basis(page2, 475, inputs)
    page2.text(30, 752, "Beam Designer calculation sheet", 7, False, GRAY)
    _write_pdf(Path(path), (page1, page2))


def _write_pdf(path: Path, pages: tuple[PdfPage, ...]) -> None:
    objects: list[bytes | None] = [None]
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(None)
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    page_ids: list[int] = []
    for page in pages:
        page_id = len(objects)
        objects.append(None)
        content = page.content()
        content_id = len(objects)
        objects.append(b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"endstream")
        objects[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode("ascii")
        page_ids.append(page_id)
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[2] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii")

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_id, body in enumerate(objects[1:], 1):
        offsets.append(len(output))
        output.extend(f"{object_id} 0 obj\n".encode("ascii"))
        output.extend(body or b"")
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects)}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(output)

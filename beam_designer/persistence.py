"""Versioned JSON persistence for Beam Designer files."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .analysis import AnalysisInput, AxialLoad, PointLoad, UniformLoad, validate
from .catalog import CATALOG


FORMAT_NAME = "beam-designer"
FORMAT_VERSION = 1


@dataclass(frozen=True)
class SavedDesign:
    support: str
    span_ft: float
    material_table: str
    member_name: str
    deflection_limit_ratio: float
    section_location_ft: float
    include_self_weight: bool
    point_loads: tuple[PointLoad, ...]
    uniform_load: UniformLoad
    axial_loads: tuple[AxialLoad, ...]

    @classmethod
    def from_analysis(
        cls,
        inputs: AnalysisInput,
        material_table: str,
        section_location_ft: float,
    ) -> SavedDesign:
        return cls(
            support=inputs.support,
            span_ft=inputs.span_ft,
            material_table=material_table,
            member_name=inputs.member.name,
            deflection_limit_ratio=inputs.deflection_limit_ratio,
            section_location_ft=section_location_ft,
            include_self_weight=inputs.include_self_weight,
            point_loads=inputs.point_loads,
            uniform_load=inputs.uniform_load,
            axial_loads=inputs.axial_loads,
        )

    def analysis_input(self) -> AnalysisInput:
        try:
            member = next(member for member in CATALOG[self.material_table] if member.name == self.member_name)
        except (KeyError, StopIteration) as error:
            raise ValueError(f"Saved member section is not available: {self.member_name}") from error
        inputs = AnalysisInput(
            support=self.support,
            span_ft=self.span_ft,
            member=member,
            point_loads=self.point_loads,
            uniform_load=self.uniform_load,
            axial_loads=self.axial_loads,
            include_self_weight=self.include_self_weight,
            deflection_limit_ratio=self.deflection_limit_ratio,
        )
        validate(inputs)
        if not 0 <= self.section_location_ft <= self.span_ft:
            raise ValueError("Saved cross-section location must be on the beam.")
        if len(self.point_loads) > 5 or len(self.axial_loads) > 5:
            raise ValueError("Saved designs may contain at most five point and five axial loads.")
        return inputs

    def to_dict(self) -> dict[str, Any]:
        uniform_end = self.span_ft if self.uniform_load.end_ft is None else self.uniform_load.end_ft
        return {
            "format": FORMAT_NAME,
            "version": FORMAT_VERSION,
            "beam": {
                "support": self.support,
                "span_ft": self.span_ft,
                "material_table": self.material_table,
                "member_section": self.member_name,
                "deflection_limit_ratio": self.deflection_limit_ratio,
                "section_location_ft": self.section_location_ft,
                "include_self_weight": self.include_self_weight,
            },
            "loads": {
                "point": [
                    {"magnitude_kip": load.magnitude_kip, "position_ft": load.position_ft}
                    for load in self.point_loads
                ],
                "uniform": {
                    "magnitude_kip_ft": self.uniform_load.magnitude_kip_ft,
                    "start_ft": self.uniform_load.start_ft,
                    "end_ft": uniform_end,
                },
                "axial": [
                    {
                        "magnitude_kip": load.magnitude_kip,
                        "position_ft": load.position_ft,
                        "direction": "tension" if load.tension else "compression",
                        "horizontal_offset_in": load.horizontal_offset_in,
                        "vertical_offset_in": load.vertical_offset_in,
                    }
                    for load in self.axial_loads
                ],
            },
        }

    @classmethod
    def from_dict(cls, payload: Any) -> SavedDesign:
        if not isinstance(payload, dict):
            raise ValueError("Design file must contain a JSON object.")
        if payload.get("format") != FORMAT_NAME:
            raise ValueError("This is not a Beam Designer file.")
        if payload.get("version") != FORMAT_VERSION:
            raise ValueError(f"Unsupported design file version: {payload.get('version')!r}.")
        beam = _mapping(payload.get("beam"), "beam")
        loads = _mapping(payload.get("loads"), "loads")
        point_data = _list(loads.get("point"), "point loads")
        axial_data = _list(loads.get("axial"), "axial loads")
        uniform_data = _mapping(loads.get("uniform"), "uniform load")
        include_self_weight = beam.get("include_self_weight")
        if not isinstance(include_self_weight, bool):
            raise ValueError("include_self_weight must be true or false.")

        design = cls(
            support=_string(beam.get("support"), "support"),
            span_ft=_number(beam.get("span_ft"), "span_ft"),
            material_table=_string(beam.get("material_table"), "material_table"),
            member_name=_string(beam.get("member_section"), "member_section"),
            deflection_limit_ratio=_number(beam.get("deflection_limit_ratio"), "deflection_limit_ratio"),
            section_location_ft=_number(beam.get("section_location_ft"), "section_location_ft"),
            include_self_weight=include_self_weight,
            point_loads=tuple(
                PointLoad(
                    _number(_mapping(item, "point load").get("magnitude_kip"), "point magnitude"),
                    _number(_mapping(item, "point load").get("position_ft"), "point position"),
                )
                for item in point_data
            ),
            uniform_load=UniformLoad(
                _number(uniform_data.get("magnitude_kip_ft"), "uniform magnitude"),
                _number(uniform_data.get("start_ft"), "uniform start"),
                _number(uniform_data.get("end_ft"), "uniform end"),
            ),
            axial_loads=tuple(_axial_load(item) for item in axial_data),
        )
        design.analysis_input()
        return design


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object.")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a JSON array.")
    return value


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number.")
    return float(value)


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be text.")
    return value


def _axial_load(value: Any) -> AxialLoad:
    item = _mapping(value, "axial load")
    direction = _string(item.get("direction"), "axial direction")
    if direction not in {"tension", "compression"}:
        raise ValueError("Axial direction must be tension or compression.")
    return AxialLoad(
        magnitude_kip=_number(item.get("magnitude_kip"), "axial magnitude"),
        position_ft=_number(item.get("position_ft"), "axial position"),
        tension=direction == "tension",
        horizontal_offset_in=_number(item.get("horizontal_offset_in"), "horizontal offset"),
        vertical_offset_in=_number(item.get("vertical_offset_in"), "vertical offset"),
    )


def save_design(path: str | Path, design: SavedDesign) -> None:
    Path(path).write_text(json.dumps(design.to_dict(), indent=2) + "\n", encoding="utf-8")


def open_design(path: str | Path) -> SavedDesign:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Design file is not valid JSON: {error.msg}.") from error
    return SavedDesign.from_dict(payload)

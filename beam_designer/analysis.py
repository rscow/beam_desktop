"""Testable statics, stress, and elastic-deflection calculations."""

from dataclasses import dataclass, field
from math import isfinite

from .catalog import Member


@dataclass(frozen=True)
class PointLoad:
    magnitude_kip: float
    position_ft: float


@dataclass(frozen=True)
class UniformLoad:
    magnitude_kip_ft: float = 0.0
    start_ft: float = 0.0
    end_ft: float | None = None


@dataclass(frozen=True)
class AxialLoad:
    magnitude_kip: float
    position_ft: float
    tension: bool = False
    horizontal_offset_in: float = 0.0
    vertical_offset_in: float = 0.0

    @property
    def signed_pounds(self) -> float:
        return self.magnitude_kip * 1000 * (1 if self.tension else -1)


@dataclass(frozen=True)
class AnalysisInput:
    support: str
    span_ft: float
    member: Member
    point_loads: tuple[PointLoad, ...] = ()
    uniform_load: UniformLoad = field(default_factory=UniformLoad)
    axial_loads: tuple[AxialLoad, ...] = ()
    include_self_weight: bool = True
    sample_count: int = 801


@dataclass(frozen=True)
class AnalysisResult:
    x_ft: tuple[float, ...]
    shear_kip: tuple[float, ...]
    moment_kip_ft: tuple[float, ...]
    deflection_in: tuple[float, ...]
    reaction_left_kip: float
    reaction_right_kip: float
    max_shear_kip: float
    max_shear_location_ft: float
    max_moment_kip_ft: float
    max_moment_location_ft: float
    max_deflection_in: float
    max_deflection_location_ft: float
    combined_stress_ksi: float
    bending_utilization: float
    deflection_limit_in: float
    deflection_utilization: float

    @property
    def bending_passes(self) -> bool:
        return self.bending_utilization <= 1

    @property
    def deflection_passes(self) -> bool:
        return self.deflection_utilization <= 1

    def nearest_index(self, position_ft: float) -> int:
        return min(range(len(self.x_ft)), key=lambda index: abs(self.x_ft[index] - position_ft))


def validate(inputs: AnalysisInput) -> None:
    if inputs.support not in {"simple", "cantilever"}:
        raise ValueError("Support condition must be simply supported or cantilever.")
    if not isfinite(inputs.span_ft) or inputs.span_ft <= 0:
        raise ValueError("Span must be greater than zero.")
    if inputs.sample_count < 101:
        raise ValueError("At least 101 calculation samples are required.")
    for load in inputs.point_loads:
        if not (isfinite(load.magnitude_kip) and isfinite(load.position_ft)):
            raise ValueError("Point-load values must be finite numbers.")
        if not 0 <= load.position_ft <= inputs.span_ft:
            raise ValueError("Every point load must be located on the beam.")
    uniform = inputs.uniform_load
    end = inputs.span_ft if uniform.end_ft is None else uniform.end_ft
    if not all(isfinite(value) for value in (uniform.magnitude_kip_ft, uniform.start_ft, end)):
        raise ValueError("Uniform-load values must be finite numbers.")
    if not (0 <= uniform.start_ft <= inputs.span_ft and 0 <= end <= inputs.span_ft):
        raise ValueError("The uniform load must begin and end on the beam.")
    for load in inputs.axial_loads:
        values = (load.magnitude_kip, load.position_ft, load.horizontal_offset_in, load.vertical_offset_in)
        if not all(isfinite(value) for value in values) or load.magnitude_kip < 0:
            raise ValueError("Axial-load values must be finite; magnitude cannot be negative.")
        if not 0 <= load.position_ft <= inputs.span_ft:
            raise ValueError("Every axial load must be located on the beam.")


def _cumulative_trapezoid(values: list[float], dx: float) -> list[float]:
    result = [0.0]
    for previous, current in zip(values, values[1:]):
        result.append(result[-1] + (previous + current) * dx / 2)
    return result


def analyze(inputs: AnalysisInput) -> AnalysisResult:
    validate(inputs)
    member = inputs.member
    length = inputs.span_ft * 12
    count = inputs.sample_count if inputs.sample_count % 2 else inputs.sample_count + 1
    xs = [index * length / (count - 1) for index in range(count)]
    points = [(load.magnitude_kip * 1000, load.position_ft * 12) for load in inputs.point_loads if load.magnitude_kip]
    uniform = inputs.uniform_load
    uniform_start = min(uniform.start_ft, uniform.end_ft if uniform.end_ft is not None else inputs.span_ft) * 12
    uniform_end = max(uniform.start_ft, uniform.end_ft if uniform.end_ft is not None else inputs.span_ft) * 12
    distributed_loads = [
        (uniform.magnitude_kip_ft * 1000 / 12, uniform_start, uniform_end),
    ]
    if inputs.include_self_weight:
        distributed_loads.append((member.weight / 12, 0.0, length))

    total_point = sum(load for load, _ in points)
    total_uniform = sum(load * max(0.0, end - start) for load, start, end in distributed_loads)
    reaction_left = reaction_right = 0.0
    if inputs.support == "simple":
        point_moment = sum(load * position for load, position in points)
        uniform_moment = sum(load * (end**2 - start**2) / 2 for load, start, end in distributed_loads)
        reaction_right = (point_moment + uniform_moment) / length
        reaction_left = total_point + total_uniform - reaction_right
    else:
        reaction_left = total_point + total_uniform

    shear: list[float] = []
    moment: list[float] = []
    for x in xs:
        if inputs.support == "simple":
            local_shear = reaction_left
            local_moment = reaction_left * x
            for load, position in points:
                if x >= position:
                    local_shear -= load
                    local_moment -= load * (x - position)
            for load, start, end in distributed_loads:
                loaded_end = min(x, end)
                if loaded_end > start:
                    loaded_length = loaded_end - start
                    local_shear -= load * loaded_length
                    local_moment -= load * loaded_length * (x - (start + loaded_length / 2))
        else:
            local_shear = local_moment = 0.0
            for load, position in points:
                if position > x:
                    local_shear += load
                    local_moment += load * (position - x)
            for load, start, end in distributed_loads:
                if end > x:
                    loaded_start = max(x, start)
                    loaded_length = max(0.0, end - loaded_start)
                    local_shear += load * loaded_length
                    local_moment += load * loaded_length * (loaded_start + loaded_length / 2 - x)

        for axial in inputs.axial_loads:
            eccentric_moment = axial.signed_pounds * axial.vertical_offset_in
            position = axial.position_ft * 12
            if inputs.support == "simple":
                local_moment -= eccentric_moment * (x / length)
                if x >= position:
                    local_moment += eccentric_moment
            elif x < position:
                local_moment -= eccentric_moment
        shear.append(local_shear)
        moment.append(local_moment)

    dx = length / (count - 1)
    first_integral = _cumulative_trapezoid(moment, dx)
    second_integral = _cumulative_trapezoid(first_integral, dx)
    elastic_rigidity = member.elastic_modulus * member.ix
    if inputs.support == "simple":
        correction = second_integral[-1] / length
        deflection = [(correction * x - value) / elastic_rigidity for x, value in zip(xs, second_integral)]
    else:
        deflection = [-value / elastic_rigidity for value in second_integral]

    shear_kip = [value / 1000 for value in shear]
    moment_kip_ft = [value / 12000 for value in moment]
    max_shear_index = max(range(count), key=lambda index: abs(shear_kip[index]))
    max_moment_index = max(range(count), key=lambda index: abs(moment_kip_ft[index]))
    max_deflection_index = max(range(count), key=lambda index: abs(deflection[index]))
    max_moment_in_lb = abs(moment[max_moment_index])

    axial_stress = sum(load.signed_pounds for load in inputs.axial_loads) / member.area
    weak_moment = sum(load.signed_pounds * load.horizontal_offset_in for load in inputs.axial_loads)
    strong_stress = max_moment_in_lb / member.sx
    weak_stress = weak_moment / member.sy
    corners = (
        axial_stress + strong_stress + weak_stress,
        axial_stress + strong_stress - weak_stress,
        axial_stress - strong_stress + weak_stress,
        axial_stress - strong_stress - weak_stress,
    )
    combined_stress_psi = max(abs(value) for value in corners)
    deflection_limit = length / 360
    max_deflection = abs(deflection[max_deflection_index])

    return AnalysisResult(
        x_ft=tuple(x / 12 for x in xs),
        shear_kip=tuple(shear_kip),
        moment_kip_ft=tuple(moment_kip_ft),
        deflection_in=tuple(deflection),
        reaction_left_kip=reaction_left / 1000,
        reaction_right_kip=reaction_right / 1000,
        max_shear_kip=abs(shear_kip[max_shear_index]),
        max_shear_location_ft=xs[max_shear_index] / 12,
        max_moment_kip_ft=abs(moment_kip_ft[max_moment_index]),
        max_moment_location_ft=xs[max_moment_index] / 12,
        max_deflection_in=max_deflection,
        max_deflection_location_ft=xs[max_deflection_index] / 12,
        combined_stress_ksi=combined_stress_psi / 1000,
        bending_utilization=combined_stress_psi / member.allowable_bending,
        deflection_limit_in=deflection_limit,
        deflection_utilization=max_deflection / deflection_limit,
    )

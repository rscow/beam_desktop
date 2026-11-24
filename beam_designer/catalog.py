"""Bundled, documented member properties used by Beam Designer."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Member:
    name: str
    material: str
    area: float  # in^2
    ix: float  # in^4
    sx: float  # in^3
    iy: float  # in^4
    sy: float  # in^3
    weight: float  # lb/ft
    elastic_modulus: float  # psi
    allowable_bending: float  # psi
    depth: float  # in
    width: float  # in
    flange_thickness: float | None = None  # in
    web_thickness: float | None = None  # in
    source: str = ""
    assumptions: str = ""


STEEL_SOURCE = "AISC Steel Construction Manual / AISC Shapes Database v16.0"
LUMBER_SOURCE = "2024 NDS Supplement, AWC, Table 4A"


def lumber_member(name: str, width: float, depth: float, allowable: float) -> Member:
    area = width * depth
    ix = width * depth**3 / 12
    sx = width * depth**2 / 6
    iy = depth * width**3 / 12
    sy = depth * width**2 / 6
    return Member(
        name=name,
        material="lumber",
        area=area,
        ix=ix,
        sx=sx,
        iy=iy,
        sy=sy,
        weight=area / 144 * 35,
        elastic_modulus=1_600_000,
        allowable_bending=allowable,
        depth=depth,
        width=width,
        source=LUMBER_SOURCE,
        assumptions="No. 2 reference values; normal load duration and dry service; adjustment factors not applied.",
    )


CATALOG: dict[str, tuple[Member, ...]] = {
    "Steel W-shapes": (
        Member("W12x26", "steel", 7.65, 204, 33.4, 17.3, 5.34, 26, 29_000_000, 23_760, 12.2, 6.49, .380, .230, STEEL_SOURCE, "ASTM A36; educational allowable Fb = 23.76 ksi."),
        Member("W14x22", "steel", 6.49, 199, 29.0, 7.0, 2.80, 22, 29_000_000, 23_760, 13.7, 5.00, .335, .230, STEEL_SOURCE, "ASTM A36; educational allowable Fb = 23.76 ksi."),
        Member("W16x26", "steel", 7.68, 301, 38.4, 9.59, 3.49, 26, 29_000_000, 23_760, 15.7, 5.50, .345, .250, STEEL_SOURCE, "ASTM A36; educational allowable Fb = 23.76 ksi."),
    ),
    "Douglas Fir-Larch lumber": (
        lumber_member("2x8 Douglas Fir-Larch No. 2", 1.5, 7.25, 900),
        lumber_member("2x10 Douglas Fir-Larch No. 2", 1.5, 9.25, 900),
        lumber_member("2x12 Douglas Fir-Larch No. 2", 1.5, 11.25, 850),
    ),
}


def find_member(name: str) -> Member:
    for members in CATALOG.values():
        for member in members:
            if member.name == name:
                return member
    raise KeyError(f"Unknown member: {name}")

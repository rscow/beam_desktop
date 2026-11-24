# Bundled member data

The application stores its member catalog in `beam_designer/catalog.py`.

## Steel W-shapes

Geometric properties for W12x26, W14x22, and W16x26 are transcribed from the
AISC Steel Construction Manual / AISC Shapes Database v16.0. Values include
area, Ix, Sx, Iy, Sy, nominal weight, depth, flange width, flange thickness,
and web thickness. The educational MVP assumes ASTM A36 steel, E = 29,000 ksi,
and an allowable bending stress of 23.76 ksi.

Source: AISC Steel Construction Manual resources,
https://www.aisc.org/publications/steel-construction-manual-resources/

## Douglas Fir-Larch lumber

The included 2x8, 2x10, and 2x12 members use surfaced dry actual dimensions.
Ix, Sx, Iy, Sy, and area are calculated from the rectangular dimensions. The
reference modulus of elasticity is 1,600,000 psi and density is assumed to be
35 lb/ft³. Reference bending values are from the 2024 NDS Supplement, AWC,
Table 4A. Normal load duration and dry service are assumed; adjustment factors
are not applied.

Source: 2024 NDS Supplement,
https://awc.org/resources/2024-nds-supplement/

These values are bundled for educational use and are not a substitute for
project-specific structural design data.

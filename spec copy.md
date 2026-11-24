# Beam Designer

## Purpose
Shear, moment, and deflection diagrams for a beam, with a check of
whether the beam is strong and stiff enough.

This is a conservative educational-strength MVP, not a general
beam-design or final structural-design tool.

## Inputs
- Support condition: simply supported or cantilever
- Span in feet
- Point loads with magnitude and position
- Uniform loads, including full-span and partial-span loads
- Steel W-shapes or lumber members from bundled property tables
- Downward loads are positive

Use unit labels beside every input. Keep catalog property values and
material assumptions clearly identified.

## Assumptions
- Loads have no eccentricity.
- Beam self-weight is included by default and can be disabled.
- Axial loads are tension or compression through the member axis at selected cross-section coordinates.
- Axial eccentricity creates combined axial and strong-/weak-axis bending stress in the cross-section view.
- Axial-load effects do not include axial deformation or P-delta analysis.
- Deflection calculations use elastic deflection behavior.
- Steel bending uses strong-axis catalog properties (`Ix` and `Sx`).
- Lumber uses actual dimensions and catalog/grade properties.
- Shear and moment diagrams use kips and kip-ft.
- Deflection diagrams use inches.
- The app is for educational use, not final structural design.

## Calculations
- Reactions, shear, and moment from statics
- Elastic deflection
- Bending stress: `fb = M / Sx`
- Bending utilization: `fb / allowable bending stress`
- Deflection utilization: `maximum deflection / (span / 360)`
- Shear and beam diagrams

Do not add a shear strength check unless shear properties and a validated
allowable-shear basis are available. If omitted, do not present a shear
check or imply one is included.

## Beam properties
Use real, standardized catalog values rather than estimates.

For steel W-shapes, store at least:
- Nominal designation, such as W12x26
- Area
- Strong-axis moment of inertia, `Ix`
- Strong-axis elastic section modulus, `Sx`
- Beam weight per foot
- Young's modulus, `E`
- Material grade or allowable bending stress

For lumber, store at least:
- Species and grade
- Nominal size
- Actual dimensions
- Moment of inertia, `Ix`
- Section modulus, `Sx`
- Young's modulus, `E`
- Allowable bending stress
- Applicable adjustment assumptions

Catalog values and any adjustments must be sourced and documented in
`01_data/`. Custom property entry may be omitted from the MVP.

## Outputs
- Beam diagram with loads, supports, and span
- Shear, moment, and deflection diagrams
- Maximum shear and its location
- Maximum moment and its location
- Maximum deflection and its location
- Cross section with bending stress distribution at maximum moment
- Cross section with average educational shear stress at maximum shear
- Axial tension and compression loads, up to five
- Axial-load location along the beam and horizontal/vertical eccentricity
- Combined axial and eccentric bending stress shown at cross-section corners
- Axial loads are labeled and represented with tension/compression arrows on the beam diagram
- A span slider selects the cross-section location for local moment and shear stress
- Vertical eccentricity affects strong-axis moment and deflection; horizontal eccentricity affects weak-axis bending stress
- Axial stress participates in the bending utilization output
- Pass/fail and utilization for bending
- Pass/fail and utilization for deflection
- Numeric units clearly shown
- Positive and negative sign conventions clearly identified

## Look and feel
Clean and professional, with an example beam loaded when it opens.

## Validation
At minimum, validate and retain hand calculations in `02_validation/`
for:
- A 20 ft simply supported W12x26 with 1 kip/ft: M = 50.0 kip-ft,
  deflection = 0.609 in
- A simply supported beam with a centered 10-kip point load
- A cantilever beam with a 10-kip tip load
- A partial distributed load
- A representative lumber beam

Record input assumptions, beam properties, equations, and expected
outputs for each case.

## Out of scope
Continuous beams and buckling.

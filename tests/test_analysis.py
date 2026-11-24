import unittest

from beam_designer.analysis import AnalysisInput, AxialLoad, PointLoad, UniformLoad, analyze
from beam_designer.catalog import CATALOG


STEEL = CATALOG["Steel W-shapes"][0]
LUMBER = CATALOG["Douglas Fir-Larch lumber"][1]


class AnalysisTests(unittest.TestCase):
    def test_simply_supported_full_span_uniform_load(self) -> None:
        result = analyze(AnalysisInput(
            support="simple",
            span_ft=20,
            member=STEEL,
            uniform_load=UniformLoad(1, 0, 20),
            include_self_weight=False,
        ))
        self.assertAlmostEqual(result.reaction_left_kip, 10, places=6)
        self.assertAlmostEqual(result.reaction_right_kip, 10, places=6)
        self.assertAlmostEqual(result.max_moment_kip_ft, 50, places=5)
        self.assertAlmostEqual(result.max_moment_location_ft, 10, places=5)
        self.assertAlmostEqual(result.max_deflection_in, 0.6085, delta=0.001)

    def test_simply_supported_center_point_load(self) -> None:
        result = analyze(AnalysisInput(
            support="simple",
            span_ft=20,
            member=STEEL,
            point_loads=(PointLoad(10, 10),),
            include_self_weight=False,
        ))
        self.assertAlmostEqual(result.reaction_left_kip, 5, places=6)
        self.assertAlmostEqual(result.reaction_right_kip, 5, places=6)
        self.assertAlmostEqual(result.max_moment_kip_ft, 50, places=5)
        expected_deflection = 10_000 * 240**3 / (48 * STEEL.elastic_modulus * STEEL.ix)
        self.assertAlmostEqual(result.max_deflection_in, expected_deflection, delta=0.002)

    def test_cantilever_tip_load(self) -> None:
        result = analyze(AnalysisInput(
            support="cantilever",
            span_ft=20,
            member=STEEL,
            point_loads=(PointLoad(10, 20),),
            include_self_weight=False,
        ))
        self.assertAlmostEqual(result.reaction_left_kip, 10, places=6)
        self.assertAlmostEqual(result.max_shear_kip, 10, places=6)
        self.assertAlmostEqual(result.max_moment_kip_ft, 200, places=5)
        expected_deflection = 10_000 * 240**3 / (3 * STEEL.elastic_modulus * STEEL.ix)
        self.assertAlmostEqual(result.max_deflection_in, expected_deflection, delta=0.01)

    def test_partial_uniform_load_reactions(self) -> None:
        result = analyze(AnalysisInput(
            support="simple",
            span_ft=20,
            member=STEEL,
            uniform_load=UniformLoad(1, 5, 15),
            include_self_weight=False,
        ))
        self.assertAlmostEqual(result.reaction_left_kip, 5, places=6)
        self.assertAlmostEqual(result.reaction_right_kip, 5, places=6)
        self.assertAlmostEqual(result.max_moment_kip_ft, 37.5, places=4)

    def test_representative_lumber_beam(self) -> None:
        result = analyze(AnalysisInput(
            support="simple",
            span_ft=12,
            member=LUMBER,
            uniform_load=UniformLoad(.1, 0, 12),
            include_self_weight=False,
        ))
        self.assertAlmostEqual(result.max_moment_kip_ft, 1.8, places=4)
        expected = 5 * (100 / 12) * 144**4 / (384 * LUMBER.elastic_modulus * LUMBER.ix)
        self.assertAlmostEqual(result.max_deflection_in, expected, delta=0.001)

    def test_axial_and_weak_axis_stress_are_combined(self) -> None:
        baseline = analyze(AnalysisInput(
            support="simple",
            span_ft=20,
            member=STEEL,
            uniform_load=UniformLoad(1, 0, 20),
            include_self_weight=False,
        ))
        combined = analyze(AnalysisInput(
            support="simple",
            span_ft=20,
            member=STEEL,
            uniform_load=UniformLoad(1, 0, 20),
            axial_loads=(AxialLoad(10, 10, False, 1, 0),),
            include_self_weight=False,
        ))
        self.assertGreater(combined.combined_stress_ksi, baseline.combined_stress_ksi)

    def test_self_weight_remains_full_span_with_partial_udl(self) -> None:
        result = analyze(AnalysisInput(
            support="simple",
            span_ft=20,
            member=STEEL,
            uniform_load=UniformLoad(0, 5, 15),
            include_self_weight=True,
        ))
        expected_total_kip = STEEL.weight * 20 / 1000
        self.assertAlmostEqual(result.reaction_left_kip + result.reaction_right_kip, expected_total_kip, places=6)

    def test_load_outside_span_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "located on the beam"):
            analyze(AnalysisInput(
                support="simple",
                span_ft=10,
                member=STEEL,
                point_loads=(PointLoad(1, 11),),
            ))


if __name__ == "__main__":
    unittest.main()

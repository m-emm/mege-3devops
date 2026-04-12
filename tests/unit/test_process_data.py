import logging
import unittest

from mege_3devops.process_data.mender3.process_data_04_high_precision import (
    PROCESS_DATA_PLA_04_HP,
)
from mege_3devops.process_data.mender3.process_data_04_high_speed import (
    PROCESS_DATA_PLA_04_HS,
    PROCESS_DATA_PETGCF_04_HS,
    PROCESS_DATA_TPU_04_HS,
)
from mege_3devops.process_data.mender3.process_data_06_high_speed import (
    PROCESS_DATA_PLA_06_HS,
    PROCESS_DATA_PETGCF_06_HS,
)
from mege_3devops.process_data.mender3.process_data_08_high_speed import (
    PROCESS_DATA_PLA_08_HS,
    PROCESS_DATA_TPU_08_HS,
)
from mege_3devops.process_data.parametric import (
    IntentSpec,
    NozzleSetup,
    load_material_spec,
    load_printer_spec,
    resolve_process_data,
    resolve_process_data_from_specs,
    volumetric_flow_multiplier_for_nozzle,
)

_logger = logging.getLogger(__name__)


def _parse_flat_value(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if value.endswith("%"):
        return float(value[:-1])
    return float(value)


class ParametricProcessDataRegressionTest(unittest.TestCase):
    def test_resolve_process_data_returns_flattened_process_overrides(self):
        _logger.info("starting smoke test for flattened process override shape")
        resolved = resolve_process_data(
            printer=load_printer_spec("megemaster"),
            material=load_material_spec("creality_pla_hs"),
            nozzle=NozzleSetup(diameter_mm=0.4, hardened=False, high_flow=False),
            intent=IntentSpec(strength_factor=0.33, quality_factor=0.7),
        )

        _logger.info("resolved smoke test output: %s", resolved)
        self.assertIn("filament", resolved)
        self.assertIn("process_overrides", resolved)
        self.assertEqual(
            resolved["filament"], "FilamentCrealityPLAHighSpeedTunedForSpeed"
        )
        for key in (
            "layer_height",
            "initial_layer_print_height",
            "line_width",
            "outer_wall_line_width",
            "inner_wall_line_width",
            "nozzle_temperature",
            "hot_plate_temp",
            "outer_wall_speed",
            "inner_wall_speed",
            "bridge_speed",
            "filament_retraction_length",
            "fan_cooling_layer_time",
            "support_threshold_angle",
            "brim_type",
            "wall_loops",
        ):
            self.assertIn(key, resolved["process_overrides"])

    def test_live_process_specs_can_be_loaded_and_used(self):
        _logger.info("starting live process spec loading test")
        printer = load_printer_spec("megemaster")
        material = load_material_spec("petg_cf_generic")
        resolved = resolve_process_data_from_specs(
            printer_id="megemaster",
            material_name="petg_cf_generic",
            nozzle=NozzleSetup(diameter_mm=0.6, hardened=True, high_flow=True),
            intent=IntentSpec(strength_factor=0.67, quality_factor=0.40),
        )

        _logger.info(
            "loaded printer=%s material=%s resolved=%s",
            printer,
            material,
            resolved,
        )

        self.assertEqual(printer.printer_id, "megemaster")
        self.assertEqual(material.material_id, "FilamentPETGCF")
        self.assertEqual(resolved["filament"], "FilamentPETGCF")
        self.assertEqual(resolved["process_overrides"]["brim_type"], "no_brim")
        self.assertIn("support_interface_spacing", resolved["process_overrides"])
        self.assertIn("overhang_fan_speed", resolved["process_overrides"])
        self.assertIn("initial_layer_infill_speed", resolved["process_overrides"])

    def test_volumetric_flow_reproduces_full_legacy_range(self):
        _logger.info("starting volumetric flow theory test")
        printer = load_printer_spec("megemaster")
        cases = [
            (
                "tpu_04_hs",
                "esun_tpu_95a",
                NozzleSetup(diameter_mm=0.4, hardened=False, high_flow=False),
                IntentSpec(strength_factor=0.0, quality_factor=0.25),
                15,
            ),
            (
                "petgcf_04_hs",
                "petg_cf_generic",
                NozzleSetup(diameter_mm=0.4, hardened=True, high_flow=False),
                IntentSpec(strength_factor=0.60, quality_factor=0.35),
                20,
            ),
            (
                "pla_06_hs",
                "creality_pla_hs",
                NozzleSetup(diameter_mm=0.6, hardened=True, high_flow=True),
                IntentSpec(strength_factor=0.67, quality_factor=0.40),
                23,
            ),
            (
                "petgcf_06_hs",
                "petg_cf_generic",
                NozzleSetup(diameter_mm=0.6, hardened=True, high_flow=True),
                IntentSpec(strength_factor=0.67, quality_factor=0.40),
                30,
            ),
            (
                "tpu_08_hs",
                "esun_tpu_95a",
                NozzleSetup(diameter_mm=0.8, hardened=True, high_flow=True),
                IntentSpec(strength_factor=0.0, quality_factor=0.35),
                30,
            ),
            (
                "pla_08_hs",
                "creality_pla_hs",
                NozzleSetup(diameter_mm=0.8, hardened=True, high_flow=True),
                IntentSpec(strength_factor=0.67, quality_factor=0.25),
                30,
            ),
        ]

        seen_values = set()
        for name, material_name, nozzle, intent, expected in cases:
            with self.subTest(case=name):
                material = load_material_spec(material_name)
                resolved = resolve_process_data(
                    printer=printer,
                    material=material,
                    nozzle=nozzle,
                    intent=intent,
                )
                actual = int(
                    _parse_flat_value(
                        resolved["process_overrides"]["filament_max_volumetric_speed"]
                    )
                )
                seen_values.add(actual)
                multiplier = volumetric_flow_multiplier_for_nozzle(nozzle.diameter_mm)
                _logger.info(
                    "volumetric flow case=%s base_material_flow=%s multiplier=%s nozzle=%.1f expected=%s actual=%s",
                    name,
                    material.base_volumetric_flow_mm3_s,
                    multiplier,
                    nozzle.diameter_mm,
                    expected,
                    actual,
                )
                self.assertEqual(
                    actual,
                    expected,
                    msg=f"{name} expected filament_max_volumetric_speed={expected} actual={actual}",
                )

        self.assertEqual(seen_values, {15, 20, 23, 30})

    def test_parametric_slice_stays_close_to_selected_legacy_profiles(self):
        _logger.info("starting regression comparison against selected legacy profiles")
        printer = load_printer_spec("megemaster")
        cases = [
            {
                "name": "pla_04_hp",
                "current": PROCESS_DATA_PLA_04_HP,
                "material": load_material_spec("creality_pla_hs"),
                "nozzle": NozzleSetup(
                    diameter_mm=0.4,
                    hardened=False,
                    high_flow=False,
                ),
                "intent": IntentSpec(strength_factor=0.33, quality_factor=0.70),
            },
            {
                "name": "tpu_04_hs",
                "current": PROCESS_DATA_TPU_04_HS,
                "material": load_material_spec("esun_tpu_95a"),
                "nozzle": NozzleSetup(
                    diameter_mm=0.4,
                    hardened=False,
                    high_flow=False,
                ),
                "intent": IntentSpec(strength_factor=0.0, quality_factor=0.25),
            },
            {
                "name": "petgcf_06_hs",
                "current": PROCESS_DATA_PETGCF_06_HS,
                "material": load_material_spec("petg_cf_generic"),
                "nozzle": NozzleSetup(
                    diameter_mm=0.6,
                    hardened=True,
                    high_flow=True,
                ),
                "intent": IntentSpec(strength_factor=0.67, quality_factor=0.40),
            },
        ]

        tolerances = {
            "layer_height": 0.03,
            "nozzle_temperature": 10.0,
            "nozzle_temperature_initial_layer": 10.0,
            "hot_plate_temp": 10.0,
            "hot_plate_temp_initial_layer": 10.0,
            "outer_wall_speed": 20.0,
            "inner_wall_speed": 35.0,
            "top_surface_speed": 20.0,
            "sparse_infill_speed": 35.0,
            "outer_wall_acceleration": 1800.0,
            "inner_wall_acceleration": 2200.0,
            "outer_wall_jerk": 2.0,
            "inner_wall_jerk": 2.0,
            "sparse_infill_density": 5.0,
            "fan_min_speed": 25.0,
            "fan_max_speed": 25.0,
            "support_top_z_distance": 0.12,
            "support_object_xy_distance": 0.25,
            "filament_flow_ratio": 0.03,
            "initial_layer_print_height": 0.10,
            "initial_layer_line_width": 0.10,
            "bridge_speed": 15.0,
            "filament_retraction_length": 0.40,
            "filament_retraction_speed": 15.0,
            "filament_deretraction_speed": 15.0,
            "support_interface_spacing": 0.30,
            "line_width": 0.10,
            "outer_wall_line_width": 0.10,
            "inner_wall_line_width": 0.10,
            "sparse_infill_line_width": 0.12,
            "support_line_width": 0.12,
            "top_surface_line_width": 0.10,
            "infill_wall_overlap": 10.0,
            "overhang_fan_speed": 25.0,
        }

        for case in cases:
            with self.subTest(case=case["name"]):
                _logger.info(
                    "case %s input: material=%s nozzle=%s intent=%s",
                    case["name"],
                    case["material"],
                    case["nozzle"],
                    case["intent"],
                )
                resolved = resolve_process_data(
                    printer=printer,
                    material=case["material"],
                    nozzle=case["nozzle"],
                    intent=case["intent"],
                )
                _logger.info(
                    "case %s resolved output: %s",
                    case["name"],
                    resolved,
                )

                self.assertEqual(
                    resolved["filament"],
                    case["current"]["filament"],
                )

                current_overrides = case["current"]["process_overrides"]
                resolved_overrides = resolved["process_overrides"]

                for key, tolerance in tolerances.items():
                    expected = _parse_flat_value(current_overrides.get(key))
                    actual = _parse_flat_value(resolved_overrides.get(key))
                    if expected is None:
                        _logger.info(
                            "case %s key %s skipped because legacy profile has no value",
                            case["name"],
                            key,
                        )
                        continue
                    self.assertIsNotNone(actual, msg=f"{case['name']} missing {key}")
                    delta = abs(actual - expected)
                    _logger.info(
                        "case %s compare key=%s expected=%s actual=%s delta=%s allowed=%s",
                        case["name"],
                        key,
                        expected,
                        actual,
                        delta,
                        tolerance,
                    )
                    self.assertAlmostEqual(
                        actual,
                        expected,
                        delta=tolerance,
                        msg=(
                            f"{case['name']} key={key} "
                            f"expected={expected} actual={actual} "
                            f"delta_allowed={tolerance}"
                        ),
                    )

    def test_dot4_pla_and_petgcf_medium_strength_matrix_is_covered(self):
        _logger.info(
            "starting .4 nozzle verification matrix for PLA and PETG-CF at medium strength"
        )
        printer = load_printer_spec("megemaster")
        required_keys = {
            "layer_height",
            "initial_layer_print_height",
            "line_width",
            "outer_wall_line_width",
            "inner_wall_line_width",
            "nozzle_temperature",
            "nozzle_temperature_initial_layer",
            "hot_plate_temp",
            "hot_plate_temp_initial_layer",
            "outer_wall_speed",
            "inner_wall_speed",
            "top_surface_speed",
            "sparse_infill_speed",
            "outer_wall_acceleration",
            "inner_wall_acceleration",
            "outer_wall_jerk",
            "inner_wall_jerk",
            "wall_loops",
            "top_shell_layers",
            "bottom_shell_layers",
            "sparse_infill_density",
            "fan_min_speed",
            "fan_max_speed",
            "support_top_z_distance",
            "support_object_xy_distance",
            "filament_flow_ratio",
            "bridge_speed",
            "filament_retraction_length",
            "filament_retraction_speed",
            "filament_deretraction_speed",
            "support_threshold_angle",
            "support_interface_spacing",
            "filament_max_volumetric_speed",
            "brim_type",
            "brim_width",
        }
        stable_key_tolerances = {
            "layer_height": 0.04,
            "nozzle_temperature": 12.0,
            "nozzle_temperature_initial_layer": 12.0,
            "hot_plate_temp": 12.0,
            "hot_plate_temp_initial_layer": 12.0,
            "sparse_infill_density": 10.0,
            "fan_min_speed": 35.0,
            "fan_max_speed": 35.0,
            "support_top_z_distance": 0.20,
            "support_object_xy_distance": 0.30,
            "filament_flow_ratio": 0.05,
            "initial_layer_print_height": 0.10,
            "initial_layer_line_width": 0.10,
            "filament_retraction_length": 0.50,
            "filament_retraction_speed": 20.0,
            "filament_deretraction_speed": 20.0,
            "support_interface_spacing": 0.40,
            "line_width": 0.10,
            "outer_wall_line_width": 0.10,
            "inner_wall_line_width": 0.10,
            "sparse_infill_line_width": 0.12,
            "support_line_width": 0.12,
            "top_surface_line_width": 0.10,
            "filament_max_volumetric_speed": 3.0,
        }
        legacy_reference_cases = [
            {
                "name": "pla_04_hs_medium_strength",
                "current": PROCESS_DATA_PLA_04_HS,
                "material": load_material_spec("creality_pla_hs"),
                "nozzle": NozzleSetup(
                    diameter_mm=0.4,
                    hardened=False,
                    high_flow=False,
                ),
                "intent": IntentSpec(strength_factor=0.5, quality_factor=0.25),
            },
            {
                "name": "pla_04_hq_medium_strength",
                "current": PROCESS_DATA_PLA_04_HP,
                "material": load_material_spec("creality_pla_hs"),
                "nozzle": NozzleSetup(
                    diameter_mm=0.4,
                    hardened=False,
                    high_flow=False,
                ),
                "intent": IntentSpec(strength_factor=0.5, quality_factor=0.70),
            },
            {
                "name": "petgcf_04_hs_medium_strength",
                "current": PROCESS_DATA_PETGCF_04_HS,
                "material": load_material_spec("petg_cf_generic"),
                "nozzle": NozzleSetup(
                    diameter_mm=0.4,
                    hardened=True,
                    high_flow=False,
                ),
                "intent": IntentSpec(strength_factor=0.5, quality_factor=0.35),
            },
        ]

        resolved_by_case = {}
        for case in legacy_reference_cases:
            with self.subTest(case=case["name"]):
                _logger.info(
                    "matrix case %s input: material=%s nozzle=%s intent=%s",
                    case["name"],
                    case["material"],
                    case["nozzle"],
                    case["intent"],
                )
                resolved = resolve_process_data(
                    printer=printer,
                    material=case["material"],
                    nozzle=case["nozzle"],
                    intent=case["intent"],
                )
                resolved_overrides = resolved["process_overrides"]
                _logger.info(
                    "matrix case %s resolved output: %s",
                    case["name"],
                    resolved,
                )
                resolved_by_case[case["name"]] = resolved

                self.assertTrue(
                    required_keys.issubset(resolved_overrides.keys()),
                    msg=(
                        f"{case['name']} missing required keys: "
                        f"{sorted(required_keys - set(resolved_overrides.keys()))}"
                    ),
                )
                self.assertEqual(resolved["filament"], case["current"]["filament"])

                current_overrides = case["current"]["process_overrides"]
                for key, tolerance in stable_key_tolerances.items():
                    expected = _parse_flat_value(current_overrides.get(key))
                    actual = _parse_flat_value(resolved_overrides.get(key))
                    if expected is None:
                        _logger.info(
                            "matrix case %s key %s skipped because legacy profile has no value",
                            case["name"],
                            key,
                        )
                        continue
                    self.assertIsNotNone(actual, msg=f"{case['name']} missing {key}")
                    delta = abs(actual - expected)
                    _logger.info(
                        "matrix case %s compare key=%s expected=%s actual=%s delta=%s allowed=%s",
                        case["name"],
                        key,
                        expected,
                        actual,
                        delta,
                        tolerance,
                    )
                    self.assertAlmostEqual(
                        actual,
                        expected,
                        delta=tolerance,
                        msg=(
                            f"{case['name']} key={key} "
                            f"expected={expected} actual={actual} "
                            f"delta_allowed={tolerance}"
                        ),
                    )

        petgcf_hq_medium = resolve_process_data(
            printer=printer,
            material=load_material_spec("petg_cf_generic"),
            nozzle=NozzleSetup(
                diameter_mm=0.4,
                hardened=True,
                high_flow=False,
            ),
            intent=IntentSpec(strength_factor=0.5, quality_factor=0.70),
        )
        petgcf_hq_medium_overrides = petgcf_hq_medium["process_overrides"]
        _logger.info(
            "matrix case petgcf_04_hq_medium_strength resolved output: %s",
            petgcf_hq_medium,
        )
        self.assertTrue(required_keys.issubset(petgcf_hq_medium_overrides.keys()))
        self.assertEqual(petgcf_hq_medium["filament"], "FilamentPETGCF")
        self.assertEqual(petgcf_hq_medium_overrides["filament_max_volumetric_speed"], "20")
        self.assertGreaterEqual(
            _parse_flat_value(petgcf_hq_medium_overrides["layer_height"]),
            0.10,
        )
        self.assertLessEqual(
            _parse_flat_value(petgcf_hq_medium_overrides["layer_height"]),
            0.30,
        )
        self.assertLessEqual(
            _parse_flat_value(petgcf_hq_medium_overrides["outer_wall_speed"]),
            _parse_flat_value(petgcf_hq_medium_overrides["inner_wall_speed"]),
        )
        self.assertEqual(petgcf_hq_medium_overrides["wall_loops"], "2")
        self.assertEqual(petgcf_hq_medium_overrides["top_shell_layers"], "2")
        self.assertEqual(petgcf_hq_medium_overrides["bottom_shell_layers"], "2")
        self.assertEqual(petgcf_hq_medium_overrides["sparse_infill_density"], "25%")

        pla_hs = resolved_by_case["pla_04_hs_medium_strength"]["process_overrides"]
        pla_hq = resolved_by_case["pla_04_hq_medium_strength"]["process_overrides"]
        petgcf_hs = resolved_by_case["petgcf_04_hs_medium_strength"]["process_overrides"]

        _logger.info(
            "regime ordering check PLA hs=%s hq=%s PETGCF hs=%s PETGCF hq=%s",
            {
                "layer_height": pla_hs["layer_height"],
                "outer_wall_speed": pla_hs["outer_wall_speed"],
                "inner_wall_speed": pla_hs["inner_wall_speed"],
                "bridge_speed": pla_hs["bridge_speed"],
            },
            {
                "layer_height": pla_hq["layer_height"],
                "outer_wall_speed": pla_hq["outer_wall_speed"],
                "inner_wall_speed": pla_hq["inner_wall_speed"],
                "bridge_speed": pla_hq["bridge_speed"],
            },
            {
                "layer_height": petgcf_hs["layer_height"],
                "outer_wall_speed": petgcf_hs["outer_wall_speed"],
                "inner_wall_speed": petgcf_hs["inner_wall_speed"],
                "bridge_speed": petgcf_hs["bridge_speed"],
            },
            {
                "layer_height": petgcf_hq_medium_overrides["layer_height"],
                "outer_wall_speed": petgcf_hq_medium_overrides["outer_wall_speed"],
                "inner_wall_speed": petgcf_hq_medium_overrides["inner_wall_speed"],
                "bridge_speed": petgcf_hq_medium_overrides["bridge_speed"],
            },
        )
        self.assertGreater(
            _parse_flat_value(pla_hs["outer_wall_speed"]),
            _parse_flat_value(pla_hq["outer_wall_speed"]),
        )
        self.assertGreater(
            _parse_flat_value(pla_hs["inner_wall_speed"]),
            _parse_flat_value(pla_hq["inner_wall_speed"]),
        )
        self.assertGreater(
            _parse_flat_value(pla_hs["layer_height"]),
            _parse_flat_value(pla_hq["layer_height"]),
        )
        self.assertGreater(
            _parse_flat_value(pla_hs["bridge_speed"]),
            _parse_flat_value(pla_hq["bridge_speed"]),
        )
        self.assertGreater(
            _parse_flat_value(petgcf_hs["outer_wall_speed"]),
            _parse_flat_value(petgcf_hq_medium_overrides["outer_wall_speed"]),
        )
        self.assertGreater(
            _parse_flat_value(petgcf_hs["inner_wall_speed"]),
            _parse_flat_value(petgcf_hq_medium_overrides["inner_wall_speed"]),
        )
        self.assertGreater(
            _parse_flat_value(petgcf_hs["layer_height"]),
            _parse_flat_value(petgcf_hq_medium_overrides["layer_height"]),
        )
        self.assertGreater(
            _parse_flat_value(petgcf_hs["bridge_speed"]),
            _parse_flat_value(petgcf_hq_medium_overrides["bridge_speed"]),
        )

    def test_strength_factor_drives_shell_counts(self):
        _logger.info("starting shell-count strength theory verification")
        printer = load_printer_spec("megemaster")
        material = load_material_spec("petg_cf_generic")
        nozzle = NozzleSetup(
            diameter_mm=0.6,
            hardened=True,
            high_flow=True,
        )

        cases = [
            (0.0, "1"),
            (0.5, "2"),
            (1.0, "4"),
        ]

        for strength_factor, expected_shells in cases:
            with self.subTest(strength_factor=strength_factor):
                resolved = resolve_process_data(
                    printer=printer,
                    material=material,
                    nozzle=nozzle,
                    intent=IntentSpec(
                        strength_factor=strength_factor,
                        quality_factor=0.5,
                    ),
                )
                overrides = resolved["process_overrides"]
                _logger.info(
                    "shell-count case strength_factor=%s -> wall_loops=%s top_shell_layers=%s bottom_shell_layers=%s",
                    strength_factor,
                    overrides["wall_loops"],
                    overrides["top_shell_layers"],
                    overrides["bottom_shell_layers"],
                )
                self.assertEqual(overrides["wall_loops"], expected_shells)
                self.assertEqual(overrides["top_shell_layers"], expected_shells)
                self.assertEqual(overrides["bottom_shell_layers"], expected_shells)

    def test_petgcf_06_support_policy_matches_verified_z_axis_behavior(self):
        _logger.info("starting PETG-CF 0.6 support policy verification")
        resolved = resolve_process_data_from_specs(
            printer_id="megemaster",
            material_name="petg_cf_generic",
            nozzle=NozzleSetup(diameter_mm=0.6, hardened=True, high_flow=True),
            intent=IntentSpec(strength_factor=0.5, quality_factor=0.4),
        )

        overrides = resolved["process_overrides"]
        self.assertEqual(overrides["support_interface_spacing"], "1")
        self.assertEqual(overrides["support_object_xy_distance"], "3")
        self.assertEqual(overrides["support_on_build_plate_only"], "1")
        self.assertEqual(overrides["support_threshold_angle"], "25")
        self.assertEqual(overrides["support_top_z_distance"], "0.40")

    def test_supports_default_to_build_plate_only_for_all_materials(self):
        _logger.info("starting support-on-build-plate-only default verification")
        cases = [
            (
                "creality_pla_hs",
                NozzleSetup(diameter_mm=0.4, hardened=False, high_flow=False),
                IntentSpec(strength_factor=0.5, quality_factor=0.5),
            ),
            (
                "petg_cf_generic",
                NozzleSetup(diameter_mm=0.6, hardened=True, high_flow=True),
                IntentSpec(strength_factor=0.5, quality_factor=0.4),
            ),
            (
                "esun_tpu_95a",
                NozzleSetup(diameter_mm=0.6, hardened=True, high_flow=True),
                IntentSpec(strength_factor=0.4, quality_factor=0.0),
            ),
        ]

        printer = load_printer_spec("megemaster")
        for material_name, nozzle, intent in cases:
            with self.subTest(material_name=material_name):
                resolved = resolve_process_data(
                    printer=printer,
                    material=load_material_spec(material_name),
                    nozzle=nozzle,
                    intent=intent,
                )
                self.assertEqual(
                    resolved["process_overrides"]["support_on_build_plate_only"],
                    "1",
                )

    def test_support_threshold_angle_defaults_to_25_for_all_materials(self):
        _logger.info("starting support-threshold-angle default verification")
        cases = [
            (
                "creality_pla_hs",
                NozzleSetup(diameter_mm=0.4, hardened=False, high_flow=False),
                IntentSpec(strength_factor=0.5, quality_factor=0.5),
            ),
            (
                "petg_cf_generic",
                NozzleSetup(diameter_mm=0.6, hardened=True, high_flow=True),
                IntentSpec(strength_factor=0.5, quality_factor=0.4),
            ),
            (
                "esun_tpu_95a",
                NozzleSetup(diameter_mm=0.6, hardened=True, high_flow=True),
                IntentSpec(strength_factor=0.4, quality_factor=0.0),
            ),
        ]

        printer = load_printer_spec("megemaster")
        for material_name, nozzle, intent in cases:
            with self.subTest(material_name=material_name):
                resolved = resolve_process_data(
                    printer=printer,
                    material=load_material_spec(material_name),
                    nozzle=nozzle,
                    intent=intent,
                )
                self.assertEqual(
                    resolved["process_overrides"]["support_threshold_angle"],
                    "25",
                )

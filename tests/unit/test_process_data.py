import json
import logging
import tempfile
import unittest
from pathlib import Path

from mege_3devops.process_data.mege_ender_3v3ke_idex import (
    DUAL_TOOLSWITCH_PRINT_AREA,
    MASTER_SETTINGS_DIR,
    PROCESS_DATA_DUAL_PLA_04_OFFSET_CALIBRATION,
    PROCESS_DATA_DUAL_PLA_04_STANDARD,
    PROCESS_DATA_DUAL_PLA_06_OFFSET_CALIBRATION,
    PROCESS_DATA_DUAL_PLA_06_STANDARD,
    PROCESS_DATA_PLA_04_COLD_BED_FIRST_PRINT,
    PLA_EXAMPLE_BED_TEMP_C,
    SAFE_BED_DEPTH_MM,
    SAFE_BED_ORIGIN,
    SAFE_BED_WIDTH_MM,
    SAFE_XY_ACCEL_MM_S2,
    SAFE_XY_JERK_MM_S,
    SAFE_XY_SPEED_MM_S,
    SAFE_X_MAX_MM,
    SAFE_X_MIN_MM,
    SAFE_Y_MAX_MM,
    SAFE_Y_MIN_MM,
    T0_SINGLE_BED_DEPTH_MM,
    T0_SINGLE_BED_ORIGIN,
    T0_SINGLE_BED_WIDTH_MM,
    T0_SINGLE_PRINT_AREA,
    T1_FILAMENT_PROFILE,
    copy_dual_pla_04_offset_calibration_process_data,
    copy_dual_pla_04_standard_process_data,
    copy_dual_pla_06_offset_calibration_process_data,
    copy_dual_pla_06_standard_process_data,
    resolve_idex_process_data_from_parameters,
)
from mege_3devops.process_data.mender3.process_data_04_high_precision import (
    PROCESS_DATA_PLA_04_HP,
)
from mege_3devops.process_data.mender3.process_data_04_high_speed import (
    PROCESS_DATA_PETGCF_04_HS,
    PROCESS_DATA_PLA_04_HS,
    PROCESS_DATA_TPU_04_HS,
)
from mege_3devops.process_data.mender3.process_data_06_high_speed import (
    PROCESS_DATA_PETGCF_06_HS,
    PROCESS_DATA_PLA_06_HS,
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
from shellforgepy.slicing.orca_slicer_settings_generator import generate_settings

_logger = logging.getLogger(__name__)

BED_TEMP_KEYS = (
    "hot_plate_temp",
    "hot_plate_temp_initial_layer",
    "cool_plate_temp",
    "cool_plate_temp_initial_layer",
    "eng_plate_temp",
    "eng_plate_temp_initial_layer",
    "supertack_plate_temp",
    "supertack_plate_temp_initial_layer",
    "textured_cool_plate_temp",
    "textured_cool_plate_temp_initial_layer",
    "textured_plate_temp",
    "textured_plate_temp_initial_layer",
)


def _parse_flat_value(value):
    if value is None:
        return None
    if isinstance(value, list):
        if not value:
            return None
        value = value[0]
    if isinstance(value, (int, float)):
        return float(value)
    if value.endswith("%"):
        return float(value[:-1])
    return float(value)


def _assert_positive_numeric_list(testcase, values):
    testcase.assertIsInstance(values, list)
    testcase.assertGreater(len(values), 0)
    for value in values:
        testcase.assertGreater(float(value), 0.0)


def _assert_ordered_print_area(testcase, print_area):
    testcase.assertEqual(
        set(print_area),
        {"mode", "x_min_mm", "x_max_mm", "y_min_mm", "y_max_mm", "z_max_mm"},
    )
    testcase.assertLess(print_area["x_min_mm"], print_area["x_max_mm"])
    testcase.assertLess(print_area["y_min_mm"], print_area["y_max_mm"])
    testcase.assertGreater(print_area["z_max_mm"], 0.0)


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
            "enable_pressure_advance",
            "pressure_advance",
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
        self.assertEqual(resolved["process_overrides"]["enable_pressure_advance"], "1")

    def test_mege_ender_idex_live_spec_matches_stock_motion_and_flow_limits(self):
        _logger.info("starting Mege Ender 3 V3 KE IDEX live spec test")
        printer = load_printer_spec("mege_ender_3v3ke_idex")
        nozzle_diameter = printer.nozzle_diameter_mm or 0.4
        resolved = resolve_process_data_from_specs(
            printer_id="mege_ender_3v3ke_idex",
            material_name="creality_pla_hs",
            nozzle=NozzleSetup(
                diameter_mm=nozzle_diameter,
                hardened=False,
                high_flow=False,
            ),
            intent=IntentSpec(strength_factor=0.5, quality_factor=0.0),
        )
        overrides = resolved["process_overrides"]

        self.assertEqual(printer.printer_id, "mege_ender_3v3ke_idex")
        self.assertIsInstance(printer.print_host, str)
        self.assertTrue(printer.print_host)
        self.assertIsInstance(printer.active_carriage, str)
        self.assertTrue(printer.active_carriage)
        self.assertGreater(nozzle_diameter, 0.0)
        self.assertLess(printer.printable_x_min_mm, printer.printable_x_max_mm)
        self.assertLess(printer.printable_y_min_mm, printer.printable_y_max_mm)
        self.assertGreater(printer.printable_z_max_mm, 0.0)
        self.assertGreater(printer.max_speed_xy_mm_s, 0.0)
        self.assertGreater(printer.max_accel_xy_mm_s2, 0.0)
        self.assertGreater(printer.max_jerk_xy_mm_s, 0.0)
        self.assertGreater(printer.hotend_base_flow_mm3_s, 0.0)
        self.assertLess(
            printer.single_t0_printable_x_min_mm,
            printer.single_t0_printable_x_max_mm,
        )
        self.assertLess(
            printer.dual_toolswitch_printable_x_min_mm,
            printer.dual_toolswitch_printable_x_max_mm,
        )

        self.assertEqual(
            _parse_flat_value(overrides["nozzle_diameter"]), nozzle_diameter
        )
        self.assertGreater(_parse_flat_value(overrides["outer_wall_speed"]), 0.0)
        self.assertGreaterEqual(
            _parse_flat_value(overrides["inner_wall_speed"]),
            _parse_flat_value(overrides["outer_wall_speed"]),
        )
        self.assertGreater(_parse_flat_value(overrides["outer_wall_acceleration"]), 0.0)
        self.assertGreaterEqual(
            _parse_flat_value(overrides["inner_wall_acceleration"]),
            _parse_flat_value(overrides["outer_wall_acceleration"]),
        )
        self.assertGreater(_parse_flat_value(overrides["outer_wall_jerk"]), 0.0)
        self.assertGreaterEqual(
            _parse_flat_value(overrides["inner_wall_jerk"]),
            _parse_flat_value(overrides["outer_wall_jerk"]),
        )
        self.assertGreater(
            _parse_flat_value(overrides["filament_max_volumetric_speed"]),
            0.0,
        )

    def test_mege_ender_idex_first_print_process_is_cold_bed(self):
        process_data = PROCESS_DATA_PLA_04_COLD_BED_FIRST_PRINT
        overrides = process_data["process_overrides"]

        self.assertEqual(
            process_data["filament"], "FilamentCrealityPLAHighSpeedTunedForSpeed"
        )
        self.assertEqual(MASTER_SETTINGS_DIR.name, "settings_master")
        self.assertTrue(MASTER_SETTINGS_DIR.exists())
        _assert_ordered_print_area(self, T0_SINGLE_PRINT_AREA)
        _assert_ordered_print_area(self, DUAL_TOOLSWITCH_PRINT_AREA)
        self.assertEqual(
            T0_SINGLE_BED_WIDTH_MM,
            T0_SINGLE_PRINT_AREA["x_max_mm"] - T0_SINGLE_PRINT_AREA["x_min_mm"],
        )
        self.assertEqual(T0_SINGLE_BED_DEPTH_MM, SAFE_BED_DEPTH_MM)
        self.assertEqual(SAFE_BED_WIDTH_MM, SAFE_X_MAX_MM - SAFE_X_MIN_MM)
        self.assertEqual(SAFE_BED_DEPTH_MM, SAFE_Y_MAX_MM - SAFE_Y_MIN_MM)
        self.assertEqual(SAFE_BED_ORIGIN, (SAFE_X_MIN_MM, SAFE_Y_MIN_MM))
        self.assertEqual(
            T0_SINGLE_BED_ORIGIN,
            (T0_SINGLE_PRINT_AREA["x_min_mm"], T0_SINGLE_PRINT_AREA["y_min_mm"]),
        )

        for key in BED_TEMP_KEYS:
            self.assertEqual(overrides[key], "0")

        self.assertEqual(overrides["enable_support"], "0")
        self.assertEqual(overrides["brim_type"], "outer_only")
        self.assertEqual(overrides["enable_pressure_advance"], "0")
        self.assertEqual(overrides["pressure_advance"], "0")
        for key in (
            "filament_max_volumetric_speed",
            "sparse_infill_speed",
            "travel_speed",
            "default_acceleration",
            "initial_layer_acceleration",
            "outer_wall_acceleration",
            "inner_wall_acceleration",
            "travel_acceleration",
            "outer_wall_jerk",
            "inner_wall_jerk",
        ):
            self.assertGreater(_parse_flat_value(overrides[key]), 0.0)

    def test_mege_ender_idex_master_settings_generate_safe_orca_json(self):
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            part_file = temp_dir / "dummy.stl"
            part_file.write_text("solid dummy\nendsolid dummy\n", encoding="utf-8")
            process_data = dict(PROCESS_DATA_PLA_04_COLD_BED_FIRST_PRINT)
            process_data["part_file"] = str(part_file)

            process_data_path = temp_dir / "process_data.json"
            process_data_path.write_text(
                json.dumps(process_data),
                encoding="utf-8",
            )

            artifacts = generate_settings(
                process_data_file=process_data_path,
                output_dir=temp_dir,
                master_settings_dir=MASTER_SETTINGS_DIR,
            )

            machine_settings = json.loads(
                Path(artifacts["machine_settings_path"]).read_text(encoding="utf-8")
            )
            process_settings = json.loads(
                Path(artifacts["process_settings_path"]).read_text(encoding="utf-8")
            )
            filament_settings = json.loads(
                Path(artifacts["filament_settings_paths"][0]).read_text(
                    encoding="utf-8"
                )
            )
            print_host = Path(artifacts["print_host_path"]).read_text(encoding="utf-8")

        self.assertEqual(len(machine_settings["printable_area"]), 4)
        for coordinate in machine_settings["printable_area"]:
            self.assertIn("x", coordinate)
        self.assertGreater(_parse_flat_value(machine_settings["printable_height"]), 0.0)
        self.assertEqual(print_host, machine_settings["print_host"])
        for key in (
            "machine_max_speed_x",
            "machine_max_speed_y",
            "machine_max_speed_z",
            "machine_max_acceleration_x",
            "machine_max_acceleration_y",
            "machine_max_acceleration_z",
            "machine_max_jerk_x",
            "machine_max_jerk_y",
        ):
            _assert_positive_numeric_list(self, machine_settings[key])
            self.assertEqual(len(machine_settings[key]), 2)
        for key in (
            "sparse_infill_speed",
            "travel_speed",
            "default_acceleration",
            "initial_layer_acceleration",
            "outer_wall_acceleration",
            "travel_acceleration",
            "default_jerk",
            "outer_wall_jerk",
        ):
            self.assertGreater(_parse_flat_value(process_settings[key]), 0.0)

        machine_gcode = (
            machine_settings["machine_start_gcode"]
            + "\n"
            + machine_settings["machine_end_gcode"]
        )
        machine_start_gcode = machine_settings["machine_start_gcode"]
        self.assertIn("M140 S[bed_temperature_initial_layer_single]", machine_gcode)
        self.assertIn("M190 S[bed_temperature_initial_layer_single]", machine_gcode)
        self.assertIn("M140 S0 ;Turn-off bed", machine_gcode)
        self.assertNotIn("heater_bed", machine_gcode)
        self.assertNotIn("X-", machine_gcode)
        self.assertNotIn("M600", machine_gcode)
        self.assertLess(
            machine_start_gcode.index("M82 ;Absolute extrusion"),
            machine_start_gcode.index(
                "G1 Y10 F1800 ;Leave Y endstop before applying tool offsets"
            ),
        )
        self.assertLess(
            machine_start_gcode.index(
                "G1 Y10 F1800 ;Leave Y endstop before applying tool offsets"
            ),
            machine_start_gcode.index("{if initial_tool==1}T1"),
        )
        self.assertIn(
            "M104 S{first_layer_temperature[0]} T0",
            machine_start_gcode,
        )
        self.assertIn(
            "M104 S{first_layer_temperature[1]} T1",
            machine_start_gcode,
        )
        self.assertNotIn(
            "T1\nM104 S{first_layer_temperature[1]}",
            machine_start_gcode,
        )
        self.assertIn("{if initial_tool==0}T0", machine_start_gcode)
        self.assertIn("{if initial_tool==1}T1", machine_start_gcode)
        self.assertNotIn("{if is_extruder_used[0]}T0", machine_start_gcode)
        self.assertNotIn("{if is_extruder_used[1]}T1", machine_start_gcode)
        self.assertIn("T0", machine_gcode)
        self.assertIn("T1", machine_gcode)
        self.assertIn("G1 Z0.60 F480 ;Lift before travel", machine_start_gcode)
        self.assertGreaterEqual(machine_start_gcode.count(" E"), 2)
        self.assertNotIn("G1 X70 Y-8 E6 F600", machine_start_gcode)
        self.assertNotIn("G1 X70 Y-2 E24 F600", machine_start_gcode)
        self.assertNotIn("G1 X10 Y70 E6 F600", machine_start_gcode)
        self.assertNotIn("G1 X10 Y140 E6 F600", machine_start_gcode)
        self.assertNotIn("G1 X12 Y70 E12 F600", machine_start_gcode)
        self.assertNotIn("G1 X12 Y140 E12 F600", machine_start_gcode)
        self.assertNotIn("G1 X16 Y70 E24 F600", machine_start_gcode)
        self.assertNotIn("G1 X16 Y140 E24 F600", machine_start_gcode)
        self.assertNotIn("G1 X24 Y10", machine_gcode)
        self.assertIn("G1 Z{min(max_layer_z+150, printable_height)}", machine_gcode)
        self.assertIn("T0 ;Park right carriage", machine_gcode)
        self.assertIn("T1 ;Park left carriage", machine_gcode)

        for key in BED_TEMP_KEYS:
            self.assertIn(process_settings.get(key, "0"), (None, "0"))
            self.assertEqual(_parse_flat_value(filament_settings[key]), 0.0)
        self.assertGreater(
            _parse_flat_value(filament_settings["filament_max_volumetric_speed"]),
            0.0,
        )

    def test_mege_ender_idex_petgcf_process_uses_idex_master_settings(self):
        process_data = resolve_idex_process_data_from_parameters(
            material_name="petg_cf_generic",
            nozzle_diameter_mm=0.6,
            nozzle_hardened=True,
            nozzle_high_flow=True,
            strength_factor=0.9,
            quality_factor=0.5,
        )
        self.assertEqual(process_data["filament"], "FilamentPETGCF")
        self.assertEqual(
            process_data["master_settings_dir"],
            MASTER_SETTINGS_DIR.resolve().as_posix(),
        )

        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            part_file = temp_dir / "dummy.stl"
            part_file.write_text("solid dummy\nendsolid dummy\n", encoding="utf-8")
            process_data = dict(process_data)
            process_data["part_file"] = str(part_file)

            process_data_path = temp_dir / "process_data.json"
            process_data_path.write_text(
                json.dumps(process_data),
                encoding="utf-8",
            )

            artifacts = generate_settings(
                process_data_file=process_data_path,
                output_dir=temp_dir,
                master_settings_dir=MASTER_SETTINGS_DIR,
            )

            machine_settings = json.loads(
                Path(artifacts["machine_settings_path"]).read_text(encoding="utf-8")
            )
            filament_settings = json.loads(
                Path(artifacts["filament_settings_paths"][0]).read_text(
                    encoding="utf-8"
                )
            )
            print_host = Path(artifacts["print_host_path"]).read_text(encoding="utf-8")

        self.assertEqual(machine_settings["name"], machine_settings["printer_model"])
        self.assertEqual(print_host, machine_settings["print_host"])
        self.assertEqual(len(machine_settings["printable_area"]), 4)
        self.assertGreater(_parse_flat_value(machine_settings["printable_height"]), 0.0)
        self.assertIn("retract_lift_above", machine_settings)
        self.assertIn("retract_lift_below", machine_settings)
        self.assertIn("retract_lift_enforce", machine_settings)
        self.assertEqual(filament_settings["name"], process_data["filament"])
        self.assertIn(
            machine_settings["printer_model"],
            filament_settings["compatible_printers"],
        )
        self.assertTrue(filament_settings["filament_settings_id"])

    def test_mege_ender_idex_dual_pla_standard_processes_are_safe_and_dual_material(
        self,
    ):
        for process_data in (
            PROCESS_DATA_DUAL_PLA_04_STANDARD,
            PROCESS_DATA_DUAL_PLA_06_STANDARD,
        ):
            with self.subTest(
                layer_height=process_data["process_overrides"]["layer_height"]
            ):
                overrides = process_data["process_overrides"]
                self.assertEqual(len(process_data["filaments"]), 2)
                self.assertEqual(process_data["filaments"][0], process_data["filament"])
                self.assertEqual(process_data["filaments"][1], T1_FILAMENT_PROFILE)
                self.assertEqual(process_data["print_area"], DUAL_TOOLSWITCH_PRINT_AREA)
                self.assertEqual(overrides["enable_prime_tower"], "1")
                self.assertEqual(overrides["prime_tower_width"], "35")
                self.assertEqual(overrides["prime_tower_brim_width"], "3")
                self.assertEqual(overrides["purge_in_prime_tower"], "1")
                self.assertEqual(overrides["wipe_tower_x"], "200")
                self.assertEqual(overrides["wipe_tower_y"], "15")
                self.assertEqual(overrides["travel_speed"], str(SAFE_XY_SPEED_MM_S))
                self.assertEqual(
                    overrides["default_acceleration"],
                    str(SAFE_XY_ACCEL_MM_S2),
                )
                self.assertEqual(
                    overrides["travel_acceleration"],
                    str(SAFE_XY_ACCEL_MM_S2),
                )
                self.assertEqual(overrides["default_jerk"], str(SAFE_XY_JERK_MM_S))
                self.assertEqual(overrides["travel_jerk"], str(SAFE_XY_JERK_MM_S))
                self.assertEqual(overrides["z_hop"], ["0.6", "0.6"])
                self.assertEqual(
                    overrides["z_hop_types"],
                    ["Normal Lift", "Normal Lift"],
                )
                self.assertEqual(overrides["filament_z_hop"], "0.6")
                self.assertEqual(overrides["filament_z_hop_types"], "retract_lift")

        self.assertEqual(
            PROCESS_DATA_DUAL_PLA_04_OFFSET_CALIBRATION,
            PROCESS_DATA_DUAL_PLA_04_STANDARD,
        )
        self.assertEqual(
            PROCESS_DATA_DUAL_PLA_06_OFFSET_CALIBRATION,
            PROCESS_DATA_DUAL_PLA_06_STANDARD,
        )
        self.assertEqual(
            copy_dual_pla_04_offset_calibration_process_data(),
            copy_dual_pla_04_standard_process_data(),
        )
        self.assertEqual(
            copy_dual_pla_06_offset_calibration_process_data(),
            copy_dual_pla_06_standard_process_data(),
        )

    def test_mege_ender_idex_dual_pla_standard_settings_generate_two_filaments(self):
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            part_file = temp_dir / "dummy.stl"
            part_file.write_text("solid dummy\nendsolid dummy\n", encoding="utf-8")
            process_data = dict(PROCESS_DATA_DUAL_PLA_06_STANDARD)
            process_data["process_overrides"] = dict(process_data["process_overrides"])
            process_data["part_file"] = str(part_file)

            process_data_path = temp_dir / "process_data.json"
            process_data_path.write_text(
                json.dumps(process_data),
                encoding="utf-8",
            )

            artifacts = generate_settings(
                process_data_file=process_data_path,
                output_dir=temp_dir,
                master_settings_dir=MASTER_SETTINGS_DIR,
            )

            machine_settings = json.loads(
                Path(artifacts["machine_settings_path"]).read_text(encoding="utf-8")
            )
            filament_settings = [
                json.loads(Path(path).read_text(encoding="utf-8"))
                for path in artifacts["filament_settings_paths"]
            ]
            process_settings = json.loads(
                Path(artifacts["process_settings_path"]).read_text(encoding="utf-8")
            )

        self.assertEqual(process_data["filaments"][1], T1_FILAMENT_PROFILE)
        self.assertEqual(len(artifacts["filament_settings_paths"]), 2)
        self.assertEqual(
            [Path(path).stem for path in artifacts["filament_settings_paths"]],
            [
                "FilamentCrealityPLAHighSpeedTunedForSpeed",
                "FilamentCrealityPLAHighSpeedTunedForSpeedT1",
            ],
        )
        self.assertEqual(
            machine_settings["default_filament_profile"],
            [Path(path).stem for path in artifacts["filament_settings_paths"]],
        )
        self.assertEqual(len(machine_settings["nozzle_diameter"]), 2)
        self.assertEqual(
            len(set(machine_settings["nozzle_diameter"])),
            1,
        )
        self.assertGreater(float(machine_settings["nozzle_diameter"][0]), 0.0)
        self.assertEqual(machine_settings["z_hop"], ["0.6", "0.6"])
        self.assertEqual(
            machine_settings["z_hop_types"],
            ["Normal Lift", "Normal Lift"],
        )
        self.assertEqual(machine_settings["extruder_offset"], ["0x0", "0x0"])
        self.assertEqual(machine_settings["single_extruder_multi_material"], "0")
        self.assertEqual(machine_settings["manual_filament_change"], "0")
        self.assertEqual(process_settings["enable_prime_tower"], "1")
        self.assertEqual(process_settings["prime_tower_width"], "35")
        self.assertEqual(process_settings["prime_tower_brim_width"], "3")
        self.assertEqual(process_settings["purge_in_prime_tower"], "1")
        self.assertEqual(process_settings["wipe_tower_x"], "200")
        self.assertEqual(process_settings["wipe_tower_y"], "15")
        self.assertEqual(process_settings["wipe_tower_no_sparse_layers"], "0")
        self.assertEqual(process_settings["standby_temperature_delta"], "0")
        self.assertEqual(machine_settings["machine_max_speed_x"], ["300", "300"])
        self.assertEqual(machine_settings["machine_max_speed_y"], ["300", "300"])
        self.assertEqual(
            machine_settings["machine_max_acceleration_x"],
            ["3500", "3500"],
        )
        self.assertEqual(
            machine_settings["machine_max_acceleration_y"],
            ["3500", "3500"],
        )
        self.assertEqual(machine_settings["machine_max_jerk_x"], ["5", "5"])
        self.assertEqual(machine_settings["machine_max_jerk_y"], ["5", "5"])
        self.assertLessEqual(
            _parse_flat_value(process_settings["travel_speed"]),
            SAFE_XY_SPEED_MM_S,
        )
        for key in (
            "default_acceleration",
            "initial_layer_acceleration",
            "outer_wall_acceleration",
            "inner_wall_acceleration",
            "top_surface_acceleration",
            "travel_acceleration",
            "sparse_infill_acceleration",
            "internal_solid_infill_acceleration",
            "bridge_acceleration",
        ):
            self.assertLessEqual(
                _parse_flat_value(process_settings[key]),
                SAFE_XY_ACCEL_MM_S2,
            )
        for key in (
            "default_jerk",
            "initial_layer_jerk",
            "outer_wall_jerk",
            "inner_wall_jerk",
            "top_surface_jerk",
            "travel_jerk",
            "infill_jerk",
        ):
            self.assertLessEqual(
                _parse_flat_value(process_settings[key]),
                SAFE_XY_JERK_MM_S,
            )
        for key in BED_TEMP_KEYS:
            self.assertEqual(
                process_data["process_overrides"][key], str(PLA_EXAMPLE_BED_TEMP_C)
            )
            self.assertEqual(
                _parse_flat_value(filament_settings[0][key]), PLA_EXAMPLE_BED_TEMP_C
            )
            self.assertEqual(
                _parse_flat_value(filament_settings[1][key]), PLA_EXAMPLE_BED_TEMP_C
            )
        for filament_setting in filament_settings:
            self.assertEqual(_parse_flat_value(filament_setting["filament_z_hop"]), 0.6)
            self.assertEqual(
                filament_setting["filament_z_hop_types"],
                "retract_lift",
            )

    def test_pressure_advance_theory_hits_known_legacy_high_speed_anchors(self):
        _logger.info("starting pressure-advance anchor verification")
        printer = load_printer_spec("megemaster")
        cases = [
            (
                "pla_04_hq_anchor",
                "creality_pla_hs",
                NozzleSetup(diameter_mm=0.4, hardened=False, high_flow=False),
                IntentSpec(strength_factor=0.33, quality_factor=0.70),
                0.02,
            ),
            (
                "pla_06_hs_anchor",
                "creality_pla_hs",
                NozzleSetup(diameter_mm=0.6, hardened=True, high_flow=True),
                IntentSpec(strength_factor=0.67, quality_factor=0.40),
                0.04,
            ),
            (
                "pla_08_hs_anchor",
                "creality_pla_hs",
                NozzleSetup(diameter_mm=0.8, hardened=True, high_flow=True),
                IntentSpec(strength_factor=0.67, quality_factor=0.25),
                0.05,
            ),
        ]

        for name, material_name, nozzle, intent, expected in cases:
            with self.subTest(case=name):
                resolved = resolve_process_data(
                    printer=printer,
                    material=load_material_spec(material_name),
                    nozzle=nozzle,
                    intent=intent,
                )
                overrides = resolved["process_overrides"]
                actual = _parse_flat_value(overrides["pressure_advance"])
                _logger.info(
                    "pressure-advance case=%s expected=%s actual=%s overrides=%s",
                    name,
                    expected,
                    actual,
                    overrides,
                )
                self.assertEqual(overrides["enable_pressure_advance"], "1")
                self.assertEqual(overrides["adaptive_pressure_advance"], "0")
                self.assertAlmostEqual(actual, expected, delta=0.001)

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
            "enable_pressure_advance",
            "pressure_advance",
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
        self.assertEqual(
            petgcf_hq_medium_overrides["filament_max_volumetric_speed"], "20"
        )
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
        petgcf_hs = resolved_by_case["petgcf_04_hs_medium_strength"][
            "process_overrides"
        ]

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
        self.assertEqual(overrides["support_top_z_distance"], "0.47")

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

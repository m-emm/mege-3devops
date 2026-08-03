import json
import logging
import re
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
    T1_SINGLE_BED_DEPTH_MM,
    T1_SINGLE_BED_ORIGIN,
    T1_SINGLE_BED_WIDTH_MM,
    T1_SINGLE_PRINT_AREA,
    copy_dual_pla_04_offset_calibration_process_data,
    copy_dual_pla_04_standard_process_data,
    copy_dual_pla_06_offset_calibration_process_data,
    copy_dual_pla_06_standard_process_data,
    resolve_idex_process_data_from_parameters,
    t1_tpu95a_06_high_speed_process_data,
)
from mege_3devops.process_data.parametric import (
    IntentSpec,
    NozzleSetup,
    load_material_spec,
    load_printer_spec,
    resolve_process_data,
    resolve_process_data_from_specs,
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


def _extract_initial_tool_block(machine_start_gcode, tool_index):
    start_marker = f"{{if initial_tool=={tool_index}}}T{tool_index}"
    start = machine_start_gcode.index(start_marker)
    end = machine_start_gcode.index("{endif}", start)
    return machine_start_gcode[start:end]


def _parse_g1_words(line):
    command = line.split(";", 1)[0].strip()
    if not command.startswith("G1 "):
        return {}
    words = {}
    for token in command.split()[1:]:
        match = re.fullmatch(r"([A-Z])(-?\d+(?:\.\d+)?)", token)
        if match:
            words[match.group(1)] = float(match.group(2))
    return words


def _segment_intersects_rect(start, end, rect):
    segment_x_min = min(start[0], end[0])
    segment_x_max = max(start[0], end[0])
    segment_y_min = min(start[1], end[1])
    segment_y_max = max(start[1], end[1])
    return max(segment_x_min, rect["x_min"]) <= min(
        segment_x_max, rect["x_max"]
    ) and max(segment_y_min, rect["y_min"]) <= min(segment_y_max, rect["y_max"])


def _assert_front_margin_purge_block(
    testcase,
    machine_start_gcode,
    tool_index,
):
    block = _extract_initial_tool_block(machine_start_gcode, tool_index)
    draw_count = 0
    for line in block.splitlines():
        words = _parse_g1_words(line)
        if "E" in words and ("X" in words or "Y" in words):
            draw_count += 1
            testcase.assertIn("Y", words, line)
            testcase.assertLess(
                words["Y"],
                DUAL_TOOLSWITCH_PRINT_AREA["y_min_mm"],
                line,
            )

    testcase.assertGreater(draw_count, 0)


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
        self.assertTrue(resolved["filament"])
        self.assertIn("process_overrides", resolved)
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

        self.assertTrue(printer.printer_id)
        self.assertTrue(material.material_id)
        self.assertTrue(resolved["filament"])
        self.assertIn("brim_type", resolved["process_overrides"])
        self.assertIn("support_interface_spacing", resolved["process_overrides"])
        self.assertIn("overhang_fan_speed", resolved["process_overrides"])
        self.assertIn("initial_layer_infill_speed", resolved["process_overrides"])
        self.assertIn("enable_pressure_advance", resolved["process_overrides"])

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

        self.assertTrue(process_data["filament"])
        self.assertEqual(MASTER_SETTINGS_DIR.name, "settings_master")
        self.assertTrue(MASTER_SETTINGS_DIR.exists())
        _assert_ordered_print_area(self, T0_SINGLE_PRINT_AREA)
        _assert_ordered_print_area(self, T1_SINGLE_PRINT_AREA)
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
        self.assertEqual(
            T1_SINGLE_BED_WIDTH_MM,
            T1_SINGLE_PRINT_AREA["x_max_mm"] - T1_SINGLE_PRINT_AREA["x_min_mm"],
        )
        self.assertEqual(T1_SINGLE_BED_DEPTH_MM, SAFE_BED_DEPTH_MM)
        self.assertEqual(
            T1_SINGLE_BED_ORIGIN,
            (T1_SINGLE_PRINT_AREA["x_min_mm"], T1_SINGLE_PRINT_AREA["y_min_mm"]),
        )

        for key in BED_TEMP_KEYS:
            self.assertIn(key, overrides)

        for key in (
            "enable_support",
            "brim_type",
            "enable_pressure_advance",
            "pressure_advance",
        ):
            self.assertIn(key, overrides)
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
        self.assertNotIn("heater_bed", machine_gcode)
        self.assertNotIn("M600", machine_gcode)
        self.assertIn("{if initial_tool==0}T0", machine_start_gcode)
        self.assertIn("{if initial_tool==1}T1", machine_start_gcode)
        self.assertIn("T0", machine_gcode)
        self.assertIn("T1", machine_gcode)
        self.assertGreaterEqual(machine_start_gcode.count(" E"), 2)
        _assert_front_margin_purge_block(
            self,
            machine_start_gcode,
            tool_index=0,
        )
        _assert_front_margin_purge_block(
            self,
            machine_start_gcode,
            tool_index=1,
        )

        for key in BED_TEMP_KEYS:
            self.assertIn(key, filament_settings)
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
        self.assertTrue(process_data["filament"])
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
        nozzle_diameters = machine_settings["nozzle_diameter"]
        if not isinstance(nozzle_diameters, list):
            nozzle_diameters = [nozzle_diameters]
        self.assertTrue(
            all(
                diameter == machine_settings["printer_variant"]
                for diameter in nozzle_diameters
            )
        )
        self.assertEqual(len(machine_settings["min_layer_height"]), 2)
        self.assertEqual(len(machine_settings["max_layer_height"]), 2)
        for nozzle, minimum, maximum in zip(
            nozzle_diameters,
            machine_settings["min_layer_height"],
            machine_settings["max_layer_height"],
        ):
            self.assertAlmostEqual(float(minimum), float(nozzle) * 0.25)
            self.assertAlmostEqual(float(maximum), float(nozzle) * 0.75)
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

    def test_mege_ender_idex_t1_process_uses_second_identical_filament_slot(self):
        process_data = resolve_idex_process_data_from_parameters(
            toolhead="T1",
            material_name="esun_tpu_95a",
            nozzle_diameter_mm=0.6,
            nozzle_hardened=True,
            nozzle_high_flow=True,
            strength_factor=0.4,
            quality_factor=0.0,
        )

        self.assertEqual(process_data["print_area"], T1_SINGLE_PRINT_AREA)
        self.assertEqual(
            process_data["filaments"],
            [process_data["filament"], process_data["filament"]],
        )

    def test_mege_ender_idex_rejects_unknown_single_toolhead(self):
        with self.assertRaisesRegex(ValueError, "T0.*T1"):
            resolve_idex_process_data_from_parameters(
                toolhead="T2",
                material_name="esun_tpu_95a",
                nozzle_diameter_mm=0.6,
                nozzle_hardened=True,
                nozzle_high_flow=True,
                strength_factor=0.4,
                quality_factor=0.0,
            )

    def test_mege_ender_idex_t1_tpu_process_reuses_workshop_high_speed_profile(self):
        process_data = t1_tpu95a_06_high_speed_process_data()
        overrides = process_data["process_overrides"]

        self.assertEqual(process_data["print_area"], T1_SINGLE_PRINT_AREA)
        self.assertEqual(
            process_data["filaments"],
            [process_data["filament"], process_data["filament"]],
        )
        self.assertGreater(
            _parse_flat_value(overrides["filament_max_volumetric_speed"]), 0.0
        )
        self.assertGreater(_parse_flat_value(overrides["outer_wall_speed"]), 0.0)
        self.assertGreaterEqual(
            _parse_flat_value(overrides["inner_wall_speed"]),
            _parse_flat_value(overrides["outer_wall_speed"]),
        )
        self.assertEqual(overrides["enable_pressure_advance"], "1")
        self.assertGreater(_parse_flat_value(overrides["pressure_advance"]), 0.0)

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
                self.assertNotEqual(
                    process_data["filaments"][1], process_data["filament"]
                )
                self.assertEqual(process_data["print_area"], DUAL_TOOLSWITCH_PRINT_AREA)
                for key in (
                    "enable_prime_tower",
                    "prime_tower_width",
                    "prime_tower_brim_width",
                    "purge_in_prime_tower",
                    "wipe_tower_x",
                    "wipe_tower_y",
                    "travel_speed",
                    "default_acceleration",
                    "travel_acceleration",
                    "default_jerk",
                    "travel_jerk",
                    "z_hop",
                    "z_hop_types",
                    "filament_z_hop",
                    "filament_z_hop_types",
                ):
                    self.assertIn(key, overrides)
                self.assertLessEqual(
                    _parse_flat_value(overrides["travel_speed"]),
                    SAFE_XY_SPEED_MM_S,
                )
                self.assertLessEqual(
                    _parse_flat_value(overrides["default_acceleration"]),
                    SAFE_XY_ACCEL_MM_S2,
                )
                self.assertLessEqual(
                    _parse_flat_value(overrides["travel_acceleration"]),
                    SAFE_XY_ACCEL_MM_S2,
                )
                self.assertLessEqual(
                    _parse_flat_value(overrides["default_jerk"]),
                    SAFE_XY_JERK_MM_S,
                )
                self.assertLessEqual(
                    _parse_flat_value(overrides["travel_jerk"]),
                    SAFE_XY_JERK_MM_S,
                )

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

        self.assertNotEqual(process_data["filaments"][1], process_data["filament"])
        self.assertEqual(len(artifacts["filament_settings_paths"]), 2)
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
        self.assertEqual(len(machine_settings["z_hop"]), 2)
        self.assertEqual(len(machine_settings["z_hop_types"]), 2)
        self.assertEqual(len(machine_settings["extruder_offset"]), 2)
        for key in (
            "single_extruder_multi_material",
            "manual_filament_change",
        ):
            self.assertIn(key, machine_settings)
        for key in (
            "enable_prime_tower",
            "prime_tower_width",
            "prime_tower_brim_width",
            "purge_in_prime_tower",
            "wipe_tower_x",
            "wipe_tower_y",
            "wipe_tower_no_sparse_layers",
            "standby_temperature_delta",
        ):
            self.assertIn(key, process_settings)
        for key in (
            "machine_max_speed_x",
            "machine_max_speed_y",
            "machine_max_acceleration_x",
            "machine_max_acceleration_y",
            "machine_max_jerk_x",
            "machine_max_jerk_y",
        ):
            _assert_positive_numeric_list(self, machine_settings[key])
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
            expected_bed_temp = process_data["process_overrides"][key]
            self.assertEqual(
                _parse_flat_value(filament_settings[0][key]),
                _parse_flat_value(expected_bed_temp),
            )
            self.assertEqual(
                _parse_flat_value(filament_settings[1][key]),
                _parse_flat_value(expected_bed_temp),
            )
        for filament_setting in filament_settings:
            self.assertGreater(
                _parse_flat_value(filament_setting["filament_z_hop"]), 0.0
            )
            self.assertTrue(filament_setting["filament_z_hop_types"])

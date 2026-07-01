"""Process data for the Mege Ender 3 V3 KE IDEX printer identity."""

from __future__ import annotations

import copy
from pathlib import Path

from mege_3devops.process_data.parametric import resolve_process_data_from_parameters

PRINTER_ID = "mege_ender_3v3ke_idex"
MASTER_SETTINGS_DIR = Path(__file__).with_name("settings_master")

T0_SINGLE_X_MIN_MM = -30.0
T0_SINGLE_X_MAX_MM = 244.0
DUAL_TOOLSWITCH_X_MIN_MM = 0.0
DUAL_TOOLSWITCH_X_MAX_MM = 244.0
PRINTABLE_Y_MIN_MM = 0.0
PRINTABLE_Y_MAX_MM = 290.0
PRINTABLE_Z_MAX_MM = 294.0

SAFE_X_MIN_MM = DUAL_TOOLSWITCH_X_MIN_MM
SAFE_X_MAX_MM = DUAL_TOOLSWITCH_X_MAX_MM
SAFE_Y_MIN_MM = PRINTABLE_Y_MIN_MM
SAFE_Y_MAX_MM = PRINTABLE_Y_MAX_MM
SAFE_Z_MAX_MM = PRINTABLE_Z_MAX_MM
SAFE_BED_WIDTH_MM = SAFE_X_MAX_MM - SAFE_X_MIN_MM
SAFE_BED_DEPTH_MM = SAFE_Y_MAX_MM - SAFE_Y_MIN_MM
SAFE_BED_ORIGIN = (SAFE_X_MIN_MM, SAFE_Y_MIN_MM)

T0_SINGLE_BED_WIDTH_MM = T0_SINGLE_X_MAX_MM - T0_SINGLE_X_MIN_MM
T0_SINGLE_BED_DEPTH_MM = SAFE_BED_DEPTH_MM
T0_SINGLE_BED_ORIGIN = (T0_SINGLE_X_MIN_MM, SAFE_Y_MIN_MM)

T0_SINGLE_PRINT_AREA = {
    "mode": "single_t0",
    "x_min_mm": T0_SINGLE_X_MIN_MM,
    "x_max_mm": T0_SINGLE_X_MAX_MM,
    "y_min_mm": SAFE_Y_MIN_MM,
    "y_max_mm": SAFE_Y_MAX_MM,
    "z_max_mm": SAFE_Z_MAX_MM,
}
DUAL_TOOLSWITCH_PRINT_AREA = {
    "mode": "dual_toolswitch",
    "x_min_mm": SAFE_X_MIN_MM,
    "x_max_mm": SAFE_X_MAX_MM,
    "y_min_mm": SAFE_Y_MIN_MM,
    "y_max_mm": SAFE_Y_MAX_MM,
    "z_max_mm": SAFE_Z_MAX_MM,
}

T0_FILAMENT_PROFILE = "FilamentCrealityPLAHighSpeedTunedForSpeed"
T1_FILAMENT_PROFILE = "FilamentCrealityPLAHighSpeedTunedForSpeedT1"
PLA_EXAMPLE_BED_TEMP_C = 60

BED_TEMP_OVERRIDE_KEYS = (
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

OFFSET_CALIBRATION_SPEED_FACTOR = 2.5
OFFSET_CALIBRATION_ACCELERATION_FACTOR = 1.25
OFFSET_CALIBRATION_ACCELERATION_CAP = 2000.0

OFFSET_CALIBRATION_SPEED_OVERRIDE_KEYS = (
    "outer_wall_speed",
    "external_perimeter_speed",
    "top_surface_speed",
    "inner_wall_speed",
    "sparse_infill_speed",
    "internal_solid_infill_speed",
    "solid_infill_speed",
    "gap_fill_speed",
    "gap_infill_speed",
    "travel_speed",
    "bridge_speed",
    "initial_layer_speed",
    "initial_layer_infill_speed",
)

OFFSET_CALIBRATION_ACCELERATION_OVERRIDE_KEYS = (
    "initial_layer_acceleration",
    "outer_wall_acceleration",
    "top_surface_acceleration",
    "bridge_acceleration",
)

OFFSET_CALIBRATION_MACHINE_SPEED_OVERRIDES = {
    "machine_max_speed_x": "500",
    "machine_max_speed_y": "500",
}


def _format_slicer_number(value: float) -> str:
    return f"{value:g}"


def _scale_numeric_override(
    overrides: dict,
    key: str,
    factor: float,
    *,
    cap: float | None = None,
) -> None:
    value = float(overrides[key]) * factor
    if cap is not None:
        value = min(value, cap)
    overrides[key] = _format_slicer_number(value)


def _set_all_plate_bed_temperatures(process_data: dict, temp_c: int) -> None:
    process_data["process_overrides"].update(
        {key: str(temp_c) for key in BED_TEMP_OVERRIDE_KEYS}
    )


def _tune_offset_calibration_for_speed(process_data: dict) -> None:
    overrides = process_data["process_overrides"]

    for key in OFFSET_CALIBRATION_SPEED_OVERRIDE_KEYS:
        _scale_numeric_override(overrides, key, OFFSET_CALIBRATION_SPEED_FACTOR)

    for key in OFFSET_CALIBRATION_ACCELERATION_OVERRIDE_KEYS:
        _scale_numeric_override(
            overrides,
            key,
            OFFSET_CALIBRATION_ACCELERATION_FACTOR,
            cap=OFFSET_CALIBRATION_ACCELERATION_CAP,
        )

    _scale_numeric_override(
        overrides,
        "filament_max_volumetric_speed",
        OFFSET_CALIBRATION_SPEED_FACTOR,
    )
    overrides.update(OFFSET_CALIBRATION_MACHINE_SPEED_OVERRIDES)


def cold_bed_pla_04_first_print_process_data() -> dict:
    """Return conservative cold-bed PLA settings for the current live machine."""

    process_data = resolve_process_data_from_parameters(
        printer_id=PRINTER_ID,
        material_name="creality_pla_hs",
        nozzle_diameter_mm=0.4,
        nozzle_hardened=False,
        nozzle_high_flow=False,
        strength_factor=0.25,
        quality_factor=0.8,
    )
    process_data["print_area"] = copy.deepcopy(DUAL_TOOLSWITCH_PRINT_AREA)
    process_data["master_settings_dir"] = MASTER_SETTINGS_DIR.resolve().as_posix()
    for machine_list_key in ("nozzle_diameter", "min_layer_height", "max_layer_height"):
        process_data["process_overrides"].pop(machine_list_key, None)

    process_data["process_overrides"].update(
        {
            "hot_plate_temp": "0",
            "hot_plate_temp_initial_layer": "0",
            "cool_plate_temp": "0",
            "cool_plate_temp_initial_layer": "0",
            "eng_plate_temp": "0",
            "eng_plate_temp_initial_layer": "0",
            "supertack_plate_temp": "0",
            "supertack_plate_temp_initial_layer": "0",
            "textured_cool_plate_temp": "0",
            "textured_cool_plate_temp_initial_layer": "0",
            "textured_plate_temp": "0",
            "textured_plate_temp_initial_layer": "0",
            "nozzle_temperature_initial_layer": "205",
            "nozzle_temperature": "210",
            "filament_max_volumetric_speed": "20",
            "filament_flow_ratio": "1.0",
            "layer_height": "0.2",
            "initial_layer_print_height": "0.2",
            "line_width": "0.42",
            "initial_layer_line_width": "0.44",
            "outer_wall_line_width": "0.4",
            "inner_wall_line_width": "0.42",
            "top_surface_line_width": "0.4",
            "sparse_infill_line_width": "0.42",
            "outer_wall_speed": "80",
            "external_perimeter_speed": "80",
            "top_surface_speed": "70",
            "inner_wall_speed": "120",
            "sparse_infill_speed": "150",
            "internal_solid_infill_speed": "120",
            "solid_infill_speed": "120",
            "gap_fill_speed": "70",
            "gap_infill_speed": "70",
            "travel_speed": "500",
            "bridge_speed": "35",
            "initial_layer_speed": "50",
            "initial_layer_infill_speed": "105",
            "default_acceleration": "8000",
            "initial_layer_acceleration": "8000",
            "outer_wall_acceleration": "6000",
            "inner_wall_acceleration": "8000",
            "top_surface_acceleration": "8000",
            "travel_acceleration": "8000",
            "sparse_infill_acceleration": "8000",
            "internal_solid_infill_acceleration": "8000",
            "bridge_acceleration": "4000",
            "default_jerk": "10",
            "initial_layer_jerk": "10",
            "outer_wall_jerk": "7",
            "inner_wall_jerk": "10",
            "top_surface_jerk": "10",
            "travel_jerk": "10",
            "infill_jerk": "10",
            "enable_support": "0",
            "brim_type": "outer_only",
            "brim_width": "5",
            "brim_object_gap": "0",
            "sparse_infill_density": "15%",
            "wall_loops": "2",
            "top_shell_layers": "3",
            "bottom_shell_layers": "3",
            "enable_pressure_advance": "0",
            "pressure_advance": "0",
            "adaptive_pressure_advance": "0",
            "adaptive_pressure_advance_bridges": "0",
            "adaptive_pressure_advance_overhangs": "0",
        }
    )
    return process_data


PROCESS_DATA_PLA_04_COLD_BED_FIRST_PRINT = cold_bed_pla_04_first_print_process_data()


def copy_cold_bed_pla_04_first_print_process_data() -> dict:
    return copy.deepcopy(PROCESS_DATA_PLA_04_COLD_BED_FIRST_PRINT)


def dual_pla_04_offset_calibration_process_data() -> dict:
    process_data = cold_bed_pla_04_first_print_process_data()
    process_data["filament"] = T0_FILAMENT_PROFILE
    process_data["filaments"] = [T0_FILAMENT_PROFILE, T1_FILAMENT_PROFILE]
    process_data["print_area"] = copy.deepcopy(DUAL_TOOLSWITCH_PRINT_AREA)
    _set_all_plate_bed_temperatures(process_data, PLA_EXAMPLE_BED_TEMP_C)
    _tune_offset_calibration_for_speed(process_data)
    process_data["process_overrides"].update(
        {
            "brim_type": "no_brim",
            "brim_width": "0",
            "sparse_infill_density": "100%",
            "wall_loops": "1",
            "top_shell_layers": "2",
            "bottom_shell_layers": "2",
            "enable_prime_tower": "1",
            "prime_tower_width": "35",
            "prime_tower_brim_width": "3",
            "purge_in_prime_tower": "1",
            "wipe_tower_x": "200",
            "wipe_tower_y": "220",
            "wipe_tower_no_sparse_layers": "0",
            "standby_temperature_delta": "0",
        }
    )
    return process_data


def cold_bed_dual_pla_04_offset_calibration_process_data() -> dict:
    return dual_pla_04_offset_calibration_process_data()


PROCESS_DATA_DUAL_PLA_04_OFFSET_CALIBRATION = (
    dual_pla_04_offset_calibration_process_data()
)


def copy_dual_pla_04_offset_calibration_process_data() -> dict:
    return copy.deepcopy(PROCESS_DATA_DUAL_PLA_04_OFFSET_CALIBRATION)


def copy_cold_bed_dual_pla_04_offset_calibration_process_data() -> dict:
    return copy_dual_pla_04_offset_calibration_process_data()

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
SAFE_XY_SPEED_MM_S = 300
SAFE_XY_ACCEL_MM_S2 = 3500
SAFE_XY_JERK_MM_S = 5
DUAL_MATERIAL_Z_HOP_MM = "0.6"
DUAL_MATERIAL_Z_HOP_TYPE = "Normal Lift"
DUAL_MATERIAL_FILAMENT_Z_HOP_TYPE = "retract_lift"

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


def resolve_idex_process_data_from_parameters(**kwargs) -> dict:
    kwargs.setdefault("printer_id", PRINTER_ID)
    process_data = resolve_process_data_from_parameters(**kwargs)
    process_data["master_settings_dir"] = MASTER_SETTINGS_DIR.resolve().as_posix()
    return process_data


def _set_all_plate_bed_temperatures(process_data: dict, temp_c: int) -> None:
    process_data["process_overrides"].update(
        {key: str(temp_c) for key in BED_TEMP_OVERRIDE_KEYS}
    )


def _enable_dual_material_z_hop(process_data: dict) -> None:
    process_data["process_overrides"].update(
        {
            "z_hop": [DUAL_MATERIAL_Z_HOP_MM, DUAL_MATERIAL_Z_HOP_MM],
            "z_hop_types": [
                DUAL_MATERIAL_Z_HOP_TYPE,
                DUAL_MATERIAL_Z_HOP_TYPE,
            ],
            "filament_z_hop": DUAL_MATERIAL_Z_HOP_MM,
            "filament_z_hop_types": DUAL_MATERIAL_FILAMENT_Z_HOP_TYPE,
        }
    )


def _standardize_dual_pla_process_data(process_data: dict) -> dict:
    process_data["filament"] = T0_FILAMENT_PROFILE
    process_data["filaments"] = [T0_FILAMENT_PROFILE, T1_FILAMENT_PROFILE]
    process_data["print_area"] = copy.deepcopy(DUAL_TOOLSWITCH_PRINT_AREA)
    _set_all_plate_bed_temperatures(process_data, PLA_EXAMPLE_BED_TEMP_C)
    _enable_dual_material_z_hop(process_data)
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
            "wipe_tower_y": "15",
            "wipe_tower_no_sparse_layers": "0",
            "standby_temperature_delta": "0",
        }
    )
    return process_data


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
            "travel_speed": str(SAFE_XY_SPEED_MM_S),
            "bridge_speed": "35",
            "initial_layer_speed": "50",
            "initial_layer_infill_speed": "105",
            "default_acceleration": str(SAFE_XY_ACCEL_MM_S2),
            "initial_layer_acceleration": "3000",
            "outer_wall_acceleration": "3000",
            "inner_wall_acceleration": str(SAFE_XY_ACCEL_MM_S2),
            "top_surface_acceleration": "3000",
            "travel_acceleration": str(SAFE_XY_ACCEL_MM_S2),
            "sparse_infill_acceleration": str(SAFE_XY_ACCEL_MM_S2),
            "internal_solid_infill_acceleration": str(SAFE_XY_ACCEL_MM_S2),
            "bridge_acceleration": "1750",
            "default_jerk": str(SAFE_XY_JERK_MM_S),
            "initial_layer_jerk": str(SAFE_XY_JERK_MM_S),
            "outer_wall_jerk": str(SAFE_XY_JERK_MM_S),
            "inner_wall_jerk": str(SAFE_XY_JERK_MM_S),
            "top_surface_jerk": str(SAFE_XY_JERK_MM_S),
            "travel_jerk": str(SAFE_XY_JERK_MM_S),
            "infill_jerk": str(SAFE_XY_JERK_MM_S),
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


def cold_bed_pla_06_first_print_process_data() -> dict:
    """Return cold-bed PLA settings for the current 0.6 mm IDEX nozzle setup."""

    process_data = cold_bed_pla_04_first_print_process_data()
    process_data["process_overrides"].update(
        {
            "layer_height": "0.3",
            "initial_layer_print_height": "0.3",
            "line_width": "0.65",
            "initial_layer_line_width": "0.70",
            "outer_wall_line_width": "0.60",
            "inner_wall_line_width": "0.65",
            "top_surface_line_width": "0.60",
            "sparse_infill_line_width": "0.70",
            "internal_solid_infill_line_width": "0.65",
            "support_line_width": "0.65",
            "nozzle_temperature_initial_layer": "210",
            "nozzle_temperature": "205",
            "bridge_speed": "30",
            "filament_retraction_length": "1.2",
            "elefant_foot_compensation": "0.1",
        }
    )
    return process_data


PROCESS_DATA_PLA_06_COLD_BED_FIRST_PRINT = cold_bed_pla_06_first_print_process_data()


def copy_cold_bed_pla_06_first_print_process_data() -> dict:
    return copy.deepcopy(PROCESS_DATA_PLA_06_COLD_BED_FIRST_PRINT)


def dual_pla_04_standard_process_data() -> dict:
    return _standardize_dual_pla_process_data(
        cold_bed_pla_04_first_print_process_data()
    )


PROCESS_DATA_DUAL_PLA_04_STANDARD = dual_pla_04_standard_process_data()


def copy_dual_pla_04_standard_process_data() -> dict:
    return copy.deepcopy(PROCESS_DATA_DUAL_PLA_04_STANDARD)


def dual_pla_04_offset_calibration_process_data() -> dict:
    return dual_pla_04_standard_process_data()


def cold_bed_dual_pla_04_offset_calibration_process_data() -> dict:
    return dual_pla_04_offset_calibration_process_data()


PROCESS_DATA_DUAL_PLA_04_OFFSET_CALIBRATION = PROCESS_DATA_DUAL_PLA_04_STANDARD


def copy_dual_pla_04_offset_calibration_process_data() -> dict:
    return copy.deepcopy(PROCESS_DATA_DUAL_PLA_04_OFFSET_CALIBRATION)


def copy_cold_bed_dual_pla_04_offset_calibration_process_data() -> dict:
    return copy_dual_pla_04_offset_calibration_process_data()


def dual_pla_06_standard_process_data() -> dict:
    return _standardize_dual_pla_process_data(
        cold_bed_pla_06_first_print_process_data()
    )


PROCESS_DATA_DUAL_PLA_06_STANDARD = dual_pla_06_standard_process_data()


def copy_dual_pla_06_standard_process_data() -> dict:
    return copy.deepcopy(PROCESS_DATA_DUAL_PLA_06_STANDARD)


def dual_pla_06_offset_calibration_process_data() -> dict:
    return dual_pla_06_standard_process_data()


PROCESS_DATA_DUAL_PLA_06_OFFSET_CALIBRATION = PROCESS_DATA_DUAL_PLA_06_STANDARD


def copy_dual_pla_06_offset_calibration_process_data() -> dict:
    return copy.deepcopy(PROCESS_DATA_DUAL_PLA_06_OFFSET_CALIBRATION)


def copy_cold_bed_dual_pla_06_offset_calibration_process_data() -> dict:
    return copy_dual_pla_06_offset_calibration_process_data()

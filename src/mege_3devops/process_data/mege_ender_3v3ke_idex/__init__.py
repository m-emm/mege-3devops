"""Process data for the Mege Ender 3 V3 KE IDEX printer identity."""

from __future__ import annotations

import copy
from pathlib import Path

from mege_3devops.process_data.parametric import resolve_process_data_from_parameters

PRINTER_ID = "mege_ender_3v3ke_idex"
MASTER_SETTINGS_DIR = Path(__file__).with_name("settings_master")

SAFE_X_MIN_MM = 155.0
SAFE_X_MAX_MM = 295.0
SAFE_Y_MIN_MM = 55.0
SAFE_Y_MAX_MM = 305.0
SAFE_BED_WIDTH_MM = SAFE_X_MAX_MM - SAFE_X_MIN_MM
SAFE_BED_DEPTH_MM = SAFE_Y_MAX_MM - SAFE_Y_MIN_MM
SAFE_BED_ORIGIN = (SAFE_X_MIN_MM, SAFE_Y_MIN_MM)


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
            "nozzle_temperature": "200",
            "filament_max_volumetric_speed": "8",
            "filament_flow_ratio": "1.0",
            "layer_height": "0.2",
            "initial_layer_print_height": "0.2",
            "line_width": "0.42",
            "initial_layer_line_width": "0.44",
            "outer_wall_line_width": "0.4",
            "inner_wall_line_width": "0.42",
            "top_surface_line_width": "0.4",
            "sparse_infill_line_width": "0.42",
            "outer_wall_speed": "35",
            "external_perimeter_speed": "35",
            "top_surface_speed": "35",
            "inner_wall_speed": "45",
            "sparse_infill_speed": "45",
            "internal_solid_infill_speed": "45",
            "solid_infill_speed": "45",
            "gap_fill_speed": "40",
            "gap_infill_speed": "40",
            "travel_speed": "60",
            "bridge_speed": "15",
            "initial_layer_speed": "15",
            "initial_layer_infill_speed": "20",
            "default_acceleration": "300",
            "initial_layer_acceleration": "300",
            "outer_wall_acceleration": "300",
            "inner_wall_acceleration": "300",
            "top_surface_acceleration": "300",
            "travel_acceleration": "300",
            "sparse_infill_acceleration": "300",
            "internal_solid_infill_acceleration": "300",
            "bridge_acceleration": "300",
            "default_jerk": "5",
            "initial_layer_jerk": "5",
            "outer_wall_jerk": "5",
            "inner_wall_jerk": "5",
            "top_surface_jerk": "5",
            "travel_jerk": "5",
            "infill_jerk": "5",
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

import copy

from mege_3devops.process_data.mender3.process_data_06_high_speed import (
    PROCESS_DATA_06_HS_BASE,
)
from mege_3devops.process_data.mender3.process_data_utils import (
    augment,
    augment_with_bed_temperatures,
)

##### 0.8 mm High-Speed Base #####
PROCESS_DATA_08_HS_BASE = copy.deepcopy(PROCESS_DATA_06_HS_BASE)
PROCESS_DATA_08_HS_BASE["process_overrides"].update(
    {
        "nozzle_diameter": "0.8",
        "line_width": "0.88",
        "outer_wall_line_width": "0.80",
        "inner_wall_line_width": "0.88",
        "solid_infill_line_width": "0.88",
        "internal_solid_infill_line_width": "0.88",
        "sparse_infill_line_width": "0.92",
        "top_surface_line_width": "0.80",
        "support_line_width": "0.88",
        "support_interface_line_width": "0.80",
        "thin_wall_line_width": "0.80",
        "gap_fill_line_width": "0.80",
        "bridge_line_width": "0.80",
        "initial_layer_line_width": "0.95",
        "wall_loops": "1",
        "sparse_infill_density": "15%",
        "support_base_pattern_spacing": "5.0",
    }
)


##### PLA 0.8 mm High Speed Profile #####
pla_08_hs_layer_height_factor = 0.75  # ~0.60mm layers for speed
pla_08_hs_quality_speed = 160  # slightly higher outer-wall speed
pla_08_hs_inner_speed = 270  # aggressively fast infill/inner walls
pla_08_hs_quality_acceleration = 5000
pla_08_hs_inner_acceleration = 8000
pla_08_hs_quality_jerk = 8
pla_08_hs_inner_jerk = 10

PROCESS_DATA_PLA_08_HS = augment(
    PROCESS_DATA_08_HS_BASE,
    layer_height_factor=pla_08_hs_layer_height_factor,
    quality_speed=pla_08_hs_quality_speed,
    inner_speed=pla_08_hs_inner_speed,
    quality_acceleration=pla_08_hs_quality_acceleration,
    inner_acceleration=pla_08_hs_inner_acceleration,
    quality_jerk=pla_08_hs_quality_jerk,
    inner_jerk=pla_08_hs_inner_jerk,
)
PROCESS_DATA_PLA_08_HS["filament"] = "FilamentCrealityPLAHighSpeedTunedForSpeed"

PROCESS_DATA_PLA_08_HS["process_overrides"].update(
    {
        "nozzle_temperature_initial_layer": "210",
        "nozzle_temperature": "205",
        "filament_flow_ratio": "1.0",
        "initial_layer_print_height": "0.35",
        "initial_layer_line_width": "0.95",
        "initial_layer_speed": "60",
        "initial_layer_infill_speed": "90",
        "filament_max_volumetric_speed": "30",
        "fan_min_speed": "100",
        "fan_max_speed": "100",
        "fan_cooling_layer_time": "10",
        "slow_down_for_layer_cooling": "0",
        "min_layer_time": "5",
        "detect_overhang_wall": "1",
        "enable_overhang_speed": "1",
        "overhang_1_4_speed": "0",
        "overhang_2_4_speed": "0",
        "overhang_3_4_speed": "50",
        "overhang_4_4_speed": "30",
        "bridge_speed": "35",
        "bridge_no_support": "0",
        "enable_support": "1",
        "support_interface_top_layers": "1",
        "support_interface_bottom_layers": "1",
        "support_threshold_angle": "65",
        "support_interface_pattern": "rectilinear",
        "support_interface_spacing": "2.2",
        "support_interface_speed": "160",
        "support_speed": "270",
        "support_object_xy_distance": "0.9",
        "support_top_z_distance": "0.36",
        "support_base_pattern_spacing": "5.0",
        "brim_type": "outer_and_inner",
        "brim_object_gap": "0",
        "brim_width": "10",
        "elefant_foot_compensation": "0.12",
        "filament_retraction_length": "1.4",
        "filament_retraction_speed": "40",
        "filament_deretraction_speed": "35",
        "resolution": "0.07",
        "xy_hole_compensation": "0.10",
        "enable_pressure_advance": "1",
        "pressure_advance": "0.05",
    }
)
PROCESS_DATA_PLA_08_HS = augment_with_bed_temperatures(
    PROCESS_DATA_PLA_08_HS, regular_temp=75, initial_temp=75
)


##### TPU 0.8 mm High Speed Profile #####
tpu_08_hs_layer_height_factor = 0.65  # ~0.52mm layers to keep TPU flexible
tpu_08_hs_quality_speed = 110
tpu_08_hs_inner_speed = 150
tpu_08_hs_quality_acceleration = 2500
tpu_08_hs_inner_acceleration = 3500
tpu_08_hs_quality_jerk = 10
tpu_08_hs_inner_jerk = 12

PROCESS_DATA_TPU_08_HS = augment(
    PROCESS_DATA_08_HS_BASE,
    layer_height_factor=tpu_08_hs_layer_height_factor,
    quality_speed=tpu_08_hs_quality_speed,
    inner_speed=tpu_08_hs_inner_speed,
    quality_acceleration=tpu_08_hs_quality_acceleration,
    inner_acceleration=tpu_08_hs_inner_acceleration,
    quality_jerk=tpu_08_hs_quality_jerk,
    inner_jerk=tpu_08_hs_inner_jerk,
)
PROCESS_DATA_TPU_08_HS["filament"] = "FilamenteSunTPU95A"
PROCESS_DATA_TPU_08_HS = augment_with_bed_temperatures(
    PROCESS_DATA_TPU_08_HS, regular_temp=55, initial_temp=60
)
PROCESS_DATA_TPU_08_HS["process_overrides"].update(
    {
        "nozzle_temperature_initial_layer": "230",
        "nozzle_temperature": "225",
        "filament_flow_ratio": "0.98",
        "filament_retraction_length": "2.1",
        "filament_retraction_speed": "45",
        "filament_deretraction_speed": "35",
        "wipe": "1",
        "wipe_distance": "1.2",
        "fan_min_speed": "40",
        "fan_max_speed": "65",
        "fan_cooling_layer_time": "12",
        "overhang_fan_speed": "65",
        "slow_down_for_layer_cooling": "0",
        "min_layer_time": "5",
        "detect_overhang_wall": "0",
        "enable_overhang_speed": "0",
        "overhang_1_4_speed": "0",
        "overhang_2_4_speed": "0",
        "overhang_3_4_speed": "60",
        "overhang_4_4_speed": "40",
        "bridge_speed": "80",
        "bridge_no_support": "0",
        "filament_max_volumetric_speed": "28",
        "initial_layer_print_height": "0.35",
        "initial_layer_line_width": "0.95",
        "initial_layer_speed": "45",
        "initial_layer_infill_speed": "70",
        "enable_support": "0",
        "support_threshold_angle": "45",
        "support_top_z_distance": "0.5",
        "support_object_xy_distance": "0.7",
        "z_hop": "0.45",
        "xy_hole_compensation": "0.06",
        "wall_loops": "2",
        "sparse_infill_density": "5%",
        "brim_type": "outer_only",
        "brim_width": "4",
        "brim_object_gap": "0",
        "elefant_foot_compensation": "0.15",
        "infill_wall_overlap": "30%",
        "resolution": "0.07",
        "wipe_on_loops": "1",
        "wipe_before_external_loop": "1",
        "role_based_wipe_speed": "1",
        "seam_gap": "0",
        "reduce_crossing_wall": "1",
    }
)


##### PETG 0.8 mm High Speed Profile #####
petg_08_hs_layer_height_factor = 0.65  # ~0.52mm layers for flow
petg_08_hs_quality_speed = 110
petg_08_hs_inner_speed = 220
petg_08_hs_quality_acceleration = 4000
petg_08_hs_inner_acceleration = 7000
petg_08_hs_quality_jerk = 6
petg_08_hs_inner_jerk = 9

PROCESS_DATA_PETG_08_HS = augment(
    PROCESS_DATA_08_HS_BASE,
    layer_height_factor=petg_08_hs_layer_height_factor,
    quality_speed=petg_08_hs_quality_speed,
    inner_speed=petg_08_hs_inner_speed,
    quality_acceleration=petg_08_hs_quality_acceleration,
    inner_acceleration=petg_08_hs_inner_acceleration,
    quality_jerk=petg_08_hs_quality_jerk,
    inner_jerk=petg_08_hs_inner_jerk,
)
PROCESS_DATA_PETG_08_HS["filament"] = "FilamentPETGMegeMaster"
PROCESS_DATA_PETG_08_HS = augment_with_bed_temperatures(
    PROCESS_DATA_PETG_08_HS, regular_temp=85, initial_temp=90
)
PROCESS_DATA_PETG_08_HS["process_overrides"].update(
    {
        "nozzle_temperature_initial_layer": "255",
        "nozzle_temperature": "250",
        "filament_flow_ratio": "1.0",
        "initial_layer_print_height": "0.35",
        "initial_layer_line_width": "0.90",
        "initial_layer_speed": "32",
        "initial_layer_infill_speed": "45",
        "filament_retraction_length": "1.1",
        "filament_retraction_speed": "35",
        "filament_deretraction_speed": "30",
        "fan_min_speed": "15",
        "fan_max_speed": "45",
        "fan_cooling_layer_time": "12",
        "overhang_fan_speed": "55",
        "infill_wall_overlap": "25%",
        "detect_overhang_wall": "1",
        "enable_overhang_speed": "1",
        "overhang_1_4_speed": "0",
        "overhang_2_4_speed": "0",
        "overhang_3_4_speed": "40",
        "overhang_4_4_speed": "25",
        "bridge_speed": "25",
        "bridge_no_support": "0",
        "filament_max_volumetric_speed": "24",
        "slow_down_for_layer_cooling": "0",
        "min_layer_time": "6",
        "support_threshold_angle": "55",
        "support_interface_top_layers": "1",
        "support_interface_bottom_layers": "1",
        "support_interface_pattern": "rectilinear",
        "support_interface_spacing": "1.5",
        "support_interface_speed": "150",
        "support_speed": "220",
        "support_object_xy_distance": "0.5",
        "support_top_z_distance": "0.35",
        "support_base_pattern_spacing": "3.5",
        "xy_hole_compensation": "0.07",
        "sparse_infill_density": "20%",
        "brim_type": "outer_and_inner",
        "brim_width": "8",
        "brim_object_gap": "0",
        "elefant_foot_compensation": "0.15",
    }
)


_all_ = [
    "PROCESS_DATA_PLA_08_HS",
    "PROCESS_DATA_TPU_08_HS",
    "PROCESS_DATA_PETG_08_HS",
]

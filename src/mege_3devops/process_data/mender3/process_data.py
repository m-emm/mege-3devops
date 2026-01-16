from shellforgepy_meges_workshop.designs.headmask.process_data_utils import (
    augment,
    augment_with_bed_temperatures,
)

#######
# This is "Legacy" process data for the 0.6mm nozzle on the Creality Ender 3V3 KE Stock Hotend
# In the meantime, the printer has a Micro Swiss hotend installed, so the parameters do no longer apply as-is
#######

PROCESS_DATA_06_BASE = {
    "filament": "FilamentCrealityPLAHighSpeedTunedForSpeed",
    "process_overrides": {
        ### WARNING: These are the BASE Settings - DO NOT TWEAK MATERIAL SPECIFIC THINGS HERE !!!
        "adaptive_layer_height": "0",
        "bottom_shell_layers": "3",  # More layers for strength
        "bridge_line_width": "0.6",
        "bridge_no_support": "1",
        "bridge_speed": "30",  # Faster bridges for PLA
        "brim_ears_detection_length": "1",
        "brim_ears_max_angle": "125",
        "brim_object_gap": "0",
        "brim_type": "outer_and_inner",  # Better adhesion than no_brim
        "brim_width": "4",
        "elefant_foot_compensation": "0.1",  # Less than PETG
        "enable_arc_fitting": "1",
        "enable_support": "0",
        "fan_cooling_layer_time": "30",  # Shorter than PETG
        "fan_max_speed": "100",  # Full cooling for PLA
        "fan_min_speed": "80",  # High minimum for PLA
        "filament_deretraction_speed": "30",
        "filament_flow_ratio": "1.0",
        "filament_retraction_length": "1.2",  # Shorter for PLA
        "filament_retraction_speed": "40",  # Faster retraction
        "gap_fill_line_width": "0.6",
        "hot_plate_temp_initial_layer": "65",  # PLA bed temp
        "infill_wall_overlap": "25%",  # Standard for PLA
        "initial_layer_line_width": "0.7",
        "initial_layer_print_height": "0.3",
        "inner_wall_line_width": "0.65",
        "internal_solid_infill_line_width": "0.65",
        "line_width": "0.65",  # ~108% of nozzle diameter for good flow
        "min_layer_time": "8",  # Shorter for PLA
        "nozzle_diameter": "0.6",
        "nozzle_temperature_initial_layer": "235",  # Slightly higher for first layer
        "nozzle_temperature": "230",
        "outer_wall_line_width": "0.6",  # Slightly smaller for quality
        "overhang_fan_speed": "100",
        "resolution": "0.05",  # Finer resolution for PLA
        "slow_down_for_layer_cooling": "1",
        "solid_infill_line_width": "0.65",
        "sparse_infill_density": "20%",
        "sparse_infill_line_width": "0.7",  # Wider for faster infill
        "sparse_infill_pattern": "cubic",
        "support_base_pattern_spacing": "2.5",
        "support_base_pattern": "rectilinear",
        "support_bottom_interface_spacing": "0.5",
        "support_interface_line_width": "0.6",
        "support_line_width": "0.65",
        "support_object_first_layer_gap": "0.3",
        "support_object_xy_distance": "0.35",
        "support_on_build_plate_only": "1",
        "support_remove_small_overhang": "1",
        "support_style": "grid",
        "support_threshold_angle": "50",  # Standard PLA support angle
        "support_threshold_overlap": "50%",
        "support_top_z_distance": "0.2",
        "support_type": "normal(auto)",
        "thin_wall_line_width": "0.6",
        "top_shell_layers": "3",
        "top_surface_line_width": "0.6",  # Finer for surface quality
        "wall_loops": "1",
        "xy_contour_compensation": "0",
        "xy_hole_compensation": "0.05",  # Less than PETG
    },
}


pla_06_layer_height_factor = 0.6
pla_06_nozzle_diameter = 0.6
pla_06_quality_speed = 55
pla_06_inner_speed = 85
pla_06_quality_acceleration = 2500
pla_06_inner_acceleration = 8000
pla_06_quality_jerk = 6
pla_06_inner_jerk = 12


PROCESS_DATA_PLA_06 = augment(
    PROCESS_DATA_06_BASE,
    layer_height_factor=pla_06_layer_height_factor,
    quality_speed=pla_06_quality_speed,
    inner_speed=pla_06_inner_speed,
    quality_acceleration=pla_06_quality_acceleration,
    inner_acceleration=pla_06_inner_acceleration,
    quality_jerk=pla_06_quality_jerk,
    inner_jerk=pla_06_inner_jerk,
)

# Apply consistent bed temperatures across all plate types
PROCESS_DATA_PLA_06 = augment_with_bed_temperatures(
    PROCESS_DATA_PLA_06, regular_temp=70, initial_temp=75
)

PROCESS_DATA_PLA_06["process_overrides"].update(  # curently optimized for bed adhesion
    {
        "bridge_speed": "30",  # (or try 28 if you still see sag)
        "brim_ears_detection_length": "1",
        "brim_ears_max_angle": "125",
        "brim_type": "outer_and_inner",  # Enhanced brim settings for better adhesion of tall thin parts
        "brim_width": "12",  # Wider brim for better adhesion
        "enable_support": "1",
        "fan_cooling_layer_time": "60",  # Longer time before full cooling
        "fan_min_speed": "50",  # Lower minimum to prevent warping
        "filament_deretraction_speed": "30",
        "filament_flow_ratio": "1.05",  # Reduced from 1.1 to decrease support adhesion
        "filament_retraction_length": "1.5",
        "filament_retraction_speed": "40",
        # Note: Bed temperatures are now set via augment_with_bed_temperatures() above
        # All plate types use 70°C/75°C for reliable PLA printing
        "initial_layer_print_height": "0.42",  # Thicker first layer for better bed adhesion (70% of 0.6mm nozzle)
        "min_layer_time": "15",  # Slower first layers for better adhesion
        "nozzle_temperature_initial_layer": "245",  # Max PLA temp for steel nozzle and fast printing
        "nozzle_temperature": "238",  # High temp to maintain flow at speed with steel nozzle
        "slow_down_for_layer_cooling": "1",
        "support_threshold_angle": "40",  # Increased from 30 to reduce support volume
        "support_interface_top_layers": "2",  # Add interface layers for easier removal
        "support_interface_bottom_layers": "2",  # Add bottom interface layers
        "support_interface_pattern": "rectilinear",  # Better for removal than grid
        "support_interface_spacing": "0.8",  # Less dense interface for easier removal
        "support_object_xy_distance": "0.5",  # Increased from base 0.35 for easier removal
        "support_top_z_distance": "0.3",  # Increased from base 0.2 for easier removal
    }
)


##### PVA profile (Water-soluble forms for epoxy casting)

pva_06_layer_height_factor = 0.4  # Fine layers for smooth epoxy surface finish
pva_06_nozzle_diameter = 0.6
pva_06_quality_speed = 25  # Slightly faster but still conservative
pva_06_inner_speed = 40  # Moderate speed for structural integrity
pva_06_quality_acceleration = 1500  # Moderate acceleration for quality
pva_06_inner_acceleration = 3000  # Conservative but not too slow
pva_06_quality_jerk = 4  # Low jerk for surface quality
pva_06_inner_jerk = 7  # Moderate inner jerk

PROCESS_DATA_PVA_06 = augment(
    PROCESS_DATA_06_BASE,
    layer_height_factor=pva_06_layer_height_factor,
    quality_speed=pva_06_quality_speed,
    inner_speed=pva_06_inner_speed,
    quality_acceleration=pva_06_quality_acceleration,
    inner_acceleration=pva_06_inner_acceleration,
    quality_jerk=pva_06_quality_jerk,
    inner_jerk=pva_06_inner_jerk,
)

PROCESS_DATA_PVA_06["filament"] = "FilamentPVAStructural"

# Apply consistent bed temperatures across all plate types - PVA benefits from slight warming
PROCESS_DATA_PVA_06 = augment_with_bed_temperatures(
    PROCESS_DATA_PVA_06,
    regular_temp=45,
    initial_temp=50,  # Warm bed for better adhesion and strength
)

PROCESS_DATA_PVA_06["process_overrides"].update(
    {
        "bottom_shell_layers": "4",  # More layers for structural integrity
        "bridge_speed": "20",  # Moderate bridge speed for strength
        "brim_type": "outer_and_inner",  # Brim for form stability during curing
        "brim_width": "6",  # Wide brim to prevent warping during epoxy cure
        "elefant_foot_compensation": "0.1",  # Slight compensation for heated bed
        "enable_support": "1",  # Forms may need supports for complex geometries
        "fan_cooling_layer_time": "30",  # Balanced cooling for strength
        "fan_max_speed": "80",  # Moderate cooling to prevent warping
        "fan_min_speed": "60",  # Consistent cooling
        "filament_deretraction_speed": "25",  # Standard retraction speed
        "filament_flow_ratio": "1.0",  # Full flow for structural integrity
        "filament_retraction_length": "1.8",  # Moderate retraction
        "filament_retraction_speed": "30",  # Standard retraction speed
        # Note: Bed temperatures are set above for form stability
        "infill_wall_overlap": "30%",  # Good bonding for strength
        "initial_layer_line_width": "0.7",  # Wide first layer for adhesion
        "initial_layer_print_height": "0.35",  # Thick first layer for stability
        "inner_wall_line_width": "0.65",  # Standard wall thickness
        "internal_solid_infill_line_width": "0.65",
        "min_layer_time": "12",  # Reasonable cooling time
        "nozzle_temperature_initial_layer": "210",  # Higher temp for first layer adhesion
        "nozzle_temperature": "205",  # Slightly higher for structural printing
        "outer_wall_line_width": "0.6",  # Good surface finish
        "overhang_fan_speed": "80",  # Moderate cooling for overhangs
        "resolution": "0.05",  # Fine resolution for smooth epoxy contact surface
        "sparse_infill_density": "35%",  # Higher infill for form rigidity during epoxy cure
        "sparse_infill_line_width": "0.7",  # Robust infill lines
        "sparse_infill_pattern": "cubic",  # Strong pattern for structural integrity
        "top_shell_layers": "5",  # More top layers for smooth surface finish
        "top_surface_line_width": "0.58",  # Fine top surface for epoxy contact
        "wall_loops": "3",  # Multiple walls for strength and chemical resistance
        "xy_contour_compensation": "0",
        "xy_hole_compensation": "0.05",  # Slight compensation for better fit
        "z_hop": "0.1",  # Small z-hop to prevent surface defects
        # Form-specific settings
        "slow_down_for_layer_cooling": "1",
        "bridge_no_support": "0",  # Forms may need bridge supports
        "gap_fill_line_width": "0.6",
        "thin_wall_line_width": "0.6",
        "solid_infill_line_width": "0.65",
        # Support settings for complex forms
        "support_threshold_angle": "45",  # Standard support angle
        "support_top_z_distance": "0.25",  # Good support interface
        "support_object_xy_distance": "0.4",  # Standard support distance
    }
)


##### TPU profile

tpu_06_layer_height_factor = 0.4
tpu_06_nozzle_diameter = 0.6
tpu_06_quality_speed = 30
tpu_06_inner_speed = 50
tpu_06_quality_acceleration = 1500
tpu_06_inner_acceleration = 4000
tpu_06_quality_jerk = 4
tpu_06_inner_jerk = 8
PROCESS_DATA_TPU_06 = augment(
    PROCESS_DATA_06_BASE,
    layer_height_factor=tpu_06_layer_height_factor,
    quality_speed=tpu_06_quality_speed,
    inner_speed=tpu_06_inner_speed,
    quality_acceleration=tpu_06_quality_acceleration,
    inner_acceleration=tpu_06_inner_acceleration,
    quality_jerk=tpu_06_quality_jerk,
    inner_jerk=tpu_06_inner_jerk,
)
PROCESS_DATA_TPU_06["filament"] = "FilamenteSunTPU95A"

# Apply consistent bed temperatures across all plate types
PROCESS_DATA_TPU_06 = augment_with_bed_temperatures(
    PROCESS_DATA_TPU_06, regular_temp=55, initial_temp=60
)

PROCESS_DATA_TPU_06["process_overrides"].update(
    {
        "enable_support": "1",
        "fan_cooling_layer_time": "60",
        "fan_max_speed": "50",
        "fan_min_speed": "30",
        "filament_deretraction_speed": "20",
        "filament_flow_ratio": "1.0",
        "filament_retraction_length": "0.8",
        "filament_retraction_speed": "20",
        # Note: Bed temperatures are now set via augment_with_bed_temperatures() above
        # All plate types use 55°C/60°C for optimal TPU printing
        "infill_wall_overlap": "50%",
        "initial_layer_line_width": "0.66",
        "initial_layer_print_height": "0.24",
        "inner_wall_line_width": "0.60",
        "internal_solid_infill_line_width": "0.60",
        "min_layer_time": "30",
        "nozzle_temperature_initial_layer": "240",
        "nozzle_temperature": "230",
        "outer_wall_line_width": "0.58",
        "overhang_fan_speed": "50",
        "resolution": "0.06",
        "sparse_infill_density": "10%",
        "sparse_infill_line_width": "0.60",
        "sparse_infill_pattern": "cubic",
        "support_threshold_angle": "40",  # was "36"
        "support_top_z_distance": "0.4",
        "top_shell_layers": "3",
        "top_surface_line_width": "0.60",
        "wall_loops": "1",
        "xy_contour_compensation": "0",
        "xy_hole_compensation": "0.0",
        "z_hop": "0.0",
    }
)


petg_quality_speed = 45
petg_inner_speed = 70

petg_quality_acceleration = 2000
petg_inner_acceleration = 7000

petg_quality_jerk = 5
petg_inner_jerk = 10

petg_layer_height_factor = 0.2

petg_vertical_layers = 2


PROCESS_DATA_PETG_06 = augment(
    PROCESS_DATA_06_BASE,
    layer_height_factor=petg_layer_height_factor,
    quality_speed=petg_quality_speed,
    inner_speed=petg_inner_speed,
    quality_acceleration=petg_quality_acceleration,
    inner_acceleration=petg_inner_acceleration,
    quality_jerk=petg_quality_jerk,
    inner_jerk=petg_inner_jerk,
)

PROCESS_DATA_PETG_06["filament"] = "FilamentPETGMegeMaster"

# Apply consistent bed temperatures across all plate types
PROCESS_DATA_PETG_06 = augment_with_bed_temperatures(
    PROCESS_DATA_PETG_06, regular_temp=75, initial_temp=78
)

PROCESS_DATA_PETG_06["process_overrides"].update(
    {
        "bottom_shell_layers": f"{petg_vertical_layers}",
        "bridge_speed": "25",
        "elefant_foot_compensation": "0.2",
        "fan_cooling_layer_time": "60",
        "fan_max_speed": "60",
        "fan_min_speed": "50",
        "brim_type": "outer_only",
        "brim_width": "3",
        "filament_deretraction_speed": "25",
        "filament_flow_ratio": "1.0",
        "filament_retraction_length": "1.6",
        "filament_retraction_speed": "30",
        # Note: Bed temperatures are now set via augment_with_bed_temperatures() above
        # All plate types use 75°C/78°C for reliable PETG printing
        "infill_wall_overlap": "55%",
        "initial_layer_line_width": "0.7",
        "initial_layer_print_height": "0.28",
        "inner_wall_line_width": "0.5",
        "internal_solid_infill_line_width": "0.5",
        "min_layer_time": "30",
        "nozzle_temperature_initial_layer": "260",
        "nozzle_temperature": "255",
        "outer_wall_line_width": "0.5",
        "overhang_fan_speed": "60",
        "sparse_infill_density": "40%",
        "sparse_infill_line_width": "0.5",
        "sparse_infill_pattern": "cubic",
        "top_shell_layers": f"{petg_vertical_layers}",
        "wall_loops": "2",
        "xy_contour_compensation": "0",
        "xy_hole_compensation": "0.1",
        "support_top_z_distance": "0.18",  # PETG doesn't bridge well
        "support_object_xy_distance": "0.2",
    }
)


_all_ = [
    "PROCESS_DATA_PLA_06",
    "PROCESS_DATA_TPU_06",
    "PROCESS_DATA_PETG_06",
    "PROCESS_DATA_PVA_06",
]


def main():

    import logging
    import os

    from shellforgepy.simple import PartList, arrange_and_export, create_box

    material = os.getenv("SHELLFORGEPY_MATERIAL", "PLA").upper()

    logging.basicConfig(level=logging.INFO)

    parts = PartList()

    _logger = logging.getLogger(__name__)

    test_part = create_box(4, 5, 3)

    parts.add(test_part, f"test_part", skip_in_production=False)
    _logger.info("Added test part to parts list.")

    if material == "PLA":
        process_data = PROCESS_DATA_PLA_06
    elif material == "TPU":
        process_data = PROCESS_DATA_TPU_06
    elif material == "PETG":
        process_data = PROCESS_DATA_PETG_06
    elif material == "PVA":
        process_data = PROCESS_DATA_PVA_06

    arrange_and_export(
        parts.as_list(),
        script_file=__file__,
        prod=True,
        process_data=process_data,
    )


if __name__ == "__main__":
    main()

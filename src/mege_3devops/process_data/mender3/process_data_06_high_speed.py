import copy

from shellforgepy_meges_workshop.designs.headmask.process_data_04_high_speed import *
from shellforgepy_meges_workshop.designs.headmask.process_data_utils import (
    augment,
    augment_with_bed_temperatures,
)

##### PLA 0.6 mm High Speed Profile #####
# For the microswiss hotend (not the stock creality hotend)
# Based on tuned PROCESS_DATA_PLA_04_HS but optimized for 0.6mm nozzle.
# Key advantage: 0.6mm nozzle can push ~2.25x more plastic per second than 0.4mm
# (cross-sectional area ratio: 0.6²/0.4² = 2.25)
#
# Volumetric flow comparison at same speed:
#   0.4mm nozzle @ 0.3mm layer × 0.42mm width @ 250mm/s = 31.5 mm³/s (too high!)
#   0.6mm nozzle @ 0.42mm layer × 0.65mm width @ 250mm/s = 68.25 mm³/s (way too high!)
#
# Practical limits (Micro Swiss hotend, PLA):
#   0.4mm nozzle: ~15-18 mm³/s sustained
#   0.6mm nozzle: ~25-30 mm³/s sustained
#
# Strategy: Use 0.6mm's flow advantage for THICKER LAYERS, not faster speed.
# This reduces layer count significantly for faster prints.

# Create a deep copy to start fresh
PROCESS_DATA_06_HS_BASE = copy.deepcopy(PROCESS_DATA_04_HS_BASE)

# Update BASE for 0.6mm nozzle - line widths
PROCESS_DATA_06_HS_BASE["process_overrides"].update(
    {
        "nozzle_diameter": "0.6",
        # Line widths scaled for 0.6mm nozzle
        "line_width": "0.65",  # ~108% of nozzle
        "outer_wall_line_width": "0.60",  # exactly nozzle diameter for quality
        "inner_wall_line_width": "0.65",
        "solid_infill_line_width": "0.65",
        "internal_solid_infill_line_width": "0.65",
        "sparse_infill_line_width": "0.70",  # wider for speed
        "top_surface_line_width": "0.60",  # quality surface
        "support_line_width": "0.65",
        "support_interface_line_width": "0.60",
        "thin_wall_line_width": "0.60",
        "gap_fill_line_width": "0.60",
        "bridge_line_width": "0.60",
        "initial_layer_line_width": "0.70",  # wider for adhesion
        "wall_loops": "1",  # fewer walls for speed
        "sparse_infill_density": "20%",  # more sparse for speed
    }
)

# Speed parameters for 0.6mm high-speed PLA
# Speeds similar to 04 HS, but flow advantage comes from thicker layers
pla_06_hs_layer_height_factor = 0.70  # 0.6 × 0.70 = 0.42mm layers (vs 0.30mm on 04)
pla_06_hs_quality_speed = 150  # outer walls - same as 04 HS
pla_06_hs_inner_speed = 250  # inner walls, infill - same as 04 HS
pla_06_hs_quality_acceleration = 5000  # same as 04 HS
pla_06_hs_inner_acceleration = 8000  # same as 04 HS
pla_06_hs_quality_jerk = 8  # same as 04 HS
pla_06_hs_inner_jerk = 10  # same as 04 HS

PROCESS_DATA_PLA_06_HS = augment(
    PROCESS_DATA_06_HS_BASE,
    layer_height_factor=pla_06_hs_layer_height_factor,
    quality_speed=pla_06_hs_quality_speed,
    inner_speed=pla_06_hs_inner_speed,
    quality_acceleration=pla_06_hs_quality_acceleration,
    inner_acceleration=pla_06_hs_inner_acceleration,
    quality_jerk=pla_06_hs_quality_jerk,
    inner_jerk=pla_06_hs_inner_jerk,
)

# Override: PLA-specific tuning for 0.6mm high-speed
PROCESS_DATA_PLA_06_HS["process_overrides"].update(
    {
        # Temperature - higher for 0.6mm to maintain flow at speed
        # Micro Swiss hotend can handle higher temps
        "nozzle_temperature_initial_layer": "210",
        "nozzle_temperature": "205",
        # Flow - 0.6mm nozzle is more forgiving, keep neutral
        "filament_flow_ratio": "1.0",
        # First layer - thicker for 0.6mm nozzle
        "initial_layer_print_height": "0.30",  # 50% of nozzle (was 0.20 for 04)
        "initial_layer_line_width": "0.70",  # wider for adhesion
        "initial_layer_speed": "50",  # can go faster with 0.6mm
        "initial_layer_infill_speed": "80",
        # Volumetric flow limit - 0.6mm can push more plastic
        # At 0.42mm layer × 0.65mm width @ 150mm/s = 40.95 mm³/s outer walls
        # At 0.42mm layer × 0.70mm width @ 250mm/s = 73.5 mm³/s infill (limited!)
        # Micro Swiss can handle ~32mm³/s with good cooling and PLA - we think; but it looks as it this is too aggressiv
        # This allows infill up to ~108mm/s, inner walls ~115mm/s
        "filament_max_volumetric_speed": "22",
        # Cooling - same as 04 HS, PLA needs aggressive cooling
        "fan_min_speed": "100",
        "fan_max_speed": "100",
        "fan_cooling_layer_time": "10",  # slightly longer for thicker layers
        # CRITICAL: Disable cooling slowdown - rely on fan, not speed reduction
        "slow_down_for_layer_cooling": "0",
        "min_layer_time": "5",
        # Overhang handling - same aggressive settings as 04 HS
        "detect_overhang_wall": "1",
        "enable_overhang_speed": "1",
        "overhang_1_4_speed": "0",  # normal speed
        "overhang_2_4_speed": "0",  # normal speed
        "overhang_3_4_speed": "50",  # slow for quality
        "overhang_4_4_speed": "30",  # slow for steep overhangs
        # Bridges - 0.6mm bridges better with thicker extrusions
        "bridge_speed": "30",  # slightly faster than 04 HS
        "bridge_no_support": "0",
        # Support settings - OPTIMIZED for speed
        # Analysis: Supports were 35.5% of total filament - major time sink!
        "enable_support": "1",
        "support_interface_top_layers": "1",
        "support_interface_bottom_layers": "1",
        "support_threshold_angle": "65",  # 55→65: fewer supports, PLA can bridge more
        "support_interface_pattern": "rectilinear",
        "support_interface_spacing": "2.0",  # 1.5→2.0: faster interface printing
        "support_object_xy_distance": "0.8",  # 0.7→0.8: easier removal, less contact
        "support_top_z_distance": "0.36",  # match layer height for clean separation
        # NEW: Reduce support density for speed
        "support_base_pattern_spacing": "4.0",  # default is 2.5, wider = less material
        "support_speed": "250",  # ensure max speed
        "support_interface_speed": "150",  # fast but quality for interface
        # Adhesion
        "brim_type": "outer_and_inner",
        "brim_object_gap": "0",
        "brim_width": "8",
        "elefant_foot_compensation": "0.1",  # slightly more for thicker first layer
        # Retraction - 0.6mm needs longer retraction
        "filament_retraction_length": "1.2",  # more than 04 (1.0)
        "filament_retraction_speed": "35",
        "filament_deretraction_speed": "30",
        # Resolution - can be coarser for 0.6mm
        "resolution": "0.06",
        # Hole compensation - 0.6mm nozzle closes holes more
        "xy_hole_compensation": "0.08",  # more than 04 HS (0.05)
        # Pressure Advance - ENABLED for high-speed to reduce blobs at wall ends
        # Value tuned for Ender 3V3 KE with Micro Swiss hotend
        "enable_pressure_advance": "1",
        "pressure_advance": "0.04",
    }
)

# Bed temperatures: same as 04 HS for cold basement
PROCESS_DATA_PLA_06_HS = augment_with_bed_temperatures(
    PROCESS_DATA_PLA_06_HS, regular_temp=75, initial_temp=75
)


##### TPU 0.6 mm High Speed Profile #####
# Optimized for Micro Swiss 0.6mm hotend with TPU 95A
# Based on successful head_band print (0.4mm) and TPU 04 HS learnings.
#
# Key insights from head_band validation:
#   - TPU 95A can handle 80mm/s outer walls, 120mm/s inner walls on 0.4mm nozzle
#   - 0.6mm nozzle flows TPU even better - can push similar or slightly higher speeds
#   - CRITICAL: disable slow_down_for_layer_cooling - TPU cools fine with fan alone
#   - CRITICAL: disable overhang detection - TPU droops less than PLA
#   - Bridge speed can be 60-80mm/s for TPU (head_band used 80!)
#
# Volumetric flow calculation:
#   0.6mm × 0.36mm layer × 100mm/s = 21.6 mm³/s (quality walls)
#   0.6mm × 0.42mm layer × 130mm/s = 32.8 mm³/s (infill) - will be limited
#   Micro Swiss can do ~20-25 mm³/s sustained for TPU 95A

tpu_06_hs_layer_height_factor = (
    0.60  # 0.6 × 0.60 = 0.36mm layers (matches PLA 06 HS ratio)
)
tpu_06_hs_quality_speed = (
    100  # outer walls - scale up from 04 HS (80) for larger nozzle
)
tpu_06_hs_inner_speed = 130  # inner walls, infill - scale up from 04 HS (120)
tpu_06_hs_quality_acceleration = 2500  # same as validated head_band
tpu_06_hs_inner_acceleration = 3500  # same as validated head_band
tpu_06_hs_quality_jerk = 10  # between head_band (12) and conservative (8)
tpu_06_hs_inner_jerk = 12  # between head_band (15) and conservative (10)

PROCESS_DATA_TPU_06_HS = augment(
    PROCESS_DATA_06_HS_BASE,
    layer_height_factor=tpu_06_hs_layer_height_factor,
    quality_speed=tpu_06_hs_quality_speed,
    inner_speed=tpu_06_hs_inner_speed,
    quality_acceleration=tpu_06_hs_quality_acceleration,
    inner_acceleration=tpu_06_hs_inner_acceleration,
    quality_jerk=tpu_06_hs_quality_jerk,
    inner_jerk=tpu_06_hs_inner_jerk,
)
PROCESS_DATA_TPU_06_HS["filament"] = "FilamenteSunTPU95A"

PROCESS_DATA_TPU_06_HS = augment_with_bed_temperatures(
    PROCESS_DATA_TPU_06_HS, regular_temp=55, initial_temp=60
)

# TPU 0.6mm High-Speed tuning - comprehensive settings
PROCESS_DATA_TPU_06_HS["process_overrides"].update(
    {
        # Temperature - slightly higher than 04 HS for better flow through 0.6mm
        # Micro Swiss hotend handles higher temps well
        # NOTE: Tried 220 - caused holes in walls without reducing stringing. Keep 225.
        "nozzle_temperature_initial_layer": "230",
        "nozzle_temperature": "225",
        # Flow - slight under-extrusion for cleaner features (proven in 04 HP/HS)
        "filament_flow_ratio": "0.98",
        # Retraction - TPU DOES string! 0.6mm nozzle holds more material = more ooze.
        # Aggressive retraction is KEY for stringing control with large nozzle TPU.
        "filament_retraction_length": "1.8",  # up from 1.2 - 0.6mm needs much more
        "filament_retraction_speed": "40",  # up from 30 - faster = less ooze time
        "filament_deretraction_speed": "30",  # up from 25 - keep up with faster retract
        # Wipe before retraction - helps clean nozzle tip before travel
        "wipe": "1",
        "wipe_distance": "1.0",  # 1mm wipe along perimeter before retraction
        # Cooling - moderate fan for TPU, don't need aggressive cooling
        "fan_min_speed": "40",  # matches 04 HS
        "fan_max_speed": "60",  # matches 04 HS
        "fan_cooling_layer_time": "12",  # slightly faster layers need less time
        "overhang_fan_speed": "60",  # boost for overhangs
        # CRITICAL: Disable cooling slowdown - this was THE key fix in head_band!
        # TPU cools fine with fan alone, slowdown kills print time (can drop to 10mm/s!)
        "slow_down_for_layer_cooling": "0",
        "min_layer_time": "5",  # low limit - no forced slowdowns
        # CRITICAL: Disable overhang speed reduction for TPU
        # TPU droops less than PLA, and slowdowns kill print time
        "detect_overhang_wall": "0",
        "enable_overhang_speed": "0",
        # But if someone re-enables, set reasonable overhang speeds
        "overhang_1_4_speed": "0",  # normal speed
        "overhang_2_4_speed": "0",  # normal speed
        "overhang_3_4_speed": "60",  # moderate slowdown
        "overhang_4_4_speed": "40",  # slow for steep overhangs
        # Bridges - TPU bridges well, especially 0.6mm. head_band used 80!
        "bridge_speed": "70",  # much faster than original (40)
        "bridge_no_support": "0",
        # Volumetric flow limit - 0.6mm TPU can push more than 0.4mm
        # At 0.36mm layer × 0.65mm width @ 130mm/s = 30.4 mm³/s (will limit inner)
        # Micro Swiss can sustain ~22-25 mm³/s for TPU 95A
        "filament_max_volumetric_speed": "22",
        # First layer - thicker for 0.6mm nozzle, slightly slower for adhesion
        "initial_layer_print_height": "0.30",  # 50% of nozzle
        "initial_layer_line_width": "0.70",  # wide for adhesion
        "initial_layer_speed": "40",  # slightly faster than 04 HS (40)
        "initial_layer_infill_speed": "60",
        # Support settings (usually off for TPU)
        "enable_support": "0",
        "support_threshold_angle": "45",
        "support_top_z_distance": "0.45",  # more distance for 0.6mm
        "support_object_xy_distance": "0.6",  # more distance for easier removal
        # Z-hop - increased to help strings break cleanly during travel
        # Was 0.15, but larger nozzle + TPU ooze needs more lift
        "z_hop": "0.35",
        # Hole compensation - TPU closes holes slightly, 0.6mm more so
        "xy_hole_compensation": "0.04",  # slightly more than 04 HS (0.02)
        # Walls - need 2 loops minimum for TPU to avoid holes
        # 1 wall loop caused holes even at good temps
        "wall_loops": "2",
        # Infill - low for flexibility (5% works well for elastic parts)
        "sparse_infill_density": "5%",
        "sparse_infill_pattern": "cubic",
        # Adhesion - TPU sticks well, minimal brim
        "brim_type": "outer_only",
        "brim_width": "3",
        "brim_object_gap": "0",
        "elefant_foot_compensation": "0.12",  # more for 0.6mm thicker first layer
        # Wall overlap - slightly higher for TPU layer bonding
        "infill_wall_overlap": "30%",
        # Resolution - can be coarser for 0.6mm
        "resolution": "0.06",
        # === Anti-stringing wipe/seam settings ===
        # Wipe on loops - tuck seam end inward, cleans nozzle before travel
        "wipe_on_loops": "1",
        # Wipe before external - de-retract inside to hide any ooze at seam start
        "wipe_before_external_loop": "1",
        # Role-based wipe speed - wipe at feature speed, not travel speed
        "role_based_wipe_speed": "1",
        # Seam gap - ZERO for TPU to avoid holes at seams
        "seam_gap": "0",
        # Reduce crossing walls - minimizes travel over printed areas
        "reduce_crossing_wall": "1",
    }
)


##### PETG 0.6 mm High Speed Profile #####

petg_06_hs_layer_height_factor = 0.60  # ~0.36mm layers
petg_06_hs_quality_speed = 100
petg_06_hs_inner_speed = 180
petg_06_hs_quality_acceleration = 4000
petg_06_hs_inner_acceleration = 7000
petg_06_hs_quality_jerk = 6
petg_06_hs_inner_jerk = 9

PROCESS_DATA_PETG_06_HS = augment(
    PROCESS_DATA_06_HS_BASE,
    layer_height_factor=petg_06_hs_layer_height_factor,
    quality_speed=petg_06_hs_quality_speed,
    inner_speed=petg_06_hs_inner_speed,
    quality_acceleration=petg_06_hs_quality_acceleration,
    inner_acceleration=petg_06_hs_inner_acceleration,
    quality_jerk=petg_06_hs_quality_jerk,
    inner_jerk=petg_06_hs_inner_jerk,
)

PROCESS_DATA_PETG_06_HS["filament"] = "FilamentPETGMegeMaster"

PROCESS_DATA_PETG_06_HS = augment_with_bed_temperatures(
    PROCESS_DATA_PETG_06_HS, regular_temp=85, initial_temp=90
)

PROCESS_DATA_PETG_06_HS["process_overrides"].update(
    {
        "nozzle_temperature_initial_layer": "255",
        "nozzle_temperature": "250",
        "filament_flow_ratio": "1.0",
        "initial_layer_print_height": "0.30",
        "initial_layer_line_width": "0.70",
        "initial_layer_speed": "30",
        "initial_layer_infill_speed": "50",
        "filament_retraction_length": "1.0",
        "filament_retraction_speed": "30",
        "filament_deretraction_speed": "25",
        "fan_min_speed": "15",
        "fan_max_speed": "40",
        "fan_cooling_layer_time": "12",
        "overhang_fan_speed": "50",
        "infill_wall_overlap": "25%",
        "detect_overhang_wall": "1",
        "enable_overhang_speed": "1",
        "overhang_3_4_speed": "40",
        "overhang_4_4_speed": "25",
        "bridge_speed": "25",
        "filament_max_volumetric_speed": "22",  # PETG flows slower than PLA
        "slow_down_for_layer_cooling": "0",
        "min_layer_time": "6",
        "support_top_z_distance": "0.40",
        "support_object_xy_distance": "0.6",
        "xy_hole_compensation": "0.06",
        "sparse_infill_density": "25%",
        "brim_type": "outer_and_inner",
        "brim_width": "6",
        "elefant_foot_compensation": "0.15",
    }
)


_all_ = [
    "PROCESS_DATA_PLA_06_HS",
    "PROCESS_DATA_TPU_06_HS",
    "PROCESS_DATA_PETG_06_HS",
]

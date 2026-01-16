import copy

from mege_3devops.process_data.mender3.process_data_04_high_precision import *
from mege_3devops.process_data.mender3.process_data_utils import (
    augment,
    augment_with_bed_temperatures,
)

PROCESS_DATA_04_HS_BASE = copy.deepcopy(PROCESS_DATA_04_HP_BASE)

pla_04_hs_layer_height_factor = 0.8
pla_04_hs_quality_speed = 150  # outer walls, top surface - machine can do 500
pla_04_hs_inner_speed = 250  # inner walls, infill - hidden, speed matters
pla_04_hs_quality_acceleration = 5000  # conservative, machine max is 8000
pla_04_hs_inner_acceleration = 8000  # max safe value for Ender 3v3 KE
pla_04_hs_quality_jerk = 8  # conservative jerk
pla_04_hs_inner_jerk = 10  # slightly higher for non-visible

PROCESS_DATA_PLA_04_HS = augment(
    PROCESS_DATA_04_HS_BASE,
    layer_height_factor=pla_04_hs_layer_height_factor,
    quality_speed=pla_04_hs_quality_speed,
    inner_speed=pla_04_hs_inner_speed,
    quality_acceleration=pla_04_hs_quality_acceleration,
    inner_acceleration=pla_04_hs_inner_acceleration,
    quality_jerk=pla_04_hs_quality_jerk,
    inner_jerk=pla_04_hs_inner_jerk,
)

# Override: PLA-specific thermal tuning ONLY.
PROCESS_DATA_PLA_04_HS["process_overrides"].update(
    {
        "nozzle_temperature_initial_layer": "195",
        "nozzle_temperature": "190",
        "filament_flow_ratio": "1.0",
        "fan_min_speed": "100",
        "fan_max_speed": "100",
        "fan_cooling_layer_time": "8",
        "initial_layer_print_height": "0.20",
        "initial_layer_line_width": "0.44",
        "support_interface_top_layers": "1",
        "support_interface_bottom_layers": "1",
        "support_threshold_angle": "55",
        "support_interface_pattern": "rectilinear",
        "support_interface_spacing": "1.2",
        "support_object_xy_distance": "0.6",
        "support_top_z_distance": "0.25",
        # ADHESION IMPROVEMENTS:
        "brim_type": "outer_and_inner",  # Better adhesion than no_brim
        "brim_object_gap": "0",
        "brim_width": "8",  # Wider brim for better hold
        # Slow first layer for good adhesion - speed doesn't matter much for 1 layer
        "initial_layer_speed": "40",
        "initial_layer_infill_speed": "60",
        # Reduce elephant foot compensation for better squish/adhesion
        "elefant_foot_compensation": "0.05",
        # NOTE: Bed temperatures are set via augment_with_bed_temperatures() below
        # Disable layer cooling slowdown - rely on fan cooling instead
        "slow_down_for_layer_cooling": "0",
        # Keep overhang detection but only slow for very steep overhangs
        "detect_overhang_wall": "1",
        "enable_overhang_speed": "1",
        # Aggressive thresholds: only slow for really steep overhangs
        # 0 = use normal speed for this level
        "overhang_1_4_speed": "0",  # 0-25% overhang: normal speed
        "overhang_2_4_speed": "0",  # 25-50% overhang: normal speed
        "overhang_3_4_speed": "50",  # 50-75% overhang: slower for quality
        "overhang_4_4_speed": "30",  # 75-100% overhang: slow for best quality
        # Moderate bridge speed - high quality for the few bridges we have
        "bridge_speed": "25",
        "bridge_no_support": "0",
        # Lower min layer time to prevent forced slowdowns
        "min_layer_time": "5",
    }
)

# Bed temperatures: higher temps for cold basement environment
PROCESS_DATA_PLA_04_HS = augment_with_bed_temperatures(
    PROCESS_DATA_PLA_04_HS, regular_temp=70, initial_temp=75
)


##### TPU profile (0.4 mm, HIGH SPEED)
# Tuned based on successful head_band prints and TPU 06 legacy experience.
# TPU 95A can handle much higher speeds than conservative HP profile.
# Key insight: disable cooling slowdowns - TPU cools fine with fan alone.

tpu_04_hs_layer_height_factor = (
    0.75  # ~0.27mm - thicker layers for speed (head_band used 0.28)
)
tpu_04_hs_quality_speed = 80  # outer walls - validated in head_band
tpu_04_hs_inner_speed = 120  # inner walls, infill - validated in head_band
tpu_04_hs_quality_acceleration = 2500  # validated in head_band
tpu_04_hs_inner_acceleration = 3500  # validated in head_band
tpu_04_hs_quality_jerk = 10  # between head_band (12) and legacy (4)
tpu_04_hs_inner_jerk = 12  # between head_band (15) and legacy (8)

PROCESS_DATA_TPU_04_HS = augment(
    PROCESS_DATA_04_HS_BASE,
    layer_height_factor=tpu_04_hs_layer_height_factor,
    quality_speed=tpu_04_hs_quality_speed,
    inner_speed=tpu_04_hs_inner_speed,
    quality_acceleration=tpu_04_hs_quality_acceleration,
    inner_acceleration=tpu_04_hs_inner_acceleration,
    quality_jerk=tpu_04_hs_quality_jerk,
    inner_jerk=tpu_04_hs_inner_jerk,
)
PROCESS_DATA_TPU_04_HS["filament"] = "FilamenteSunTPU95A"

# Bed temps - same as HP, TPU doesn't need hot bed
PROCESS_DATA_TPU_04_HS = augment_with_bed_temperatures(
    PROCESS_DATA_TPU_04_HS, regular_temp=55, initial_temp=60
)

# TPU High-Speed tuning - consolidated from head_band success + HP base
PROCESS_DATA_TPU_04_HS["process_overrides"].update(
    {
        # Temperature - same as HP, calibrated with temp tower
        "nozzle_temperature_initial_layer": "225",
        "nozzle_temperature": "220",
        # Flow - neutral to slight under-extrusion for cleaner features
        "filament_flow_ratio": "0.98",
        # Retraction - TPU doesn't like aggressive retraction
        "filament_retraction_length": "1.0",  # shorter than HP (1.2) for speed
        "filament_retraction_speed": "25",  # faster than HP (20)
        "filament_deretraction_speed": "25",  # faster than HP (20)
        # Cooling - moderate fan, TPU doesn't need aggressive cooling
        "fan_min_speed": "40",  # slightly higher than HP for speed
        "fan_max_speed": "60",  # slightly higher than HP for speed
        "fan_cooling_layer_time": "12",  # less than HP (18) - faster layers cool faster
        # CRITICAL: Disable cooling slowdown - rely on fan, not speed reduction!
        # This was the key fix in head_band that prevented 10mm/s slowdowns
        "slow_down_for_layer_cooling": "0",
        "min_layer_time": "5",  # much lower than HP (18) - no forced slowdowns
        # CRITICAL: Disable overhang speed reduction for TPU
        # TPU droops less than PLA, and slowdowns kill print time
        "detect_overhang_wall": "0",
        "enable_overhang_speed": "0",
        # But if someone re-enables, set reasonable overhang speeds
        "overhang_1_4_speed": "0",  # normal speed
        "overhang_2_4_speed": "0",  # normal speed
        "overhang_3_4_speed": "50",  # moderate slowdown
        "overhang_4_4_speed": "35",  # slow for steep overhangs
        # Bridges - TPU bridges okay, don't need to crawl
        "bridge_speed": "50",  # much faster than HP default
        "bridge_no_support": "0",
        # Volumetric flow limit - TPU 95A can handle 10-15 mm³/s easily
        # With 0.27mm layer × 0.4mm width: 15 mm³/s → ~139 mm/s max
        "filament_max_volumetric_speed": "15",
        # First layer - slower for adhesion, TPU sticks well anyway
        "initial_layer_speed": "40",
        "initial_layer_infill_speed": "60",
        "initial_layer_print_height": "0.25",  # slightly thicker for adhesion
        "initial_layer_line_width": "0.46",  # slightly wider for adhesion
        # Support settings (if enabled)
        "enable_support": "0",  # default off for TPU
        "support_threshold_angle": "45",
        "support_top_z_distance": "0.4",
        "support_object_xy_distance": "0.5",
        # Z-hop - minimal, TPU doesn't need much
        "z_hop": "0.15",  # reduced from HP (0.2)
        # Hole compensation - TPU closes holes slightly
        "xy_hole_compensation": "0.02",
        # Infill - TPU parts often want low infill for flexibility
        "sparse_infill_density": "10%",
        # Adhesion - TPU sticks well, minimal brim
        "brim_type": "outer_only",
        "brim_width": "3",
        "brim_object_gap": "0",
        "elefant_foot_compensation": "0.1",
    }
)


##### PETG 0.4 mm High Speed Profile #####
# PETG Hyper series can print fast, but not quite as fast as PLA
# Needs higher temps, less cooling, hot bed

petg_04_hs_layer_height_factor = 0.7  # ~0.25 mm layer height for speed
petg_04_hs_quality_speed = 100  # outer walls - PETG is more viscous than PLA
petg_04_hs_inner_speed = 180  # inner walls, infill

petg_04_hs_quality_acceleration = 4000  # slightly lower than PLA
petg_04_hs_inner_acceleration = 7000

petg_04_hs_quality_jerk = 6
petg_04_hs_inner_jerk = 9


PROCESS_DATA_PETG_04_HS = augment(
    PROCESS_DATA_04_HS_BASE,
    layer_height_factor=petg_04_hs_layer_height_factor,
    quality_speed=petg_04_hs_quality_speed,
    inner_speed=petg_04_hs_inner_speed,
    quality_acceleration=petg_04_hs_quality_acceleration,
    inner_acceleration=petg_04_hs_inner_acceleration,
    quality_jerk=petg_04_hs_quality_jerk,
    inner_jerk=petg_04_hs_inner_jerk,
)

PROCESS_DATA_PETG_04_HS["filament"] = "FilamentPETGMegeMaster"

# Override: PETG-specific tuning for high-speed
PROCESS_DATA_PETG_04_HS["process_overrides"].update(
    {
        # Higher temps for flow at speed
        "nozzle_temperature_initial_layer": "250",
        "nozzle_temperature": "245",
        # Flow - slight over-extrusion helps at speed
        "filament_flow_ratio": "1.0",
        # First layer - slower for adhesion (PETG is finicky)
        "initial_layer_print_height": "0.25",
        "initial_layer_line_width": "0.50",
        "initial_layer_speed": "30",
        "initial_layer_infill_speed": "40",
        # PETG retraction - slightly longer & faster to reduce stringing at speed
        "filament_retraction_length": "0.9",  # HP uses 0.8, slightly more for speed
        "filament_retraction_speed": "30",  # HP uses 25
        "filament_deretraction_speed": "25",  # HP uses 20
        # Cooling - keep conservative like HP profile to prevent warping
        "fan_min_speed": "15",  # same as HP - PETG warps with too much fan
        "fan_max_speed": "40",  # slightly more than HP (35) for speed
        "fan_cooling_layer_time": "12",  # HP uses 10
        "overhang_fan_speed": "50",  # HP uses 40, slightly more for speed
        # NOTE: Bed temperatures are set via augment_with_bed_temperatures() below
        # PETG specific
        "infill_wall_overlap": "25%",  # slightly more overlap for layer bonding at speed
        # Overhang handling - PETG droops more than PLA
        "detect_overhang_wall": "1",
        "enable_overhang_speed": "1",
        "overhang_1_4_speed": "0",  # normal speed
        "overhang_2_4_speed": "0",  # normal speed
        "overhang_3_4_speed": "40",  # slow down earlier than PLA
        "overhang_4_4_speed": "25",  # quite slow for steep overhangs
        # Bridges - PETG bridges poorly, go slow
        "bridge_speed": "20",
        "bridge_no_support": "0",
        # Support tuning - PETG sticks to supports, need more distance
        "support_top_z_distance": "0.35",
        "support_object_xy_distance": "0.5",
        "support_interface_spacing": "1.0",
        # Hole compensation (PETG shrinks slightly)
        "xy_hole_compensation": "0.04",
        # Infill
        "sparse_infill_density": "25%",
        # Layer cooling
        "slow_down_for_layer_cooling": "0",  # rely on fan, not slowdown
        "min_layer_time": "6",
        # Adhesion - PETG needs good first layer
        "brim_type": "outer_and_inner",
        "brim_width": "6",
        "brim_object_gap": "0",
        "elefant_foot_compensation": "0.1",  # PETG squishes more
    }
)

# Bed temperatures: PETG needs hot bed, even hotter for cold basement
PROCESS_DATA_PETG_04_HS = augment_with_bed_temperatures(
    PROCESS_DATA_PETG_04_HS, regular_temp=85, initial_temp=90
)


##### PETG-CF 0.4 mm High Speed Profile #####
# PETG-CF: higher viscosity, lower ooze/stringing, stiffer & more brittle
# Strategy vs PETG: hotter, slower, slightly fatter lines, gentler cooling, softer retraction

petgcf_04_hs_layer_height_factor = 0.72  # ~0.26 mm - keep flow channels generous
petgcf_04_hs_quality_speed = 70  # slower outer walls for layer bonding
petgcf_04_hs_inner_speed = 130  # ~30% slower than PETG to respect flow limits

petgcf_04_hs_quality_acceleration = 3500
petgcf_04_hs_inner_acceleration = 6000

petgcf_04_hs_quality_jerk = 5
petgcf_04_hs_inner_jerk = 8


PROCESS_DATA_PETGCF_04_HS = augment(
    PROCESS_DATA_04_HS_BASE,
    layer_height_factor=petgcf_04_hs_layer_height_factor,
    quality_speed=petgcf_04_hs_quality_speed,
    inner_speed=petgcf_04_hs_inner_speed,
    quality_acceleration=petgcf_04_hs_quality_acceleration,
    inner_acceleration=petgcf_04_hs_inner_acceleration,
    quality_jerk=petgcf_04_hs_quality_jerk,
    inner_jerk=petgcf_04_hs_inner_jerk,
)

PROCESS_DATA_PETGCF_04_HS["filament"] = "FilamentPETGCF"

# Bed temperatures: CF shrinks a bit more - keep PETG temps
PROCESS_DATA_PETGCF_04_HS = augment_with_bed_temperatures(
    PROCESS_DATA_PETGCF_04_HS, regular_temp=85, initial_temp=90
)

# Override: PETG-CF specific tuning
PROCESS_DATA_PETGCF_04_HS["process_overrides"].update(
    {
        # Hotter for CF-filled viscosity
        "nozzle_temperature_initial_layer": "265",
        "nozzle_temperature": "260",
        # Slightly fuller lines to avoid starvation
        "filament_flow_ratio": "1.02",
        # First layer: thicker/wider for grip with stiffer filament
        "initial_layer_print_height": "0.26",
        "initial_layer_line_width": "0.52",
        "initial_layer_speed": "28",
        "initial_layer_infill_speed": "36",
        # Retraction: CF oozes less - shorten/slow to avoid pressure loss and wear
        "filament_retraction_length": "0.7",
        "filament_retraction_speed": "26",
        "filament_deretraction_speed": "22",
        # Cooling: gentler to preserve layer adhesion (CF runs crisp already)
        "fan_min_speed": "10",
        "fan_max_speed": "30",
        "fan_cooling_layer_time": "10",
        "overhang_fan_speed": "35",
        # Limit flow; CF hates high back-pressure
        "filament_max_volumetric_speed": "9",
        # Overhang/bridge handling: CF bridges cleaner, keep moderate slowdowns
        "detect_overhang_wall": "1",
        "enable_overhang_speed": "1",
        "overhang_1_4_speed": "0",
        "overhang_2_4_speed": "0",
        "overhang_3_4_speed": "45",
        "overhang_4_4_speed": "30",
        "bridge_speed": "22",
        "bridge_no_support": "0",
        # Support tuning - same clearances as PETG
        "support_top_z_distance": "0.35",
        "support_object_xy_distance": "0.5",
        "support_interface_spacing": "1.0",
        # Dimensional tweaks
        "xy_hole_compensation": "0.04",
        # Infill - slightly denser for stiff CF parts
        "sparse_infill_density": "30%",
        # Layer cooling throttling off; rely on fan curve above
        "slow_down_for_layer_cooling": "0",
        "min_layer_time": "6",
        # Adhesion
        "brim_type": "outer_and_inner",
        "brim_width": "6",
        "brim_object_gap": "0",
        "elefant_foot_compensation": "0.1",
    }
)


##### PLA-CF 0.4 mm High Speed Profile #####
# Ported from legacy 0.6mm steel nozzle PROCESS_DATA_06_PLACF (moebius_placf.FCMacro)
# Adapted for 0.4mm nozzle with Microswiss FlowTech hotend (hardened steel)
# PLA-CF: abrasive, more viscous, needs higher temps, moderate speeds
# Key: reduced retraction to minimize wear, higher temps for CF-filled flow

placf_04_hs_layer_height_factor = 0.6  # ~0.22mm - slightly thicker for strength
placf_04_hs_quality_speed = 80  # outer walls - CF more viscous than plain PLA
placf_04_hs_inner_speed = (
    140  # inner walls, infill - faster than old 70, but conservative
)
placf_04_hs_quality_acceleration = 3500  # lower than PLA due to higher viscosity
placf_04_hs_inner_acceleration = 6000  # same as legacy CF profile
placf_04_hs_quality_jerk = 6  # conservative for quality
placf_04_hs_inner_jerk = 10  # same as legacy CF profile

PROCESS_DATA_PLACF_04_HS = augment(
    PROCESS_DATA_04_HS_BASE,
    layer_height_factor=placf_04_hs_layer_height_factor,
    quality_speed=placf_04_hs_quality_speed,
    inner_speed=placf_04_hs_inner_speed,
    quality_acceleration=placf_04_hs_quality_acceleration,
    inner_acceleration=placf_04_hs_inner_acceleration,
    quality_jerk=placf_04_hs_quality_jerk,
    inner_jerk=placf_04_hs_inner_jerk,
)

PROCESS_DATA_PLACF_04_HS["filament"] = "FilamentPLACF"

# Bed temperatures: PLA-CF same as regular PLA, maybe slightly lower
PROCESS_DATA_PLACF_04_HS = augment_with_bed_temperatures(
    PROCESS_DATA_PLACF_04_HS, regular_temp=65, initial_temp=70
)

# Override: PLA-CF specific tuning - adapted from legacy 0.6mm profile
PROCESS_DATA_PLACF_04_HS["process_overrides"].update(
    {
        # Temperature - higher than plain PLA for CF flow (legacy used 230/234)
        # FlowTech hotend runs slightly hotter than stock Creality
        "nozzle_temperature_initial_layer": "235",
        "nozzle_temperature": "230",
        # Flow - neutral, CF already increases friction
        "filament_flow_ratio": "1.0",
        # First layer - slower for adhesion, CF is heavier
        "initial_layer_print_height": "0.22",
        "initial_layer_line_width": "0.46",
        "initial_layer_speed": "35",
        "initial_layer_infill_speed": "50",
        # Retraction - CRITICAL: reduce wear on abrasive filament (legacy used 1.0/30/25)
        # FlowTech has shorter melt zone, can use slightly shorter retraction
        "filament_retraction_length": "0.8",
        "filament_retraction_speed": "25",
        "filament_deretraction_speed": "20",
        # Cooling - moderate, CF dissipates heat well (legacy: 40-80%)
        "fan_min_speed": "50",
        "fan_max_speed": "85",
        "fan_cooling_layer_time": "10",
        "overhang_fan_speed": "95",
        # Layer cooling - disabled, rely on fan (same pattern as other HS profiles)
        "slow_down_for_layer_cooling": "0",
        "min_layer_time": "6",
        # Overhang handling - CF is stiffer, droops less than plain PLA
        "detect_overhang_wall": "1",
        "enable_overhang_speed": "1",
        "overhang_1_4_speed": "0",  # normal speed
        "overhang_2_4_speed": "0",  # normal speed
        "overhang_3_4_speed": "45",  # CF handles overhangs well
        "overhang_4_4_speed": "28",  # slow for steep overhangs
        # Bridges - CF bridges better than plain PLA due to stiffness
        "bridge_speed": "28",  # same as legacy
        "bridge_no_support": "1",  # legacy setting
        # Support settings - CF is stiff, separates well
        "enable_support": "0",  # default off, CF parts usually designed without
        "support_threshold_angle": "50",  # legacy value
        "support_top_z_distance": "0.28",
        "support_object_xy_distance": "0.5",
        "support_interface_top_layers": "1",
        "support_interface_bottom_layers": "1",
        # Hole/contour compensation - CF shrinks slightly less than plain PLA
        "xy_hole_compensation": "0.04",
        "xy_contour_compensation": "0",
        "elefant_foot_compensation": "0.08",
        # Infill - CF parts often structural, higher density (legacy: 85% cubic)
        "sparse_infill_density": "40%",  # balanced for HS, increase per-part as needed
        "sparse_infill_pattern": "cubic",  # isotropic strength
        # Shell structure - extra for strength (legacy: 3 bottom/top, 2 walls)
        "bottom_shell_layers": "3",
        "top_shell_layers": "3",
        "wall_loops": "2",
        # Quality settings from legacy
        "infill_wall_overlap": "20%",
        "resolution": "0.05",
        # Adhesion - CF is heavier, needs good grip
        "brim_type": "outer_and_inner",
        "brim_width": "6",
        "brim_object_gap": "0",
    }
)


_all_ = [
    "PROCESS_DATA_PLA_04_HS",
    "PROCESS_DATA_TPU_04_HS",
    "PROCESS_DATA_PETG_04_HS",
    "PROCESS_DATA_PETGCF_04_HS",
    "PROCESS_DATA_PLACF_04_HS",
]

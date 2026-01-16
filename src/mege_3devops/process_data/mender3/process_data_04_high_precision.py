import numpy as np

PROCESS_DATA_04_HP_BASE = {
    "filament": "FilamentCrealityPLAHighSpeedTunedForSpeed",
    "process_overrides": {
        ###  BASE high-precision .4 mm setup  ###
        #  – tuned for dimensional accuracy and small features –
        #  – material-specific flow, temps, and fans are to be set later –
        "adaptive_layer_height": "1",  # allow fine layer variation for detail
        "bottom_shell_layers": "3",  # unchanged
        "bridge_line_width": "0.45",  # scale with nozzle size
        "bridge_no_support": "1",
        "bridge_speed": "20",  # slower → cleaner bridges
        "brim_ears_detection_length": "1",
        "brim_ears_max_angle": "125",
        "brim_object_gap": "0",
        "brim_type": "outer_only",
        "brim_width": "4",
        "elefant_foot_compensation": "0.15",  # slightly more for precision parts
        "enable_arc_fitting": "1",
        "enable_support": "0",
        "fan_cooling_layer_time": "30",
        "fan_max_speed": "100",
        "fan_min_speed": "80",
        "filament_deretraction_speed": "30",
        "filament_flow_ratio": "1.0",  # keep neutral; adjust per material later
        "filament_retraction_length": "1.0",  # a bit shorter for tighter path & detail
        "filament_retraction_speed": "35",
        "gap_fill_line_width": "0.40",  # narrower for fine gaps
        "hot_plate_temp_initial_layer": "65",
        "infill_wall_overlap": "20%",  # lower overlap = truer holes
        "initial_layer_line_width": "0.48",
        "initial_layer_print_height": "0.20",
        "inner_wall_line_width": "0.42",  # ~105% of nozzle
        "internal_solid_infill_line_width": "0.42",
        "line_width": "0.42",  # global reference width
        "min_layer_time": "10",  # allow adequate cooling
        "nozzle_diameter": "0.4",  # main change
        "nozzle_temperature_initial_layer": "235",  # placeholder, override in material
        "nozzle_temperature": "230",
        "outer_wall_line_width": "0.40",  # nearly equal to nozzle diameter
        "overhang_fan_speed": "100",
        "resolution": "0.03",  # finer geometry resolution
        "slow_down_for_layer_cooling": "1",
        "solid_infill_line_width": "0.42",
        "sparse_infill_density": "20%",  # unchanged
        "sparse_infill_line_width": "0.45",
        "sparse_infill_pattern": "cubic",
        "support_base_pattern_spacing": "2.5",
        "support_base_pattern": "rectilinear",
        "support_bottom_interface_spacing": "0.5",
        "support_interface_line_width": "0.4",
        "support_line_width": "0.42",
        "support_object_first_layer_gap": "0.25",
        "support_object_xy_distance": "0.35",
        "support_on_build_plate_only": "1",
        "support_remove_small_overhang": "1",
        "support_style": "rectilinear",
        "support_threshold_angle": "60",
        "support_threshold_overlap": "50%",
        "support_top_z_distance": "0.2",
        "support_type": "normal(auto)",
        "thin_wall_line_width": "0.40",  # for single-extrusion features
        "top_shell_layers": "4",  # one more for smoother top finish
        "top_surface_line_width": "0.40",
        "wall_loops": "2",  # double perimeters for accuracy & strength
        "xy_contour_compensation": "0",
        "xy_hole_compensation": "0.05",  # keep; fine-tune per material later
    },
}


def augment_with_speeds(process_data, quality_speed, inner_speed):
    pd = dict(process_data)
    pd["process_overrides"] = dict(pd.get("process_overrides", {}))
    pd["process_overrides"]["external_perimeter_speed"] = f"{quality_speed}"
    pd["process_overrides"]["initial_layer_infill_speed"] = f"{quality_speed}"
    pd["process_overrides"]["initial_layer_speed"] = f"{quality_speed}"
    pd["process_overrides"]["inner_wall_speed"] = f"{inner_speed}"
    pd["process_overrides"]["internal_solid_infill_speed"] = f"{inner_speed}"
    pd["process_overrides"]["gap_fill_speed"] = f"{inner_speed}"
    pd["process_overrides"]["gap_infill_speed"] = f"{inner_speed}"
    pd["process_overrides"]["solid_infill_speed"] = f"{inner_speed}"
    pd["process_overrides"]["sparse_infill_speed"] = f"{inner_speed}"
    pd["process_overrides"]["support_interface_speed"] = f"{inner_speed}"
    pd["process_overrides"]["support_speed"] = f"{inner_speed}"
    pd["process_overrides"]["top_surface_speed"] = f"{quality_speed}"
    pd["process_overrides"]["outer_wall_speed"] = f"{quality_speed}"
    return pd


def augment_with_accelerations(process_data, quality_acceleration, inner_acceleration):
    pd = dict(process_data)
    pd["process_overrides"] = dict(pd.get("process_overrides", {}))
    pd["process_overrides"]["initial_layer_acceleration"] = f"{quality_acceleration}"
    pd["process_overrides"]["outer_wall_acceleration"] = f"{quality_acceleration}"
    pd["process_overrides"]["top_surface_acceleration"] = f"{quality_acceleration}"
    pd["process_overrides"]["inner_wall_acceleration"] = f"{inner_acceleration}"
    pd["process_overrides"]["solid_infill_acceleration"] = f"{inner_acceleration}"
    pd["process_overrides"]["sparse_infill_acceleration"] = f"{inner_acceleration}"
    pd["process_overrides"]["support_acceleration"] = f"{inner_acceleration}"
    pd["process_overrides"]["support_interface_acceleration"] = f"{inner_acceleration}"
    return pd


def augment_with_jerks(process_data, quality_jerk, inner_jerk):
    pd = dict(process_data)
    pd["process_overrides"] = dict(pd.get("process_overrides", {}))
    pd["process_overrides"]["initial_layer_jerk"] = f"{quality_jerk}"
    pd["process_overrides"]["outer_wall_jerk"] = f"{quality_jerk}"
    pd["process_overrides"]["top_surface_jerk"] = f"{quality_jerk}"
    pd["process_overrides"]["inner_wall_jerk"] = f"{inner_jerk}"
    pd["process_overrides"]["solid_infill_jerk"] = f"{inner_jerk}"
    pd["process_overrides"]["sparse_infill_jerk"] = f"{inner_jerk}"
    pd["process_overrides"]["support_interface_jerk"] = f"{inner_jerk}"
    pd["process_overrides"]["support_jerk"] = f"{inner_jerk}"
    return pd


def augment_with_layer_height(process_data, layer_height_factor):
    pd = dict(process_data)
    pd["process_overrides"] = dict(pd.get("process_overrides", {}))
    nozzle_diameter = float(pd["process_overrides"]["nozzle_diameter"])
    min_layer_height = nozzle_diameter * 0.25
    max_layer_height = nozzle_diameter * 0.75
    layer_height = np.round(
        min_layer_height + (max_layer_height - min_layer_height) * layer_height_factor,
        2,
    )
    pd["process_overrides"]["max_layer_height"] = f"{max_layer_height}"
    pd["process_overrides"]["min_layer_height"] = f"{min_layer_height}"
    pd["process_overrides"]["layer_height"] = f"{layer_height}"
    return pd


def augment_with_bed_temperatures(process_data, regular_temp, initial_temp):
    """Set consistent bed temperatures across all plate types"""
    pd = dict(process_data)
    pd["process_overrides"] = dict(pd.get("process_overrides", {}))

    # Set temperatures for all plate types to ensure consistency
    pd["process_overrides"]["hot_plate_temp"] = f"{regular_temp}"
    pd["process_overrides"]["hot_plate_temp_initial_layer"] = f"{initial_temp}"
    pd["process_overrides"]["cool_plate_temp"] = f"{regular_temp}"
    pd["process_overrides"]["cool_plate_temp_initial_layer"] = f"{initial_temp}"
    pd["process_overrides"]["eng_plate_temp"] = f"{regular_temp}"
    pd["process_overrides"]["eng_plate_temp_initial_layer"] = f"{initial_temp}"
    pd["process_overrides"]["textured_plate_temp"] = f"{regular_temp}"
    pd["process_overrides"]["textured_plate_temp_initial_layer"] = f"{initial_temp}"

    return pd


def augment(
    process_data,
    layer_height_factor,
    quality_speed,
    inner_speed,
    quality_acceleration,
    inner_acceleration,
    quality_jerk,
    inner_jerk,
):
    pd = augment_with_layer_height(process_data, layer_height_factor)
    pd = augment_with_speeds(pd, quality_speed, inner_speed)
    pd = augment_with_accelerations(pd, quality_acceleration, inner_acceleration)
    pd = augment_with_jerks(pd, quality_jerk, inner_jerk)
    return pd


PROCESS_DATA_PLA_04_HP = augment(
    PROCESS_DATA_04_HP_BASE,
    layer_height_factor=0.45,  # ~0.14 mm layers on a 0.4 nozzle
    quality_speed=20,  # slow, crisp walls
    inner_speed=30,
    quality_acceleration=1200,
    inner_acceleration=2500,
    quality_jerk=5,
    inner_jerk=8,
)

# Override: PLA-specific thermal tuning ONLY.
PROCESS_DATA_PLA_04_HP["process_overrides"].update(
    {
        "nozzle_temperature_initial_layer": "195",
        "nozzle_temperature": "190",
        "filament_flow_ratio": "1.0",
        "fan_min_speed": "100",
        "fan_max_speed": "100",
        "fan_cooling_layer_time": "8",
        "initial_layer_print_height": "0.20",  # thin, crisp adhesion
        "initial_layer_line_width": "0.44",
        "support_interface_top_layers": "1",
        "support_interface_bottom_layers": "1",
        "support_threshold_angle": "55",
        "support_interface_pattern": "rectilinear",
        "support_interface_spacing": "1.2",
        "support_object_xy_distance": "0.6",
        "support_top_z_distance": "0.25",
    }
)

PROCESS_DATA_PLA_04_HP = augment_with_bed_temperatures(
    PROCESS_DATA_PLA_04_HP, regular_temp=60, initial_temp=65
)


##### TPU profile

##### TPU profile (0.4 mm, high precision-ish, conservative speed)

tpu_04_hp_layer_height_factor = 0.45  # ~0.19 mm layer height
tpu_04_hp_quality_speed = 20  # slow & safe for TPU
tpu_04_hp_inner_speed = 25  # slightly faster inside
tpu_04_hp_quality_acceleration = 800  # very gentle
tpu_04_hp_inner_acceleration = 1500
tpu_04_hp_quality_jerk = 3
tpu_04_hp_inner_jerk = 6

PROCESS_DATA_TPU_04_HP = augment(
    PROCESS_DATA_04_HP_BASE,
    layer_height_factor=tpu_04_hp_layer_height_factor,
    quality_speed=tpu_04_hp_quality_speed,
    inner_speed=tpu_04_hp_inner_speed,
    quality_acceleration=tpu_04_hp_quality_acceleration,
    inner_acceleration=tpu_04_hp_inner_acceleration,
    quality_jerk=tpu_04_hp_quality_jerk,
    inner_jerk=tpu_04_hp_inner_jerk,
)
PROCESS_DATA_TPU_04_HP["filament"] = "FilamenteSunTPU95A"

# Bed temps:
PROCESS_DATA_TPU_04_HP = augment_with_bed_temperatures(
    PROCESS_DATA_TPU_04_HP, regular_temp=55, initial_temp=60
)

# TPU-specific tuning ONLY
PROCESS_DATA_TPU_04_HP["process_overrides"].update(
    {
        "nozzle_temperature_initial_layer": "225",
        "nozzle_temperature": "220",  # calibratred with Filamente Sun TPU 95A, temperature tower
        "filament_flow_ratio": "0.98",  # tiny under-extrusion for clean features
        "filament_retraction_length": "1.2",
        "filament_retraction_speed": "20",
        "filament_deretraction_speed": "20",
        "fan_min_speed": "35",
        "fan_max_speed": "55",
        "fan_cooling_layer_time": "18",  # enough to cool TPU on tiny parts
        "min_layer_time": "18",
        "enable_support": "1",
        "support_threshold_angle": "45",
        "support_top_z_distance": "0.4",
        "support_object_xy_distance": "0.5",
        "z_hop": "0.2",  # safer for smeary TPU on small parts
        # TPU tends to close holes; keep a bit of positive XY opening, or 0 if you prefer
        "xy_hole_compensation": "0.02",
        # infill specific:
        "sparse_infill_density": "10%",
        # line widths, wall_loops, etc. are inherited from HP base on purpose
    }
)


##### PETG 0.4 mm High Precision Profile #####

petg_04_fast_layer_height_factor = 0.25  # ~0.15 mm layer height
petg_04_fast_quality_speed = 25
petg_04_fast_inner_speed = 35

petg_04_fast_quality_acceleration = 1200
petg_04_fast_inner_acceleration = 2500

petg_04_fast_quality_jerk = 4
petg_04_fast_inner_jerk = 8


PROCESS_DATA_PETG_04_HP = augment(
    PROCESS_DATA_04_HP_BASE,
    layer_height_factor=petg_04_fast_layer_height_factor,
    quality_speed=petg_04_fast_quality_speed,
    inner_speed=petg_04_fast_inner_speed,
    quality_acceleration=petg_04_fast_quality_acceleration,
    inner_acceleration=petg_04_fast_inner_acceleration,
    quality_jerk=petg_04_fast_quality_jerk,
    inner_jerk=petg_04_fast_inner_jerk,
)

PROCESS_DATA_PETG_04_HP["filament"] = "FilamentPETGMegeMaster"


# Bed temperatures — PETG likes a hot bed for adhesion
PROCESS_DATA_PETG_04_HP = augment_with_bed_temperatures(
    PROCESS_DATA_PETG_04_HP, regular_temp=83, initial_temp=83
)


PROCESS_DATA_PETG_04_HP["process_overrides"].update(
    {
        # PETG temperatures
        "nozzle_temperature_initial_layer": "235",
        "nozzle_temperature": "230",
        # Flow
        "filament_flow_ratio": "0.98",
        # First layer
        "initial_layer_print_height": "0.20",
        "initial_layer_line_width": "0.50",
        # PETG retraction
        "filament_retraction_length": "0.8",
        "filament_retraction_speed": "25",
        "filament_deretraction_speed": "20",
        # Cooling
        "fan_min_speed": "15",
        "fan_max_speed": "35",
        "fan_cooling_layer_time": "10",
        # Keep BASE geometry
        # (inner/outer wall widths from HP base)
        # PETG specific
        "infill_wall_overlap": "20%",
        "overhang_fan_speed": "40",
        # Support tuning for PETG
        "support_top_z_distance": "0.30",
        "support_object_xy_distance": "0.35",
        # Slight hole compensation (PETG shrinks)
        "xy_hole_compensation": "0.04",
        # Infill
        "sparse_infill_density": "30%",
    }
)


_all_ = [
    "PROCESS_DATA_PLA_04_HP",
    "PROCESS_DATA_TPU_04_HP",
    "PROCESS_DATA_PETG_04_HP",
]


def create_hole_cylinder_calibration():
    """
    Create a calibration part with cylinders of different diameters
    to test hole accuracy and dimensional precision.
    """
    from shellforgepy.simple import (
        Alignment,
        PartCollector,
        align,
        create_box,
        create_cylinder,
        create_text_object,
        get_bounding_box_center,
        translate,
    )

    diameters = [2, 4, 8]
    base_thickness = 2
    post_height = 4
    x_gap = 10
    y_gap = 6  # Increased from 4 to 6 for better spacing
    border = 3
    font_size = 7  # ShellForgePy text size is in mm, much more reasonable
    text_x_offset = -3
    text_y_offset = 2.5

    base_width = sum(diameters) + (len(diameters) - 1) * x_gap + 2 * border
    base_height = 3 * max(diameters) + 4 * y_gap + 2 * border  # Space for 3 rows

    # Create base plate
    base = create_box(base_width, base_height, base_thickness)
    original_base = base  # Keep reference to original base for alignment

    # Collect all text objects for cutting
    text_collector = PartCollector()

    cur_x = border

    for i, d in enumerate(diameters):
        cur_x += d / 2

        # Create cylinder post (do this first to get position reference)
        x = cur_x
        y = base_height - border - max(diameters) / 2
        z = base_thickness

        post = create_cylinder(d / 2, post_height)
        post = translate(x, y, z)(post)

        # Add text label for diameter - centered on the cylinder in x-axis
        try:
            text_obj = create_text_object(
                str(d), size=font_size, thickness=base_thickness + 2
            )  # Cut all the way through
            bbox_center = get_bounding_box_center(text_obj)
            text_obj = translate(-bbox_center[0], -bbox_center[1], -bbox_center[2])(
                text_obj
            )

            # Center text in x-axis to the cylinder, align to original base
            text_obj = align(
                text_obj, post, Alignment.CENTER, axes=[0]
            )  # x-axis centering
            text_obj = align(text_obj, original_base, Alignment.FRONT)
            text_obj = align(
                text_obj, original_base, Alignment.CENTER, axes=[2]
            )  # Center in z-axis through the base
            text_obj = translate(0, text_y_offset, 0)(text_obj)  # Only y offset needed

            # Collect the text for cutting instead of fusing
            text_collector = text_collector.fuse(text_obj)
        except:
            # If text creation fails, continue without text
            pass

        base = base.fuse(post)

        # Create test hole (second row)
        y -= max(diameters) + y_gap
        hole_cutter = create_cylinder(d / 2, base_thickness + 1)  # +1 for complete cut
        hole_cutter = translate(x, y, -0.5)(hole_cutter)  # -0.5 to ensure clean cut
        base = base.cut(hole_cutter)

        # Create test square (third row)
        y -= max(diameters) + y_gap
        square_cutter = create_box(
            d, d, base_thickness + 1
        )  # Square with side length = diameter
        square_cutter = translate(x - d / 2, y - d / 2, -0.5)(
            square_cutter
        )  # Center the square
        base = base.cut(square_cutter)

        cur_x += d / 2 + x_gap

    # Cut out the text from the base
    base = base.cut(text_collector)

    return base


def main():

    import logging
    import os

    from shellforgepy.simple import PartList, arrange_and_export

    material = os.getenv("SHELLFORGEPY_MATERIAL", "PLA").upper()

    logging.basicConfig(level=logging.INFO)

    parts = PartList()

    _logger = logging.getLogger(__name__)

    # Create hole/cylinder calibration part for high precision testing
    calibration_part = create_hole_cylinder_calibration()

    parts.add(
        calibration_part,
        f"hole_cyl_calibration_{material.lower()}",
        skip_in_production=False,
    )
    _logger.info("Added hole/cylinder calibration part to parts list.")

    if material == "PLA":
        process_data = PROCESS_DATA_PLA_04_HP
    elif material == "TPU":
        process_data = PROCESS_DATA_TPU_04_HP
    elif material == "PETG":
        process_data = PROCESS_DATA_PETG_04_HP
    else:
        _logger.warning(f"Unknown material {material}, defaulting to PLA")
        process_data = PROCESS_DATA_PLA_04_HP

    arrange_and_export(
        parts.as_list(),
        script_file=__file__,
        prod=True,
        process_data=process_data,
    )


if __name__ == "__main__":
    main()

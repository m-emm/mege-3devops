import numpy as np


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

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_logger = logging.getLogger(__name__)
_PROCESS_SPECS_DIR = Path(__file__).with_name("process_specs")


@dataclass(frozen=True)
class PrinterSpec:
    printer_id: str
    max_speed_xy_mm_s: float
    max_accel_xy_mm_s2: float
    max_jerk_xy_mm_s: float
    hotend_base_flow_mm3_s: float
    min_layer_height_ratio: float = 0.25
    max_layer_height_ratio: float = 0.75


@dataclass(frozen=True)
class NozzleSetup:
    diameter_mm: float
    hardened: bool
    high_flow: bool


@dataclass(frozen=True)
class MaterialSpec:
    material_id: str
    family: str
    nozzle_temp_c: float
    cooling_factor: float
    warp_factor: float
    stringing_factor: float
    support_stickiness: float
    flow_factor: float
    base_volumetric_flow_mm3_s: float | None = None
    bed_temp_c: float | None = None
    initial_bed_temp_c: float | None = None


@dataclass(frozen=True)
class IntentSpec:
    strength_factor: float
    quality_factor: float


DEFAULT_PRINTER = PrinterSpec(
    printer_id="megemaster",
    max_speed_xy_mm_s=500.0,
    max_accel_xy_mm_s2=8000.0,
    max_jerk_xy_mm_s=10.0,
    hotend_base_flow_mm3_s=15.0,
)

_FAMILY_RULES = {
    "PLA": {
        "outer_speed_ceiling": 200.0,
        "inner_speed_multiplier": 1.7,
        "outer_accel_ceiling": 5000.0,
        "outer_jerk_ceiling": 8.0,
        "inner_jerk_ceiling": 10.0,
        "bridge_speed_factor": 0.60,
        "bridge_speed_cap_at_04": 25.0,
        "bridge_speed_cap_gain_per_mm": 20.0,
        "retraction_length_factor": 2.5,
        "retraction_speed": 35.0,
        "deretraction_speed": 30.0,
        "infill_wall_overlap_pct": 20.0,
        "support_threshold_angle": 25.0,
        "support_interface_spacing": 1.2,
        "initial_layer_speed": 20.0,
        "initial_layer_infill_speed": 20.0,
        "overhang_fan_multiplier": 1.0,
        "fan_cooling_layer_time": 8.0,
        "slow_down_for_layer_cooling": 1.0,
        "brim_type": "outer_only",
        "brim_width": 4.0,
        "brim_object_gap": 0.0,
        "pressure_advance_base": 0.020,
        "pressure_advance_nozzle_gain_per_02mm": 0.010,
        "pressure_advance_throughput_gain": 0.005,
        "pressure_advance_high_flow_bonus": 0.005,
        "pressure_advance_max": 0.060,
    },
    "TPU": {
        "outer_speed_ceiling": 130.0,
        "inner_speed_multiplier": 1.5,
        "outer_accel_ceiling": 4000.0,
        "outer_jerk_ceiling": 10.0,
        "inner_jerk_ceiling": 12.0,
        "bridge_speed_factor": 0.60,
        "bridge_speed_cap_at_04": 50.0,
        "bridge_speed_cap_gain_per_mm": 30.0,
        "retraction_length_factor": 2.5,
        "retraction_speed": 25.0,
        "deretraction_speed": 25.0,
        "infill_wall_overlap_pct": 30.0,
        "support_threshold_angle": 25.0,
        "support_interface_spacing": 1.0,
        "initial_layer_speed": 40.0,
        "initial_layer_infill_speed": 60.0,
        "overhang_fan_multiplier": 2.0,
        "fan_cooling_layer_time": 12.0,
        "slow_down_for_layer_cooling": 0.0,
        "brim_type": "outer_only",
        "brim_width": 3.0,
        "brim_object_gap": 0.0,
        "pressure_advance_base": 0.010,
        "pressure_advance_nozzle_gain_per_02mm": 0.005,
        "pressure_advance_throughput_gain": 0.0025,
        "pressure_advance_high_flow_bonus": 0.0025,
        "pressure_advance_max": 0.030,
    },
    "PETG_CF": {
        "outer_speed_ceiling": 180.0,
        "inner_speed_multiplier": 1.75,
        "outer_accel_ceiling": 7000.0,
        "outer_jerk_ceiling": 6.0,
        "inner_jerk_ceiling": 9.0,
        "bridge_speed_factor": 0.22,
        "bridge_speed_cap_at_04": 30.0,
        "bridge_speed_cap_gain_per_mm": 20.0,
        "retraction_length_factor": 1.33,
        "retraction_speed": 35.0,
        "deretraction_speed": 30.0,
        "infill_wall_overlap_pct": 20.0,
        "support_threshold_angle": 25.0,
        "support_interface_spacing": 1.0,
        "initial_layer_speed": 25.0,
        "initial_layer_infill_speed": 35.0,
        "overhang_fan_multiplier": 1.17,
        "fan_cooling_layer_time": 10.0,
        "slow_down_for_layer_cooling": 0.0,
        "brim_type": "no_brim",
        "brim_width": 6.0,
        "brim_object_gap": 0.0,
        "pressure_advance_base": 0.015,
        "pressure_advance_nozzle_gain_per_02mm": 0.0075,
        "pressure_advance_throughput_gain": 0.005,
        "pressure_advance_high_flow_bonus": 0.005,
        "pressure_advance_max": 0.045,
    },
}


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _round_step(value: float, step: float) -> float:
    return round(value / step) * step


def _format_number(value: float, digits: int = 2) -> str:
    rounded = round(value, digits)
    if abs(rounded - int(rounded)) < 1e-9:
        return str(int(rounded))
    return f"{rounded:.{digits}f}"


def _format_percent(value: float) -> str:
    return f"{int(round(value))}%"


def _strength_shell_count(strength: float) -> int:
    # Quadratic strength theory anchored to:
    # 0.0 -> 1 shell
    # 0.5 -> 2 shells
    # 1.0 -> 4 shells
    shell_count = round(2.0 * strength * strength + strength + 1.0)
    return int(_clamp(shell_count, 1, 4))


def _pressure_advance_value(
    *,
    material_family: str,
    nozzle: NozzleSetup,
    throughput: float,
    family_rules: dict[str, float | str],
) -> float:
    base = float(family_rules["pressure_advance_base"])
    nozzle_gain = float(family_rules["pressure_advance_nozzle_gain_per_02mm"])
    throughput_gain = float(family_rules["pressure_advance_throughput_gain"])
    high_flow_bonus = float(family_rules["pressure_advance_high_flow_bonus"])
    max_value = float(family_rules["pressure_advance_max"])

    pressure_advance = base
    pressure_advance += nozzle_gain * max(0.0, nozzle.diameter_mm - 0.4) / 0.2
    pressure_advance += throughput_gain * throughput
    pressure_advance += high_flow_bonus if nozzle.high_flow else 0.0
    pressure_advance = _clamp(pressure_advance, base, max_value)
    pressure_advance = _round_step(pressure_advance, 0.005)
    _logger.info(
        "pressure advance theory: family=%s base=%.3f nozzle_gain=%.4f throughput_gain=%.4f high_flow_bonus=%.4f nozzle_diameter=%.2f throughput=%.3f high_flow=%s -> pressure_advance=%.3f",
        material_family,
        base,
        nozzle_gain,
        throughput_gain,
        high_flow_bonus,
        nozzle.diameter_mm,
        throughput,
        nozzle.high_flow,
        pressure_advance,
    )
    return pressure_advance


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    _logger.info("loading process spec yaml: %s", path)
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    _logger.info("loaded process spec yaml %s: %s", path.name, data)
    return data


def load_printer_spec(printer_id: str) -> PrinterSpec:
    path = _PROCESS_SPECS_DIR / "printers" / f"{printer_id}.yaml"
    data = _load_yaml_mapping(path)
    spec = PrinterSpec(**data)
    _logger.info("resolved printer spec %s -> %s", printer_id, spec)
    return spec


def load_material_spec(material_name: str) -> MaterialSpec:
    path = _PROCESS_SPECS_DIR / "materials" / f"{material_name}.yaml"
    data = _load_yaml_mapping(path)
    spec = MaterialSpec(**data)
    _logger.info("resolved material spec %s -> %s", material_name, spec)
    return spec


def volumetric_flow_multiplier_for_nozzle(
    diameter_mm: float,
) -> float:
    # Global nozzle-size theory:
    # volumetric capability scales linearly with nozzle diameter relative to 0.4mm.
    # This is intentionally aggressive. Conservative slowing should come from
    # quality factor and motion limits, not from an artificially low flow cap.
    multiplier = diameter_mm / 0.4
    _logger.info(
        "volumetric flow nozzle theory: diameter=%.2f reference=0.40 -> multiplier=%.6f",
        diameter_mm,
        multiplier,
    )
    return multiplier


def resolve_process_data_from_specs(
    printer_id: str,
    material_name: str,
    nozzle: NozzleSetup,
    intent: IntentSpec,
) -> dict:
    _logger.info(
        "resolve_process_data_from_specs start: printer_id=%s material_name=%s nozzle=%s intent=%s",
        printer_id,
        material_name,
        nozzle,
        intent,
    )
    printer = load_printer_spec(printer_id)
    material = load_material_spec(material_name)
    return resolve_process_data(
        printer=printer,
        material=material,
        nozzle=nozzle,
        intent=intent,
    )


def resolve_process_data_from_parameters(
    *,
    printer_id: str,
    material_name: str,
    nozzle_diameter_mm: float,
    nozzle_hardened: bool = False,
    nozzle_high_flow: bool = False,
    strength_factor: float,
    quality_factor: float,
) -> dict:
    _logger.info(
        "resolve_process_data_from_parameters start: printer_id=%s material_name=%s nozzle={diameter_mm=%.2f hardened=%s high_flow=%s} intent={strength_factor=%.3f quality_factor=%.3f}",
        printer_id,
        material_name,
        nozzle_diameter_mm,
        nozzle_hardened,
        nozzle_high_flow,
        strength_factor,
        quality_factor,
    )
    return resolve_process_data_from_specs(
        printer_id=printer_id,
        material_name=material_name,
        nozzle=NozzleSetup(
            diameter_mm=nozzle_diameter_mm,
            hardened=nozzle_hardened,
            high_flow=nozzle_high_flow,
        ),
        intent=IntentSpec(
            strength_factor=strength_factor,
            quality_factor=quality_factor,
        ),
    )


def resolve_process_data(
    printer: PrinterSpec,
    material: MaterialSpec,
    nozzle: NozzleSetup,
    intent: IntentSpec,
) -> dict:
    _logger.info(
        "resolve_process_data start: printer=%s material=%s family=%s nozzle={diameter_mm=%.2f hardened=%s high_flow=%s} intent={strength_factor=%.3f quality_factor=%.3f}",
        printer.printer_id,
        material.material_id,
        material.family,
        nozzle.diameter_mm,
        nozzle.hardened,
        nozzle.high_flow,
        intent.strength_factor,
        intent.quality_factor,
    )

    throughput = 1.0 - _clamp(intent.quality_factor, 0.0, 1.0)
    strength = _clamp(intent.strength_factor, 0.0, 1.0)
    family_rules = _FAMILY_RULES.get(material.family, _FAMILY_RULES["PLA"])
    _logger.info(
        "normalized intent factors: throughput=%.3f strength=%.3f family_rules=%s",
        throughput,
        strength,
        family_rules,
    )

    min_layer_height = nozzle.diameter_mm * printer.min_layer_height_ratio
    max_layer_height = nozzle.diameter_mm * printer.max_layer_height_ratio
    layer_height_ratio = 0.35 + 0.35 * throughput + 0.05 * (1.0 - material.flow_factor)
    layer_height = _clamp(
        nozzle.diameter_mm * layer_height_ratio,
        min_layer_height,
        max_layer_height,
    )
    layer_height = round(layer_height, 2)
    initial_layer_height = nozzle.diameter_mm * (
        0.45 + 0.10 * material.warp_factor + 0.04 * throughput
    )
    initial_layer_height = round(
        _clamp(initial_layer_height, min_layer_height, max_layer_height),
        2,
    )
    _logger.info(
        "layer height theory: min=%.3f max=%.3f ratio=%.3f -> layer_height=%.3f initial_layer_height=%.3f",
        min_layer_height,
        max_layer_height,
        layer_height_ratio,
        layer_height,
        initial_layer_height,
    )

    steady_nozzle_temp = material.nozzle_temp_c
    steady_nozzle_temp += max(0.0, nozzle.diameter_mm - 0.4) * 25.0
    steady_nozzle_temp += 5.0 if nozzle.high_flow else 0.0
    initial_nozzle_temp = steady_nozzle_temp + 5.0
    _logger.info(
        "nozzle temperature theory: base=%.1f diameter_bonus=%.1f high_flow_bonus=%.1f -> steady=%.1f initial=%.1f",
        material.nozzle_temp_c,
        max(0.0, nozzle.diameter_mm - 0.4) * 25.0,
        5.0 if nozzle.high_flow else 0.0,
        steady_nozzle_temp,
        initial_nozzle_temp,
    )

    if material.bed_temp_c is not None:
        bed_temp = round(material.bed_temp_c)
        if material.initial_bed_temp_c is not None:
            initial_bed_temp = round(material.initial_bed_temp_c)
        else:
            initial_bed_temp = bed_temp
        _logger.info(
            "bed temperature override: material bed_temp_c=%s initial_bed_temp_c=%s -> bed=%s initial_bed=%s",
            material.bed_temp_c,
            material.initial_bed_temp_c,
            bed_temp,
            initial_bed_temp,
        )
    elif material.family == "PLA":
        bed_temp = 0.5 * steady_nozzle_temp - 35.0
        bed_temp = round(bed_temp)
        initial_bed_temp = bed_temp + 5
        _logger.info(
            "bed temperature theory: family=%s steady_nozzle=%.1f -> bed=%s initial_bed=%s",
            material.family,
            steady_nozzle_temp,
            bed_temp,
            initial_bed_temp,
        )
    elif material.family == "TPU":
        bed_temp = 0.3 * steady_nozzle_temp - 11.0
        bed_temp = round(bed_temp)
        initial_bed_temp = bed_temp + 5
        _logger.info(
            "bed temperature theory: family=%s steady_nozzle=%.1f -> bed=%s initial_bed=%s",
            material.family,
            steady_nozzle_temp,
            bed_temp,
            initial_bed_temp,
        )
    else:
        bed_temp = 0.5 * steady_nozzle_temp - 45.0
        bed_temp = round(bed_temp)
        initial_bed_temp = bed_temp + 5
        _logger.info(
            "bed temperature theory: family=%s steady_nozzle=%.1f -> bed=%s initial_bed=%s",
            material.family,
            steady_nozzle_temp,
            bed_temp,
            initial_bed_temp,
        )

    family_outer_speed_ceiling = family_rules["outer_speed_ceiling"]
    nozzle_speed_factor = 1.0 + 0.5 * max(0.0, nozzle.diameter_mm - 0.4) / 0.2
    outer_speed = 20.0 + (family_outer_speed_ceiling * nozzle_speed_factor - 20.0) * (
        throughput**2
    )
    outer_speed = round(_clamp(outer_speed, 20.0, printer.max_speed_xy_mm_s))
    _logger.info(
        "speed theory: family_outer_ceiling=%.1f nozzle_speed_factor=%.3f throughput=%.3f -> outer_speed=%s",
        family_outer_speed_ceiling,
        nozzle_speed_factor,
        throughput,
        outer_speed,
    )

    family_inner_multiplier = family_rules["inner_speed_multiplier"]
    inner_speed = round(
        _clamp(outer_speed * family_inner_multiplier, outer_speed, 250.0)
    )
    top_surface_speed = outer_speed
    sparse_infill_speed = inner_speed
    _logger.info(
        "derived speeds: inner_multiplier=%.3f -> inner=%s top_surface=%s sparse_infill=%s",
        family_inner_multiplier,
        inner_speed,
        top_surface_speed,
        sparse_infill_speed,
    )

    family_outer_accel_ceiling = family_rules["outer_accel_ceiling"]
    outer_acceleration = 1200.0 + (family_outer_accel_ceiling - 1200.0) * (
        throughput**2
    )
    outer_acceleration = round(_clamp(outer_acceleration, 800.0, 8000.0))
    inner_acceleration = round(
        _clamp(outer_acceleration * 1.6, outer_acceleration, 8000.0)
    )
    _logger.info(
        "acceleration theory: family_outer_ceiling=%.1f throughput=%.3f -> outer=%s inner=%s",
        family_outer_accel_ceiling,
        throughput,
        outer_acceleration,
        inner_acceleration,
    )

    family_outer_jerk_ceiling = family_rules["outer_jerk_ceiling"]
    family_inner_jerk_ceiling = family_rules["inner_jerk_ceiling"]
    outer_jerk = round(5.0 + (family_outer_jerk_ceiling - 5.0) * throughput)
    inner_jerk = round(8.0 + (family_inner_jerk_ceiling - 8.0) * throughput)
    _logger.info(
        "jerk theory: outer_ceiling=%.1f inner_ceiling=%.1f throughput=%.3f -> outer=%s inner=%s",
        family_outer_jerk_ceiling,
        family_inner_jerk_ceiling,
        throughput,
        outer_jerk,
        inner_jerk,
    )

    infill_density = _round_step(10.0 + 30.0 * strength, 5.0)
    infill_density = _clamp(infill_density, 5.0, 40.0)
    _logger.info(
        "strength theory: strength=%.3f -> infill_density=%.1f%%",
        strength,
        infill_density,
    )

    wall_loops = _strength_shell_count(strength)
    top_shell_layers = _strength_shell_count(strength)
    bottom_shell_layers = _strength_shell_count(strength)
    _logger.info(
        "shell count theory: strength=%.3f -> wall_loops=%s top_shell_layers=%s bottom_shell_layers=%s",
        strength,
        wall_loops,
        top_shell_layers,
        bottom_shell_layers,
    )

    fan_min_speed = 100.0 * material.cooling_factor * (1.0 - material.warp_factor)
    fan_min_speed = round(_clamp(fan_min_speed, 10.0, 100.0))
    fan_max_speed = 100.0 * material.cooling_factor * (1.0 - 0.2 * material.warp_factor)
    fan_max_speed = round(_clamp(fan_max_speed, 30.0, 100.0))
    _logger.info(
        "cooling theory: cooling_factor=%.3f warp_factor=%.3f -> fan_min=%s fan_max=%s",
        material.cooling_factor,
        material.warp_factor,
        fan_min_speed,
        fan_max_speed,
    )

    initial_layer_line_width = nozzle.diameter_mm * (
        1.10 + 0.10 * material.warp_factor + 0.02 * (1.0 - material.cooling_factor)
    )
    initial_layer_line_width = round(initial_layer_line_width, 2)
    line_width = nozzle.diameter_mm * (1.02 + 0.05 * strength + 0.04 * throughput)
    line_width = round(line_width, 2)
    outer_wall_line_width = round(nozzle.diameter_mm, 2)
    inner_wall_line_width = line_width
    internal_solid_infill_line_width = line_width
    sparse_infill_line_width = round(nozzle.diameter_mm * (1.05 + 0.10 * throughput), 2)
    support_line_width = round(nozzle.diameter_mm * (1.02 + 0.08 * throughput), 2)
    top_surface_line_width = outer_wall_line_width
    _logger.info(
        "line width theory: initial=%.2f line=%.2f outer=%.2f inner=%.2f infill=%.2f support=%.2f top_surface=%.2f",
        initial_layer_line_width,
        line_width,
        outer_wall_line_width,
        inner_wall_line_width,
        sparse_infill_line_width,
        support_line_width,
        top_surface_line_width,
    )

    support_top_z_distance = nozzle.diameter_mm * (
        0.45 + 0.55 * material.support_stickiness
    )
    support_top_z_distance = round(support_top_z_distance, 2)
    support_object_xy_distance = 0.3 + 0.35 * material.support_stickiness
    support_object_xy_distance += max(0.0, nozzle.diameter_mm - 0.4) * 0.5
    support_object_xy_distance = round(support_object_xy_distance, 2)
    support_on_build_plate_only = 1
    if material.family == "PETG_CF" and nozzle.diameter_mm >= 0.6:
        support_object_xy_distance = max(support_object_xy_distance, 3.0)
    _logger.info(
        "support theory: support_stickiness=%.3f nozzle_diameter=%.2f family=%s -> top_z=%.2f object_xy=%.2f build_plate_only=%s",
        material.support_stickiness,
        nozzle.diameter_mm,
        material.family,
        support_top_z_distance,
        support_object_xy_distance,
        support_on_build_plate_only,
    )

    bridge_speed_cap = family_rules["bridge_speed_cap_at_04"]
    bridge_speed_cap += family_rules["bridge_speed_cap_gain_per_mm"] * max(
        0.0, nozzle.diameter_mm - 0.4
    )
    bridge_speed = round(
        _clamp(
            min(
                outer_speed * family_rules["bridge_speed_factor"],
                bridge_speed_cap,
            ),
            15.0,
            printer.max_speed_xy_mm_s,
        )
    )
    overhang_fan_speed = round(
        _clamp(
            fan_max_speed * family_rules["overhang_fan_multiplier"],
            fan_max_speed,
            100.0,
        )
    )
    fan_cooling_layer_time = round(
        family_rules["fan_cooling_layer_time"]
        + max(0.0, 0.2 - material.cooling_factor) * 10.0
    )
    slow_down_for_layer_cooling = int(family_rules["slow_down_for_layer_cooling"])
    slow_down_layer_time = round(
        5.0 + 4.0 * material.cooling_factor + 2.0 * intent.quality_factor
    )
    support_threshold_angle = round(family_rules["support_threshold_angle"])
    support_interface_spacing = round(
        family_rules["support_interface_spacing"]
        + max(0.0, nozzle.diameter_mm - 0.4) * 0.5,
        2,
    )
    if material.family == "PETG_CF" and nozzle.diameter_mm >= 0.6:
        support_interface_spacing = round(family_rules["support_interface_spacing"], 2)
    _logger.info(
        "bridging/overhang/support policy: bridge_speed=%s bridge_speed_cap=%.2f overhang_fan=%s fan_cooling_layer_time=%s slow_down_for_layer_cooling=%s slow_down_layer_time=%s support_threshold_angle=%s support_interface_spacing=%.2f support_on_build_plate_only=%s",
        bridge_speed,
        bridge_speed_cap,
        overhang_fan_speed,
        fan_cooling_layer_time,
        slow_down_for_layer_cooling,
        slow_down_layer_time,
        support_threshold_angle,
        support_interface_spacing,
        support_on_build_plate_only,
    )

    flow_ratio = 1.0
    flow_ratio += 0.04 * (material.flow_factor - 0.6)
    flow_ratio -= 0.03 * material.stringing_factor
    flow_ratio += 0.01 if nozzle.high_flow else 0.0
    flow_ratio += 0.005 * max(0.0, nozzle.diameter_mm - 0.4) / 0.2
    flow_ratio = _clamp(flow_ratio, 0.97, 1.03)
    _logger.info(
        "flow ratio theory: flow_factor=%.3f stringing_factor=%.3f diameter=%.2f high_flow=%s -> flow_ratio=%.3f",
        material.flow_factor,
        material.stringing_factor,
        nozzle.diameter_mm,
        nozzle.high_flow,
        flow_ratio,
    )

    if material.base_volumetric_flow_mm3_s is not None:
        nozzle_multiplier = volumetric_flow_multiplier_for_nozzle(nozzle.diameter_mm)
        max_volumetric_flow = math.ceil(
            material.base_volumetric_flow_mm3_s * nozzle_multiplier
        )
        _logger.info(
            "volumetric flow theory: base_material_flow=%.1f family=%s nozzle_diameter=%.2f -> max_volumetric_flow=%s",
            material.base_volumetric_flow_mm3_s,
            material.family,
            nozzle.diameter_mm,
            max_volumetric_flow,
        )
    else:
        max_volumetric_flow = printer.hotend_base_flow_mm3_s * (
            1.0 + 0.6 * max(0.0, nozzle.diameter_mm - 0.4) / 0.2
        )
        max_volumetric_flow *= 1.05 if nozzle.high_flow else 1.0
        max_volumetric_flow = round(max_volumetric_flow)
        _logger.info(
            "volumetric flow theory: fallback formula base=%.1f diameter=%.2f high_flow=%s -> max_volumetric_flow=%s",
            printer.hotend_base_flow_mm3_s,
            nozzle.diameter_mm,
            nozzle.high_flow,
            max_volumetric_flow,
        )

    retraction_length = round(
        nozzle.diameter_mm * family_rules["retraction_length_factor"], 2
    )
    retraction_speed = round(family_rules["retraction_speed"])
    deretraction_speed = round(family_rules["deretraction_speed"])
    infill_wall_overlap = round(family_rules["infill_wall_overlap_pct"])
    brim_type = family_rules["brim_type"]
    brim_width = round(family_rules["brim_width"])
    brim_object_gap = round(family_rules["brim_object_gap"], 2)
    initial_layer_speed = round(family_rules["initial_layer_speed"])
    initial_layer_infill_speed = round(family_rules["initial_layer_infill_speed"])
    detect_overhang_wall = 0 if material.family == "TPU" else 1
    enable_overhang_speed = detect_overhang_wall
    enable_support = 0
    pressure_advance = _pressure_advance_value(
        material_family=material.family,
        nozzle=nozzle,
        throughput=throughput,
        family_rules=family_rules,
    )
    _logger.info(
        "adhesion/retraction/policy theory: retraction_length=%.2f retraction_speed=%s deretraction_speed=%s infill_wall_overlap=%s brim_type=%s brim_width=%s initial_layer_speed=%s initial_layer_infill_speed=%s pressure_advance=%.3f",
        retraction_length,
        retraction_speed,
        deretraction_speed,
        infill_wall_overlap,
        brim_type,
        brim_width,
        initial_layer_speed,
        initial_layer_infill_speed,
        pressure_advance,
    )

    result = {
        "filament": material.material_id,
        "process_overrides": {
            "nozzle_diameter": _format_number(nozzle.diameter_mm, digits=1),
            "layer_height": _format_number(layer_height),
            "max_layer_height": _format_number(max_layer_height),
            "min_layer_height": _format_number(min_layer_height),
            "initial_layer_print_height": _format_number(initial_layer_height),
            "initial_layer_line_width": _format_number(initial_layer_line_width),
            "line_width": _format_number(line_width),
            "outer_wall_line_width": _format_number(outer_wall_line_width),
            "inner_wall_line_width": _format_number(inner_wall_line_width),
            "internal_solid_infill_line_width": _format_number(
                internal_solid_infill_line_width
            ),
            "sparse_infill_line_width": _format_number(sparse_infill_line_width),
            "support_line_width": _format_number(support_line_width),
            "top_surface_line_width": _format_number(top_surface_line_width),
            "nozzle_temperature": _format_number(steady_nozzle_temp, digits=0),
            "nozzle_temperature_initial_layer": _format_number(
                initial_nozzle_temp, digits=0
            ),
            "hot_plate_temp": _format_number(bed_temp, digits=0),
            "hot_plate_temp_initial_layer": _format_number(initial_bed_temp, digits=0),
            "outer_wall_speed": _format_number(outer_speed, digits=0),
            "external_perimeter_speed": _format_number(outer_speed, digits=0),
            "top_surface_speed": _format_number(top_surface_speed, digits=0),
            "inner_wall_speed": _format_number(inner_speed, digits=0),
            "sparse_infill_speed": _format_number(sparse_infill_speed, digits=0),
            "initial_layer_speed": _format_number(initial_layer_speed, digits=0),
            "initial_layer_infill_speed": _format_number(
                initial_layer_infill_speed, digits=0
            ),
            "bridge_speed": _format_number(bridge_speed, digits=0),
            "outer_wall_acceleration": _format_number(outer_acceleration, digits=0),
            "inner_wall_acceleration": _format_number(inner_acceleration, digits=0),
            "outer_wall_jerk": _format_number(outer_jerk, digits=0),
            "inner_wall_jerk": _format_number(inner_jerk, digits=0),
            "wall_loops": _format_number(wall_loops, digits=0),
            "top_shell_layers": _format_number(top_shell_layers, digits=0),
            "bottom_shell_layers": _format_number(bottom_shell_layers, digits=0),
            "sparse_infill_density": _format_percent(infill_density),
            "infill_wall_overlap": _format_percent(infill_wall_overlap),
            "fan_min_speed": _format_number(fan_min_speed, digits=0),
            "fan_max_speed": _format_number(fan_max_speed, digits=0),
            "fan_cooling_layer_time": _format_number(fan_cooling_layer_time, digits=0),
            "overhang_fan_speed": _format_number(overhang_fan_speed, digits=0),
            "slow_down_for_layer_cooling": _format_number(
                slow_down_for_layer_cooling, digits=0
            ),
            "slow_down_layer_time": _format_number(slow_down_layer_time, digits=0),
            "support_top_z_distance": _format_number(support_top_z_distance),
            "support_object_xy_distance": _format_number(support_object_xy_distance),
            "support_on_build_plate_only": _format_number(
                support_on_build_plate_only, digits=0
            ),
            "support_threshold_angle": _format_number(
                support_threshold_angle, digits=0
            ),
            "support_interface_spacing": _format_number(support_interface_spacing),
            "enable_support": _format_number(enable_support, digits=0),
            "detect_overhang_wall": _format_number(detect_overhang_wall, digits=0),
            "enable_overhang_speed": _format_number(enable_overhang_speed, digits=0),
            "filament_retraction_length": _format_number(retraction_length),
            "filament_retraction_speed": _format_number(retraction_speed, digits=0),
            "filament_deretraction_speed": _format_number(deretraction_speed, digits=0),
            "enable_pressure_advance": "1",
            "pressure_advance": _format_number(pressure_advance, digits=3),
            "adaptive_pressure_advance": "0",
            "adaptive_pressure_advance_bridges": "0",
            "adaptive_pressure_advance_overhangs": "0",
            "filament_flow_ratio": _format_number(flow_ratio),
            "filament_max_volumetric_speed": _format_number(
                max_volumetric_flow, digits=0
            ),
            "brim_type": brim_type,
            "brim_width": _format_number(brim_width, digits=0),
            "brim_object_gap": _format_number(brim_object_gap),
        },
    }
    _logger.info("resolve_process_data result: %s", result)
    return result

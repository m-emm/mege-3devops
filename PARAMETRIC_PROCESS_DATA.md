# Parametric Process Data

## Goal

Replace the current zoo of hand-authored flat slicer profiles with a more declarative system:

- YAML for printer capabilities
- YAML for material properties
- Python code that derives slicer-ready process data from a small user-facing intent

Target user input should usually be only:

- material
- nozzle diameter
- is the nozzle hardened
- is the nozzle high-flow
- strength factor `0.0 .. 1.0`
- quality factor `0.0 .. 1.0`
- printer id

Everything else should be derived.

## Current State

The current system already contains useful building blocks, but they are mixed together too early.

### Existing assets

- Machine master YAML:
  - `src/mege_3devops/process_data/mender3/settings_master/machine.yaml`
- Process master YAML:
  - `src/mege_3devops/process_data/mender3/settings_master/process.yaml`
- Filament master YAMLs:
  - `src/mege_3devops/process_data/mender3/settings_master/FilamentCrealityPLAHighSpeedTunedForSpeed.yaml`
  - `src/mege_3devops/process_data/mender3/settings_master/FilamentPETGCF.yaml`
  - `src/mege_3devops/process_data/mender3/settings_master/FilamenteSun_TPU_95A.yaml`
  - and others
- Python preset families:
  - `src/mege_3devops/process_data/mender3/process_data.py`
  - `src/mege_3devops/process_data/mender3/process_data_04_high_precision.py`
  - `src/mege_3devops/process_data/mender3/process_data_04_high_speed.py`
  - `src/mege_3devops/process_data/mender3/process_data_06_high_speed.py`
  - `src/mege_3devops/process_data/mender3/process_data_08_high_speed.py`
- Helper logic already grouping related knobs:
  - `src/mege_3devops/process_data/mender3/process_data_utils.py`

### What is already good

- Printer, material, and process are already separate in the `settings_master` area.
- Python already knows that some settings should move together:
  - speed families
  - acceleration families
  - jerk families
  - layer-height derivation from nozzle diameter
  - consistent multi-plate bed temperatures
- Real-world validated knowledge exists in the current `PROCESS_DATA_*` presets.

### What is not good

The flattening happens too early.

Today, each combination is effectively encoded as a new preset:

- material
- nozzle diameter
- speed/quality family
- sometimes hotend assumptions
- sometimes special support/adhesion behavior

That causes:

- duplication of many flat override keys
- weak traceability of why a value is what it is
- poor scalability when adding a new material or nozzle
- hardcoded entanglement between physical facts and print intent
- inconsistent reuse of the `settings_master` YAMLs
- copy-paste drift between profile families

There is also direct code duplication already visible:

- `process_data_04_high_precision.py` redefines helper functions that also exist in `process_data_utils.py`

## Diagnosis Of The Current Model

The current `PROCESS_DATA_*` files are not random. They encode four different concerns:

### 1. Printer capability

Examples:

- max speeds
- max acceleration
- jerk limits
- printable area
- plate-specific temperature handling

These belong to printer capability data, not to a part preset.

### 2. Nozzle and hotend capability

Examples:

- nozzle diameter
- hardened or not
- normal-flow vs high-flow
- realistic volumetric flow limit
- line-width ranges
- layer-height ranges
- pressure-advance expectations

These are partly baked into the current nozzle-specific presets, but should be explicit inputs.

### 3. Material behavior

Examples:

- temperature range
- recommended bed temperature
- cooling appetite
- warping tendency
- bridge behavior
- support stickiness
- support Z gap tendency
- flow sensitivity
- hole-closing tendency

These belong to material specs, augmented by your own observed tuning.

### 4. Print intent

Examples:

- strong vs decorative
- fast vs beautiful
- dimensionally critical vs forgiving
- support avoidance vs support cleanliness

This should be driven from a small intent model, not by selecting one of many large flat preset dicts.

## Target Architecture

The new system should have a staged pipeline.

### Stage A: Declarative specs

Principle: only model what is needed to reproduce and generalize the current verified data sets. Do not build a large metadata catalog.

#### Printer spec YAML

One YAML per printer or printer configuration.

Contents:

- printable size
- machine max speeds
- machine max acceleration
- machine max jerk
- bed type behavior
- chamber availability
- motion system notes
- extruder type
- hotend family

Example path:

- `process_specs/printers/megemaster.yaml`

#### Nozzle input

The nozzle should not be identified by a long text id in the public API.

It should be described directly by three fields:

- `diameter_mm`
- `hardened`
- `high_flow`

If nozzle definitions are stored on disk for defaults, that is an internal implementation detail. The user-facing interface should remain those three values.

#### Material spec YAML

One YAML per material definition.

This should not mirror vendor datasheets or slicer export files. It should contain only the smallest set of properties needed to derive the current tuned profiles.

Recommended minimal contents for the first implementation:

- `family`
  - one of `PLA`, `PETG`, `TPU`, `PVA`, `PLA_CF`, `PETG_CF`
- `nozzle_temp_c`
  - the nominal steady-state nozzle temperature for a medium case
- `cooling_factor`
  - normalized `0.0 .. 1.0`
- `warp_factor`
  - normalized `0.0 .. 1.0`
- `stringing_factor`
  - normalized `0.0 .. 1.0`
- `support_stickiness`
  - normalized `0.0 .. 1.0`
- `flow_factor`
  - normalized `0.0 .. 1.0`

That is intentionally sparse.

Not included initially:

- vendor name
- product marketing ranges
- bridge friendliness as its own top-level knob
- moisture sensitivity
- density and cost
- large sets of observational sub-properties that do not yet have a clear mapping to generated parameters

Example path:

- `process_specs/materials/esun_tpu_95a.yaml`

#### Intent / strategy inputs

This is the user-facing reduced parameter set.

Example:

```yaml
printer: megemaster
material: filament_petgcf
nozzle:
  diameter_mm: 0.6
  hardened: true
  high_flow: true
strength_factor: 0.9
quality_factor: 0.35
part_traits:
  supports_allowed: true
  dimensional_accuracy_priority: 0.7
  overhang_heavy: false
  thin_tall_part: true
```

`part_traits` should stay optional and small. The main public contract remains the four core inputs.

### Stage B: Python domain model

Implement a real library, not just more dict patching.

Suggested types:

- `PrinterSpec`
- `MaterialSpec`
- `IntentSpec`
- `PartTraits`
- `NozzleSetup`
- `DerivedProcessProfile`
- `SlicerProcessData`

These should be typed dataclasses or Pydantic models.

### Stage C: Resolution pipeline

The resolver should work in layers.

#### 1. Capability envelope

Combine:

- printer limits
- nozzle geometry and nozzle-type limits
- hotend limits

Output:

- allowed speed ceilings
- allowed acceleration ceilings
- allowed layer-height range
- allowed line-width range
- volumetric flow ceilings by material family

#### 2. Material envelope

Apply material constraints and biases:

- steady-state nozzle temperature
- cooling tendency
- warping tendency
- stringing tendency
- support-release tendency
- warp risk
- stringing risk

#### 3. Intent mapping

Map `strength_factor` and `quality_factor` to strategy axes, for example:

- layer height bias
- line width bias
- wall count bias
- infill density bias
- top/bottom shell bias
- quality vs throughput speed weighting
- support density vs removability weighting
- brim aggressiveness

This is the core abstraction that replaces many hand-authored profile variants.

#### 4. Derived geometry strategy

Compute:

- layer height
- initial layer height
- line widths
- wall loops
- shell counts
- infill pattern and density
- support thresholds
- brim choice

#### 5. Derived kinematics strategy

Compute:

- outer wall speed
- inner wall speed
- top surface speed
- support speed
- bridge speed
- first-layer speeds
- matching accelerations
- matching jerk
- cooling slowdown policy

This should preserve the current good idea from `augment_with_speeds`, `augment_with_accelerations`, and `augment_with_jerks`, but move it into a higher-level policy model.

#### 6. Material-specific detail passes

Apply second-order corrections, for example:

- TPU: lower cooling, more Z-hop, cautious retraction, low support use
- PETG: less fan, more support distance, anti-stringing bias
- PLA: more fan, more aggressive bridge settings
- CF materials: harder-nozzle requirement, lower fan, conservative bridge/support assumptions

#### 7. Emit slicer-flattened data

Only at the end should the system flatten into Orca/Bambu-style `process_overrides`.

This final stage can still return the same shape used today:

```python
{
    "filament": "...",
    "process_overrides": {...}
}
```

That keeps downstream compatibility.

## Key Design Principle

The library should distinguish between:

- facts
- heuristics
- policies
- final slicer keys

Today these are mixed together inside the same flat dicts.

The new model should keep them separate until the final render step.

## How To Reuse The Existing Verified Profiles

Do not throw the current presets away. They are the training corpus.

The current `PROCESS_DATA_*` families should be treated as verified examples of successful outputs.

Use them as:

- regression targets
- rule-discovery examples
- acceptance references
- migration fixtures

### Practical extraction approach

For each current preset, extract:

- printer assumptions
- nozzle assumptions
- material assumptions
- intent assumptions
- explicit special-case rules

Example:

- `PROCESS_DATA_TPU_04_HS`
  - printer: MegeMaster / Ender 3 V3 KE class
  - nozzle: `0.4`, standard-flow
  - material: TPU 95A
  - quality factor: low to medium
  - strength factor: medium to low
  - special rules:
    - disable cooling slowdown
    - disable overhang slowdown
    - low infill
    - low support usage

This turns the current hand-tuned corpus into structured rule sources.

## Recommended Rule Model

The derivation should not be a giant pile of `if material == ...`.

Use weighted traits and bounded formulas.

### Minimal normalized traits

Each material spec can define traits in `0.0 .. 1.0`:

- `warp_risk`
- `stringing_risk`
- `cooling_need`
- `support_stickiness`
- `flow_ease`

Nozzle input should define only:

- `diameter_mm`
- `hardened`
- `high_flow`

Each intent can define:

- `strength_factor`
- `quality_factor`

Then formulas can combine them.

### Example formula directions

- layer height:
  - larger nozzle => higher base layer height
  - higher quality => lower layer height
  - stronger part => slightly lower layer height only if bonding benefits
- wall loops:
  - stronger part => more loops
  - flexible material => fewer loops for flexibility unless mechanical shell is required
- support Z gap:
  - high support stickiness => larger gap
  - high quality => smaller gap if removable enough
- fan speed:
  - high cooling need => increase
  - high warp risk => decrease
- bed temperature:
  - derived from nozzle temperature by material-family-specific linear mapping
- brim:
  - high warp risk or thin-tall part => larger brim
- print speed:
  - capped by printer max
  - capped by volumetric flow
  - reduced by quality factor
  - reduced by difficult materials

## Proposed Package Structure

Suggested new structure:

```text
src/mege_3devops/process_data/
  parametric/
    models.py
    loader.py
    resolver.py
    emit_orca.py
    rules/
      geometry.py
      kinematics.py
      cooling.py
      supports.py
      adhesion.py
      materials.py
  process_specs/
    printers/
      megemaster.yaml
    materials/
      creality_pla_hs.yaml
      esun_tpu_95a.yaml
      petg_cf_generic.yaml
```

The current `mender3/process_data_*.py` files can remain for compatibility while generation is phased in.

## Public API Proposal

The new library should expose something like:

```python
from mege_3devops.process_data.parametric import resolve_process_data

process_data = resolve_process_data(
    printer="megemaster",
    material="esun_tpu_95a",
    nozzle={"diameter_mm": 0.6, "hardened": True, "high_flow": True},
    strength_factor=0.85,
    quality_factor=0.30,
)
```

Optional extended API:

```python
process_data = resolve_process_data(
    printer="megemaster",
    material="petg_cf_generic",
    nozzle={"diameter_mm": 0.4, "hardened": True, "high_flow": False},
    strength_factor=0.95,
    quality_factor=0.60,
    part_traits={
        "thin_tall_part": True,
        "supports_allowed": True,
        "dimensional_accuracy_priority": 0.8,
    },
)
```

## Migration Strategy

### Phase 1: Introduce the domain model

- Add `PrinterSpec`, `NozzleSpec`, `MaterialSpec`, `IntentSpec`
- Add YAML loaders
- Keep all current `PROCESS_DATA_*` modules untouched

### Phase 2: Encode master data declaratively

- Move printer capability facts out of ad hoc preset files
- Keep nozzle input simple: diameter, hardened, high-flow
- Normalize only the minimal material trait YAMLs
- Avoid expanding into vendor metadata unless the generator actually needs it

Recommended pattern inside material YAML:

```yaml
family: TPU
nozzle_temp_c: 225
cooling_factor: 0.45
warp_factor: 0.20
stringing_factor: 0.80
support_stickiness: 0.65
flow_factor: 0.55
```

### Phase 3: Build the resolver

- Reimplement the current grouped augment logic in structured form
- Add formulas and bounded heuristics
- Emit the same flat `process_overrides` shape as today

### Phase 4: Golden regression tests

For selected current presets:

- generate with the new resolver
- compare against current known-good output
- allow controlled tolerances where intentional

Examples:

- `PROCESS_DATA_PLA_04_HP`
- `PROCESS_DATA_TPU_04_HS`
- `PROCESS_DATA_PETG_06_HS`
- `PROCESS_DATA_PETGCF_06_HS`

### Phase 5: Compatibility shims

Re-export legacy constants through the new resolver:

```python
PROCESS_DATA_TPU_04_HS = resolve_process_data(
    printer="megemaster",
    material="esun_tpu_95a",
    nozzle={"diameter_mm": 0.4, "hardened": False, "high_flow": False},
    strength_factor=0.35,
    quality_factor=0.25,
)
```

This keeps existing part scripts working while the implementation underneath becomes parametric.

### Phase 6: Reduce the preset zoo

Once enough goldens pass:

- stop hand-maintaining most flat preset files
- keep only compatibility aliases and a few curated named profiles

## Important Non-Goals

This system should not try to become a generic slicer clone.

It should:

- produce a solid default basis automatically
- capture proven house knowledge
- reduce manual parameter churn
- preserve the ability to override special cases

It should not:

- attempt perfect optimization for every geometry automatically
- hide all special cases
- eliminate expert overrides

## Override Model

Even in the new world, overrides remain necessary.

But overrides should be allowed only at the final flat slicer-key level.

Do not allow overriding:

- printer facts
- material facts
- nozzle facts
- intermediate derived policy values
- strength factor / quality factor from inside a part override

Allowed override scope:

- only final printer-defined slicer parameters, for example:
  - `outer_wall_speed`
  - `support_top_z_distance`
  - `brim_width`
  - `layer_height`

That keeps behavior understandable:

- the high-level inputs produce a resolved profile
- a part may override only the final emitted values
- the value seen in the slicer GUI is exactly the value the part override set

## Why This Matches The Existing Codebase

This direction is not a radical break. It is the natural continuation of what already exists:

- `settings_master/machine.yaml` already contains printer facts
- filament YAMLs already contain material-adjacent facts
- `process_data_utils.py` already groups some multi-key derivations
- the many `PROCESS_DATA_*` constants already represent validated real outputs

The real missing piece is a central typed resolver that keeps the declarative inputs separate until the final flattening step.

## Concrete First Implementation Slice

The first useful thin slice should be small.

Recommended first target:

- printer:
  - `megemaster`
- nozzle combinations:
  - `diameter_mm=0.4`, `hardened=false`, `high_flow=false`
  - `diameter_mm=0.6`, `hardened=true`, `high_flow=true`
- materials:
  - `creality_pla_hs`
  - `esun_tpu_95a`
  - `petg_cf_generic`

And only two public continuous knobs:

- `strength_factor`
- `quality_factor`

First milestone success criterion:

- produce generated outputs close enough to:
  - `PROCESS_DATA_PLA_04_HP`
  - `PROCESS_DATA_TPU_04_HS`
  - `PROCESS_DATA_PETGCF_06_HS`

That is enough to prove the architecture before migrating the rest.

## Final Recommendation

Treat the current preset corpus as validated output examples, not as the long-term authoring model.

Author long-term knowledge in:

- printer YAML
- structured nozzle input:
  - `diameter_mm`
  - `hardened`
  - `high_flow`
- material YAML
- compact intent inputs

Then derive slicer-flat process data in Python through a real resolver pipeline.

That preserves your verified tuning, reduces duplication, makes new materials and nozzles cheaper to add, and moves the project toward declarative intent instead of an ever-growing library of flat preset dicts.

## Appendix: Required Theories

This section lists the concrete theories the implementation must define up front. If these are not explicit, the generator will turn into another parameter zoo.

### A1. Quality Factor Theory

`quality_factor` means:

- `0.0` = as fast as safely possible
- `1.0` = highest quality the current printer/material/nozzle combination can reasonably deliver

It should influence:

- layer height
- outer wall speed
- top surface speed
- inner and infill speed
- acceleration
- jerk
- support interface density, if needed

Recommended first theory:

- define a normalized throughput factor:
  - `throughput = 1.0 - quality_factor`
- derive layer height ratio from nozzle diameter:
  - `layer_height_ratio = lerp(0.30, 0.75, throughput)`
- then clamp by nozzle and printer limits:
  - `layer_height = clamp(nozzle_diameter * layer_height_ratio, min_layer_height, max_layer_height)`
- derive speeds from capability ceilings:
  - `outer_wall_speed = outer_wall_ceiling * lerp(0.25, 1.0, throughput)`
  - `top_surface_speed = outer_wall_speed * 0.8`
  - `inner_wall_speed = inner_wall_ceiling * lerp(0.35, 1.0, throughput)`
  - `sparse_infill_speed = infill_ceiling * lerp(0.40, 1.0, throughput)`
- derive acceleration and jerk with the same direction, but with tighter lower and upper clamps than speed

Meaning:

- higher quality gives thinner layers and lower visible-feature speeds
- lower quality gives thicker layers and more aggressive speeds

### A2. Strength Factor Theory

`strength_factor` means:

- `0.0` = decorative / lightweight
- `1.0` = mechanical / strength-oriented

It should influence:

- wall loops
- top and bottom shell count
- infill density
- line-width bias
- brim aggressiveness for difficult tall parts

Recommended first theory:

- `wall_loops = round(lerp(1, 4, strength_factor))`
- `top_shell_layers = round(lerp(2, 5, strength_factor))`
- `bottom_shell_layers = round(lerp(2, 5, strength_factor))`
- `sparse_infill_density = lerp(10%, 40%, strength_factor)`
- `line_width_ratio_inner = lerp(1.00, 1.12, strength_factor)`

Strength factor should not be the primary driver of speed. It is mainly a geometry strategy knob.

### A3. Nozzle Temperature Theory

The material YAML should initially specify only one temperature:

- `nozzle_temp_c`

This is the nominal steady-state nozzle temperature for a medium print.

Derived temperatures:

- `steady_nozzle_temp_c`
- `initial_nozzle_temp_c`

Recommended first theory:

- `steady_nozzle_temp_c = material.nozzle_temp_c + nozzle_diameter_bonus + high_flow_bonus + throughput_bonus`
- where:
  - `nozzle_diameter_bonus` is small and positive for larger nozzles
  - `high_flow_bonus` is small and positive for high-flow nozzles at the same throughput
  - `throughput_bonus` rises as `quality_factor` decreases
- then clamp by material-family and printer-safe limits

Recommended first-layer theory:

- `initial_nozzle_temp_c = steady_nozzle_temp_c + first_layer_boost_c`
- where `first_layer_boost_c` is a bounded function of:
  - `warp_factor`
  - first-layer speed
  - maybe nozzle diameter

Keep this simple at first:

- first-layer boost in the range `0 .. 10 C`

### A4. Bed Temperature Theory

Yes, bed temperature can initially be derived from nozzle temperature instead of being stored directly per material.

But this should be a material-family-specific linear mapping, not one global linear formula for all materials.

Recommended first theory:

- `bed_temp_c = clamp(a_family * steady_nozzle_temp_c + b_family + warp_bonus_c, printer_bed_min, printer_bed_max)`

Examples of family-specific affine mappings:

- PLA family:
  - lower slope, moderate temperatures
- PETG family:
  - higher slope, hotter bed
- TPU family:
  - low slope, cool bed

Where:

- `warp_bonus_c = lerp(0, 10, warp_factor)`

Derived first-layer bed temperature:

- `initial_bed_temp_c = bed_temp_c + first_layer_bed_boost_c`
- keep boost small, for example `0 .. 8 C`

If this model proves too weak, the next allowed extension should be a single `bed_temp_offset_c` in the material YAML, not a full second temperature database.

### A5. Nozzle Diameter Theory

Nozzle diameter should influence:

- minimum and maximum layer height
- default line widths
- initial layer height and width
- volumetric throughput ceiling
- support Z distances
- XY hole compensation tendency
- retraction and Z-hop tendency, mildly

Recommended first theory:

- `min_layer_height = 0.25 * nozzle_diameter`
- `max_layer_height = 0.75 * nozzle_diameter`
- `outer_wall_line_width = 1.00 * nozzle_diameter`
- `inner_wall_line_width = lerp(1.02, 1.12, strength_factor) * nozzle_diameter`
- `sparse_infill_line_width = 1.08 * nozzle_diameter`
- `initial_layer_height = min(max_layer_height, 0.50 * nozzle_diameter)`
- `initial_layer_line_width = 1.15 * nozzle_diameter`
- `support_top_z_distance = round_to_layer_fraction(layer_height, family_rule)`

This is close to what the current hand-authored profiles already do.

### A6. Flow Capacity And Flow Ratio Theory

These are not the same thing and should be treated separately.

#### Flow capacity

This answers:

- how much plastic can be melted and pushed per second

Inputs:

- printer / hotend capability
- nozzle diameter
- `high_flow`
- material `flow_factor`

Recommended first theory:

- `hotend_base_flow_mm3_s` comes from the printer spec
- `diameter_multiplier` is a bounded function of nozzle diameter
- `high_flow_multiplier` is `> 1.0` if `high_flow=true`
- `material_flow_multiplier = lerp(0.7, 1.2, flow_factor)`
- `max_volumetric_flow = hotend_base_flow_mm3_s * diameter_multiplier * high_flow_multiplier * material_flow_multiplier`

That ceiling then limits all speeds.

#### Flow ratio

This answers:

- how much extrusion multiplier around `1.0` is needed

Recommended first theory:

- keep this near `1.0`
- derive only a small correction from material flow behavior and nozzle setup

Example:

- `flow_ratio = clamp(1.0 + material_flow_trim + diameter_trim + nozzle_type_trim, 0.97, 1.03)`

To keep the model small, start with:

- `material_flow_trim` derived from the same `flow_factor`
- `diameter_trim` and `nozzle_type_trim` very small

If later this proves insufficient, only then introduce a dedicated material property such as `flow_ratio_bias`.

### A7. Minimal Material Theory

For the first implementation, the material YAML should answer only these questions:

- what family is this
- what nominal nozzle temperature does it want
- how much cooling does it want
- how much does it warp
- how much does it string
- how sticky are supports
- how easily does it flow

That is enough to derive the major differences visible in the current data sets.

Everything beyond that should stay out until there is a proven formula that uses it.

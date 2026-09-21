# Onshape assembly

[Open the native assembly](https://cad.onshape.com/documents/88edbeda4232642329938c14/w/19f5435855c2974f02fa7c68/e/ea6ef29b6f90442d8a9d563b)

The Onshape document contains a positioned Part Studio with 155 solids, a separate Part Studio with the 17 unique printable parts, and a native assembly of all 155 instances. The Onshape Free account stores this document publicly; the Git repository is private by default.

## Installed mating structure

- The chassis is fixed.
- **136 fastened mates** collect the solid instances into **19 rigid links**.
- **18 revolute mates** provide yaw, hip and knee motion for six legs.
- Joint origins and axes match the CAD and MuJoCo neutral geometry.
- Yaw limits are ±20°; hip and knee limits are ±15° relative to the neutral CAD pose.
- API readback reports no feature solver errors and neutral transforms within 5 × 10⁻¹³ of their intended values.

The exact graph and instance IDs are in [`onshape_mate_plan.json`](../simulation/onshape_mate_plan.json). Installation checks are in [`onshape_validation.json`](../simulation/onshape_validation.json). Native motion-command verification is tracked separately; creation of valid mates and zero-pose consistency do not themselves validate a dynamic gait.

For one leg, the rigid structure is:

```text
fixed chassis ── revolute yaw ── coxa ── revolute hip ── femur ── revolute knee ── tibia + foot
```

The other five legs repeat this chain. Within a rigid link, brackets, clamps, servo cases, horns, shims and references are fastened. Each servo case belongs to the upstream link; its rotating horn assembly belongs to the downstream link.

## Inspecting or editing

Open the assembly and filter the feature tree by `R_L1_yaw`, `R_L1_hip` or `R_L1_knee` to inspect the joint definitions. `F_` features are fastened mates. `MC_` and `J_` features are explicit mate connectors used to keep axes stable without depending on tessellated edge selection.

The neutral hip geometry is +15° above horizontal and the neutral knee is −80° relative to the femur. The mate values are offsets from this geometry, not the absolute link angles. Do not equate these with raw servo encoder values until calibration.

The CAD STEP imports preserve solid geometry and names, not the CadQuery feature history. Modify the source in `src/build_cad.py` to regenerate the mechanism. Native Onshape identifiers from the original import are mapped to English repository labels in [`onshape_name_map.json`](../cad/onshape_name_map.json).

## Export to MuJoCo

The supplied MuJoCo export uses the same 19-link graph and physical joint frames. It is generated from the positioned CAD solids, not from a screenshot or the print-bed-oriented STL files. Follow [the simulation guide](simulation.md) and [regeneration guide](development.md).

The resting floor pose in MuJoCo is vertically shifted from the CAD origin so the feet meet the ground. That global height adjustment does not change the local link geometry or mate origins.

# Onshape assembly

[Open the native assembly](https://cad.onshape.com/documents/88edbeda4232642329938c14/w/19f5435855c2974f02fa7c68/e/ea6ef29b6f90442d8a9d563b)

The document contains an assembly-source Part Studio with **499 positioned solids**, a separate Part Studio with **14 unique printable solids**, and a native assembly with the 499 corresponding instances. The imported STEP preserves the corrected symmetric geometry, including the complete dummy-side knee eyes, real button-head screw envelopes, metal horns on the inside of the cheeks, and no loose shims. The Onshape Free document and GitHub repository are public.

## Native mate structure

- The chassis is fixed.
- **480 fastened mates** connect the parts into **19 rigid links**, including every modeled screw, heat-set insert, metal horn and foot locknut.
- **18 revolute mates** provide yaw, hip and knee motion for six legs.
- Mate connectors place the joint axes at the same locations as the CAD and MuJoCo neutral geometry.
- The revolute limits follow [`joint_map.json`](../simulation/joint_map.json): front/rear yaw up to 64° inward and 35° outward, middle yaw ±35°, hip −35°/+15° and knee −15°/+80° relative to the neutral CAD pose.

The exact graph and instance IDs are in [`onshape_mate_plan.json`](../simulation/onshape_mate_plan.json). Native API readback and feature status are in [`onshape_validation.json`](../simulation/onshape_validation.json); the [limit report](../simulation/onshape_motion_validation.json) records each revolute mate. The mate and limit readbacks check the definitions at neutral, while the separate [CAD motion check](../validation/motion_validation.json) and [MuJoCo checks](../simulation/simulation_validation.json) check sampled motion. Native interactive animation has not been separately verified.

For one leg, the rigid structure is:

```text
fixed chassis ── revolute yaw ── coxa ── revolute hip ── femur ── revolute knee ── tibia + foot
```

The other five legs repeat this chain. Each servo case belongs to the upstream link; its rotating metal horns and horn screws belong to the downstream link. Within a rigid link, the printed pieces, clamps, screws and inserts are fastened.

## Inspecting or editing

Open the assembly and filter the feature tree by `R_L1_yaw`, `R_L1_hip` or `R_L1_knee` to inspect the joint definitions. `F_` features are fastened mates. `MC_` and `J_` features are explicit mate connectors; they do not depend on tessellated edge selection. The neutral hip geometry is +15° above horizontal and the neutral knee is −80° relative to the femur. Mate values are offsets from this neutral pose, not raw servo encoder values.

The imported STEP does not retain CadQuery feature history. Modify [`src/build_cad.py`](../src/build_cad.py) and regenerate the STEP to change geometry. The API assembly uses legacy mate connector names for some original parts; [`onshape_name_map.json`](../cad/onshape_name_map.json) preserves that alias mapping. The direct-horn revision is also captured by the [orthographic leg view](../assets/cad-leg-top.png) and the [four-screw knee view](../assets/cad-horn-detail.png).

## Export to MuJoCo

The supplied MuJoCo export uses the same 19-link graph and joint frames. It is generated from the positioned CAD solids, not from a screenshot or the print-bed-oriented STL files. Follow the [simulation guide](simulation.md) and [regeneration guide](development.md). A global height adjustment places the floating-base robot's feet on the floor without changing the local link geometry or mate origins.

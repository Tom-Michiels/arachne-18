# Printing and assembly

[Back to the project](../README.md) · [Print BOM](../print/print_bom.csv) · [Hardware BOM](hardware-bom.csv)

## Design and dimensions

ARACHNE uses eighteen **12 V STS3215** servos, arranged as yaw, hip, and knee on each of six legs. The main chassis is approximately 188 × 181 mm. The neutral robot envelope is approximately 374 × 514 × 214 mm. All print and STEP dimensions are in millimetres.

The supplied STLs contain 17 unique files: 99 pieces are used in the robot, one additional fit gauge is recommended, and two optional thin shim variants have a default quantity of zero. Purchased servos, metal horns, fasteners, electronics, straps and battery must not be printed.

## Start with the servo interface

The model follows the common STS3215 case drawing: **45.23 × 24.73 × 35 mm**, with the axis 12.5 mm from the centre along the long direction. The supplied circular horns are represented as **19.95 mm diameter**, with four M3 holes on a **14 mm pitch circle**. Use the original driven horn, passive-side disc and central screws. The splines are not printed.

**The horns belong inside the brackets.** On either side, the stack from the servo outward is:

```text
servo → original metal horn/disc → adjustment shim → printed cheek → washer + screw head
```

The four outside M3 screws pass through the printed cheek and shim into the metal horn. The outside joint face remains printed polymer with individual screw heads; it is not covered by a metal horn. A central opening allows access to the manufacturer's central fastener.

The printed cheeks have a **45 mm inside separation**. The reference assumes the outer faces of the two installed horns are 40 mm apart, with one 2.5 mm shim on each side. Measure one real assembly first:

```text
combined shim thickness = 45 mm − measured outside-to-outside horn width
```

Distribute the shims without pulling the bracket sideways or preloading the servo. Optional 0.5 mm and 1.0 mm shims are included. Horn variants may need different shims.

Print `15_fit_gauge` and one `08_servo_clamp_cap` before the full set. Check the bolt circle, 3.4 mm clearance holes and 4.2 mm insert bores. The motor end of the case is held by a removable clamp. A thin rubber or TPU strip can take up the approximate 0.3 mm fit clearance. Tighten lightly and leave the rear cable exit unobstructed.

## H2D print setup

Slice at **100% scale in mm**. All individual parts fit the H2D. The STL files sit on Z=0; this does not mean every part prints without support. Check the slicer preview around bridges, servo cradles, holes and the shell dome.

| Components | Starting material/settings | Orientation and support |
|---|---|---|
| Chassis, coxa, femur, tibia | PETG or tough nylon; 0.20 mm layers; 5–6 walls; 35–45% infill | Choose strong layer directions around joint eyes; support bridges and projecting cradles |
| Dorsal deck, battery tray, controller plate | PETG; 4 walls; 25–35% infill | Flat base on the bed; inspect overhangs |
| Organic shell | PETG; 3–4 walls | Opening down; support below dome; remove through large underside opening |
| Separate cheek plates and clamp caps | PETG; 5 walls | Flat; usually no support |
| Horn shims | PETG, solid | Flat; choose a layer height suitable for 0.5 mm shims |
| Feet | TPU 95A; 4 walls | Flexible slip-on fit; inspect internal support accessibility |

Use support interfaces appropriate to the selected material. Confirm all support can be removed before printing a batch. There are no deliberately enclosed support chambers. Nylon drying and slicer settings depend on the actual filament used.

## Battery and electronics

The battery tray has an internal footprint of **117 × 42 mm**. The reserved battery envelope is **115 × 40 × 35 mm**, excluding projecting plugs. Select an assembled **3S battery pack** that fits with its wrap and cable exit: 11.1 V nominal and 12.6 V fully charged. This is a variable 3S supply, not a regulated constant 12 V output.

Two straps up to 15 mm wide restrain the pack. Add a thin anti-slip pad and route its cable toward the rear service opening. Remove the pack for charging with its compatible charger.

The controller plate measures **108 × 75 mm**, with 3.4 mm slots. The generic controller envelope is **90 × 60 × 18 mm**, above four 6 mm spacers. Its reference block is not a specific controller product. Move the stand-offs along the slots to suit the chosen board.

Use a compatible half-duplex TTL bus interface. Provide a separate regulated logic supply if the controller needs 5 V. The manufacturer lists 2.7 A stall current per servo: three stalled servos would be 8.1 A and eighteen would be 48.6 A. These are peak/fault conditions, not predicted continuous consumption. Size the pack, connector, wiring and fuses using the real application. Distribute servo power by leg; do not route the full robot current through one small servo bus connector.

## Hardware

Use **DIN 7380 / EN ISO 7380-1 button-head hex-socket screws** for all listed M3 assembly screws. M3 reference head diameter is 5.7 mm, head height 1.65 mm, and the hex key is 2 mm ([Norelem dimensions](https://www.norelemusa.com/en-us/Product-Overview/Flexible-standard-component-system/07000/Nuts-screws-washers-securing-elements/Button-head-screws-EN-ISO-7380/Hexagon-socket-button-head-screws-EN-ISO-7380-1-Style-A/p/agid.18464)). Retain the original Feetech central screws: these are specific to the servo shaft. Detailed purchased screw geometry is omitted from the main 155-solid CAD assembly; the BOM defines the fastener selection.

The [hardware CSV](hardware-bom.csv) is ready to import into a spreadsheet. Screw lengths are starting values: verify engagement with the actual horns and shims so screw tips cannot touch the servo case.

| Item | Quantity | Purpose |
|---|---:|---|
| STS3215 12 V servo | 18 | Six yaw, six hip, six knee |
| Original driven/passive metal horns | 18 + 18 | Both sides of each servo |
| Original central servo screws | 36 | Keep each manufacturer's correct type |
| M3 × 10 + approximately 0.5 mm washer | 144 | Four per horn; approximately 2.5 mm engagement with standard shim |
| M3 × 8 | 112 | 72 clamps, 12 coxa, 12 femur, 4 deck, 4 tray, 4 controller plate, 4 shell |
| M3 heat-set inserts for 4.2 mm bore | 112 | Deck inserts no longer than 3 mm; verify selected insert in the gauge |
| M3 × 16 and M3 nut | 4 + 4 | Controller and stand-offs |
| M3 × 25 and locknut | 6 + 6 | Feet |
| Battery straps, 15 mm maximum | 2 | Battery restraint |
| Anti-slip strips, cable ties, bus cables | As needed | Fit, strain relief and wiring |

The short deck inserts have less pull-out resistance than the deeper cradle inserts. Deck accessories do not carry leg loads; tighten their screws gently.

## Assembly order

1. **Check fit.** Print the gauge and one clamp. Fit both original horns to one servo and establish shim thickness. Set the servo centres and assign unique IDs 1–18.
2. **Prepare the chassis.** Install inserts. Fit six yaw servos and their clamp caps, leaving the horns and cables free.
3. **Build each coxa.** Fit a hip servo into the main coxa bracket. Place the two yaw cheek halves around the yaw horns with shims, then close the bottom plate with its two screws.
4. **Build each femur.** Fit a knee servo into the femur cradle. Mount the paired femur cheeks onto the hip horns with shims. Fasten the removable cheek to the two cross-ties.
5. **Fit the tibia and foot.** Slide the open-ended tibia fork around the knee servo and attach it to the two horns through the shims. Fit the TPU foot and transverse retention bolt.
6. **Install the dorsal compartment.** Add the deck and battery tray. Route cables through the oval windows, provide strain relief and a free loop at every joint, then fit the battery, controller plate and board.
7. **Close and calibrate.** Attach the shell with its four accessible side screws. Check every joint unpowered. Calibrate real encoder offsets and directions against the [joint map](../simulation/joint_map.json), then start with slow unloaded motion.

## Operating envelope

The neutral hip points 15° upward; the tibia points 65° below horizontal, giving a relative knee angle of −80°. The current simulation limits are yaw ±20°, hip ±15° around neutral, and knee ±15° around neutral. These are conservative sampled design ranges, not a verified full gait envelope.

The manufacturer lists 10 kg·cm nominal torque and 30 kg·cm stall torque at 12 V. Stall torque is not a continuous rating. At the model's approximately 2.45 kg total mass and roughly 122 mm horizontal hip-to-foot reach, an ideal three-foot load split already implies about 10 kg·cm per supporting hip before detailed leg weight and dynamic effects. Keep the robot light, begin with slow six-foot-supported tests, and establish payload experimentally. No physical load test or FEA has been performed.

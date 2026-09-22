# Printing and assembly

[Back to the project](../README.md) · [Print BOM](../print/print_bom.csv) · [Hardware BOM](hardware-bom.csv)

## Design basis

ARACHNE uses eighteen **12 V STS3215** servos in six yaw–hip–knee chains. The scalloped chassis is approximately 188 × 150 mm; the neutral robot envelope is approximately 375 × 514 × 214 mm. All print and STEP dimensions are millimetres. There are **14 unique printable files**: 63 pieces in the robot and one recommended fit gauge. All fit the Bambu Lab H2D.

## Servo and horn interface

The servo reference follows the published 45.23 × 24.73 × 35 mm case dimensions. The owner measured **36.5 mm between the outside faces of the two installed horns**. The driven horn is 2.5 mm thick and the dummy-side horn is 2.0 mm thick. The printed cheeks have a **36.9 mm inside span**, leaving 0.2 mm nominal clearance per side. There are **no separate horn shims**. The supplied metal horns remain on the *inside* of the printed cheeks; only screw heads and the central access opening show outside.

The dummy-side shaft protrudes approximately 6.5 mm in diameter, so every horn eye has a **7.2 mm centre opening**. The driven side remains accessible for the manufacturer's central retaining screw. The four attachment holes use a 14 mm pitch circle; the horn is clocked 45° relative to the leg to free space near the dummy-side plugs.

The owner-provided servo photograph shows **two adjacent cable sockets on the dummy side**, below the shaft. Both printed cheeks sit at the same distance from the servo centre, with 5.25 mm nominal thickness. Local swept openings in the dummy cheek allow a nominal 20.5 mm-wide, 12.5 mm-deep plug envelope and a straight cable exit through the checked joint sweep. This envelope is inferred from the photograph; measure the supplied plug housings before printing all six legs. Do not trap a cable under a cheek or use it as a joint stop.

Print [the direct-horn fit gauge](../print/stl/14_direct_horn_fit_gauge.stl), one servo clamp and one complete leg first. The gauge checks the horn bolt circle, 7.2 mm shaft opening, 36.9 mm cheek span and 4.0/4.1/4.2 mm insert test bores. Trial-fit *both* plugs with the dummy-side cheek in place, move the unpowered leg through its range, and inspect the cable loop.

## H2D print setup

Slice at **100% scale in mm**. STLs sit on Z=0; inspect support and bridging before printing a full batch.

| Components | Starting setup | Orientation |
|---|---|---|
| Chassis, coxa, femur, tibia | PETG or tough nylon; 0.20 mm layers; 5–6 walls; 35–45% infill | Orient joint eyes for strong layer paths; support projecting cradles where needed |
| Dorsal deck, battery tray, controller plate | PETG; 4 walls; 25–35% infill | Broad base on the bed |
| Organic shell | PETG; 3–4 walls | Open side down; remove accessible dome supports |
| Separate side plates and clamp caps | PETG or nylon; 5 walls | Flat on the bed |
| Foot | TPU 95A; 4 walls | Check the internal slit and retention eye |

Inspect the thin bridge between the central shaft opening and each M3 head recess in the slicer; keep a continuous wall and remove any plug-window supports. PLA works for the gauge and low-load trial assembly, and [ruthex lists PLA as insert-compatible](https://www.ruthex.de/en/collections/gewindeeinsatze/products/ruthex-gewindeeinsatz-m3-100-stuck-rx-m3x5-7-messing-gewindebuchsen). Loaded legs should use a tougher, less heat-sensitive material; inspect PLA prototypes frequently for cracks at the horn eyes.

## DIN 7380 screws and inserts

All listed M3 assembly screws use **DIN 7380 / EN ISO 7380-1 button heads**. The modeled M3 head is 5.7 mm diameter × 1.65 mm high, with a 2 mm hex socket ([dimensional reference](https://www.accu.co.uk/api/product-datasheet?id=795623)). The CAD positions 262 screws, 112 simplified ruthex inserts and six foot locknuts individually.

Both cheeks are 5.25 mm thick. The driven side has a 1.5 mm head recess and the dummy side a **1.45 mm head recess**; both use **M3 × 6** screws into the metal horns. At the measured nominal stack, the driven screw stops about 0.45 mm before the inner horn face, while the dummy screw reaches about flush with it. Check the actual metal thread depth, plate thickness and central retaining hardware on one servo; the nominal dummy stack has no spare length. Use the manufacturer's central screws, whose thread is not modeled as generic M3.

Structural and cover screws are **M3 × 8**, except the 24 coxa/femur cheek-joint screws, which are **M3 × 10** for 4.75 mm nominal insert engagement. They use [ruthex RX-M3x5.7 heat-set inserts](https://www.ruthex.de/en/collections/gewindeeinsatze/products/ruthex-gewindeeinsatz-m3-100-stuck-rx-m3x5-7-messing-gewindebuchsen). Printed blind bores are **4.0 mm diameter and 6.0 mm deep**, with supporting bosses. The insert envelope is 4.6 mm diameter × 5.7 mm long. Tune hole compensation using the gauge and actual filament. Install inserts squarely with controlled heat, let them cool, then tighten.

The knee clamp has four straight driver ports through the removable femur cheek. Two small contact bosses seat it against the cheek; two cross-ties meet the side plate directly. The shell's four mounting screws are reached through roof ports. Remove the shell to reach the remaining screws. CAD reports no screw-to-print overlap and no blocked local straight driver paths in this service sequence. Confirm the shaft of your physical hex bit fits.

| Item | Quantity | Use |
|---|---:|---|
| 12 V STS3215 servo | 18 | Six of each yaw, hip and knee |
| Supplied driven and dummy-side horns | 18 + 18 | Direct to the printed cheeks |
| Manufacturer central horn screws | Per servo set | Retain original types |
| DIN 7380 M3 × 6 | 144 | Four per horn, both sides of 18 servos |
| DIN 7380 M3 × 8 | 88 | Covers and servo clamps |
| DIN 7380 M3 × 10 | 24 | Coxa and femur cheek joints |
| ruthex RX-M3x5.7 inserts | 112 | One per M3 × 8 or M3 × 10 location |
| DIN 7380 M3 × 25 + M3 locknut | 6 + 6 | Foot retention |
| M3 × 16 + M3 nuts | 4 + 4 | Controller board as required |
| Battery straps ≤15 mm | 2 | Battery restraint |

## Battery and electronics

The tray reserves **115 × 40 × 35 mm** for a 3S pack, excluding protruding connectors. A 3S lithium pack supplies 11.1 V nominal and reaches 12.6 V fully charged; it is not a regulated fixed 12 V rail. Secure it with two straps and a thin anti-slip pad, and route its lead toward the aft shell opening. Remove the pack for charging with a suitable charger.

The slotted controller plate is **108 × 75 mm** and reserves a **90 × 60 × 18 mm** generic board envelope on four removable 6 mm standoffs. Fit the actual controller and half-duplex TTL interface before drilling or relocating standoffs. Provide a regulated logic rail if the controller needs it.

The [Feetech 12 V specification](https://www.feetechrc.com/525603.html) lists 2.7 A stall current per servo. Eighteen simultaneously stalled servos would nominally total 48.6 A, a fault/peak scenario rather than normal consumption. Size battery, distribution, wiring and protection from measured duty cycles. Distribute servo power by leg instead of passing the full robot current through one small bus plug.

## Assembly order

1. **Trial fit.** Print the gauge, clamp and one leg set. Fit both metal horns and both dummy-side plugs to a real servo. Check shaft clearance, screw length, unplugging access and cable bend radius.
2. **Prepare inserts.** Fit 112 inserts to the printed 4.0 mm bores. Check every boss after cooling.
3. **Build chassis and coxae.** Install six yaw servos, attach the direct-horn coxa cheeks and integrated dummy-side bottom plates, then fit the hip servos and removable caps.
4. **Build femurs and knees.** Attach femur brackets directly to the hip horns. The widened local knee-cheek sections clear the knee clamp; close each removable side plate against its cross-ties with two M3 × 10 screws.
5. **Install tibiae and feet.** Attach each fork directly to the two knee horns with recessed M3 × 6 screws. Fit TPU feet, transverse M3 × 25 bolts and locknuts.
6. **Wire and close.** Route each pair of plugs through dummy-side openings with a free loop at every joint. Secure wiring to the fixed link, not the rotating horn. Fit the deck, strapped 3S pack, controller and shell.
7. **Calibrate.** Assign IDs 1–18, confirm directions and encoder zeros against the [joint map](../simulation/joint_map.json), and begin with slow unloaded motion.

## Checked movement

The neutral hip is +15° above horizontal; the tibia is 65° below horizontal, giving a −80° knee angle relative to the femur. Front/rear yaw is limited inward to 64° and outward to 35°; middle legs use ±35°. The hip is −20° to +30° absolute, and the knee −95° to 0° relative to the femur. Per-joint limits do not guarantee that arbitrary simultaneous poses are clear.

The checked front toe-contact pose is L1/L6 yaw −58.3°/+58.3°, hip −20°, knee 0°. The rear pair mirrors it. An eight-step coordinated path brings the TPU feet together without hard-part intersection; turning two neutral bent legs inward independently can collide. The nominal connector envelope was checked in **594 plug and straight-exit positions**. Actual flexible cables can bow elsewhere, so repeat the unpowered motion test with the real harness before a fast gait.

The model mass is approximately 2.346 kg including assumed battery, controller and hardware. The manufacturer quotes 10 kg·cm rated and 30 kg·cm stall torque at 12 V. Stall torque is not continuous torque. No physical load or fatigue test has been performed; establish payload and gait speed experimentally.

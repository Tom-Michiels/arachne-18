# Validation record

These checks establish internal consistency of this prototype's digital model. They do not substitute for a physical fit or load test.

| Check | Result | Evidence |
|---|---|---|
| Printable CAD validity | 14/14 valid, one solid each | [CAD report](../validation/cad_validation.json) |
| Print mesh validity | 14/14 watertight, one connected component each | [STL report](../validation/stl_validation.json) |
| Horn screw bearing support | 1,152 material samples below the 24 unique horn screw positions; all supported | [Horn report](../validation/horn_support_validation.json) |
| Assembly composition | 499 solids, including 18 servo references, 262 screws and 112 inserts | [CAD report](../validation/cad_validation.json) |
| Neutral interference | No overlap above 0.05 mm³ | [CAD report](../validation/cad_validation.json) |
| Sampled leg motion | 99 configurations without overlap above 0.2 mm³ | [Motion report](../validation/motion_validation.json) |
| Paired toe reach | 18 coordinated poses; TPU toes touch without hard-part interference | [Reach report](../validation/pair_contact_validation.json) |
| Dummy-side plugs | 594 sampled nominal plug and straight-exit positions without print overlap | [Cable report](../validation/cable_validation.json) |
| Screw accessibility | 262 positioned screws; no screw/print intersections or blocked local driver paths | [Fastener report](../validation/fastener_validation.json) |
| Native Onshape assembly | 499 instances; 480 fastened and 18 revolute mates; no feature errors | [Onshape report](../simulation/onshape_validation.json) |
| Native joint limits | 18 limits match the MuJoCo joint map | [Limit report](../simulation/onshape_motion_validation.json) |
| MuJoCo topology | 19 links, 18 hinges, 18 motors; 25 qpos / 24 qvel for free base | [Simulation report](../simulation/simulation_validation.json) |
| Inertia | Positive masses and inertias | [Simulation report](../simulation/simulation_validation.json) |
| Joint axes | All 18 perturbations affect the intended subtree | [Simulation report](../simulation/simulation_validation.json) |
| Standing | 10 s at 11.1, 12.0 and 12.6 V; six foot contacts each | [Simulation report](../simulation/simulation_validation.json) |
| Fixed-base sweep | 12 s; maximum tracking error after 2 s about 0.75° | [Simulation report](../simulation/simulation_validation.json) |
| Grounded body motion | 10 s, six continuous foot contacts after settling, no solver warnings | [Grounded report](../simulation/grounded_validation.json) |
| Animation | 100 frames, six contacts throughout, floating base | [Animation report](../validation/grounded_animation.json) |
| Reset | Reproducible MuJoCo and BAM state | [Simulation report](../simulation/simulation_validation.json) |

The 99 CAD poses sample the revised leg limits, hip 0/15/30° above horizontal and relative knee −95/−80/−65° on three representative legs. Other legs remain neutral. The cable check uses a nominal plug envelope estimated from the owner's servo photograph; actual plug dimensions, wire flex, full simultaneous gaits and continuous paths require physical checking.

The horn-bearing test checks two depths and two bearing radii around every hole on both faces of all three joint types. It was added after a visual inspection found unsupported knee horn screws in an earlier revision. The [corrected knee view](../assets/cad-horn-detail.png) shows the full dummy-side tibia eye.

The simulation uses collision proxies and estimated masses. Its quiet standing results do not validate a walking controller, payload or actuator thermal capacity. No physical assembly, FEA, fatigue or impact test has been completed.

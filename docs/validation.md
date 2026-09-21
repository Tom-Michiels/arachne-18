# Validation record

These checks establish internal consistency of this prototype's digital model. They do not substitute for a physical fit or load test.

| Check | Result | Evidence |
|---|---|---|
| Printable CAD validity | 17/17 valid, one solid each | [CAD report](../validation/cad_validation.json) |
| Print mesh validity | 17/17 watertight, one connected component each | [STL report](../validation/stl_validation.json) |
| Assembly composition | 155 solids, including 18 servo references | [CAD report](../validation/cad_validation.json) |
| Neutral interference | No overlap above 0.05 mm³ | [CAD report](../validation/cad_validation.json) |
| Sampled leg motion | 54 configurations without overlap above 0.2 mm³ | [Motion report](../validation/motion_validation.json) |
| MuJoCo topology | 19 links, 18 hinges, 18 motors; 25 qpos / 24 qvel for free base | [Simulation report](../simulation/simulation_validation.json) |
| Inertia | Positive masses and inertias | [Simulation report](../simulation/simulation_validation.json) |
| Joint axes | All 18 perturbations affect the intended subtree | [Simulation report](../simulation/simulation_validation.json) |
| Standing | 10 s at 11.1, 12.0 and 12.6 V; six foot contacts each | [Simulation report](../simulation/simulation_validation.json) |
| Fixed-base sweep | 12 s; maximum tracking error after 2 s about 0.75° | [Simulation report](../simulation/simulation_validation.json) |
| Grounded body motion | 10 s, six continuous foot contacts after settling, no solver warnings | [Grounded report](../simulation/grounded_validation.json) |
| Animation | 100 frames, six contacts throughout, floating base | [Animation report](../validation/grounded_animation.json) |
| Reset | Reproducible MuJoCo and BAM state | [Simulation report](../simulation/simulation_validation.json) |

The 54 CAD poses sample yaw −20/0/+20°, hip 0/15/30° above horizontal and relative knee −95/−80/−65° on a diagonal leg and a middle leg. Other legs remain neutral. Cable loops, detailed fasteners, simultaneous full-leg gaits and continuous paths are not covered by this sample.

The simulation uses collision proxies and estimated masses. Its quiet standing results do not validate a walking controller, payload or actuator thermal capacity. No physical assembly, FEA, fatigue or impact test has been completed.

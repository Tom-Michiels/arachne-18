# Simulating ARACHNE in MuJoCo

[Back to the project](../README.md) · [BAM model](bam-model.md) · [Validation](validation.md)

## Installation

Use **Python 3.12** and the pinned packages in `simulation/requirements.txt`. Run these commands from the repository root:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r simulation/requirements.txt
python simulation/simulate.py --headless --seconds 10
```

On Windows, activate with `.venv\Scripts\activate` instead. A headless run prints the final joint positions, pre-friction motor torques, body position and contact count. The default command holds the CAD-neutral joint targets at 12 V.

For an interactive viewer on macOS:

```sh
mjpython simulation/simulate.py --seconds 300
```

On Linux/Windows, use `python simulation/simulate.py --seconds 300`. MuJoCo's passive viewer requires `mjpython` on macOS because its GUI must run on the main thread.

## Standing, bench motion and logs

```sh
# Floating robot with a nominal 3S supply
python simulation/simulate.py --headless --voltage 11.1 --seconds 10 --log stand_run.json

# Raised, fixed base for an 18-joint exercise
mjpython simulation/simulate.py --fixed --mode sweep --seconds 300

# Numerical regression checks
python simulation/validate.py
```

`stand` commands all 18 joints to zero. `sweep` uses a 6° amplitude, 0.25 Hz sinusoid with a two-second ramp. The fixed model raises the chassis by 180 mm so the feet are clear of the floor. Use the fixed model for this exercise; a fixed chassis at standing height would force the feet through the ground. Neither mode is a walking gait controller.

The optional log records state every 20 simulation steps. Time is in seconds, angles in radians, distances in metres, and torques in Nm. The torque field is named `torque_before_friction_Nm`: it is the motor torque sent to MuJoCo before the modeled joint friction acts.

## Grounded body motion

The README animation uses the floating-base robot, not the raised test fixture. An inverse-kinematics target gently changes body height by ±8 mm at 0.25 Hz while preserving the nominal horizontal foot positions. BAM and MuJoCo solve the actual motion and floor contact. The recorded 10-second test maintains six foot contacts after settling and has no solver warnings. This is a body-height exercise, not a walking gait.

```sh
# macOS viewer; use python instead on Linux/Windows
mjpython simulation/grounded_demo.py --seconds 300
python simulation/grounded_demo.py --headless --seconds 10 --report grounded_run.json
```

See [grounded validation](../simulation/grounded_validation.json) and [animation contact checks](../validation/grounded_animation.json).

## Files

| File | Purpose |
|---|---|
| `arachne.xml` | Floating base, ground plane, foot contacts |
| `arachne_fixed.xml` | Raised static base for joint tests |
| `meshes/` | 155 visual CAD meshes, in metres and in each link's local frame |
| `joint_map.json` | Servo IDs, names, parent/child links, axes and limits |
| `mass_properties.json` | Link mass, centre of mass, inertia and assumptions |
| `simulate.py` | BAM initialization, target delay, integration, reset and viewer |
| `validate.py` | Topology, kinematics, dynamics and repeatability checks |
| `bam_sts3215_12v_approx_m6.json` | Provisional 12 V M6 model |
| `bam_sts3215_7p4v_m6_original.json` | Unmodified upstream identification snapshot |
| `fit_bam_12v.py` | Reproduces the 12 V parameter fit |
| `simulation_validation.json` | Recorded validation results |

These meshes are **not the print STLs**. Print meshes were rotated onto the bed and use mm; simulation meshes use SI and the correct link frames. Substituting one for the other will misplace or resize the robot.

## Coordinates and joint targets

The MJCF uses **m, kg, s, rad, N and Nm**. Nineteen rigid links collect the 155 solids into one body and three moving links per leg. Fastened parts have no separate dynamic degree of freedom.

`q = 0` is the CAD neutral pose: the hip geometry is already inclined +15° and the knee is −80° relative to the femur. Joint values are offsets from that pose.

| Joint | Servo IDs | Range relative to neutral | Neutral geometry |
|---|---|---|---|
| `L1_yaw` … `L6_yaw` | 1, 4, 7, 10, 13, 16 | −20° to +20° | Radial coxa |
| `L1_hip` … `L6_hip` | 2, 5, 8, 11, 14, 17 | −15° to +15° | +15° above horizontal |
| `L1_knee` … `L6_knee` | 3, 6, 9, 12, 15, 18 | −15° to +15° | −80° relative to femur |

Leg azimuths are 45°, 90°, 135°, 225°, 270° and 315°. Yaw axes are +Z. Hip and knee axes are `[sin(azimuth), -cos(azimuth), 0]` in the neutral world frame; positive hip motion lifts the leg. See the JSON map for exact origins. Real servo encoder centres and directions still require hardware calibration.

## Write a controller

Save a controller beside `simulation/simulate.py`, or add that directory to your Python import path:

```python
import numpy as np
from simulate import Robot

robot = Robot(fixed=True, voltage=12.0)
target = np.zeros(18)
target[1] = np.deg2rad(5)  # L1 hip: 5 degrees above CAD neutral
for _ in range(10000):
    robot.step(target)

q = robot.data.qpos[robot.controller.qpos_indexes]
print(np.rad2deg(q))
robot.reset()
```

Each `step()` checks the target shape, clamps joint limits, applies the inherited command delay, updates BAM and advances MuJoCo by **1 ms**. `reset()` resets both the MuJoCo state and BAM's firmware target smoothing.

**Do not write target angles into `data.ctrl`.** The XML actuators are torque motors. BAM fills `data.ctrl` with motor torques; it is not a MuJoCo position-actuator interface. Opening the XML in a generic viewer gives the mechanism and geometry but does not load the BAM controller.

A gait controller can generate the 18 target angles passed to `Robot.step()`. Use the joint map for inverse kinematics and respect the current limits. Full multi-leg collision and stability studies remain future work.

## Mass and contact assumptions

The estimated total mass is **2.4496 kg**. Servo mass is 55 g each. Printed parts use an effective density of 700 kg/m³ and TPU 1000 kg/m³; the battery is assumed to weigh 190 g and the controller 45 g. Wiring and hardware are added as lumped mass. Replace those values with slicer estimates and measurements for load studies.

CAD volume integrals supply centres of mass and inertia, scaled to these masses and combined with the parallel-axis theorem. Servo, battery and controller mass distributions are approximate.

Detailed meshes are visual only. Contact uses 18 servo boxes, a chassis ellipsoid, tibia capsules and six foot spheres. These proxy shapes do not prove the detailed CAD is collision-free. Collision geoms are in group 3 and hidden by the supplied viewer; enable that group in MuJoCo to inspect them.

## Rebuild and troubleshoot

See [development](development.md) for CAD regeneration and export. After changing dimensions, update link origins, inertial assumptions, joint limits and collision proxies together, then rerun validation.

| Symptom | Action |
|---|---|
| macOS viewer complains about the main thread | Launch with `mjpython` from the activated environment |
| Robot falls after opening XML directly | Start `simulate.py`; plain XML loading does not activate BAM |
| Meshes are huge, rotated or misplaced | Use the supplied simulation meshes, not the print STLs |
| BAM API or smoothing attribute errors | Install the exact pinned requirements; upstream development API differs |
| Headless graphics fails on a server | The normal headless physics test needs no renderer; image capture needs a supported GL backend |
| New hardware differs from the prediction | Load a measured 12 V parameter file with `--parameters path/to/model.json` and update mass assumptions |

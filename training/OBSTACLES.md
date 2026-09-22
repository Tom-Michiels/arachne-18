# Stones, rocks and bending grass

Uneven terrain includes discrete obstacles as well as height variations. The
reference simulator now includes individual collision stones and passive,
bending grass tufts. [Watch the obstacle films](https://tom-michiels.github.io/arachne-18/#terrain-pebbles).

## Physical models

- **Stones:** individually placed, partly buried ellipsoids with random size,
  height, orientation and position. They are fixed to the ground in this first
  model; rolling or displaced stones are a later extension.
- **Grass:** three capsule-shaped blades per tuft, mounted on two passive
  spring-and-damper hinges. Contact bends the tuft and the spring restores it.
  Tufts interact with the robot and ground, but not with each other.
  This is an uncalibrated mechanical proxy, not a botanical or soft-soil model.
- **Mixed obstacles:** both models in the same scene. Heights are actual metres;
  the videos do not exaggerate them. A clear spawn area prevents initial overlap.

The actor still receives IMU gravity and angular velocity, commands and gait
phase. It has no obstacle map or camera. This tests a gait's ability to tolerate
contact; it does not yet demonstrate visual route planning or deliberate
selection of individual footholds. The added objects run in reference MuJoCo
with full BAM servo dynamics. They are not represented by the experimental
Metal heightfield backend.

## Curriculum

[obstacle_curriculum.json](obstacle_curriculum.json) is a separate progression,
so the earlier heightfield results retain their original meaning:

| Stage | Physical obstacle | Command speed |
|---|---|---:|
| Flat admission | Original plane | 14 cm/s |
| Small pebbles | 4–8 mm protruding stones | 10 cm/s |
| Short grass | 18–30 mm stem lengths | 10 cm/s |
| Larger stones | 8–18 mm protruding stones | 10 cm/s |
| Stones and grass | 8–18 mm stones with 20–40 mm grass | 10 cm/s |
| Tall grass | 30–60 mm stems | 10 cm/s |
| Large rocks | 25–50 mm protruding rocks | 10 cm/s |

These are curriculum targets, not a claim that every stage is mastered.
Promotion uses two independent seed batches, intermediate headings, walking
turns, IMU noise and flat-ground retention after refinement. Training replays
25% flat-ground tasks. It rewards progress and tracking while penalizing tilt,
bouncing, slipping and abrupt motor motion. Failed promotion preserves the last
accepted policy. Future work on large rocks may need more expressive control,
contact sensing and perception rather than only a higher open-loop leg lift.

Encounter gates additionally require recorded foot–stone contact or vegetation
contact; walking through an empty patch cannot pass solely through forward
progress. Solid stone contact is included in support-foot slip and non-foot
collision checks. Flexible grass contact is tracked separately: brushing a
blade is not treated as striking the body against a rock. Grass joints are
excluded from robot motor-speed metrics, and grass tips do not redefine the
load-bearing ground-clearance reference.

## Initial results and videos

The existing general controller was evaluated on three layouts per obstacle
class, using a 10 cm/s forward command for 12 seconds:

| Obstacle class | Passed examples | Result |
|---|---:|---|
| Small pebbles | 3/3 | 8.37–8.77 cm/s actual speed; 0.43–0.62° tilt RMS |
| Short grass | 3/3 | 9.11–9.15 cm/s actual speed; 0.06–0.08° tilt RMS |
| Larger stones | 0/3 | Tracking and clearance-rate limits exceeded |
| Stones and grass | 0/3 | Tracking and clearance-rate limits exceeded |

The two published films show seed 701 at simulation-time playback. The pebble
film records 486 control steps with foot–stone contact. The grass film records
98 control steps with robot–vegetation contact and visible passive bending.
Both recordings pass their gates. These forward examples are not equivalent to
full curriculum promotion. Larger obstacles remain unmastered; failed trials
are retained in the [assessment report](results/obstacle_admission.json).

The subsequent full admission check passes both flat batches. For small stones,
29/30 and 28/30 held-out cases pass; the second batch falls below the required
95%. Three cases exceed velocity-tracking limits. No stone-stage promotion is
claimed, and later stages were not attempted by that admission run.
[Full admission results](results/obstacle_curriculum_admission.json).

## Reproduce

```sh
python -m unittest discover -s training -p 'test_*.py'
python training/assess_obstacles.py
python training/render_obstacles.py
python training/curriculum.py --config training/obstacle_curriculum.json \
  --assess-only --max-stage 6 --out training/runs/obstacle-admission
```

To refine a failing stage after admission checks, omit `--assess-only` and set
a training budget, for example `--generations 8 --population 24`. The curriculum
stops at the first stage that cannot be promoted. Tall grass and large rocks
are proposed later stages, not validated capabilities. Spring stiffness,
damping, stem geometry and terrain friction need measurements before this
proxy can predict performance in real grass.

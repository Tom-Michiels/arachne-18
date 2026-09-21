# Start on another computer

The repository is public. Clone it without signing in:

```sh
git clone https://github.com/Tom-Michiels/arachne-18.git
cd arachne-18
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r simulation/requirements.txt
python simulation/validate.py
python simulation/grounded_demo.py --headless --seconds 10
```

On Windows, activate with `.venv\Scripts\activate`. For an interactive viewer, run `python simulation/grounded_demo.py` on Linux/Windows or `mjpython simulation/grounded_demo.py` on macOS.

Use `git pull` to retrieve later project updates. GitHub stores all required model assets directly; Git LFS and Onshape credentials are not required.

## Training integration

The package supplies a physical model and BAM actuator runner, not a trained locomotion policy. An RL training framework should wrap `simulation/simulate.py`'s `Robot` class:

- Reset with `robot.reset()` at the beginning of each episode.
- Supply 18 joint targets in radians, relative to CAD neutral, using the order in `joint_map.json`.
- Call `robot.step(target)` for each 1 ms physics tick; for a 50 Hz policy, hold the action for 20 ticks.
- Read joint angles and velocities using `robot.controller.qpos_indexes` and `robot.controller.dof_indexes`. Body orientation/velocity and contacts are available in `robot.data`.
- Define the observation, reward, termination rules, action scaling and terrain in the training environment.
- Run physics headlessly for training. No GPU renderer is needed unless observations include images.

BAM currently runs through its Python/CPU MuJoCo integration. The provided model is not automatically compatible with MJX/JAX batched GPU training. Loading the XML through another simulator interface bypasses the BAM controller unless that integration is explicitly implemented.

The 12 V actuator parameters are a datasheet-based approximation; use measured parameters and masses before transferring a learned policy to hardware. See [the BAM model notes](bam-model.md) and [the full simulation guide](simulation.md).

# Regenerating CAD and simulation assets

The authoritative editable source is `src/build_cad.py`. STEP exports contain solid geometry and assembly placement, but do not retain CadQuery feature history when imported into Onshape. Constants at the top of the builder control the main dimensions; other contours are defined in its construction functions. Editing `cad/parameters.json` alone does not modify the geometry.

## CAD environment

Use a separate Python 3.11 environment for CadQuery:

```sh
python3.11 -m venv .venv-cad
source .venv-cad/bin/activate
python -m pip install -r src/requirements-cad.txt
python src/build_cad.py
python src/check_cad.py
python src/check_motion.py
```

The builder writes into ignored `build/`, including STEP files, bed-oriented STLs, a print BOM and `.cad_cache/` BREP solids. The checks use that cache. `check_cad.py` checks neutral solid interference and creates technical renders. `check_motion.py` checks the 54 sampled representative-leg configurations. Run `python src/check_print_meshes.py --stl-dir build/STL --output build/stl_validation.json` to verify regenerated STLs before replacing release assets. Release results are in `validation/stl_validation.json`.

`src/render_gallery.py` regenerates the four README CAD images directly from the simulation meshes. It needs VTK, supplied by the CAD environment, and writes into `assets/`.

## MuJoCo export

```sh
python src/export_mujoco.py --cad-cache build/.cad_cache --output simulation
```

The exporter writes 155 link-local mesh assets, two MJCF files, the joint map, CAD instance metadata and mass properties. It preserves the runtime scripts and actuator parameter files. CAD inputs use mm; MJCF and mesh outputs use metres.

Joint origins, collision proxy dimensions and mass assumptions in the exporter are specific to this design. Keep them synchronized with CAD changes. The motion checker also contains fixed reference dimensions and must be updated when the mechanism changes.

Switch to the Python 3.12 simulation environment afterward:

```sh
deactivate
source .venv/bin/activate
python simulation/validate.py
```

Review generated changes before copying `build/` STEP/STL outputs into `cad/` and `print/stl/`. Update the validation reports and rendered media with the same design revision.

## Names and Onshape identity

Repository part names, filenames and documentation are English. The original native Onshape import used earlier internal part labels. `cad/onshape_name_map.json` maps English instance labels back to those native identifiers; Onshape instance IDs in the mate plan remain stable. These identifiers are retained for traceability, not as user-facing instructions.

The Git repository deliberately excludes virtual environments, BREP caches, temporary downloads, session logs and credentials. No API key is needed to run the local simulation or rebuild the CAD.


## Native assembly authoring

`src/onshape_mates.py` is the API authoring source used for the native mates. It reads the checked-in mate plan and English-to-native name map. It resumes by feature name and refuses to reuse an errored feature. Its `--stage verify` mode checks the native mate counts, feature statuses, fixed chassis and neutral transforms. It does not verify animation.

The checked-in plan targets the existing project document and its exact instance IDs. Do not use it against a different document without rebuilding the plan. For maintenance, supply your own read/write Onshape key in an external mode-0600 JSON file with `accessKey` and `secretKey` fields; never commit that file. Run `python src/onshape_mates.py --help` for options. API credentials are unnecessary for local CAD builds, simulation or training integration.

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
python src/check_pair_contact.py
python src/check_cables.py
```

The builder writes into ignored `build/`, including STEP files, bed-oriented STLs, a print BOM and `.cad_cache/` BREP solids. It also checks 262 screw placements, 112 insert placements, local driver passages and 1,152 horn-bearing samples. `check_cad.py` checks neutral structural interference and creates technical renders. `check_motion.py` checks 99 sampled representative-leg configurations; `check_pair_contact.py` checks the coordinated front/rear toe-reach path. `check_cables.py` sweeps a nominal two-plug envelope over the moving dummy-side cheeks. Run `python src/check_print_meshes.py --stl-dir build/STL --output build/stl_validation.json` before replacing release assets. Release reports are in `validation/`.

`src/render_gallery.py` regenerates the four full-robot CAD images directly from the simulation meshes. `src/render_leg_top.py` renders a close orthographic view of a single leg, and `src/render_horn_detail.py` shows the supported knee horn screws, both from the BREP cache. These renderers need VTK from the CAD environment and write into `assets/`.

## MuJoCo export

```sh
python src/export_mujoco.py --cad-cache build/.cad_cache --output simulation
```

The exporter writes 499 link-local mesh assets, two MJCF files, the joint map, CAD instance metadata and mass properties. It preserves the runtime scripts and actuator parameter files. CAD inputs use mm; MJCF and mesh outputs use metres.

Joint origins, collision proxy dimensions and mass assumptions in the exporter are specific to this design. Keep them synchronized with CAD changes. The motion checker also contains fixed reference dimensions and must be updated when the mechanism changes.

Switch to the Python 3.12 simulation environment afterward:

```sh
deactivate
source .venv/bin/activate
python simulation/validate.py
```

Review generated changes before copying `build/` STEP/STL outputs into `cad/` and `print/stl/`. Update the validation reports and rendered media with the same design revision.

## Names and Onshape identity

Repository part names, filenames and documentation are English. The original native Onshape import used earlier internal part labels. `cad/onshape_name_map.json` maps the original English instance labels back to those native connector identifiers; the revised imported part names are English. These identifiers are retained for native-mate traceability, not as user-facing instructions.

The Git repository deliberately excludes virtual environments, BREP caches, temporary downloads, session logs and credentials. No API key is needed to run the local simulation or rebuild the CAD.


## Native assembly authoring

`src/onshape_mates.py` is the API authoring source used for the native mates. It reads the checked-in mate plan and English-to-native name map. It resumes by feature name and refuses to reuse an errored feature. `src/refresh_onshape_plan.py` rebuilds the 499-instance, 480-fastened, 18-revolute plan after a STEP revision; `src/update_onshape_limits.py --apply` aligns the native revolute limits with the joint map. The `onshape_mates.py --stage verify` mode checks native mate counts, feature statuses, fixed chassis and neutral transforms. It does not verify animation.

The checked-in plan targets the existing project document and its exact instance IDs. Do not use it against a different document without rebuilding the plan. For maintenance, supply your own read/write Onshape key in an external mode-0600 JSON file with `accessKey` and `secretKey` fields; never commit that file. Run `python src/onshape_mates.py --help` for options. API credentials are unnecessary for local CAD builds, simulation or training integration.

After updating both source STEP blobs in the existing Onshape document, refresh and verify the native assembly with:

```sh
python src/refresh_onshape_plan.py --key-file /path/to/onshape-key.json
python src/onshape_mates.py --key-file /path/to/onshape-key.json --stage all
python src/update_onshape_limits.py --key-file /path/to/onshape-key.json --apply
python src/onshape_mates.py --key-file /path/to/onshape-key.json --stage verify
```

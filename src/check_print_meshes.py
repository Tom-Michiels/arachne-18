"""Check print STLs for watertightness, connected components and bed placement."""
from pathlib import Path
import argparse,json
import trimesh
ROOT=Path(__file__).resolve().parent.parent
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--stl-dir',type=Path,default=ROOT/'print/stl')
p.add_argument('--output',type=Path,default=ROOT/'validation/stl_validation.json')
a=p.parse_args();report={}
for path in sorted(a.stl_dir.glob('*.stl')):
 mesh=trimesh.load_mesh(path)
 components=len(mesh.split(only_watertight=False))
 report[path.name]=dict(watertight=bool(mesh.is_watertight),components=components,extents_mm=mesh.extents.tolist(),min_z_mm=float(mesh.bounds[0,2]))
 assert mesh.is_watertight and components==1 and abs(mesh.bounds[0,2])<.001,path.name
assert len(report)==17,'Expected 17 print meshes'
a.output.write_text(json.dumps(report,indent=2))
print('PASS: 17 watertight single-component print STLs, each on Z=0')

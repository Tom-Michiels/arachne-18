"""Record real-time, true-scale terrain videos in original MuJoCo + full BAM."""
import hashlib
import json
import imageio.v2 as imageio
from PIL import Image
from gait import ROOT,load
from evaluate import evaluate
from curriculum import gate


def main():
    config=json.loads((ROOT/'training/terrain_curriculum.json').read_text())
    policy=ROOT/'training/policies/omni.json'
    cases=[(2,'rolling','Rolling ground / up to 4 mm'),
           (3,'slope','Smooth slope / up to 2 degrees'),
           (4,'steps','Low plateaus / 4 mm')]
    for index,name,label in cases:
        stage=config['stages'][index]
        path=ROOT/f'assets/arachne-terrain-{name}.mp4'
        result=evaluate(load(policy),[.1,0,0],12.,terrain=stage['terrain'],seed=701,
                        video=path,width=1280,height=800,
                        video_label=f'{label}  /  True scale  /  MuJoCo + BAM')
        result.update(policy='training/policies/omni.json',policy_sha256=hashlib.sha256(policy.read_bytes()).hexdigest(),
                      playback='Real time: one video second per simulated second',
                      geometry='Original collision model; terrain height is not exaggerated',
                      gate_failures=gate(result,stage,config),seed=701)
        path.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
        assert not result['gate_failures'],result['gate_failures']
        reader=imageio.get_reader(str(path));frame=reader.get_data(450);reader.close()
        Image.fromarray(frame).save(path.with_suffix('.jpg'),quality=90)
        print(name,'recorded and checked',flush=True)


if __name__=='__main__':main()

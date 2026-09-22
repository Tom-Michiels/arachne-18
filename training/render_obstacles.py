"""Render actual pebble and passive-grass encounters at native simulation time."""
import hashlib
import json
import imageio.v2 as imageio
from gait import ROOT,load
from evaluate import evaluate
from curriculum import gate


def main():
    config=json.loads((ROOT/'training/obstacle_curriculum.json').read_text())
    policy=ROOT/'training/policies/omni.json'
    for index,name,label in [(1,'pebbles','Discrete stones / 4-8 mm'),(2,'grass','Bending grass proxies / 18-30 mm')]:
        stage=config['stages'][index];out=ROOT/f'assets/arachne-terrain-{name}.mp4'
        r=evaluate(load(policy),[.1,0,0],12.,terrain=stage['terrain'],seed=701,
            video=out,width=1280,height=800,video_label=label+' / MuJoCo + BAM')
        r.update(policy='training/policies/omni.json',policy_sha256=hashlib.sha256(policy.read_bytes()).hexdigest(),
                 seed=701,gate_failures=gate(r,stage,config),playback='One video second per simulated second')
        out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n')
        assert not r['gate_failures'],r['gate_failures']
        reader=imageio.get_reader(str(out));imageio.imwrite(str(out.with_suffix('.jpg')),reader.get_data(450));reader.close()
        print(name,'passed',r['rock_foot_contact_steps'],r['vegetation_contact_steps'],flush=True)


if __name__=='__main__':main()

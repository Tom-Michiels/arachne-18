"""Record the faster forward gait at real simulation time, including start/stop."""
import argparse
import hashlib
import json
from gait import ROOT, load
from evaluate import evaluate
from benchmark_speed import passes


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--policy',type=str,default='training/policies/sprint.json')
    ap.add_argument('--command',type=float,default=.34)
    ap.add_argument('--out',type=str,default='assets/arachne-faster-stride.mp4')
    args=ap.parse_args()
    policy=ROOT/args.policy;out=ROOT/args.out
    schedule=[(0,[0,0,0]),(.5,[args.command,0,0]),(17,[0,0,0])]
    r=evaluate(load(policy),[0,0,0],20.,video=out,width=1280,height=800,
               schedule=schedule,video_label='Longer steps / Smooth forward gait / MuJoCo + BAM')
    r.update(policy=str(policy.relative_to(ROOT)),policy_sha256=hashlib.sha256(policy.read_bytes()).hexdigest(),
             playback='1 second of video per 1 second of simulated physics',
             faster_gait_gates_passed=passes(r))
    out.with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n')
    import imageio.v2 as imageio
    reader=imageio.get_reader(str(out));imageio.imwrite(str(out.with_suffix('.jpg')),reader.get_data(400));reader.close()
    print(json.dumps(r,indent=2))


if __name__=='__main__':main()

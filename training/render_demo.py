"""Capture continuous start, walking, direction changes, turning and stop."""
import argparse
import hashlib
import json
from pathlib import Path
from gait import ROOT, load
from evaluate import evaluate

SCHEDULE=[(0,[0,0,0]),(1,[.14,0,0]),(7,[0,.12,0]),(12,[-.12,0,0]),
          (17,[.09,-.09,0]),(22,[0,0,.4]),(29,[.10,0,-.3]),(36,[0,0,0])]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--policy',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=ROOT/'assets/arachne-learned-omni.mp4')
    ap.add_argument('--forward',action='store_true')
    ap.add_argument('--fast',action='store_true',help='Longer-stride speed and direction showcase')
    args=ap.parse_args()
    schedule=[(0,[0,0,0]),(1,[.14,0,0]),(11,[0,0,0])] if args.forward else SCHEDULE
    seconds=14. if args.forward else 40.
    if args.fast:
        schedule=[(0,[0,0,0]),(1,[.14,0,0]),(5,[.26,0,0]),(12,[0,.24,0]),
                  (18,[-.24,0,0]),(24,[.17,-.17,0]),(30,[0,0,.35]),
                  (34,[.20,0,-.3]),(40,[0,0,0])]
        seconds=44.
    result=evaluate(load(args.policy),[0,0,0],seconds,
                    video=args.out,width=1280,height=800,schedule=schedule)
    result['policy']=str(args.policy)
    result['policy_sha256']=hashlib.sha256(args.policy.read_bytes()).hexdigest()
    result['playback']='1 second of video per 1 second of simulated physics'
    args.out.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()

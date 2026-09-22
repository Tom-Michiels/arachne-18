"""Capture continuous start, walking, direction changes, turning and stop."""
import argparse
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
    args=ap.parse_args()
    schedule=[(0,[0,0,0]),(1,[.14,0,0]),(11,[0,0,0])] if args.forward else SCHEDULE
    result=evaluate(load(args.policy),[0,0,0],14. if args.forward else 40.,
                    video=args.out,width=1280,height=800,schedule=schedule)
    args.out.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()

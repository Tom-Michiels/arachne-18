"""Align the 18 native revolute limits with the checked MuJoCo joint map."""
from pathlib import Path
import argparse
import copy
import json
from urllib.parse import quote
from onshape_mates import Client, ROOT, OUT

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--key-file',type=Path,required=True)
parser.add_argument('--apply',action='store_true',help='Write the checked limits to Onshape')
args=parser.parse_args()
client=Client(args.key_file)
map_joints=json.loads((ROOT/'simulation/joint_map.json').read_text())['joints']
snapshot=client.call('GET','/features')
by_name={feature['name']:feature for feature in snapshot['features']}

def parameter(feature,identifier):
    return next(p for p in feature['parameters'] if p['parameterId']==identifier)

for joint in map_joints:
    name='R_'+joint['name']
    original=by_name[name]
    desired=joint['range_delta_deg']
    actual=[parameter(original,pid)['expression'] for pid in ('limitAxialZMin','limitAxialZMax')]
    target=[f'{value} deg' for value in desired]
    if actual==target:
        continue
    print(name,actual,'->',target,flush=True)
    if not args.apply:
        continue
    feature=copy.deepcopy(original)
    parameter(feature,'limitsEnabled')['value']=True
    for pid,expression in zip(('limitAxialZMin','limitAxialZMax'),target):
        p=parameter(feature,pid)
        p['expression']=expression
        p['isNull']=False
    result=client.call('POST','/features/featureid/'+quote(feature['featureId'],safe=''),
                       {'feature':feature})
    assert result['featureState']['featureStatus']=='OK',(name,result['featureState'])

if args.apply:
    snapshot=client.call('GET','/features')
    by_name={feature['name']:feature for feature in snapshot['features']}
    errors={fid:state for fid,state in snapshot['featureStates'].items()
            if state.get('featureStatus')!='OK'}
    limits={}
    for joint in map_joints:
        name='R_'+joint['name'];feature=by_name[name]
        current=[parameter(feature,pid)['expression']
                 for pid in ('limitAxialZMin','limitAxialZMax')]
        expected=[f'{value} deg' for value in joint['range_delta_deg']]
        assert current==expected,(name,current,expected)
        limits[name]=current
    assert not errors,errors
    report=dict(revolute_count=len(limits),native_limits_deg=limits,feature_errors=errors)
    path=OUT/'onshape_motion_validation.json'
    path.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Native revolute limits verified: {len(limits)}',flush=True)

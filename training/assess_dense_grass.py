"""Three forward layouts of the dense-grass video patch; no stage promotion."""
import copy
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from gait import ROOT,load
from evaluate import evaluate
from curriculum import gate


def run(seed):
    config=json.loads((ROOT/'training/obstacle_curriculum.json').read_text())
    stage=copy.deepcopy(config['stages'][2]);stage['terrain']['grass_bounds_m']=[.30,1.3,-.48,.48]
    r=evaluate(load(ROOT/'training/policies/omni.json'),[.1,0,0],12.,terrain=stage['terrain'],seed=seed)
    return dict(seed=seed,gate_failures=gate(r,stage,config),metrics=r)


def main():
    with ProcessPoolExecutor(3) as pool:rows=list(pool.map(run,[701,702,703]))
    report=dict(scope='Three forward dense-grass layouts; not full curriculum admission',
        policy='training/policies/omni.json',policy_sha256=hashlib.sha256((ROOT/'training/policies/omni.json').read_bytes()).hexdigest(),
        tuft_spacing_m=.03,blades_per_tuft=7,nominal_blades_per_square_m=7/.03**2,
        prior_nominal_blades_per_square_m=3/.16**2,cases=rows)
    (ROOT/'training/results/dense_grass_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    for row in rows:print(row['seed'],row['gate_failures'],row['metrics']['vegetation_contact_steps'],flush=True)


if __name__=='__main__':main()

"""Check physical obstacle surfaces, passive vegetation and encounter gates."""
import json
import unittest
import mujoco
import numpy as np
from gait import ROOT,load
from terrain import make_model,height_below
from evaluate import evaluate
from curriculum import gate


class ObstacleTests(unittest.TestCase):
    def test_rocks_are_collision_surfaces_and_seeded(self):
        spec=dict(kind='rocks',rock_height_m=[.004,.008])
        m,a=make_model(spec,72);_,b=make_model(spec,72)
        self.assertEqual(a,b)
        d=mujoco.MjData(m);mujoco.mj_resetDataKeyframe(m,d,0);mujoco.mj_forward(m,d)
        for rock in a['obstacles'][::29]:
            x,y=rock['xy'];self.assertAlmostEqual(height_below(m,d,x,y),rock['height_m'],places=7)
            self.assertGreater(np.hypot(x,y)-.035,.38)
        self.assertEqual(m.nq,25)

    def test_grass_is_passive_and_bends_back(self):
        m,info=make_model(dict(kind='grass',grass_spacing_m=.6),73)
        self.assertGreater(info['passive_dofs'],0);self.assertEqual(m.nu,18)
        d=mujoco.MjData(m);mujoco.mj_resetDataKeyframe(m,d,0)
        # Passive vegetation follows the original 25 robot coordinates.
        d.qpos[25]=.35
        for _ in range(1500):mujoco.mj_step(m,d)
        self.assertLess(abs(d.qpos[25]),.15)
        grass=info['obstacles'][0]
        self.assertAlmostEqual(height_below(m,d,*grass['xy']),0.,places=7)

    def test_dense_patch_has_physical_blades_and_passive_joints(self):
        spec=dict(kind='grass',grass_spacing_m=.03,grass_blades_per_tuft=7,
                  grass_spread_m=.014,grass_bounds_m=[.5,.62,-.06,.06])
        m,info=make_model(spec,701);tufts=len(info['obstacles'])
        self.assertGreaterEqual(tufts,16)
        names=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,i) or '' for i in range(m.ngeom)]
        blades=[i for i,n in enumerate(names) if n.startswith('obstacle_grass_')]
        self.assertEqual(len(blades),7*tufts)
        self.assertTrue(all(m.geom_contype[i]!=0 for i in blades))
        self.assertEqual(info['passive_dofs'],2*tufts)
        self.assertEqual(m.nu,18)

    def test_passing_requires_actual_obstacle_exposure(self):
        c=json.loads((ROOT/'training/obstacle_curriculum.json').read_text());s=c['stages'][1]
        r=evaluate(load(ROOT/'training/policies/omni.json'),[.1,0,0],2.)
        self.assertIn('rock_foot_contact_steps',gate(r,s,c))


if __name__=='__main__':unittest.main()

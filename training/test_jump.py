"""Jump clearance matches MuJoCo geometry distance even when the body tilts."""
import unittest
import mujoco
import numpy as np
from jump import Robot,LOW,HIGH,INITIAL,target,geometry_floor,evaluate
from gait import LIMITS


class JumpTests(unittest.TestCase):
    def test_clearance_matches_mujoco(self):
        robot=Robot();m,d=robot.model,robot.data
        ids=np.flatnonzero((m.geom_bodyid>0)&((m.geom_contype!=0)|(m.geom_conaffinity!=0)))
        rng=np.random.default_rng(72)
        for _ in range(8):
            d.qpos[2]=.4;d.qpos[3:7]=rng.normal(size=4);d.qpos[3:7]/=np.linalg.norm(d.qpos[3:7]);mujoco.mj_forward(m,d)
            exact=[mujoco.mj_geomDistance(m,d,m.geom('ground').id,int(g),2.,None) for g in ids]
            np.testing.assert_allclose(geometry_floor(m,d,ids),exact,atol=1e-9)

    def test_symmetric_and_per_leg_targets_match(self):
        p=np.r_[INITIAL[:4],*[np.tile(INITIAL[4+3*i:7+3*i],6) for i in range(3)]]
        for t in np.linspace(0,3.5,200):np.testing.assert_array_equal(target(p,t),target(INITIAL,t))

    def test_targets_stay_inside_original_limits(self):
        rng=np.random.default_rng(6)
        for p in rng.uniform(LOW,HIGH,(20,len(LOW))):
            for t in np.linspace(0,3.5,100):self.assertTrue((np.abs(target(p,t))<=LIMITS).all())

    def test_standing_cannot_earn_jump_reward(self):
        p=INITIAL.copy();p[4:]=0
        r=evaluate(p);self.assertEqual(r['score_m'],0);self.assertEqual(r['airborne_time_s'],0)


if __name__=='__main__':unittest.main()

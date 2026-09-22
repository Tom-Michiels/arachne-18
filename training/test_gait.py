"""Geometry and controller checks independent of training reward."""
import unittest
import numpy as np
import mujoco
from gait import ROOT, INITIAL, LOW, HIGH, LIMITS, feet, target, rotate


class GaitTests(unittest.TestCase):
    def setUp(self):
        self.m=mujoco.MjModel.from_xml_path(str(ROOT/'simulation/arachne.xml'))
        self.d=mujoco.MjData(self.m)
        mujoco.mj_resetDataKeyframe(self.m,self.d,0)

    def test_foot_fk_matches_original_mujoco(self):
        rng=np.random.default_rng(3)
        for _ in range(20):
            self.d.qpos[7:]=rng.uniform(-LIMITS,LIMITS)
            self.d.qpos[3:7]=rng.normal(size=4)
            self.d.qpos[3:7]/=np.linalg.norm(self.d.qpos[3:7])
            mujoco.mj_forward(self.m,self.d)
            exact=np.array([self.d.site(f'L{i}_foot').xpos for i in range(1,7)])
            np.testing.assert_allclose(feet(self.d.qpos[None,:])[0],exact,atol=3e-7)

    def test_commands_remain_inside_joint_limits(self):
        rng=np.random.default_rng(5);n=1000
        p=rng.uniform(LOW,HIGH,(n,len(INITIAL)))
        qp=np.tile(self.d.qpos,(n,1));cmd=rng.uniform(-.2,.2,(n,3))
        q=target(p,rng.uniform(0,1,n),cmd,qp,2.,gyro=np.zeros((n,3)))
        self.assertTrue(np.isfinite(q).all())
        self.assertTrue((np.abs(q)<=LIMITS-.0039).all())

    def test_zero_command_is_stationary(self):
        p=INITIAL[None,:]; qp=self.d.qpos[None,:]
        q=target(p,np.array([.23]),np.zeros((1,3)),qp,2.)
        np.testing.assert_allclose(q,0,atol=1e-10)

    def test_imu_policy_ignores_global_position_and_yaw(self):
        p=INITIAL[None,:]; qp=self.d.qpos[None,:].copy()
        cmd=np.array([[.1,.04,.2]])
        reference=target(p,np.array([.32]),cmd,qp,2.,gyro=np.zeros((1,3)))
        qp[0,:3]=[42,-20,1.7];qp[0,3:7]=[np.cos(.6),0,0,np.sin(.6)]
        np.testing.assert_allclose(target(p,np.array([.32]),cmd,qp,2.,gyro=np.zeros((1,3))),reference,atol=1e-10)


if __name__=='__main__':unittest.main()

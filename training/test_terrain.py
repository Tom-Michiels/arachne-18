"""Regression tests for terrain geometry and promotion safeguards."""
import copy
import json
import unittest
import mujoco
import numpy as np
from gait import ROOT
from terrain import height_map,make_model,height_below,EXTENT,RESOLUTION
from curriculum import gate


class TerrainTests(unittest.TestCase):
    def test_seed_spawn_and_amplitude(self):
        spec=dict(kind='bumps',amplitude_m=.004,wavelength_m=[.1,.2])
        a=height_map(spec,17)
        np.testing.assert_array_equal(a,height_map(spec,17))
        self.assertFalse(np.array_equal(a,height_map(spec,18)))
        self.assertLessEqual(abs(a).max(),.004)
        xy=np.linspace(-EXTENT,EXTENT,RESOLUTION);x,y=np.meshgrid(xy,xy)
        self.assertTrue((a[x*x+y*y<.32**2]==0).all())

    def test_ray_matches_collision_grid(self):
        spec=dict(kind='bumps',amplitude_m=.004,wavelength_m=[.1,.2])
        m,_=make_model(spec,9);d=mujoco.MjData(m);mujoco.mj_resetDataKeyframe(m,d,0)
        mujoco.mj_forward(m,d);z=height_map(spec,9)
        for row,col in [(200,200),(215,270),(95,130),(280,65)]:
            x=-EXTENT+col*.01;y=-EXTENT+row*.01
            self.assertAlmostEqual(height_below(m,d,x,y),z[row,col],places=7)

    def test_slope_entry_is_bounded(self):
        z=height_map(dict(kind='slope',slope_deg=2),5)
        gx,gy=np.gradient(z,.01)
        self.assertLessEqual(np.hypot(gx,gy).max(),np.tan(np.deg2rad(2))+1e-12)

    def test_promotion_rejects_stationary_unexposed_and_rough_motion(self):
        config=json.loads((ROOT/'training/terrain_curriculum.json').read_text())
        stage=config['stages'][1]
        good=dict(passed=True,warnings=0,nonfoot_contacts=0,tilt_max_deg=.3,
                  tilt_rms_deg=.15,clearance_std_mm=.8,velocity_rmse=.01,yaw_rmse=.02,
                  slip_rms_m_s=.02,target_rate_rms=1,target_acceleration_rms=22,
                  target_jerk_rms=800,clearance_rate_rms=.012,joint_speed_max=3,
                  clearance_min_m=.09,command=[.1,0,0],measured_velocity=[.095,0,0],
                  terrain_exposure_fraction=.4)
        self.assertEqual(gate(good,stage,config),[])
        for changes,reason in [({'measured_velocity':[0,0,0]},'progress_ratio'),
                               ({'terrain_exposure_fraction':0},'terrain_exposure_fraction'),
                               ({'target_jerk_rms':2500},'target_jerk_rms'),
                               ({'slip_rms_m_s':float('nan')},'slip_rms_m_s')]:
            bad=copy.deepcopy(good);bad.update(changes)
            self.assertIn(reason,gate(bad,stage,config))


if __name__=='__main__':unittest.main()

"""Create a provisional 12 V BAM model from the published 7.4 V M6 model.

Fits effective DC constants to C018 no-load speed and stall output torque.
This is NOT a system identification and does not fit electrical current.
"""
from pathlib import Path
import json, math, hashlib, importlib.metadata
from scipy.optimize import brentq
from bam.model import load_model

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'bam_sts3215_7p4v_m6_original.json'
model=load_model(str(SOURCE))
source=json.loads(SOURCE.read_text())
voltage=12.; pwm=model.actuator.max_pwm
speed=math.radians(60)/.222
stall=30*.0980665
def friction(torque,load,velocity):
    constant,damping=model.compute_frictions(torque,-load,velocity)
    return float(constant+damping*abs(velocity))
motor_at_stall=brentq(lambda t:t-stall-friction(t,stall,0),stall,10)
motor_no_load=brentq(lambda t:t-friction(t,0,speed),0,2)
kt=voltage*pwm/speed*(1-motor_no_load/motor_at_stall)
resistance=kt*voltage*pwm/motor_at_stall
params={**source,'kt':kt,'R':resistance,'q_offset':0.,'max_velocity':speed}
(HERE/'bam_sts3215_12v_approx_m6.json').write_text(json.dumps(params,indent=2))
report={
    'status':'PROVISIONAL_DATASHEET_FIT_NOT_IDENTIFIED',
    'source_motor':'feetech_sts3215_7_4V',
    'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'bam_version':importlib.metadata.version('better-actuator-models'),
    'datasheet':'Feetech ST-3215-C018 A/0, 2023-07-20, pp. 3-4',
    'voltage_V':voltage,'max_pwm_inherited':pwm,
    'target_no_load_rad_s':speed,'target_output_stall_Nm':stall,
    'effective_kt':kt,'effective_R':resistance,
    'motor_torque_at_stall_before_friction_Nm':motor_at_stall,
    'motor_torque_at_no_load_before_friction_Nm':motor_no_load,
    'fitted_output_stall_Nm':motor_at_stall-friction(motor_at_stall,stall,0),
    'no_load_equilibrium_residual_Nm':motor_no_load-friction(motor_no_load,0,speed),
    'inherited':['M6 friction coefficients','armature','position P gain scaling','command_delay'],
    'overridden':['kt','R','max_velocity','q_offset=0; rig offset not a robot joint offset'],
    'not_validated':['real 12V servo dynamics','electrical current','thermal/overload protection','backlash'],
    'current_note':'Effective kt/R fit torque and speed; do not use their inferred current for battery or wiring sizing. Datasheet 2.7A stall is separate.',
}
(HERE/'bam_12v_fit_report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))

# STS3215 12 V: provisional BAM M6 model

The upstream BAM project provides an identified **STS3215 7.4 V** model. This project uses a separately labeled **12 V approximation**, authorized for this prototype. It is not an identification of the user's 12 V hardware.

## Provenance

The original M6 parameter file is preserved as `simulation/bam_sts3215_7p4v_m6_original.json`, from [Rhoban/BAM](https://github.com/Rhoban/bam), commit `e9a619d56da5236206f4de6ceec2c1ee1b497b5c`. Its SHA-256 is `74d5068bd4453046fd5e33a11bfcc69a7f121740409f6818706a789b000df5e9`. Runtime dependency: PyPI `better-actuator-models==1.0.2`.

The parameter source snapshot and PyPI release do not expose exactly the same runtime API. This project's runner explicitly initializes the Feetech firmware target-smoothing state on reset, because the installed release normally initializes it when loading a measurement log.

## What was fitted

The official Feetech ST-3215-C018 12 V datasheet specifies **30 kg·cm (2.941995 Nm) stall output torque** and **0.222 s/60° no-load speed** at 12 V. `fit_bam_12v.py` solves for effective `kt` and `R` so the M6 net output matches those points with inherited friction.

| Parameter | Approximation |
|---|---:|
| Supply voltage | 12 V; runtime can override it |
| Effective motor constant `kt` | 2.3572085648 |
| Effective resistance `R` | 6.2986515716 |
| Firmware speed limit | 4.7171060865 rad/s |
| Net stall output after modeled friction | 2.941995 Nm |
| PWM limit | 0.97, inherited |

The M6 friction parameters, apparent rotor inertia, proportional-control scale and approximately 4.98 ms command delay are inherited from the 7.4 V identification. The original test-rig angle offset is set to zero. The runner interpolates delayed target history at the 1 ms simulation timestep. Voltage sag is disabled.

Reproduce the fit:

```sh
python simulation/fit_bam_12v.py
python simulation/validate.py
```

The output files are `bam_sts3215_12v_approx_m6.json` and `bam_12v_fit_report.json`. This modifies the tracked parameter/report files; inspect the diff before committing.

## Interpretation and limits

`kt` and `R` are **effective model coefficients**, not measured electrical properties. The datasheet's terminal resistance and current figures do not produce a consistent ideal DC motor model when combined directly with every torque/speed figure; this fit therefore targets the two mechanical points explicitly.

Do not use the model's inferred electrical current for wire sizing, pack sizing or battery-life estimates. The datasheet separately specifies 2.7 A stall current per servo. Thermal behavior, voltage sag, gearbox backlash and overload shutdown are not modeled reliably. Stall output torque is not a continuous load rating.

The 12 V approximation needs measured data before it can support quantitative hardware predictions. A useful next step is an actual BAM identification on the 12 V servos with the intended supply, firmware settings and load. Use `--parameters` to load a replacement model.

Sources: [BAM actuator catalogue](https://bam.readthedocs.io/en/latest/usage/actuators.html), [BAM MuJoCo integration](https://bam.readthedocs.io/en/latest/usage/mujoco_cpu.html), [Feetech 12 V datasheet](https://cdn.robotshop.com/media/F/Fit/RB-Fit-155/pdf/feetech_12v_30kg_cm_magnetic_encoding_servo_sts321_specification_pdf.pdf).

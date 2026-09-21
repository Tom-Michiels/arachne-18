# Sources and third-party notices

## Better Actuator Models

[BAM](https://github.com/Rhoban/bam) is developed by Rhoban and distributed under Apache-2.0. This repository includes an original STS3215 7.4 V M6 parameter snapshot and a modified 12 V approximation. The modification fits effective torque/speed coefficients to Feetech's 12 V datasheet; it is not an upstream identified 12 V model. See [the model notes](docs/bam-model.md) and the [included license](licenses/BAM_APACHE_2.0.txt).

Upstream parameter snapshot: `e9a619d56da5236206f4de6ceec2c1ee1b497b5c`. Installed runtime: `better-actuator-models==1.0.2` from PyPI.

## Mechanical and electrical references

- [Feetech ST-3215-C018 12 V specification](https://cdn.robotshop.com/media/F/Fit/RB-Fit-155/pdf/feetech_12v_30kg_cm_magnetic_encoding_servo_sts321_specification_pdf.pdf): torque, speed, voltage and current. Revision A/0, 20 July 2023, pages 3–4.
- [Feetech STS3215 translated drawing](https://core-electronics.com.au/attachments/uploads/sts3215-smart-servo-datasheet-translated.pdf): common case and both horn interfaces, pages 6–7. Check the actual supplied hardware before printing the full set.
- [Waveshare ST3215](https://www.waveshare.com/wiki/ST3215_Servo): TTL interface and 3S/12.6 V compatibility.
- [Norelem EN ISO 7380-1 button-head screws](https://www.norelemusa.com/en-us/Product-Overview/Flexible-standard-component-system/07000/Nuts-screws-washers-securing-elements/Button-head-screws-EN-ISO-7380/Hexagon-socket-button-head-screws-EN-ISO-7380-1-Style-A/p/agid.18464): M3 head diameter 5.7 mm, height 1.65 mm and 2 mm hex socket.

Vendor documents are linked rather than redistributed. The servo, horn, controller and battery solids are simplified project references, not official manufacturer CAD.

## Tools

- [MuJoCo](https://github.com/google-deepmind/mujoco) and [modeling documentation](https://mujoco.readthedocs.io/en/stable/modeling.html).
- [CadQuery](https://github.com/CadQuery/cadquery) for construction and STEP export.
- [Onshape assembly API](https://onshape-public.github.io/docs/api-adv/assemblies/) for native mating.

These products and their trademarks belong to their respective owners. Their use does not imply endorsement. Runtime dependencies retain their own licenses.

## Project and artwork

No project-wide license has been selected by the owner. Inclusion on GitHub is not itself an open-source license grant. The BAM material retains the separate license above. Image provenance and the generation prompts are documented in [media.md](docs/media.md).

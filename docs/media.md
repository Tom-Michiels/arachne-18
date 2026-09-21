# Image provenance and generation prompts

## Gallery

| Asset | Origin |
|---|---|
| `assets/hero-workbench.png` | AI-assisted composite using the owner's supplied mancave photograph and the corrected robot rendering |
| `assets/hero-studio.png` | AI-assisted studio presentation based on the actual CAD overview, with horn placement corrected |
| `assets/cad-overview.png` | Direct VTK render of the exported CAD meshes |
| `assets/cad-internals.png` | Same geometry, with the shell hidden; blue and amber blocks are reserved controller/battery envelopes |
| `assets/cad-top.png` | Direct CAD top view |
| `assets/cad-service.png` | Direct CAD render with the shell translated upward to show access |
| `assets/mujoco-preview.png` | Actual MuJoCo grounded body-height exercise after settling |
| `assets/mujoco-grounded.gif` | Actual BAM-driven floating-base body-height exercise; all six feet stay in contact with the floor |

The presentation artwork is illustrative. Hardware detail, lighting, material texture and room arrangement may differ from the CAD or eventual build. The technical renders, model files and build guide define the mechanical design. The purchased fasteners are specified in the BOM and omitted from the main 155-solid CAD export. Metal horns are inside the cheeks; outside faces show individual DIN 7380 / ISO 7380-1 screw heads.

The workbench photograph was provided by the project owner for this composite. The original photo is not redistributed here. All generated artwork was produced with the **built-in image-generation tool** using reference-image editing; no external image API or local generation CLI was used.

## Generation instructions

### Studio rendering

Create one spectacular cinematic product rendering of the exact six-legged robotics prototype in the supplied CAD reference. Wide landscape 16:9 hero banner for an engineering GitHub README. Preserve the recognizable geometry and proportions: exactly six radial legs, three box-shaped black servo joints per leg, teal printed double-sided mechanical brackets with circular servo horns, thin tapered forked shin legs ending in small black rubber feet, rounded dark teal vertical dorsal shell with small rectangular vents, compact scalloped chassis. Preserve the leg stance and camera viewpoint so all six legs remain traceable. Do not add legs, eyes, sensors, headlights, claws, giant armor, decorative mechanisms, wires, weapons or new hardware. Tactile satin deep petrol teal printed polymer, black servo cases, warm amber rim light and cool cyan softbox, charcoal studio stage, restrained reflection and soft shadow. No text, logo, caption or border. Presentation artwork based on a real CAD model, not a redesign.

The first result incorrectly put metal discs outside the cheeks and was rejected. The repository contains the corrected result only.

### Mechanical correction

Correct the robot rendering while preserving its camera, six legs, colors, lighting and composition. Remove every exposed silver circular horn disc from the outside of every teal leg bracket. Horns are inside, sandwiched between the black servo and the inside surface of each teal cheek. Replace outside disc surfaces with continuous matte petrol teal printed polymer. Show only four separate small stainless M3 socket-head screw heads on a 14 mm bolt circle and a central access hole. No silver backing plate joins the outside screws. A real horn may appear only as a thin edge between servo and inside cheek. Preserve the printed circular cheek silhouette. No other redesign and no text.

### Mancave composite

Create a photorealistic composite of ARACHNE on the owner's actual electronics workbench, using the supplied photographs as the location plate and the corrected robot rendering/CAD as identity references. Retain the green cutting mat, worn workshop wall, large orange-brown horizontal pipe, white task lamp, oscilloscopes and power supplies to the left, component drawers to the right, tools and cables. Place one robot on the free central-front area of the mat with realistic perspective and shadows. Its actual dimensions are about 51 cm across and 21 cm tall. Preserve exactly six legs, three compact black STS3215 servos per leg, petrol teal printed brackets, vented rounded shell, forked shins and black TPU feet. Metal horns are inside the brackets; outside faces show four small separate rounded DIN 7380 / ISO 7380-1 M3 button-head hex-socket screws and a central access hole. No external metal discs. Discreetly move only loose objects directly under the footprint. Match the workshop light with a warm pool from the existing lamp, realistic layer texture, sharp robot and slightly softer recognizable background. No new hardware, text or watermarks.

### Realism revision for the workbench

The cinematic workbench result was replaced after owner feedback. Use the original cluttered bench photograph as the authoritative location, preserving the real camera viewpoint, dim flat ambient lighting, tools, wires, orange pipe, white lamp and equipment. Insert a realistically scaled six-legged first-build robot with dull teal PETG, subtle FDM layer lines, small scuffs, ordinary black servo cases and separate DIN 7380 button-head screws. Match photographic noise, exposure and sharpness. Keep all six feet on the mat with small natural contact shadows. Do not beautify or clean the workshop, invent equipment, alter labels, add dramatic lighting, use glossy CGI surfaces or apply cinematic grading. The result should resemble a casual workshop photograph.

## Reproduce technical images

```sh
# In the CadQuery/VTK environment
python src/render_gallery.py

# In the simulation environment, with Pillow installed
python -m pip install Pillow==12.3.0
python src/render_simulation.py
```

The technical render scripts use the repository geometry directly. Regenerating a studio image from a prompt is stochastic and will not reproduce identical pixels.

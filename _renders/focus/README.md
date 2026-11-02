# Focus-page illustrations

Sources for the three research-direction images on the Focus page
(`images/focus_2d_materials.jpg`, `images/focus_multiferroics.jpg`, `images/focus_nanoscopy.jpg`).
The scenes are built and path-traced with Blender (Cycles) from Python, so colors, camera, and details can be
changed in code and re-rendered. This folder starts with an underscore, so Jekyll does not publish it.

All three scenes share one setup (`bcommon.py`): a bright photo studio with a seamless backdrop, the same camera,
lights and depth of field, a red pump beam focused onto the sample, and a blue THz pulse leaving it.

| Script | Image | Shows |
| --- | --- | --- |
| `render_2d_materials.py` | `focus_2d_materials.jpg` | MoS₂ flake on an oxidized Si wafer under a ferromagnetic film, spin carriers entering the monolayer |
| `render_multiferroics.py` | `focus_multiferroics.jpg` | BiFeO₃ crystal with a ferron wave in the polarization (violet) and the spins (blue) following it |
| `render_nanoscopy.py` | `focus_nanoscopy.jpg` | Scanning tip over antiparallel magnetic domains, laser focused on the apex, THz emitted from the tip |

## Re-rendering

```bash
python3 -m venv bvenv
./bvenv/bin/pip install bpy==5.2.3 pillow numpy   # Blender as a Python module (needs Python 3.13)

# full quality: 1500 x 1200 px (5:4, matches the Focus cards), about 6 minutes per image on 4 CPU cores
./bvenv/bin/python render_2d_materials.py --out /tmp/2d.png --samples 110 --exp 0.65
# light bloom and vignette, then save as JPEG
./bvenv/bin/python post.py /tmp/2d.png ../../images/focus_2d_materials.jpg 0 0.92 0.12
```

For quick previews, add `--pct 50 --samples 40` (renders at half resolution in about a minute).

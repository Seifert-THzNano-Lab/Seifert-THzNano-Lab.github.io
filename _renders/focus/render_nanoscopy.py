import sys, math, os
sys.path.insert(0, os.path.dirname(__file__))
from bcommon import *

sc = reset()
CAM, TGT = (10.5, -13.5, 8.2), (1.15, 0.1, 1.0)
studio(CAM, TGT)

# sample with magnetic domains (alternating tiles, antiparallel in-plane order printed as flat arrows)
LX, LY, HS = 7.0, 4.6, 0.5
rbox('body', (LX, LY, HS), (0, 0, HS / 2), mat('body', (0.30, 0.33, 0.40), metallic=0.6, rough=0.25), bevel=0.025)
NX, NY = 8, 5
dx, dy = LX / NX, LY / NY
tA = mat('domA', (0.10, 0.28, 0.66), rough=0.35, coat=0.35)
tB = mat('domB', (0.80, 0.85, 0.92), rough=0.35, coat=0.35)
aA = mat('arrA', (0.92, 0.95, 1.0), rough=0.25, coat=1.0)
aB = mat('arrB', (0.18, 0.36, 0.66), rough=0.25, coat=1.0)
th = 0.05
top = HS + th
for i in range(NX):
    for j in range(NY):
        x = -LX / 2 + (i + 0.5) * dx
        y = -LY / 2 + (j + 0.5) * dy
        A = (i + j) % 2 == 0
        rbox('tile', (dx - 0.008, dy - 0.008, th), (x, y, HS + th / 2), tA if A else tB, bevel=0.006, segs=2)
        s = 1 if A else -1
        flat_arrow('arr', (x - s * 0.28, y, top), (x + s * 0.28, y, top), 0.07, aA if A else aB,
                   thick=0.018, head_w=0.21, head_l=0.2)

# scanning probe: pyramidal tip under a cantilever, on a chip
apex = Vector((0.35, -0.35, top + 0.04))
gold = mat('probe', (0.95, 0.80, 0.56), metallic=1.0, rough=0.18)
chip_m = mat('chip', (0.55, 0.57, 0.62), metallic=0.7, rough=0.3)
tipH = 1.0
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.0, radius2=0.42, depth=tipH,
                      matrix=Matrix.Translation(apex + Vector((0, 0, tipH / 2))) @ Matrix.Rotation(math.pi / 4, 4, 'Z'))
mesh_obj('tip', bm, gold, smooth=False)
tilt = math.radians(8)
cl, cw, ct = 3.2, 0.72, 0.09
cant = rbox('cantilever', (cw, cl, ct), (0, 0, 0), gold, bevel=0.02, segs=3)
cant.rotation_euler = (tilt, 0, 0)
cant.location = apex + Vector((0, 0, tipH + ct / 2)) + Vector((0, cl / 2 - 0.3, math.sin(tilt) * (cl / 2 - 0.3)))
chip = rbox('chip', (1.9, 1.4, 0.55), (0, 0, 0), chip_m, bevel=0.03)
chip.rotation_euler = (tilt, 0, 0)
end = apex + Vector((0, 0, tipH + ct / 2)) + Vector((0, cl - 0.3, math.sin(tilt) * (cl - 0.3)))
chip.location = end + Vector((0, 0.55, 0.18))

# pump focused onto the apex, local near-field glow
laser(apex, apex + Vector((-5.5, 4.0, 9.0)), r_src=0.8, r_focus=0.02, strength=3.5)
point_light('nf', apex + Vector((0, 0, -0.02)), 25, (1.0, 0.25, 0.1), radius=0.03)

# THz radiated from the apex
thz_pulse(apex + Vector((0.12, -0.05, 0.08)), (1.0, -0.2, 0.45), (-0.4, 0.1, 1), length=4.6, amp=0.5, r=0.045)

area_light('key', (-8, -8, 12), (0, 0, 0.5), 2600, 9, color=(1.0, 0.98, 0.95))
area_light('rim', (6, 11, 6), (0, 0, 0.6), 1400, 6, color=(0.8, 0.88, 1.0))
area_light('fill', (13, -4, 5), (0, 0, 0.5), 500, 6, color=(1.0, 1.0, 1.0))
area_light('bg', (-4, 9, 14), (-9, 18, 2), 2500, 14, color=(1.0, 1.0, 1.0))

camera(CAM, TGT, lens=64, focus=apex, fstop=1.4)
render(sys.argv[sys.argv.index('--out') + 1])

import sys, math, os
sys.path.insert(0, os.path.dirname(__file__))
from bcommon import *

sc = reset()
CAM, TGT = (10.5, -13.5, 8.2), (1.15, -0.1, 0.75)
studio(CAM, TGT)

# substrate: Si wafer piece with SiO2 thin-film interference
LX, LY, HS = 7.0, 4.6, 0.5
sub_m = mat('wafer', (0.30, 0.31, 0.34), metallic=0.75, rough=0.12, thin_film=315.0, coat=0.0)
rbox('substrate', (LX, LY, HS), (0, 0, HS / 2), sub_m, bevel=0.025)

# MoS2 monolayer
a = 0.5
z0 = HS + 0.2
dz = 0.16
Mo, S = [], []
for i in range(-40, 40):
    for j in range(-40, 40):
        x = 1.5 * a * (i + j); y = math.sqrt(3) / 2 * a * (i - j)
        if abs(x) < LX / 2 - 0.15 and abs(y) < LY / 2 - 0.15: Mo.append((x, y))
        if abs(x + a) < LX / 2 - 0.15 and abs(y) < LY / 2 - 0.15: S.append((x + a, y))
mo_m = mat('Mo', (0.42, 0.46, 0.55), metallic=0.85, rough=0.22, coat=0.6)
s_m = mat('S', (0.98, 0.68, 0.06), metallic=0.0, rough=0.22, coat=1.0)
bond_m = mat('bond', (0.55, 0.6, 0.68), metallic=0.8, rough=0.3)
spheres('Mo', [(x, y, z0) for x, y in Mo], 0.1, mo_m)
spheres('S', [(x, y, z0 + dz) for x, y in S] + [(x, y, z0 - dz) for x, y in S], 0.08, s_m)
bonds = []
for m in Mo:
    for s in S:
        if abs(math.hypot(m[0] - s[0], m[1] - s[1]) - a) < 0.01:
            bonds.append(((m[0], m[1], z0), (s[0], s[1], z0 + dz)))
            bonds.append(((m[0], m[1], z0), (s[0], s[1], z0 - dz)))
cylinders('bonds', bonds, 0.019, bond_m, n=8, caps=False)

# ferromagnetic film covering the back part
fm_top = z0 + dz + 0.09 + 0.3
fm_m = mat('FM', (0.6, 0.62, 0.66), metallic=1.0, rough=0.3, aniso=0.6)
FY0, FY1 = -0.15, LY / 2
rbox('FM', (LX, FY1 - FY0, 0.3), (0, (FY0 + FY1) / 2, fm_top - 0.15), fm_m, bevel=0.02)

# magnetisation arrow on the film
flat_arrow('M', (-2.9, 1.45, fm_top), (-1.1, 1.45, fm_top), 0.12,
           mat('Marrow', (0.02, 0.06, 0.16), metallic=0.3, rough=0.25, coat=1.0), thick=0.025, head_w=0.36, head_l=0.36)

# spin carriers drifting out of the film into the monolayer
spin_m = mat('spin', (0.0, 0.18, 0.8), rough=0.1, coat=1.0, emission=(0.0, 0.3, 1.0), estr=0.25)
sarr_m = mat('spinarrow', (0.92, 0.95, 1.0), rough=0.25, coat=1.0)
for (x, y, h) in [(0.1, -0.55, 0.42), (1.05, -0.95, 0.34), (-0.85, -1.3, 0.3)]:
    p = Vector((x, y, z0 + h))
    spheres('carrier', [p], 0.15, spin_m, seg=32, rings=18)
    arrow('sarrow', p + Vector((-0.34, 0, 0)), p + Vector((0.5, 0, 0)), 0.028, sarr_m, head_r=0.075, head_l=0.16)

# pump beam onto the film
focus = Vector((0.4, 0.75, fm_top + 0.003))
laser(focus, focus + Vector((-5.5, 4.0, 9.0)), r_src=0.8, r_focus=0.025, strength=3.5)

# THz transient emitted from the interface region
thz_pulse((LX / 2 - 0.2, -0.75, z0), (1.0, -0.62, 0.22), (0, 0.15, 1), length=4.4, amp=0.5, r=0.045)

# lighting: big soft key from upper left, cool rim from behind, gentle fill from the right
area_light('key', (-8, -8, 12), (0, 0, 0.5), 2600, 9, color=(1.0, 0.98, 0.95))
area_light('rim', (6, 11, 6), (0, 0, 0.6), 1400, 6, color=(0.8, 0.88, 1.0))
area_light('fill', (13, -4, 5), (0, 0, 0.5), 500, 6, color=(1.0, 1.0, 1.0))
# backdrop light: brightens the sweep behind the subject for a clean high-key background
area_light('bg', (-4, 9, 14), (-9, 18, 2), 2500, 14, color=(1.0, 1.0, 1.0))

camera(CAM, TGT, lens=64, focus=focus, fstop=1.4)

render(sys.argv[sys.argv.index('--out') + 1])

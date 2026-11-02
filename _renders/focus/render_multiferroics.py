import sys, math, os
sys.path.insert(0, os.path.dirname(__file__))
from bcommon import *

sc = reset()
CAM, TGT = (10.5, -13.5, 8.2), (1.15, -0.1, 0.75)
studio(CAM, TGT)

# BiFeO3 crystal: dark polished crystal with a faint warm interference sheen
LX, LY, HC = 7.0, 4.6, 1.0
crys_m = mat('BFO', (0.085, 0.065, 0.05), rough=0.12, coat=1.0, thin_film=420.0)
rbox('crystal', (LX, LY, HC), (0, 0, HC / 2), crys_m, bevel=0.05)
top = HC

# lattice sites across the surface (fine texture)
site_m = mat('site', (0.95, 0.93, 0.9), rough=0.25, coat=1.0)
g = 0.5
sites = [(-LX / 2 + 0.25 + g * i, -LY / 2 + 0.3 + g * j, top + 0.02) for i in range(14) for j in range(9)]
spheres('sites', sites, 0.035, site_m, seg=16, rings=10)

# pump spot at the left end; a ferron (polar wave, violet) runs along the crystal,
# with the spins (blue) following it in step: the coupled orders
focus = Vector((-2.45, -0.75, top + 0.003))
k = 2 * math.pi / 3.6
p_m = mat('P', (0.30, 0.10, 0.75), rough=0.18, coat=1.0)
s_m = mat('spinA', (0.0, 0.2, 0.85), rough=0.15, coat=1.0)
yP, yS = -0.25, -1.25
tipsP, tipsS = [], []
xs = [-1.75 + 0.5 * i for i in range(11)]
for x in xs:
    damp = math.exp(-(x - focus.x) / 7.0)
    th = 0.42 * damp * math.sin(k * (x - focus.x) - 0.9)
    L = 0.95
    a0 = Vector((x, yP, top + 0.02))
    tp = a0 + Vector((math.sin(th), 0, math.cos(th))) * L
    arrow('P', a0, tp, 0.045, p_m, head_r=0.11, head_l=0.23)
    tipsP.append(tp + Vector((math.sin(th), 0, math.cos(th))) * 0.02)
    # spin: lying in the surface, pointing towards the viewer, swinging in-plane with the wave
    ph = 1.1 * th
    c = Vector((x, yS, top + 0.09))
    d = Vector((math.sin(ph), -math.cos(ph), 0))
    arrow('S', c - d * 0.32, c + d * 0.32, 0.035, s_m, head_r=0.085, head_l=0.18)
    tipsS.append(c + d * 0.34)
wave_m = mat('waveline', (0.30, 0.10, 0.75), rough=0.3, emission=(0.35, 0.15, 0.9), estr=0.3)
tube_mesh('Pwave', [Vector(p) for p in tipsP], 0.012, wave_m, n=10)

laser(focus, focus + Vector((-5.5, 4.0, 9.0)), r_src=0.8, r_focus=0.025, strength=3.5)

# THz transient leaving the crystal
thz_pulse((LX / 2 - 0.2, -0.75, top * 0.6), (1.0, -0.62, 0.22), (0, 0.15, 1), length=4.4, amp=0.5, r=0.045)

area_light('key', (-8, -8, 12), (0, 0, 0.5), 2600, 9, color=(1.0, 0.98, 0.95))
area_light('rim', (6, 11, 6), (0, 0, 0.6), 1400, 6, color=(0.8, 0.88, 1.0))
area_light('fill', (13, -4, 5), (0, 0, 0.5), 500, 6, color=(1.0, 1.0, 1.0))
area_light('bg', (-4, 9, 14), (-9, 18, 2), 2500, 14, color=(1.0, 1.0, 1.0))

camera(CAM, TGT, lens=64, focus=focus, fstop=1.4)
render(sys.argv[sys.argv.index('--out') + 1])

"""Shared Blender (Cycles) setup for the three focus-area renders: dark cinematic look."""
import math, sys
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion

RES = (1500, 1200)

# palette (linear-ish RGB tuples)
RED = (1.0, 0.05, 0.03)
BLUE = (0.02, 0.45, 1.0)
CYAN = (0.15, 0.75, 1.0)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = int(sys.argv[sys.argv.index('--samples') + 1]) if '--samples' in sys.argv else 160
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.cycles.transparent_max_bounces = 16
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.resolution_percentage = int(sys.argv[sys.argv.index('--pct') + 1]) if '--pct' in sys.argv else 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '16'
    sc.render.film_transparent = False
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Punchy'
        sc.view_settings.exposure = float(sys.argv[sys.argv.index('--exp') + 1]) if '--exp' in sys.argv else 0.6
    except Exception as e:
        print('view transform:', e)
    return sc


def world(top=(0.004, 0.009, 0.025), strength=1.0):
    w = bpy.data.worlds.new('World'); bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes['Background']
    bg.inputs['Color'].default_value = (*top, 1)
    bg.inputs['Strength'].default_value = strength
    return w


def mat(name, color=(0.8, 0.8, 0.8), metallic=0.0, rough=0.4, coat=0.0, emission=None, estr=0.0, alpha=1.0,
        transmission=0.0, ior=1.45, aniso=0.0, thin_film=0.0, spec=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    I = p.inputs
    I['Base Color'].default_value = (*color, 1)
    I['Metallic'].default_value = metallic
    I['Roughness'].default_value = rough
    I['IOR'].default_value = ior
    if 'Coat Weight' in I: I['Coat Weight'].default_value = coat
    if 'Transmission Weight' in I: I['Transmission Weight'].default_value = transmission
    if aniso and 'Anisotropic' in I: I['Anisotropic'].default_value = aniso
    if thin_film and 'Thin Film Thickness' in I:
        I['Thin Film Thickness'].default_value = thin_film
        I['Thin Film IOR'].default_value = 1.46
    if 'Specular IOR Level' in I: I['Specular IOR Level'].default_value = spec
    if emission is not None:
        I['Emission Color'].default_value = (*emission, 1)
        I['Emission Strength'].default_value = estr
    if alpha < 1:
        I['Alpha'].default_value = alpha
    return m


def emit_mat(name, color, strength, fresnel_alpha=False, alpha=1.0):
    """Pure emission; optionally fading at grazing angles (soft glowing tube/beam look)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    for n in list(N): N.remove(n)
    out = N.new('ShaderNodeOutputMaterial')
    em = N.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*color, 1); em.inputs['Strength'].default_value = strength
    if not fresnel_alpha and alpha >= 1:
        L.new(em.outputs[0], out.inputs['Surface']); return m
    tr = N.new('ShaderNodeBsdfTransparent')
    mix = N.new('ShaderNodeMixShader')
    if fresnel_alpha:
        lw = N.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
        inv = N.new('ShaderNodeMath'); inv.operation = 'POWER'; inv.inputs[1].default_value = 2.0
        L.new(lw.outputs['Facing'], inv.inputs[0])
        sub = N.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'; sub.inputs[0].default_value = 1.0
        L.new(inv.outputs[0], sub.inputs[1])
        mul = N.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = alpha
        L.new(sub.outputs[0], mul.inputs[0])
        L.new(mul.outputs[0], mix.inputs['Fac'])
    else:
        mix.inputs['Fac'].default_value = alpha
    L.new(tr.outputs[0], mix.inputs[1]); L.new(em.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs['Surface'])
    return m


def link(obj):
    bpy.context.scene.collection.objects.link(obj); return obj


def mesh_obj(name, bm, material=None, smooth=True):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); link(ob)
    if material: me.materials.append(material)
    return ob


def rbox(name, size, loc, material, bevel=0.03, segs=4):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(loc), verts=bm.verts)
    ob = mesh_obj(name, bm, material, smooth=False)
    if bevel:
        md = ob.modifiers.new('bevel', 'BEVEL'); md.width = bevel; md.segments = segs
        md.limit_method = 'ANGLE'
        try: md.harden_normals = True
        except Exception: pass
        for p in ob.data.polygons: p.use_smooth = True
    return ob


def spheres(name, pts, r, material, seg=24, rings=14):
    bm = bmesh.new()
    for p in pts:
        bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r, matrix=Matrix.Translation(Vector(p)))
    return mesh_obj(name, bm, material)


def cylinders(name, segs_list, r, material, n=12, caps=True):
    """segs_list: list of (a, b) points. Builds all cylinders into one mesh."""
    bm = bmesh.new()
    for a, b in segs_list:
        a, b = Vector(a), Vector(b)
        d = b - a; L = d.length
        if L < 1e-6: continue
        q = Vector((0, 0, 1)).rotation_difference(d.normalized())
        M = Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=caps, segments=n, radius1=r, radius2=r, depth=L, matrix=M)
    return mesh_obj(name, bm, material)


def arrow(name, a, b, r, material, head_r=None, head_l=None, n=24):
    a, b = Vector(a), Vector(b)
    d = b - a; L = d.length; u = d.normalized()
    head_r = head_r or r * 2.6; head_l = head_l or r * 5.5
    q = Vector((0, 0, 1)).rotation_difference(u)
    bm = bmesh.new()
    s_end = a + u * (L - head_l)
    M = Matrix.Translation((a + s_end) / 2) @ q.to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=n, radius1=r, radius2=r, depth=(L - head_l), matrix=M)
    M2 = Matrix.Translation(s_end + u * head_l / 2) @ q.to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=n, radius1=head_r, radius2=0.0, depth=head_l, matrix=M2)
    return mesh_obj(name, bm, material)


def tube(name, pts, r, material, n=16, closed=False):
    """Smooth tube through points (via curve object with bevel)."""
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1)
    cu.bevel_depth = r; cu.bevel_resolution = n // 4; cu.use_fill_caps = True
    ob = bpy.data.objects.new(name, cu); link(ob)
    cu.materials.append(material)
    return ob


def area_light(name, loc, target, power, size, color=(1, 1, 1), size_y=None, shape='RECTANGLE'):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = power; ld.color = color
    ld.shape = shape; ld.size = size
    if size_y: ld.size_y = size_y
    ob = bpy.data.objects.new(name, ld); link(ob)
    ob.location = Vector(loc)
    look_at(ob, Vector(target))
    return ob


def point_light(name, loc, power, color, radius=0.05):
    ld = bpy.data.lights.new(name, 'POINT'); ld.energy = power; ld.color = color
    ld.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, ld); link(ob); ob.location = Vector(loc); return ob


def look_at(ob, target):
    d = target - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def camera(loc, target, lens=70, focus=None, fstop=2.8):
    cd = bpy.data.cameras.new('Cam'); cd.lens = lens
    ob = bpy.data.objects.new('Cam', cd); link(ob)
    ob.location = Vector(loc); look_at(ob, Vector(target))
    bpy.context.scene.camera = ob
    if focus is not None:
        cd.dof.use_dof = True
        cd.dof.focus_distance = (Vector(focus) - Vector(loc)).length
        cd.dof.aperture_fstop = fstop
    return ob


def laser(focus, src, r_src=0.35, r_focus=0.02, strength=14.0):
    """Focused pump beam: converging cone with soft glowing edges + hot spot + local light."""
    focus, src = Vector(focus), Vector(src)
    d = focus - src; L = d.length
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bm = bmesh.new()
    M = Matrix.Translation((src + focus) / 2) @ q.to_matrix().to_4x4()
    # cone radius1 at -z (src side), radius2 at +z (focus side)
    bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=r_src, radius2=r_focus, depth=L, matrix=M)
    beam = mesh_obj('beam', bm, emit_mat('beamMat', (1.0, 0.03, 0.02), strength, fresnel_alpha=True, alpha=1.0))
    beam.visible_shadow = False
    # brighter inner core
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=32, radius1=r_src * 0.35, radius2=r_focus * 0.6, depth=L, matrix=M)
    core = mesh_obj('beamcore', bm, emit_mat('coreMat', (1.0, 0.12, 0.06), strength * 1.5, fresnel_alpha=True, alpha=1.0))
    core.visible_shadow = False
    # hot spot
    hs = spheres('hotspot', [focus], 0.05, emit_mat('hsMat', (1.0, 0.75, 0.55), 60.0))
    hs.visible_shadow = False
    point_light('spotlight', focus + Vector((0, 0, 0.12)), 60, (1.0, 0.3, 0.12), radius=0.08)
    return beam


def thz_wave(origin, direction, up, length=4.0, amp=0.5, cycles=3.4, r=0.035, strength=9.0, color=CYAN, bright=False):
    origin, direction, up = Vector(origin), Vector(direction).normalized(), Vector(up).normalized()
    pts = []
    N = 300; t0, sig = 0.5, 0.16
    for i in range(N + 1):
        t = i / N
        env = math.exp(-((t - t0) / sig) ** 2)
        v = amp * env * math.sin(2 * math.pi * cycles * (t - t0) + 1.2)
        pts.append(origin + direction * (t * length) + up * v)
    if bright:
        # glossy, slightly self-luminous blue tube: reads well on a light background
        m = mat('thzMat', (0.005, 0.12, 0.6), rough=0.15, coat=1.0, emission=(0.0, 0.25, 1.0), estr=0.8)
        ob = tube('thz', pts, r * 1.3, m)
        glow = tube('thzglow', pts, r * 3.0, emit_mat('thzGlow', (0.05, 0.4, 1.0), 0.6, fresnel_alpha=True, alpha=0.18))
        glow.visible_shadow = False
        return ob
    ob = tube('thz', pts, r, emit_mat('thzMat', color, strength))
    ob.visible_shadow = False
    glow = tube('thzglow', pts, r * 4, emit_mat('thzGlow', color, 1.2, fresnel_alpha=True, alpha=0.35))
    glow.visible_shadow = False
    return ob


def render(path):
    sc = bpy.context.scene
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def studio(cam_loc, target, world_col=(0.86, 0.89, 0.93), world_str=0.6, sweep_col=(0.88, 0.9, 0.93)):
    """Bright photo studio: seamless curved backdrop (cyclorama) behind the subject, light-grey world."""
    world(world_col, world_str)
    cam_loc, target = Vector(cam_loc), Vector(target)
    v = (target - cam_loc); v.z = 0; v.normalize()          # horizontal viewing direction
    side = Vector((-v.y, v.x, 0))
    # profile in (u along v, z): floor -> quarter circle -> wall
    prof = []
    for k in range(0, 2): prof.append((-40 + 45 * k, 0.0))          # u=-40 .. 5
    R = 9.0
    for k in range(1, 25):
        t = k / 24 * math.pi / 2
        prof.append((5 + R * math.sin(t), R - R * math.cos(t)))
    prof.append((5 + R, 45.0))
    bm = bmesh.new()
    rows = []
    for s in (-60.0, 60.0):
        row = []
        for (u, z) in prof:
            p = target * 0 + Vector((target.x, target.y, 0)) + v * u + side * s + Vector((0, 0, z))
            row.append(bm.verts.new(p))
        rows.append(row)
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = mesh_obj('sweep', bm, mat('sweep', sweep_col, rough=0.45, spec=0.35))
    return ob


def tube_mesh(name, pts, r, material, n=20, r_profile=None):
    """Tube mesh along pts with a 'fade' color attribute holding the arc-length fraction (0..1)."""
    pts = [Vector(p) for p in pts]
    bm = bmesh.new()
    L = [0.0]
    for i in range(1, len(pts)): L.append(L[-1] + (pts[i] - pts[i - 1]).length)
    tot = L[-1]
    rings = []
    prev_n = None
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        if prev_n is None:
            a = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
            nrm = t.cross(a).normalized()
        else:
            nrm = (prev_n - t * prev_n.dot(t)).normalized()
        prev_n = nrm
        bnm = t.cross(nrm)
        rr = r * (r_profile(L[i] / tot) if r_profile else 1.0)
        ring = []
        for k in range(n):
            ang = 2 * math.pi * k / n
            ring.append(bm.verts.new(p + (nrm * math.cos(ang) + bnm * math.sin(ang)) * rr))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(n):
            bm.faces.new((rings[i][k], rings[i][(k + 1) % n], rings[i + 1][(k + 1) % n], rings[i + 1][k]))
    bm.verts.ensure_lookup_table()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    attr = me.color_attributes.new('fade', 'FLOAT_COLOR', 'POINT')
    for vi in range(len(me.vertices)):
        f = L[vi // n] / tot
        attr.data[vi].color = (f, f, f, 1)
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); link(ob)
    me.materials.append(material)
    return ob


def fade_ends(m, a=0.12, b=0.1):
    """Wrap material m's surface so it fades to transparent at both tube ends (uses 'fade' attribute)."""
    nt = m.node_tree; N = nt.nodes; Lk = nt.links
    out = [n for n in N if n.type == 'OUTPUT_MATERIAL'][0]
    src = out.inputs['Surface'].links[0].from_socket
    attr = N.new('ShaderNodeAttribute'); attr.attribute_name = 'fade'
    s1 = N.new('ShaderNodeMapRange'); s1.inputs['From Min'].default_value = 0.0; s1.inputs['From Max'].default_value = a
    s1.interpolation_type = 'SMOOTHSTEP'
    s2 = N.new('ShaderNodeMapRange'); s2.inputs['From Min'].default_value = 1.0; s2.inputs['From Max'].default_value = 1.0 - b
    s2.interpolation_type = 'SMOOTHSTEP'
    Lk.new(attr.outputs['Fac'], s1.inputs['Value']); Lk.new(attr.outputs['Fac'], s2.inputs['Value'])
    mul = N.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    Lk.new(s1.outputs['Result'], mul.inputs[0]); Lk.new(s2.outputs['Result'], mul.inputs[1])
    tr = N.new('ShaderNodeBsdfTransparent'); mix = N.new('ShaderNodeMixShader')
    Lk.new(mul.outputs[0], mix.inputs['Fac']); Lk.new(tr.outputs[0], mix.inputs[1]); Lk.new(src, mix.inputs[2])
    Lk.new(mix.outputs[0], out.inputs['Surface'])
    return m


def thz_pulse(origin, direction, up, length=4.0, amp=0.5, cycles=3.4, r=0.045, sig=0.16):
    """Photoreal THz transient: glossy blue light-tube fading in/out, plus a faint glow sheath."""
    origin, direction, up = Vector(origin), Vector(direction).normalized(), Vector(up).normalized()
    pts = []
    N = 260; t0 = 0.5
    for i in range(N + 1):
        t = i / N
        env = math.exp(-((t - t0) / sig) ** 2)
        v = amp * env * math.sin(2 * math.pi * cycles * (t - t0) + 1.2)
        pts.append(origin + direction * (t * length) + up * v)
    m = mat('thzMat', (0.005, 0.14, 0.65), rough=0.15, coat=1.0, emission=(0.0, 0.3, 1.0), estr=1.0)
    ob = tube_mesh('thz', pts, r, fade_ends(m, 0.2, 0.15))
    ob.visible_shadow = False
    g = emit_mat('thzGlow', (0.1, 0.45, 1.0), 0.8, fresnel_alpha=True, alpha=0.22)
    glow = tube_mesh('thzglow', pts, r * 2.8, fade_ends(g, 0.2, 0.15), n=16)
    glow.visible_shadow = False
    return ob


def flat_arrow(name, a, b, width, material, thick=0.02, head_w=None, head_l=None, z_up=Vector((0, 0, 1))):
    """Extruded flat arrow lying in the plane perpendicular to z_up (e.g. printed on a surface)."""
    a, b = Vector(a), Vector(b)
    d = (b - a); L = d.length; u = d.normalized(); nrm = z_up.cross(u).normalized()
    head_w = head_w or width * 2.6; head_l = head_l or width * 2.6
    s = a + u * (L - head_l)
    outline = [a + nrm * width / 2, s + nrm * width / 2, s + nrm * head_w / 2, b,
               s - nrm * head_w / 2, s - nrm * width / 2, a - nrm * width / 2]
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in outline]
    f = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    moved = [e for e in ext['geom'] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=z_up * thick, verts=moved)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = mesh_obj(name, bm, material, smooth=False)
    md = ob.modifiers.new('bevel', 'BEVEL'); md.width = thick * 0.4; md.segments = 3
    return ob

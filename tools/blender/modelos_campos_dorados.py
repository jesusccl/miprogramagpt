"""
Modelos 3D de "Campos Dorados" hechos con Blender.

Todos los modelos se construyen por código (bmesh) en coordenadas del juego
(Y hacia arriba, el frente de los personajes mira a +Z) y se exportan como
glTF binario (.glb) sin texturas: el juego les aplica las texturas generadas
por texturas_campos_dorados.py según el nombre de cada material.

Los personajes están hechos de piezas rígidas colgadas de "articulaciones"
(empties) con los mismos nombres y pivotes que usa la animación procedural del
juego (hips, chest, neck, shR, elR, handR, sword, hipL, kneeL...).
La oclusión ambiental se hornea en colores de vértice con trazado de rayos.

Uso (cualquiera de las dos):
    blender -b --python tools/blender/modelos_campos_dorados.py
    python tools/blender/modelos_campos_dorados.py            # con el módulo `bpy`
Para generar solo algunos:  python tools/blender/modelos_campos_dorados.py augusto lobo

Salida: assets/campos-dorados/modelos/*.glb  (+ tools/blender/muestrario_modelos.jpg)
"""
import math
import os
import sys

import bpy  # noqa: I001  (bpy debe importarse antes que bmesh)
import bmesh
import numpy as np
from mathutils import Euler, Matrix, Vector, noise
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, 'assets', 'campos-dorados', 'modelos')
PREV = os.path.join(HERE, '_previas')
TAU = 2 * math.pi

# Color base de cada material (solo para las vistas previas; el juego usa sus texturas).
MAT_COLORS = {
    'piel': '#d8a67c', 'pelo': '#2a1f18', 'ojo': '#140e0b', 'tunica': '#5b5a42', 'pantalon': '#3a3026',
    'cuero': '#4a3322', 'venda': '#c9b99a', 'rojo': '#a3232d', 'rojo_osc': '#7c1620', 'paja': '#d6b262',
    'banda': '#3658a8', 'acero': '#d9dee4', 'oro': '#c9a03a', 'vaina': '#3a2a20',
    'pelaje': '#6c6660', 'pelaje_osc': '#3a3632', 'pelaje_claro': '#9a9186', 'nariz': '#141212',
    'diente': '#e8e0cc', 'brillo': '#ffb040',
    'madera': '#6b4a2b', 'abrigo': '#4b4a30', 'paja_suelta': '#cfa651', 'cuerda': '#7a5a36',
    'arpillera': '#a99366', 'sombrero': '#2e2a24', 'metal': '#9da3a6', 'hilo': '#241709', 'espina': '#3b2a1c',
    'piedra': '#958e7e', 'piedra_osc': '#6e695e', 'roca': '#8a857a', 'musgo': '#5d6a32',
    'corteza': '#4a3a2a', 'hojas': '#6f8a3a',
    # equipo
    'fieltro': '#2a2522', 'hierro': '#3c3b3d',
    # pueblo y puerto
    'yeso': '#e4dac3', 'teja': '#b5582f', 'tablas': '#7b5a39', 'viga': '#4a3524', 'vidrio': '#26303a',
    'puerta': '#5a3b22', 'contraventana': '#3d6e8a', 'lampara': '#ffd27a', 'toldo': '#a3272c', 'faro_rojo': '#b3302c',
    'agua_fuente': '#4a8aa0', 'fruta_roja': '#b02a2a', 'fruta_verde': '#6a9a3a', 'fruta_naranja': '#d8842a',
    'tela_azul': '#2d4f8a', 'tela_verde': '#3f6a3a', 'flor': '#d8455a',
    # barcos
    'vela': '#e6dcc2', 'casco': '#3b2a1f', 'casco_color': '#2f4f6a', 'casco_franja': '#c9a03a', 'casco_fondo': '#5a2a20',
    'casco_verde': '#2f5a4a', 'cubierta': '#8a6a44',
    # vecinos
    'camisa': '#dcd3bf', 'pantalon_azul': '#35486a', 'chaleco_v': '#5a3a28', 'delantal': '#cfc3a8', 'vestido': '#6a2e3e',
    'rayas': '#1f2d55', 'cinta': '#d8c050', 'pelo_gris': '#8a8680', 'pelo_rubio': '#c9a45a', 'pelo_rojo': '#8a3a20',
    'piel_osc': '#9c6a48', 'piel_clara': '#ecc6a0',
    # rasgos de la cara
    'ojo_blanco': '#efe9df', 'iris_marron': '#4a2e18', 'iris_azul': '#2e5a8a', 'iris_verde': '#3a6a2e', 'labios': '#a85a50',
    'suela': '#1e1712',
    # fauna
    'delfin': '#6d7f8c', 'delfin_vientre': '#d9dcd6', 'cangrejo': '#c2502a', 'ala': '#e8a030', 'ala_borde': '#2a1f18', 'pez': '#9ab0b8',
}


def lin(hexstr):
    h = hexstr.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (c[0], c[1], c[2], 1.0)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def get_mat(name):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = lin(MAT_COLORS[name])
    bsdf.inputs['Roughness'].default_value = 0.85
    return m


def M4(loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    return (Matrix.Translation(Vector(loc)) @ Euler(rot, 'XYZ').to_matrix().to_4x4()
            @ Matrix.Diagonal(Vector((scale[0], scale[1], scale[2], 1.0))))


def ellipse(rx, rz, y=0.0, n=16, cx=0.0, cz=0.0):
    return [(cx + rx * math.cos(TAU * k / n), y, cz + rz * math.sin(TAU * k / n)) for k in range(n)]


def ring_pts(axis, t, r1, r2, c1, c2, seg, a0, arc, fn):
    pts = []
    n = seg if arc is None else seg + 1
    for k in range(n):
        a = a0 + (TAU * k / seg if arc is None else arc[0] + (arc[1] - arc[0]) * k / seg)
        u, w = c1 + r1 * math.cos(a), c2 + r2 * math.sin(a)
        p = (u, t, w) if axis == 'y' else (u, w, t) if axis == 'z' else (t, u, w)
        if fn:
            p = fn(p, a)
        pts.append(tuple(p))
    return pts


# ---------------------------------------------------------------- geometría
class Geo:
    """Acumula primitivas en un bmesh, con un material por cara."""

    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []

    def mi(self, name):
        if name not in self.mats:
            self.mats.append(name)
        return self.mats.index(name)

    def _apply(self, verts, m, M=None, deform=None, recalc=True):
        if M is not None:
            bmesh.ops.transform(self.bm, matrix=M, verts=verts)
        if deform:
            for v in verts:
                v.co = Vector(deform(v.co.copy()))
        faces = list({f for v in verts for f in v.link_faces})
        idx = self.mi(m)
        for f in faces:
            f.material_index = idx
        if recalc and faces:
            bmesh.ops.recalc_face_normals(self.bm, faces=faces)
        return verts, faces

    def mesh(self, pts, polys, m, M=None, deform=None):
        vs = [self.bm.verts.new(p) for p in pts]
        for poly in polys:
            if len(set(poly)) < 3:
                continue
            try:
                self.bm.faces.new([vs[i] for i in poly])
            except ValueError:
                pass
        return self._apply(vs, m, M, deform)

    def rings(self, rings, m, closed=True, cap0=True, cap1=True, loop=False, M=None, deform=None):
        """Une anillos consecutivos; un anillo de un solo punto es una punta."""
        pts, polys, idx = [], [], []
        for r in rings:
            idx.append(list(range(len(pts), len(pts) + len(r))))
            pts += [tuple(p) for p in r]
        pairs = list(zip(idx, idx[1:])) + ([(idx[-1], idx[0])] if loop else [])
        for a, b in pairs:
            if len(a) == 1 and len(b) == 1:
                continue
            if len(a) == 1:
                n = len(b)
                polys += [(a[0], b[k], b[(k + 1) % n]) for k in range(n if closed else n - 1)]
            elif len(b) == 1:
                n = len(a)
                polys += [(a[k], a[(k + 1) % n], b[0]) for k in range(n if closed else n - 1)]
            else:
                n = len(a)
                polys += [(a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]) for k in range(n if closed else n - 1)]
        if closed and not loop:
            if cap0 and len(idx[0]) > 2:
                polys.append(tuple(idx[0]))
            if cap1 and len(idx[-1]) > 2:
                polys.append(tuple(idx[-1]))
        return self.mesh(pts, polys, m, M, deform)

    def loft(self, secs, m, seg=16, axis='y', cap0=True, cap1=True, arc=None, fn=None, M=None, a0=0.0):
        """Secciones elípticas (t, r1, r2[, c1, c2]) a lo largo de un eje; r=0 es una punta."""
        rings = []
        for i, s in enumerate(secs):
            t, r1, r2 = s[0], s[1], s[2]
            c1 = s[3] if len(s) > 3 else 0.0
            c2 = s[4] if len(s) > 4 else 0.0
            f = (lambda p, a, i=i: fn(p, a, i)) if fn else None
            if r1 < 1e-6 and r2 < 1e-6:
                p = (c1, t, c2) if axis == 'y' else (c1, c2, t) if axis == 'z' else (t, c1, c2)
                rings.append([f(p, 0.0) if f else p])
            else:
                rings.append(ring_pts(axis, t, r1, r2, c1, c2, seg, a0, arc, f))
        return self.rings(rings, m, closed=arc is None, cap0=cap0, cap1=cap1, M=M)

    def tube(self, path, radius, m, seg=8, closed=False, cap=True, flat=1.0, M=None, fn=None):
        P = [Vector(p) for p in path]
        n = len(P)
        R = list(radius) if isinstance(radius, (list, tuple)) else [radius] * n
        T = []
        for i in range(n):
            d = (P[(i + 1) % n] - P[(i - 1) % n]) if closed else (P[min(i + 1, n - 1)] - P[max(i - 1, 0)])
            T.append(d.normalized())
        ref = Vector((0, 1, 0)) if abs(T[0].y) < 0.95 else Vector((1, 0, 0))
        N = T[0].cross(ref).normalized()
        rings = []
        for i in range(n):
            N = (N - T[i] * N.dot(T[i])).normalized()
            B = T[i].cross(N)
            ring = []
            for k in range(seg):
                a = TAU * k / seg
                p = P[i] + N * math.cos(a) * R[i] + B * math.sin(a) * R[i] * flat
                if fn:
                    p = Vector(fn(p, i, a))
                ring.append(p)
            rings.append(ring)
        return self.rings(rings, m, closed=True, cap0=cap and not closed, cap1=cap and not closed, loop=closed, M=M)

    def sphere(self, r, m, seg=16, rings=10, M=None, deform=None):
        ret = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=rings, radius=r)
        return self._apply(ret['verts'], m, M, deform)

    def ico(self, r, m, sub=1, M=None, deform=None):
        ret = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r)
        return self._apply(ret['verts'], m, M, deform)

    def box(self, m, M=None, deform=None):
        ret = bmesh.ops.create_cube(self.bm, size=1.0)
        return self._apply(ret['verts'], m, M, deform)

    def recolor(self, faces, fn):
        for f in faces:
            name = fn(f.calc_center_median())
            if name:
                f.material_index = self.mi(name)


def joint(name, parent, loc, rot=(0, 0, 0)):
    ob = bpy.data.objects.new(name, None)
    ob.empty_display_size = 0.05
    bpy.context.scene.collection.objects.link(ob)
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def part(name, parent, loc, build, rot=(0, 0, 0), sharp=48, subsurf=0):
    g = Geo()
    build(g)
    me = bpy.data.meshes.new(name)
    g.bm.to_mesh(me)
    g.bm.free()
    for mn in g.mats:
        me.materials.append(get_mat(mn))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = rot
    if subsurf:
        mod = ob.modifiers.new('sub', 'SUBSURF')
        mod.levels = mod.render_levels = subsurf
        ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        nm = bpy.data.meshes.new_from_object(ev)
        ob.modifiers.clear()
        ob.data = nm
        me = nm
    me.shade_smooth()
    if sharp:
        me.set_sharp_from_angle(angle=math.radians(sharp))
    return ob


def fnoise(p, freq, amp, seed=0.0):
    v = Vector(p)
    return v * (1.0 + amp * noise.noise(v * freq + Vector((seed, seed * 1.7, seed * 0.3))))


def bands(y0, y1, r0, r1, n, bump, c=(0.0, 0.0), rz_ratio=1.0):
    """Secciones con abultamientos alternos (vendas, empuñaduras)."""
    out = []
    for k in range(n + 1):
        t = k / n
        r = (r0 + (r1 - r0) * t) * (1 + bump * (k % 2))
        out.append((y0 + (y1 - y0) * t, r, r * rz_ratio, c[0], c[1]))
    return out


# ---------------------------------------------------------------- oclusión ambiental
def bake_ao(dist, rays=24, strength=1.0, min_ao=0.28, ground=None):
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    V, F = [], []
    for o in meshes:
        mw = o.matrix_world
        base = len(V)
        V.extend([mw @ v.co for v in o.data.vertices])
        F.extend([[base + i for i in p.vertices] for p in o.data.polygons])
    if ground is not None:
        b = len(V)
        s = 400.0
        V.extend([Vector((-s, ground, -s)), Vector((s, ground, -s)), Vector((s, ground, s)), Vector((-s, ground, s))])
        F.append([b, b + 1, b + 2, b + 3])
    bvh = BVHTree.FromPolygons(V, F)
    dirs = []
    for i in range(rays):
        u = (i + 0.5) / rays
        r, phi = math.sqrt(u), i * 2.399963
        dirs.append((r * math.cos(phi), r * math.sin(phi), math.sqrt(1 - u)))
    for o in meshes:
        me = o.data
        mw = o.matrix_world
        nm = mw.to_3x3().inverted_safe().transposed()
        attr = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
        me.color_attributes.active_color = attr
        me.color_attributes.render_color_index = me.color_attributes.active_color_index
        off = dist * 0.01
        for v in me.vertices:
            p = mw @ v.co
            n = (nm @ v.normal).normalized()
            t = n.orthogonal().normalized()
            b = n.cross(t)
            occ = 0.0
            for (x, y, z) in dirs:
                hit = bvh.ray_cast(p + n * off, t * x + b * y + n * z, dist)
                if hit[0] is not None:
                    occ += 1.0 - 0.6 * hit[3] / dist
            ao = max(min_ao, 1.0 - strength * occ / rays)
            attr.data[v.index].color = (ao, ao, ao, 1.0)


def export(fname):
    bpy.context.view_layer.update()
    props = {p.identifier for p in bpy.ops.export_scene.gltf.get_rna_type().properties}
    kw = dict(filepath=os.path.join(OUT, fname), export_format='GLB', export_yup=False, export_apply=True,
              export_materials='EXPORT', export_vertex_color='ACTIVE', export_texcoords=False, export_normals=True,
              export_cameras=False, export_lights=False, use_selection=False, export_extras=False, export_animations=False)
    bpy.ops.export_scene.gltf(**{k: v for k, v in kw.items() if k in props or k == 'filepath'})
    print('  ->', fname, '%.0f KB' % (os.path.getsize(os.path.join(OUT, fname)) / 1024))


# ---------------------------------------------------------------- vista previa
def preview(fname, target, dist, elev=0.32, azim=0.75, size=(420, 420)):
    sc = bpy.context.scene
    for m in bpy.data.materials:
        nt = m.node_tree
        bsdf = nt.nodes.get('Principled BSDF')
        if not bsdf:
            continue
        at = nt.nodes.new('ShaderNodeAttribute')
        at.attribute_name = 'Col'
        mx = nt.nodes.new('ShaderNodeMix')
        mx.data_type, mx.blend_type = 'RGBA', 'MULTIPLY'
        mx.inputs[0].default_value = 1.0
        mx.inputs[6].default_value = bsdf.inputs['Base Color'].default_value[:]
        nt.links.new(at.outputs['Color'], mx.inputs[7])
        nt.links.new(mx.outputs[2], bsdf.inputs['Base Color'])
        if m.name == 'brillo':
            bsdf.inputs['Emission Color'].default_value = lin('#ffb040')
            bsdf.inputs['Emission Strength'].default_value = 3.0
    gm = bpy.data.materials.new('suelo_prev')
    gm.use_nodes = True
    gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = lin('#a48b58')
    me = bpy.data.meshes.new('suelo_prev')
    s = 60.0
    me.from_pydata([(-s, 0, -s), (s, 0, -s), (s, 0, s), (-s, 0, s)], [], [(3, 2, 1, 0)])
    me.materials.append(gm)
    gob = bpy.data.objects.new('suelo_prev', me)
    sc.collection.objects.link(gob)
    tgt = Vector(target)
    cpos = tgt + Vector((math.sin(azim) * math.cos(elev), math.sin(elev), math.cos(azim) * math.cos(elev))) * dist
    cd = bpy.data.cameras.new('cam_prev')
    cd.lens = 50
    cam = bpy.data.objects.new('cam_prev', cd)
    sc.collection.objects.link(cam)
    cam.location = cpos
    fwd = (tgt - cpos).normalized()
    right = fwd.cross(Vector((0, 1, 0))).normalized()
    upv = right.cross(fwd)
    cam.rotation_euler = Matrix((right, upv, -fwd)).transposed().to_euler()
    sc.camera = cam
    ld = bpy.data.lights.new('sol_prev', 'SUN')
    ld.energy = 3.2
    ld.angle = math.radians(8)
    sun = bpy.data.objects.new('sol_prev', ld)
    sc.collection.objects.link(sun)
    sun.rotation_euler = (-Vector((-0.55, 0.7, 0.45))).to_track_quat('-Z', 'Y').to_euler()
    w = bpy.data.worlds.new('cielo_prev')
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = lin('#b9c9d8')
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
    sc.world = w
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 40
    sc.cycles.max_bounces = 3
    try:
        sc.cycles.use_denoising = True
    except Exception:
        pass
    sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x, sc.render.resolution_y = size
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    os.makedirs(PREV, exist_ok=True)
    sc.render.filepath = os.path.join(PREV, fname)
    try:
        bpy.ops.render.render(write_still=True)
    except RuntimeError:
        sc.cycles.use_denoising = False
        bpy.ops.render.render(write_still=True)


# ---------------------------------------------------------------- rasgos comunes de los personajes
def face(g, skin, hair, iris='iris_marron', brow=0.0, smile=0.4):
    """Cabeza con cara: ojos (blanco, iris y pupila) con párpados, cejas, nariz, labios y orejas.
    Coordenadas del cuello: la cabeza es una esfera de radio 0.12 centrada en y=0.15."""
    def jaw(p):
        x, y, z = p
        dy = y - 0.15
        if dy < 0:
            k = min(1.0, -dy / 0.12)
            x *= 1 - 0.21 * k
            z = z * (1 - 0.07 * k) + (0.014 * k if z > 0 else 0.0)
        if z > 0.06 and -0.035 < dy < 0.0:   # pómulos
            x *= 1.0 + 0.035 * (1 - abs(dy + 0.017) / 0.018)
        if z > 0.07 and 0.0 < dy < 0.03 and abs(x) < 0.07:   # cuencas de los ojos
            z -= 0.006 * math.sin(math.pi * dy / 0.03) * (1 - abs(abs(x) - 0.041) / 0.03 if abs(abs(x) - 0.041) < 0.03 else 0)
        return (x, y, z)
    g.sphere(0.12, skin, 26, 18, M4((0, 0.15, 0), scale=(0.93, 1.06, 1.0)), deform=jaw)
    for s in (1, -1):
        c = Vector((0.041 * s, 0.166, 0.097))
        g.sphere(0.02, 'ojo_blanco', 12, 10, M4(tuple(c)))
        g.sphere(0.0115, iris, 12, 8, M4((c.x, c.y, c.z + 0.0165), scale=(1, 1, 0.42)))
        g.sphere(0.0056, 'ojo', 8, 6, M4((c.x, c.y, c.z + 0.0205), scale=(1, 1, 0.4)))
        # párpados: casquete superior e inferior de piel sobre el globo ocular
        g.sphere(0.0215, skin, 12, 8, M4(tuple(c), rot=(-0.25, 0, 0)), deform=lambda p, cy=c.y: (p[0], max(p[1], cy + 0.005), p[2]))
        g.sphere(0.0212, skin, 12, 8, M4(tuple(c), rot=(0.3, 0, 0)), deform=lambda p, cy=c.y: (p[0], min(p[1], cy - 0.012), p[2]))
        # cejas
        g.tube([(0.018 * s, 0.19 + brow * 0.004, 0.114), (0.04 * s, 0.195 + brow * 0.006, 0.113), (0.063 * s, 0.19 - brow * 0.004, 0.103)],
               [0.0055, 0.0065, 0.0045], hair, 6, flat=0.45)
        # orejas con reborde
        g.sphere(1.0, skin, 10, 8, M4((0.111 * s, 0.152, -0.008), rot=(0, 0.25 * s, 0), scale=(0.012, 0.032, 0.023)))
        g.tube([(0.118 * s, 0.128, 0.004), (0.123 * s, 0.155, 0.012), (0.121 * s, 0.182, 0.0), (0.117 * s, 0.176, -0.022), (0.114 * s, 0.14, -0.018)],
               0.0045, skin, 5)
    # nariz: tabique, punta y aletas
    g.tube([(0, 0.168, 0.112), (0, 0.145, 0.124), (0, 0.128, 0.132)], [0.008, 0.011, 0.012], skin, 8)
    g.sphere(0.0125, skin, 10, 8, M4((0, 0.127, 0.131), scale=(1.15, 0.9, 1.0)))
    for s in (1, -1):
        g.sphere(0.008, skin, 8, 6, M4((0.011 * s, 0.123, 0.125), scale=(1.1, 0.9, 1.0)))
    # labios con las comisuras según la sonrisa
    up = [(-0.024, 0.1035 + 0.003 * smile, 0.112), (-0.011, 0.105, 0.118), (0.0, 0.1045, 0.12), (0.011, 0.105, 0.118), (0.024, 0.1035 + 0.003 * smile, 0.112)]
    lo = [(-0.021, 0.1005 + 0.003 * smile, 0.112), (0.0, 0.097, 0.119), (0.021, 0.1005 + 0.003 * smile, 0.112)]
    g.tube(up, [0.003, 0.0042, 0.004, 0.0042, 0.003], 'labios', 6, flat=0.6)
    g.tube(lo, [0.0035, 0.0052, 0.0035], 'labios', 6, flat=0.6)


def hand(g, skin, side, grip=0.3):
    """Mano colgando a lo largo de -y: palma hacia el cuerpo, cuatro dedos y pulgar (grip 0 abierta, 1 cerrada)."""
    inward = -side
    g.loft([(0.018, 0.017, 0.03), (-0.02, 0.019, 0.036), (-0.058, 0.016, 0.037), (-0.07, 0.013, 0.033)], skin, seg=10,
           M=M4((inward * 0.002, 0, 0)))
    for k, L in enumerate((0.046, 0.052, 0.049, 0.04)):
        z = 0.024 - k * 0.016
        base = Vector((0.0, -0.068, z))
        mid = base + Vector((inward * 0.012 * grip, -L * 0.52, 0.0))
        tip = base + Vector((inward * (0.006 + 0.04 * grip), -L * (0.98 - 0.45 * grip), 0.0))
        g.tube([base, mid, tip], [0.0092, 0.0084, 0.0072], skin, 6)
        g.sphere(0.0072, skin, 6, 5, M4(tuple(tip)))
    g.tube([(inward * 0.012, -0.018, 0.028), (inward * 0.022, -0.04, 0.042), (inward * (0.02 + 0.012 * grip), -0.06, 0.05)],
           [0.011, 0.0095, 0.008], skin, 6)
    g.sphere(0.0078, skin, 6, 5, M4((inward * (0.02 + 0.012 * grip), -0.06, 0.05)))


# ================================================================ AUGUSTO
def build_augusto():
    reset()
    root = joint('augusto', None, (0, 0, 0))
    hips = joint('hips', root, (0, 0.95, 0))

    def pelvis(g):
        g.loft([(-0.1, 0.15, 0.12), (-0.06, 0.162, 0.13), (0.05, 0.158, 0.127), (0.18, 0.168, 0.132),
                (0.32, 0.172, 0.13)], 'tunica', seg=20)

        def hem(p, a, i):
            k = (0.0, 0.35, 0.7, 1.0)[i]
            r = 1 + 0.05 * math.sin(a * 9) * k
            y = p[1] - (0.018 * abs(math.sin(a * 6.0)) + 0.008 * math.sin(a * 13) if i == 3 else 0)
            return (p[0] * r, y, p[2] * r)
        for a0, a1 in ((36, 86), (94, 144), (216, 266), (274, 324)):
            g.loft([(0.03, 0.168, 0.138), (-0.12, 0.2, 0.17), (-0.3, 0.235, 0.2), (-0.5, 0.265, 0.23)],
                   'tunica', seg=6, arc=(math.radians(a0), math.radians(a1)), fn=hem)
        g.loft([(-0.035, 0.172, 0.142), (0.0, 0.179, 0.149), (0.075, 0.177, 0.147), (0.1, 0.17, 0.14)], 'rojo_osc',
               seg=24, fn=lambda p, a, i: (p[0] * (1 + 0.02 * math.sin(a * 7)), p[1], p[2] * (1 + 0.02 * math.sin(a * 7))))
        g.loft([(-0.058, 0.177, 0.147), (-0.022, 0.177, 0.147)], 'cuero', seg=24)
        g.box('oro', M4((0, -0.04, 0.151), scale=(0.05, 0.042, 0.012)))
        g.sphere(0.035, 'rojo_osc', 10, 8, M4((0.15, 0.03, 0.085), scale=(1, 0.8, 0.8)))
        g.tube([(0.16, 0.02, 0.095), (0.19, -0.08, 0.11), (0.2, -0.2, 0.12)], [0.028, 0.026, 0.02], 'rojo_osc', 8, flat=0.35)
        g.tube([(0.14, 0.02, 0.105), (0.15, -0.1, 0.14), (0.14, -0.16, 0.16)], [0.025, 0.022, 0.018], 'rojo_osc', 8, flat=0.35)
        g.sphere(0.06, 'cuero', 12, 8, M4((-0.15, -0.07, -0.1), scale=(0.9, 1.1, 0.7)))
        g.box('cuero', M4((-0.15, -0.02, -0.1), rot=(0.2, 0.6, 0), scale=(0.1, 0.02, 0.075)))
        a, b = Vector((0.2, -0.01, 0.1)), Vector((0.25, -0.43, -0.46))
        pts = [a.lerp(b, t) + Vector((0, -0.03 * math.sin(t * math.pi), 0)) for t in (i / 8 for i in range(9))]
        g.tube(pts, 0.024, 'vaina', 8, flat=0.7)
        g.tube(pts[:2], 0.03, 'oro', 8, flat=0.75)
        g.tube([pts[-1], b + (b - a).normalized() * 0.045], [0.026, 0.01], 'oro', 8, flat=0.7)
        g.tube(ellipse(0.034, 0.03, 0, 10), 0.008, 'cuero', 5, closed=True, M=M4(tuple(pts[2]), rot=(0.9, 0, 0)))
    part('pelvis', hips, (0, 0, 0), pelvis)

    chest = joint('chest', hips, (0, 0.52, 0))

    def torso(g):
        g.loft([(-0.27, 0.168, 0.13), (-0.18, 0.185, 0.14), (-0.08, 0.212, 0.148), (-0.02, 0.212, 0.14),
                (0.03, 0.17, 0.115), (0.07, 0.09, 0.08)], 'tunica', seg=20)
        g.tube(ellipse(0.085, 0.072, 0.055, 16), 0.018, 'venda', 6, closed=True)
        g.tube([(-0.17, -0.02, 0.1), (-0.08, -0.1, 0.153), (0.05, -0.19, 0.153), (0.16, -0.27, 0.125)], 0.012, 'cuero', 6, flat=0.35)
    part('torso', chest, (0, 0, 0), torso)

    part('chaleco', chest, (0, 0, 0), lambda g: g.loft(
        [(-0.28, 0.18, 0.142), (-0.18, 0.196, 0.152), (-0.08, 0.224, 0.16), (-0.02, 0.224, 0.152), (0.03, 0.18, 0.126)],
        'cuero', seg=26, arc=(math.radians(112), math.radians(428))))

    def buttons(g):
        for y in (-0.06, -0.13, -0.2):
            for sd in (1, -1):
                g.sphere(0.012, 'oro', 8, 6, M4((0.055 * sd, y, 0.15), scale=(1, 1, 0.6)))
    part('botones', chest, (0, 0, 0), buttons)

    def mantle(g):
        def f(p, a, i):
            k = (0.0, 0.2, 0.45, 0.7, 0.85, 1.0)[i]
            r = 1 + 0.07 * math.sin(a * 9 + 0.5) * k
            y = p[1] - 0.07 * max(0.0, -math.sin(a)) * k
            if i == 5:
                y -= 0.025 * abs(math.sin(a * 5.5)) + 0.01 * math.sin(a * 17)
            return (p[0] * r, y, p[2] * r)
        g.loft([(0.07, 0.11, 0.09), (0.04, 0.2, 0.15), (0.0, 0.3, 0.2), (-0.06, 0.35, 0.25), (-0.16, 0.39, 0.3),
                (-0.27, 0.42, 0.34)], 'rojo', seg=44, cap0=False, cap1=False, fn=f)
    part('manto', chest, (0, 0, 0), mantle, sharp=0)

    def scarf(g):
        g.tube(ellipse(0.118, 0.106, 0.075, 18), 0.042, 'rojo_osc', 8, closed=True,
               fn=lambda p, i, a: p + (p - Vector((0, 0.075, 0))).normalized() * 0.006 * math.sin(i * 2.3 + a))
        g.sphere(0.038, 'rojo_osc', 10, 8, M4((0.05, 0.05, 0.12)))
        g.tube([(0.06, 0.04, 0.14), (0.08, -0.03, 0.24), (0.09, -0.12, 0.3), (0.1, -0.24, 0.36)], [0.03, 0.029, 0.026, 0.02], 'rojo_osc', 8, flat=0.35)
        g.tube([(0.03, 0.04, 0.14), (0.03, -0.05, 0.23), (0.02, -0.14, 0.29)], [0.028, 0.025, 0.018], 'rojo_osc', 8, flat=0.35)
    part('bufanda', chest, (0, 0, 0), scarf)

    neck = joint('neck', chest, (0, 0.06, 0))
    part('cuello', neck, (0, 0, 0), lambda g: g.loft([(-0.02, 0.05, 0.05), (0.1, 0.047, 0.047)], 'piel', seg=12))

    def head(g):
        def jaw(p):
            x, y, z = p
            dy = y - 0.15
            if dy < 0:
                k = min(1.0, -dy / 0.12)
                x *= 1 - 0.22 * k
                z = z * (1 - 0.08 * k) + (0.012 * k if z > 0 else 0.0)
            return (x, y, z)
        face(g, 'piel', 'pelo', 'iris_marron', brow=0.6, smile=0.5)
        g.sphere(0.127, 'pelo', 18, 12, M4((0, 0.172, -0.016), scale=(1.0, 0.85, 1.02)))
        # flequillo y patillas
        for k in range(7):
            x = -0.066 + k * 0.022
            g.tube([(x, 0.262, 0.06), (x * 1.08, 0.238, 0.095), (x * 1.12 + 0.01, 0.208, 0.107)], [0.014, 0.01, 0.003], 'pelo', 8)
        for s in (1, -1):
            g.tube([(0.1 * s, 0.19, 0.04), (0.108 * s, 0.155, 0.05), (0.106 * s, 0.128, 0.052)], [0.012, 0.01, 0.004], 'pelo', 5)
        for k in range(9):
            a = math.pi + (k - 4) * 0.33
            base = Vector((math.sin(a) * 0.105, 0.14, math.cos(a) * 0.105 - 0.02))
            tip = base + Vector((math.sin(a) * 0.035, -0.07 - 0.02 * (k % 2), math.cos(a) * 0.03))
            g.tube([base, base.lerp(tip, 0.5), tip], [0.022, 0.014, 0.002], 'pelo', 6)
        g.sphere(0.03, 'pelo', 10, 8, M4((0, 0.16, -0.135)))
        g.tube([(0, 0.15, -0.14), (0, 0.08, -0.17), (0, 0.01, -0.16)], [0.025, 0.018, 0.004], 'pelo', 8)
    part('cabeza', neck, (0, 0, 0), head)

    def hat(g):
        # sombrero cónico de viajero (paja trenzada) con un aro interior y cordones al mentón
        prof = [(0.0, 0.12), (-0.02, 0.26), (-0.048, 0.4), (-0.074, 0.5), (-0.082, 0.515), (-0.07, 0.518),
                (-0.056, 0.5), (-0.012, 0.4), (0.06, 0.28), (0.13, 0.16), (0.19, 0.06), (0.215, 0.018), (0.222, 0.0)]
        wav = lambda p, a, i: (p[0], p[1] + (0.008 * math.sin(a * 4 + 0.7) if 2 <= i <= 7 else 0.0), p[2])
        g.loft([(y, r, r) for y, r in prof], 'paja', seg=40, cap0=False, fn=wav)
        g.loft([(-0.005, 0.13, 0.13), (0.035, 0.125, 0.125)], 'banda', seg=24, cap0=False, cap1=False)
        g.sphere(0.018, 'paja', 8, 6, M4((0, 0.225, 0), scale=(1, 0.7, 1)))
        for sd in (1, -1):
            g.tube([(0.115 * sd, -0.01, 0.0), (0.1 * sd, -0.1, 0.05), (0.03 * sd, -0.19, 0.1)], 0.006, 'banda', 5)
        g.sphere(0.014, 'banda', 6, 5, M4((0, -0.195, 0.105)))
    part('sombrero', neck, (0, 0.25, 0), hat, rot=(-0.1, 0, 0), sharp=0)

    def tricorn(g):
        # ala levantada en tres lados con puntas bajas adelante y atrás
        def lift(p, a, i):
            corner = max(0.0, math.cos(1.5 * (a - math.pi / 2))) ** 6 + max(0.0, math.cos(1.5 * (a - math.pi / 2 - TAU / 3))) ** 6 \
                + max(0.0, math.cos(1.5 * (a - math.pi / 2 + TAU / 3))) ** 6
            L = max(0.0, 1.0 - 1.4 * corner) * (i / 3)
            r = math.hypot(p[0], p[2])
            k = (r - 0.07 * L) / max(r, 1e-6)
            return (p[0] * k, p[1] + 0.13 * L, p[2] * k)
        g.loft([(0.0, 0.15, 0.15), (0.004, 0.22, 0.22), (0.008, 0.28, 0.28), (0.014, 0.31, 0.31)], 'fieltro', seg=48,
               cap0=False, cap1=False, fn=lift)
        g.sphere(0.15, 'fieltro', 18, 10, M4((0, 0.03, 0), scale=(1.0, 0.85, 1.05)))
        edge = []
        for k in range(48):
            a = TAU * k / 48
            p = lift((math.cos(a) * 0.31, 0.016, math.sin(a) * 0.31), a, 3)
            edge.append(p)
        g.tube(edge, 0.009, 'oro', 5, closed=True)
    part('tricornio', neck, (0, 0.24, 0), tricorn, rot=(-0.08, 0, 0), sharp=0)

    def bandana(g):
        g.sphere(0.133, 'rojo_osc', 20, 12, M4((0, 0.175, -0.012), scale=(1.0, 0.82, 1.04)),
                 deform=lambda p: (p[0], max(p[1], 0.15 - 0.05 * max(0.0, -p[2]) / 0.13), p[2]))
        g.sphere(0.03, 'rojo_osc', 8, 6, M4((0, 0.16, -0.14)))
        g.tube([(0.01, 0.155, -0.145), (0.03, 0.08, -0.17), (0.05, 0.0, -0.16)], [0.024, 0.02, 0.012], 'rojo_osc', 6, flat=0.35)
        g.tube([(-0.01, 0.155, -0.145), (-0.03, 0.09, -0.175), (-0.045, 0.03, -0.17)], [0.022, 0.018, 0.01], 'rojo_osc', 6, flat=0.35)
    part('panuelo', neck, (0, 0, 0), bandana, sharp=0)

    for side, nm in ((-1, 'R'), (1, 'L')):
        sh = joint('sh' + nm, chest, (0.25 * side, -0.03, 0))

        def upper(g):
            g.sphere(0.05, 'tunica', 12, 8, M4((0, -0.015, 0)))
            g.loft([(0.0, 0.057, 0.055), (-0.1, 0.056, 0.054), (-0.2, 0.05, 0.049), (-0.305, 0.047, 0.046)], 'tunica', seg=12)
        part('brazo' + nm, sh, (0, 0, 0), upper)
        el = joint('el' + nm, sh, (0, -0.3, 0))

        def fore(g):
            g.sphere(0.047, 'tunica', 10, 8, M4((0, 0.005, 0)))
            g.loft(bands(0.0, -0.235, 0.046, 0.038, 12, 0.07), 'venda', seg=12)
            g.loft([(-0.212, 0.045, 0.043), (-0.248, 0.045, 0.043)], 'cuero', seg=12)
        part('antebrazo' + nm, el, (0, 0, 0), fore)
        hand_j = joint('hand' + nm, el, (0, -0.29, 0))

        def handg(g, side=side, nm=nm):
            # la derecha empuña la espada; la izquierda va más relajada
            hand(g, 'piel', side, grip=0.95 if nm == 'R' else 0.35)
            g.loft([(0.01, 0.034, 0.042), (-0.03, 0.036, 0.044)], 'cuero', seg=12)
        part('mano' + nm, hand_j, (0, 0, 0), handg)
        if nm == 'R':
            sword = joint('sword', hand_j, (0, 0, 0))

            def swordg(g):
                g.loft(bands(0.1, -0.098, 0.019, 0.019, 10, 0.1), 'cuero', seg=10)
                g.sphere(0.024, 'oro', 10, 8, M4((0, 0.114, 0), scale=(1, 0.8, 1)))
                g.loft([(-0.098, 0.05, 0.038), (-0.11, 0.055, 0.042), (-0.122, 0.049, 0.037)], 'oro', seg=16)
                g.loft([(-0.122, 0.011, 0.025), (-0.15, 0.01, 0.023)], 'oro', seg=8)
                secs = []
                for k in range(12):
                    t = k / 11
                    secs.append((-0.15 - t * 0.8, 0.0055, 0.019 - 0.003 * t, 0.0, 0.012 * t * t))
                secs.append((-1.0, 0.0, 0.0, 0.0, 0.017))
                g.loft(secs, 'acero', seg=4)
            part('espada', sword, (0, 0, 0), swordg, sharp=30)

            def sable(g):
                g.loft(bands(0.1, -0.09, 0.018, 0.018, 10, 0.1), 'cuero', seg=10)
                g.sphere(0.022, 'oro', 10, 8, M4((0, 0.11, 0)))
                g.tube([(0, 0.105, 0.02), (0, 0.08, 0.07), (0, 0.0, 0.088), (0, -0.08, 0.065), (0, -0.1, 0.02)], 0.007, 'oro', 6)
                g.sphere(1.0, 'oro', 12, 8, M4((0, -0.1, 0.01), scale=(0.045, 0.018, 0.07)))
                secs = [(-0.12 - t * 0.74, 0.005, 0.025 - 0.004 * t, 0.0, -0.05 * t * t) for t in (k / 11 for k in range(12))]
                secs.append((-0.93, 0.0, 0.0, 0.0, -0.075))
                g.loft(secs, 'acero', seg=4)
            part('sable', sword, (0, 0, 0), sable, sharp=30)

            def hacha(g):
                g.loft([(0.13, 0.021, 0.021), (-0.45, 0.02, 0.02), (-0.7, 0.019, 0.019), (-0.74, 0.0, 0.0)], 'madera', seg=8)
                g.loft(bands(0.1, -0.08, 0.023, 0.023, 8, 0.1), 'cuero', seg=8)
                poly = [(0.02, -0.5), (0.13, -0.48), (0.22, -0.45), (0.27, -0.55), (0.28, -0.64), (0.24, -0.74), (0.14, -0.72), (0.02, -0.68)]
                rings = [[(x, y, z) for z, y in poly] for x in (0.012, -0.012)]
                g.rings(rings, 'hierro')
                g.tube([(0, y, z) for z, y in poly[2:6]], 0.006, 'acero', 5)
                g.loft([(0.0, 0.022, 0.022, 0.0, -0.59), (-0.14, 0.0, 0.0, 0.0, -0.59)], 'hierro', seg=6, axis='z')
                g.loft([(-0.5, 0.03, 0.03), (-0.69, 0.03, 0.03)], 'hierro', seg=8)
            part('hacha', sword, (0, 0, 0), hacha, sharp=30)

            def katana(g):
                g.loft(bands(0.12, -0.09, 0.016, 0.016, 12, 0.14), 'venda', seg=8)
                g.sphere(0.017, 'hierro', 8, 6, M4((0, 0.125, 0), scale=(1, 0.6, 1)))
                g.loft([(-0.095, 0.048, 0.048), (-0.107, 0.048, 0.048)], 'hierro', seg=20)
                g.loft([(-0.107, 0.01, 0.02), (-0.13, 0.009, 0.018)], 'oro', seg=8)
                secs = [(-0.13 - t * 0.92, 0.0045, 0.016 - 0.003 * t, 0.0, 0.04 * t * t) for t in (k / 13 for k in range(14))]
                secs.append((-1.1, 0.0, 0.0, 0.0, 0.05))
                g.loft(secs, 'acero', seg=4)
            part('katana', sword, (0, 0, 0), katana, sharp=30)

            def alba(g):
                g.loft(bands(0.11, -0.09, 0.02, 0.02, 10, 0.1), 'cuero', seg=10)
                g.sphere(0.03, 'oro', 10, 8, M4((0, 0.125, 0)))
                g.sphere(0.014, 'rojo', 8, 6, M4((0, 0.125, 0.026)))
                for sd in (1, -1):
                    g.tube([(0, -0.1, 0), (0, -0.095, 0.06 * sd), (0, -0.06, 0.1 * sd), (0, -0.02, 0.11 * sd)], [0.012, 0.01, 0.008, 0.003], 'oro', 6)
                secs = [(-0.11 - t * 0.85, 0.007, 0.03 - 0.006 * t) for t in (k / 11 for k in range(12))]
                secs.append((-1.06, 0.0, 0.0))
                g.loft(secs, 'acero', seg=4)
                g.box('oro', M4((0, -0.5, 0), scale=(0.016, 0.66, 0.008)))
            part('espada_alba', sword, (0, 0, 0), alba, sharp=30)
            joint('swordBase', sword, (0, -0.15, 0))
            joint('swordTip', sword, (0, -1.0, 0))

    for side, nm in ((1, 'L'), (-1, 'R')):
        hip = joint('hip' + nm, hips, (0.1 * side, -0.02, 0))

        def thigh(g):
            g.loft([(0.04, 0.085, 0.082), (-0.12, 0.084, 0.08), (-0.3, 0.072, 0.07), (-0.46, 0.064, 0.062)], 'pantalon', seg=12)
            g.sphere(0.063, 'pantalon', 12, 8, M4((0, -0.46, 0.005)))
        part('muslo' + nm, hip, (0, 0, 0), thigh)
        knee = joint('knee' + nm, hip, (0, -0.46, 0))

        def shin(g):
            secs = bands(0.0, -0.33, 0.062, 0.05, 14, 0.06)
            secs = [(y, r * (1 + 0.08 * math.exp(-((y + 0.1) / 0.08) ** 2)), rz * (1 + 0.1 * math.exp(-((y + 0.1) / 0.08) ** 2)), c1, c2)
                    for y, r, rz, c1, c2 in secs]
            g.loft(secs, 'venda', seg=12)
            g.loft([(-0.31, 0.053, 0.055), (-0.39, 0.057, 0.061), (-0.44, 0.059, 0.064)], 'cuero', seg=12)
            g.loft([(-0.075, 0.054, 0.042, 0.0, -0.432), (-0.02, 0.06, 0.05, 0.0, -0.428), (0.06, 0.056, 0.042, 0.0, -0.438),
                    (0.13, 0.046, 0.032, 0.0, -0.446), (0.172, 0.0, 0.0, 0.0, -0.45)], 'cuero', seg=12, axis='z')
            g.box('suela', M4((0, -0.462, 0.045), scale=(0.118, 0.022, 0.26)))
            g.box('suela', M4((0, -0.448, -0.06), scale=(0.1, 0.03, 0.07)))
            for k in range(3):
                g.tube([(-0.035, -0.37 - k * 0.02, 0.05 + k * 0.012), (0.035, -0.37 - k * 0.02, 0.05 + k * 0.012)], 0.004, 'venda', 4)
        part('pierna' + nm, knee, (0, 0, 0), shin)

    bake_ao(0.14, rays=24, ground=0.0)
    export('augusto.glb')
    for n in ('tricornio', 'panuelo', 'sable', 'hacha', 'katana', 'espada_alba', 'chaleco', 'botones'):
        bpy.data.objects[n].hide_render = True
    preview('augusto.png', (0, 0.95, 0), 3.4, azim=math.radians(200))


# ================================================================ LOBO
def build_lobo():
    reset()
    root = joint('lobo', None, (0, 0, 0))
    body = joint('body', root, (0, 0.66, 0))

    def torso(g):
        def fur(p, a, i):
            v = fnoise(p, 9.0, 0.05, 1.0)
            if v.y < -0.05 and -0.32 < v.z < 0.05:
                v.y += 0.035 * (1 - abs(v.z + 0.14) / 0.18)
            return v
        secs = [(-0.54, 0.05, 0.06, 0, 0.04), (-0.48, 0.12, 0.14, 0, 0.03), (-0.38, 0.165, 0.18, 0, 0.01),
                (-0.22, 0.158, 0.172, 0, -0.005), (-0.05, 0.155, 0.17, 0, -0.01), (0.1, 0.175, 0.2, 0, 0.0),
                (0.25, 0.19, 0.225, 0, 0.02), (0.38, 0.165, 0.21, 0, 0.06), (0.5, 0.11, 0.14, 0, 0.12), (0.57, 0.07, 0.08, 0, 0.15)]
        _, fs = g.loft(secs, 'pelaje', seg=18, axis='z', fn=fur)
        g.recolor(fs, lambda c: 'pelaje_claro' if c.y < -0.11 else ('pelaje_osc' if c.y > 0.15 else None))
        spiky = lambda p, a, i: fnoise(p, 15.0, 0.16, 4.0)
        g.loft([(0.1, 0.19, 0.22, 0, 0.02), (0.22, 0.225, 0.265, 0, 0.04), (0.36, 0.21, 0.255, 0, 0.08), (0.48, 0.15, 0.19, 0, 0.12),
                (0.55, 0.09, 0.11, 0, 0.14)], 'pelaje_osc', seg=22, axis='z', fn=spiky)
    part('torso_lobo', body, (0, 0, 0), torso, sharp=0)

    head = joint('head', body, (0, 0.14, 0.52))

    def headg(g):
        g.sphere(0.13, 'pelaje', 16, 12, M4((0, 0.0, 0.08), scale=(1.0, 0.92, 1.12)), deform=lambda p: fnoise(p, 14, 0.04, 2))
        g.loft([(0.14, 0.07, 0.066, 0, -0.025), (0.26, 0.06, 0.054, 0, -0.04), (0.37, 0.048, 0.044, 0, -0.048),
                (0.43, 0.034, 0.032, 0, -0.05), (0.447, 0.0, 0.0, 0, -0.05)], 'pelaje_claro', seg=12, axis='z')
        g.sphere(0.028, 'nariz', 10, 8, M4((0, -0.035, 0.44), scale=(1.15, 0.8, 0.9)))
        g.loft([(0.1, 0.055, 0.028, 0, -0.085), (0.25, 0.045, 0.022, 0, -0.088), (0.37, 0.034, 0.016, 0, -0.08),
                (0.4, 0.0, 0.0, 0, -0.078)], 'pelaje_claro', seg=10, axis='z')
        for s in (1, -1):
            g.loft([(0.0, 0.052, 0.022), (0.15, 0.0, 0.0)], 'pelaje_osc', seg=3, a0=math.pi / 2,
                   M=M4((0.075 * s, 0.085, 0.03), rot=(-0.25, 0, -0.35 * s)))
            g.loft([(0.0, 0.032, 0.008), (0.1, 0.0, 0.0)], 'pelaje_claro', seg=3, a0=math.pi / 2,
                   M=M4((0.075 * s, 0.092, 0.046), rot=(-0.25, 0, -0.35 * s)))
            g.sphere(0.022, 'brillo', 8, 6, M4((0.074 * s, 0.035, 0.2)))
            g.box('pelaje_osc', M4((0.07 * s, 0.068, 0.19), rot=(0.3, 0, 0.35 * s), scale=(0.07, 0.022, 0.05)))
            g.loft([(0.0, 0.008, 0.008), (-0.032, 0.0, 0.0)], 'diente', seg=6, M=M4((0.028 * s, -0.07, 0.36)))
            g.loft([(0.0, 0.05, 0.035), (0.13, 0.0, 0.0)], 'pelaje', seg=6, M=M4((0.1 * s, -0.04, 0.05), rot=(0.4, 0, 1.3 * s)))
    part('cabeza_lobo', head, (0, 0, 0), headg)

    tail = joint('tail', body, (0, 0.12, -0.46))
    part('cola', tail, (0, 0, 0), lambda g: g.tube(
        [(0, 0, 0.03), (0, -0.04, -0.12), (0, -0.14, -0.26), (0, -0.28, -0.34), (0, -0.42, -0.37)],
        [0.05, 0.07, 0.078, 0.058, 0.012], 'pelaje_osc', 10, fn=lambda p, i, a: fnoise(p, 16.0, 0.12, 7.0)), sharp=0)

    for nm, x, z, front in (('legFL', 0.14, 0.32, True), ('legFR', -0.14, 0.32, True),
                            ('legBL', 0.14, -0.34, False), ('legBR', -0.14, -0.34, False)):
        lj = joint(nm, body, (x, -0.12, z))

        def legg(g, front=front):
            if front:
                secs = [(0.12, 0.075, 0.09, 0, 0.0), (-0.05, 0.06, 0.07, 0, 0.01), (-0.22, 0.042, 0.048, 0, 0.0),
                        (-0.44, 0.032, 0.036, 0, 0.005), (-0.5, 0.034, 0.038, 0, 0.012)]
            else:
                secs = [(0.14, 0.085, 0.12, 0, -0.02), (-0.06, 0.068, 0.09, 0, 0.03), (-0.2, 0.045, 0.05, 0, -0.03),
                        (-0.3, 0.036, 0.04, 0, -0.07), (-0.46, 0.032, 0.035, 0, -0.03), (-0.5, 0.033, 0.036, 0, -0.01)]
            _, fs = g.loft(secs, 'pelaje', seg=10, fn=lambda p, a, i: fnoise(p, 12.0, 0.05, 3.0))
            g.recolor(fs, lambda c: 'pelaje_osc' if c.y < -0.3 else None)
            g.sphere(0.043, 'pelaje_osc', 10, 8, M4((0, -0.52, 0.028), scale=(1.0, 0.55, 1.35)))
        part(nm + '_malla', lj, (0, 0, 0), legg)

    bake_ao(0.18, rays=24, ground=-0.66)
    export('lobo.glb')
    preview('lobo.png', (0, 0.55, 0), 2.6, azim=math.radians(50))


# ================================================================ ESPANTAPÁJAROS
def build_espantapajaros():
    reset()
    root = joint('espantapajaros', None, (0, 0, 0))
    rig = joint('rig', root, (0, 0, 0))

    def pole(g):
        g.loft([(0.0, 0.055, 0.055), (0.4, 0.05, 0.052, 0.01, 0.0), (0.9, 0.048, 0.05, 0.0, 0.01), (1.32, 0.045, 0.047, -0.01, 0.0)],
               'madera', seg=8, fn=lambda p, a, i: fnoise(p, 20, 0.06, 5))
        for y in (0.3, 0.345, 0.39):
            g.tube(ellipse(0.058, 0.058, y, 12), 0.011, 'cuerda', 5, closed=True)
    part('poste', rig, (0, 0, 0), pole)

    body = joint('body', rig, (0, 1.25, 0))

    def coat(g):
        def f(p, a, i):
            k = (0.0, 0.2, 0.45, 0.75, 1.0)[i]
            r = 1 + 0.06 * math.sin(a * 7 + 1.1) * k + 0.03 * math.sin(a * 13) * k
            y = p[1]
            if i == 4:
                y -= 0.08 * max(0.0, math.sin(a * 5 + 0.4)) + 0.03 * abs(math.sin(a * 11))
            return (p[0] * r, y, p[2] * r)
        g.loft([(0.68, 0.11, 0.1), (0.6, 0.2, 0.15), (0.35, 0.22, 0.17), (0.05, 0.27, 0.21), (-0.25, 0.37, 0.31)],
               'abrigo', seg=32, cap0=True, cap1=False, fn=f)
        for y, z in ((0.45, 0.17), (0.3, 0.18), (0.15, 0.198)):
            g.sphere(0.022, 'madera', 8, 6, M4((0, y, z), scale=(1, 1, 0.6)))
        g.tube(ellipse(0.285, 0.225, 0.03, 24), 0.022, 'cuerda', 6, closed=True)
        g.sphere(0.03, 'cuerda', 8, 6, M4((0.12, 0.03, 0.21)))
        g.tube([(0.12, 0.02, 0.22), (0.14, -0.08, 0.25), (0.13, -0.18, 0.27)], [0.018, 0.016, 0.012], 'cuerda', 6)
        for k in range(12):
            a = TAU * k / 12 + 0.2
            for j in range(3):
                aa = a + (j - 1) * 0.12
                b = Vector((math.cos(aa) * 0.3, -0.18, math.sin(aa) * 0.25))
                tip = b + Vector((math.cos(aa) * 0.08, -0.18 - 0.05 * ((k + j) % 3), math.sin(aa) * 0.07))
                g.tube([b, tip], [0.016, 0.002], 'paja_suelta', 5)
        for k in range(8):
            a = TAU * k / 8
            b = Vector((math.cos(a) * 0.09, 0.66, math.sin(a) * 0.08))
            g.tube([b, b + Vector((math.cos(a) * 0.08, 0.1, math.sin(a) * 0.07))], [0.014, 0.002], 'paja_suelta', 5)
        g.loft([(-0.74, 0.03, 0.03, 0.55, 0.0), (0.74, 0.03, 0.03, 0.55, 0.0)], 'madera', seg=8, axis='x')
    part('abrigo', body, (0, 0, 0), coat, sharp=0)

    for s, nm in ((1, 'L'), (-1, 'R')):
        arm = joint('arm' + nm, body, (0.16 * s, 0.55, 0))

        def sleeve(g, s=s):
            def f(p, a, i):
                x = p[0] + (s * (-0.05 * max(0.0, math.sin(a * 4 + 0.5)) - 0.015 * math.sin(a * 9)) if i == 3 else 0.0)
                r = 1 + 0.05 * math.sin(a * 5 + i) * (i / 3)
                return (x, p[1] * r, p[2] * r)
            g.loft([(0.0, 0.1, 0.1), (0.2 * s, 0.093, 0.09), (0.42 * s, 0.086, 0.083), (0.58 * s, 0.08, 0.078)], 'abrigo',
                   seg=14, axis='x', cap0=False, cap1=False, fn=f)
            g.tube([(0.56 * s, 0.06 * math.cos(TAU * k / 12), 0.06 * math.sin(TAU * k / 12)) for k in range(12)], 0.014, 'cuerda', 5, closed=True)
            for j in range(8):
                ang = TAU * j / 8
                b = Vector((0.55 * s, math.cos(ang) * 0.035, math.sin(ang) * 0.035))
                tip = Vector((s * (0.78 + 0.05 * (j % 3)), math.cos(ang) * 0.1, math.sin(ang) * 0.1))
                g.tube([b, tip], [0.018, 0.002], 'paja_suelta', 5)
        part('manga' + nm, arm, (0, 0, 0), sleeve, sharp=0)
        if nm == 'R':
            scythe = joint('scythe', arm, (-0.62, 0, 0))

            def scy(g):
                g.loft([(-0.6, 0.026, 0.026), (0.2, 0.027, 0.027, 0.01, 0.0), (0.8, 0.026, 0.026, 0.0, 0.01), (1.1, 0.024, 0.024, -0.01, 0.0)],
                       'madera', seg=8)
                for y in (0.2, 0.6):
                    g.loft([(0.0, 0.014, 0.014, 0.0, y), (0.13, 0.013, 0.013, 0.0, y)], 'madera', seg=6, axis='z')
                for y in (0.99, 1.03, 1.07):
                    g.tube(ellipse(0.03, 0.03, y, 10), 0.008, 'cuerda', 5, closed=True)
                rings = []
                for k in range(15):
                    t = k / 14
                    y = 1.08 - 0.12 * t * t
                    z = 0.02 + 0.62 * t
                    w = 0.1 * (1 - t) ** 0.8 + 0.004
                    th = 0.009 * (1 - 0.6 * t)
                    if k == 14:
                        rings.append([(0.0, y - 0.01, z + 0.02)])
                    else:
                        rings.append([(th / 2, y, z), (-th / 2, y, z), (0.0, y - w, z + 0.03 * w)])
                g.rings(rings, 'metal')
            part('guadana', scythe, (0, 0, 0), scy, sharp=35)

    head = joint('head', body, (0, 0.9, 0))

    def sack(g):
        g.sphere(0.21, 'arpillera', 20, 14, M4((0, 0, 0), scale=(1, 1.08, 0.95)), deform=lambda p: fnoise(p, 8.0, 0.035, 9))
        g.loft([(-0.15, 0.1, 0.1), (-0.2, 0.12, 0.12), (-0.28, 0.17, 0.16)], 'arpillera', seg=24, cap0=False, cap1=False,
               fn=lambda p, a, i: (p[0] * (1 + 0.14 * math.sin(a * 12) * i / 2), p[1], p[2] * (1 + 0.14 * math.sin(a * 12) * i / 2)))
        g.tube(ellipse(0.106, 0.106, -0.175, 16), 0.022, 'cuerda', 6, closed=True)

        def zs(x, y):
            return 0.1995 * math.sqrt(max(0.0, 1 - (x / 0.21) ** 2 - (y / 0.227) ** 2)) + 0.006
        pts = [(x, -0.075 + (0.012 if k % 2 else -0.01), zs(x, -0.075)) for k, x in enumerate(-0.1 + i * 0.025 for i in range(9))]
        g.tube(pts, 0.006, 'hilo', 5)
        for i in range(8):
            x = -0.088 + i * 0.025
            g.tube([(x - 0.004, -0.1, zs(x, -0.1)), (x + 0.004, -0.05, zs(x, -0.05))], 0.0045, 'hilo', 4)
        g.box('arpillera', M4((0.185, 0.06, -0.06), rot=(0.1, 0.35, 0.25), scale=(0.02, 0.1, 0.09)))
        for k in range(7):
            y = 0.02 + k * 0.014
            g.tube([(0.2, y, -0.02), (0.21, y + 0.006, -0.1)], 0.003, 'hilo', 4)
    part('saco', head, (0, 0, 0), sack, sharp=0)

    hatj = joint('sombrero_pivote', head, (0, 0.16, -0.02), rot=(-0.15, 0, 0.18))

    def hatg(g):
        prof = [(0.0, 0.17), (-0.012, 0.3), (-0.025, 0.37), (-0.015, 0.375), (0.0, 0.35), (0.015, 0.21), (0.03, 0.2),
                (0.14, 0.17), (0.26, 0.13), (0.38, 0.08), (0.48, 0.04), (0.52, 0.0)]

        def f(p, a, i):
            x, y, z = p
            if 1 <= i <= 4:
                y += 0.035 * math.sin(a * 3 + 0.5)
            if i >= 7:
                t = (y - 0.14) / 0.38
                x += 0.16 * t * t
                y -= 0.06 * t * t
            return (x, y, z)
        g.loft([(y, r, r) for y, r in prof], 'sombrero', seg=28, cap0=False, fn=f)
        g.loft([(0.02, 0.205, 0.205), (0.075, 0.192, 0.192)], 'cuerda', seg=28, cap0=False, cap1=False)
    part('sombrero', hatj, (0, 0, 0), hatg, sharp=0)

    def thorns(g):
        for k in range(8):
            a = TAU * k / 8 + 0.2
            base = Vector((math.cos(a) * 0.3, 0.02, math.sin(a) * 0.3))
            tip = Vector((math.cos(a) * 0.44, 0.24 + 0.06 * (k % 2), math.sin(a) * 0.44))
            mid = base.lerp(tip, 0.5) + Vector((0, 0.03, 0))
            g.tube([base, mid, tip], [0.02, 0.013, 0.002], 'espina', 5)
            for u in (0.35, 0.65):
                p = base.lerp(tip, u)
                g.tube([p, p + Vector((math.cos(a + 1.2) * 0.05, 0.04, math.sin(a + 1.2) * 0.05))], [0.008, 0.001], 'espina', 4)
    part('espinas', hatj, (0, 0, 0), thorns)

    bake_ao(0.16, rays=24, ground=0.0)
    export('espantapajaros.glb')
    preview('espantapajaros.png', (0, 1.3, 0), 4.6, azim=math.radians(30))


# ================================================================ SANTUARIO
def build_santuario():
    reset()
    root = joint('santuario', None, (0, 0, 0))

    def base(g):
        oc = dict(seg=8, a0=math.pi / 8)
        g.loft([(-0.3, 3.05, 3.05), (0.22, 3.05, 3.05), (0.3, 2.96, 2.96), (0.3, 2.0, 2.0), (0.56, 2.0, 2.0),
                (0.63, 1.92, 1.92), (0.63, 0.0, 0.0)], 'piedra', **oc)
        g.tube(ellipse(2.02, 2.02, 0.32, 8), 0.03, 'piedra_osc', 4, closed=True, M=M4(rot=(0, math.pi / 8, 0)))
        for k, (a, r) in enumerate(((0.4, 2.5), (1.9, 2.6), (3.3, 2.4), (4.6, 2.7), (5.6, 1.6), (2.6, 1.5))):
            y = 0.3 if r > 2.05 else 0.62
            g.ico(1.0, 'musgo', 1, M4((math.cos(a) * r, y, math.sin(a) * r), scale=(0.45 + 0.1 * (k % 3), 0.05, 0.3)),
                  deform=lambda p, k=k: fnoise(p, 2.0, 0.3, k))
    part('base_santuario', root, (0, 0, 0), base, sharp=30)

    hw = lambda y: 0.48 - 0.18 * (y - 0.62) / 3.58

    def chamf(h, y, c=0.05):
        return [(h, y, -h + c), (h, y, h - c), (h - c, y, h), (-h + c, y, h), (-h, y, h - c), (-h, y, -h + c), (-h + c, y, -h), (h - c, y, -h)]

    def mono(g):
        rings = [chamf(hw(y), y) for y in (0.62, 1.3, 2.0, 2.7, 3.4, 4.2)]
        rings += [chamf(0.345, 4.2, 0.04), chamf(0.345, 4.29, 0.04), chamf(0.3, 4.29, 0.04), [(0.0, 4.82, 0.0)]]
        g.rings(rings, 'roca', deform=lambda p: Vector(p) + Vector((noise.noise(Vector(p) * 3.0), 0, noise.noise(Vector(p) * 3.0 + Vector((5, 5, 5))))) * 0.012)
        g.rings([chamf(0.62, 0.6), chamf(0.62, 0.86), chamf(0.56, 0.9)], 'piedra_osc')
        t = math.atan(0.18 / 3.58)
        for s in (1, -1):
            g.box('piedra_osc', M4((0, 2.5, s * hw(2.5)), rot=(-t * s, 0, 0), scale=(0.52, 1.62, 0.016)))
    part('monolito', root, (0, 0, 0), mono, sharp=35)
    t = math.atan(0.18 / 3.58)
    joint('runa_frente', root, (0, 2.5, hw(2.5) + 0.012), rot=(-t, 0, 0))
    joint('runa_atras', root, (0, 2.5, -hw(2.5) - 0.012), rot=(-t, math.pi, 0))

    def menhirs(g):
        for k in range(6):
            a = TAU * k / 6 + 0.3
            r = 3.7 + 0.15 * math.sin(k * 3.1)
            h = 0.65 + 0.35 * ((k * 7) % 5) / 4
            fallen = k in (2, 5)
            if fallen:
                M = M4((math.cos(a) * (r + 0.3), 0.22, math.sin(a) * (r + 0.3)), rot=(0.1, -a, math.pi / 2 - 0.15), scale=(0.3, h, 0.25))
            else:
                M = M4((math.cos(a) * r, h * 0.75, math.sin(a) * r), rot=(0.08 * math.sin(k), -a, 0.1 * math.cos(k * 2)), scale=(0.33, h, 0.27))
            g.ico(1.0, 'roca', 2, M, deform=lambda p, k=k: fnoise(p, 1.4, 0.12, 10 + k))
        for k in range(7):
            a = TAU * k / 7 + 1.0
            r = 2.3 + 1.6 * ((k * 3) % 4) / 3
            g.ico(1.0, 'roca', 1, M4((math.cos(a) * r, 0.05, math.sin(a) * r), rot=(k, k * 2, 0), scale=(0.16, 0.1, 0.13)),
                  deform=lambda p, k=k: fnoise(p, 2.0, 0.25, 20 + k))
    part('menhires', root, (0, 0, 0), menhirs, sharp=35)

    bake_ao(1.2, rays=24, ground=0.0)
    export('santuario.glb')
    preview('santuario.png', (0, 1.8, 0), 12.0, elev=0.28, azim=math.radians(35))


# ================================================================ ÁRBOLES
def build_arboles():
    reset()
    root = joint('arboles', None, (0, 0, 0))
    # los árboles se separan para hornear la oclusión sin que se tapen entre sí
    OFF = {'pino': 0.0, 'roble': 30.0, 'rojo': 60.0, 'palma': 90.0}

    def pino_tronco(g):
        g.loft([(-0.3, 0.34, 0.34), (0.0, 0.3, 0.3), (1.5, 0.21, 0.21), (4.5, 0.12, 0.12), (7.6, 0.04, 0.04)], 'corteza', seg=8,
               fn=lambda p, a, i: fnoise(p, 2.0, 0.12, 30))

    def pino_copa(g):
        for n, (yb, r, h) in enumerate(((1.4, 2.3, 3.2), (2.6, 1.95, 2.8), (3.8, 1.55, 2.4), (5.0, 1.15, 1.9), (6.1, 0.75, 1.6))):
            def f(p, a, i, r=r, n=n):
                x, y, z = p
                if i == 1:
                    k = int(round(a / (TAU / 14)))
                    s = 1.14 if k % 2 else 0.84
                    x, z = x * s, z * s
                    y -= 0.3 if k % 2 else 0.0
                v = fnoise((x, y, z), 0.9, 0.08, 40 + n)
                return v
            g.loft([(yb - 0.2, r * 0.3, r * 0.3), (yb, r, r), (yb + 0.22, r * 0.78, r * 0.78), (yb + h, 0.0, 0.0)],
                   'hojas', seg=14, fn=f, a0=n * 0.4)

    def roble_tronco(g):
        g.loft([(-0.3, 0.46, 0.44), (0.0, 0.36, 0.35), (0.5, 0.29, 0.28), (2.0, 0.24, 0.23), (3.3, 0.17, 0.17)], 'corteza', seg=9,
               fn=lambda p, a, i: fnoise(p, 1.5, 0.12, 31))
        for tip in ((1.2, 4.2, 0.4), (-1.0, 4.0, -0.5), (0.2, 4.6, -1.0), (-0.3, 4.5, 1.0)):
            g.tube([(0, 2.6, 0), (tip[0] * 0.5, 3.4, tip[2] * 0.5), tip], [0.16, 0.11, 0.05], 'corteza', 6)

    def roble_copa(g):
        for k, (c, r) in enumerate((((0.0, 4.7, 0.0), 1.8), ((1.3, 4.3, 0.4), 1.35), ((-1.1, 4.4, -0.5), 1.4),
                                    ((0.3, 5.8, 0.2), 1.25), ((-0.4, 4.2, 1.1), 1.2), ((0.6, 4.6, -1.2), 1.25))):
            g.ico(r, 'hojas', 1, M4(c, rot=(k, k * 2.1, k * 0.7)), deform=lambda p, k=k: fnoise(p, 0.9, 0.18, 50 + k))

    def rojo_tronco(g):
        g.loft([(-0.3, 0.36, 0.34), (0.0, 0.28, 0.27), (0.6, 0.22, 0.22), (2.0, 0.18, 0.17), (2.8, 0.13, 0.13)], 'corteza', seg=9,
               fn=lambda p, a, i: fnoise(p, 1.6, 0.14, 32))
        for tip in ((1.2, 3.4, 0.3), (-1.1, 3.3, -0.4), (0.3, 3.7, -1.1), (-0.4, 3.6, 1.1), (0.1, 3.9, 0.1)):
            g.tube([(0, 2.1, 0), (tip[0] * 0.5, 2.8, tip[2] * 0.5), tip], [0.13, 0.09, 0.04], 'corteza', 6)

    def rojo_copa(g):
        for k, (c, r) in enumerate((((0.0, 3.9, 0.0), 1.45), ((1.3, 3.5, 0.3), 1.1), ((-1.2, 3.5, -0.4), 1.15),
                                    ((0.3, 3.6, -1.2), 1.05), ((-0.4, 3.5, 1.2), 1.05), ((0.2, 4.8, 0.2), 1.05),
                                    ((0.9, 4.4, -0.7), 0.9), ((-0.8, 4.4, 0.7), 0.9))):
            g.ico(r, 'hojas', 2, M4(c, rot=(k, k * 1.7, k * 0.4)), deform=lambda p, k=k: fnoise(p, 1.3, 0.16, 60 + k))

    # palmera de las islas: tronco curvo anillado y penachos de hojas colgantes
    PALM_TOP = Vector((1.35, 7.2, 0.0))

    def palma_tronco(g):
        path = [Vector((0.0, -0.3, 0.0))]
        for k in range(1, 15):
            t = k / 14
            path.append(Vector((1.35 * t ** 2.2, -0.3 + 7.5 * t, 0.0)))
        radii = [0.3 * (1.0 - 0.45 * (k / 14)) * (1.0 + 0.1 * (k % 2)) for k in range(15)]
        g.tube(path, radii, 'corteza', 9, fn=lambda p, i, a: fnoise(p, 2.5, 0.05, 33))
        for k in range(4):
            a = k * 1.7
            g.sphere(0.13, 'corteza', 8, 6, M4(PALM_TOP + Vector((math.cos(a) * 0.2, -0.35, math.sin(a) * 0.2))))

    def palma_copa(g):
        for n in range(13):
            a = TAU * n / 13 + 0.3 * math.sin(n * 2.1)
            L = 3.3 + 0.6 * math.sin(n * 1.7)
            lift = 1.1 - 0.6 * (n % 3) / 2
            d = Vector((math.cos(a), 0.0, math.sin(a)))
            side = Vector((-d.z, 0.0, d.x))
            rings = []
            m = 18
            for k in range(m + 1):
                t = k / m
                c = PALM_TOP + d * (L * t) + Vector((0, lift * math.sin(t * 2.4) - 1.8 * t * t, 0))
                w = (0.1 + 0.85 * math.sin(math.pi * min(1.0, t * 1.1)) ** 0.7) * (0.62 if k % 2 else 1.0)
                h = 0.05 * (1 - t) + 0.01
                rings.append([c - side * w + Vector((0, -0.12 * w, 0)), c + Vector((0, h, 0)), c + side * w + Vector((0, -0.12 * w, 0)),
                              c + Vector((0, -h * 0.5, 0))])
            g.rings(rings, 'hojas', closed=True, cap0=False, cap1=False)
        g.sphere(0.35, 'hojas', 10, 6, M4(PALM_TOP + Vector((0, 0.05, 0)), scale=(1.0, 0.6, 1.0)))

    objs = []
    for name, fn in (('pino_tronco', pino_tronco), ('pino_copa', pino_copa), ('roble_tronco', roble_tronco),
                     ('roble_copa', roble_copa), ('rojo_tronco', rojo_tronco), ('rojo_copa', rojo_copa),
                     ('palma_tronco', palma_tronco), ('palma_copa', palma_copa)):
        objs.append(part(name, root, (OFF[name.split('_')[0]], 0, 0), fn, sharp=0))
    bake_ao(2.2, rays=20, ground=0.0, min_ao=0.35)
    for o in objs:
        o.location.x = 0.0
    export('arboles.glb')
    for o in objs:
        o.location.x = OFF[o.name.split('_')[0]] * 0.19
    preview('arboles.png', (9.0, 4.4, 0), 34.0, elev=0.12, azim=0.0, size=(760, 420))


# ================================================================ ROCAS
def build_rocas():
    reset()
    root = joint('rocas', None, (0, 0, 0))
    objs = []
    for i, seed in enumerate((3.0, 7.0, 11.0)):
        def rock(g, seed=seed):
            def d(p):
                v = Vector(p)
                v *= 1.0 + 0.3 * noise.noise(v * 1.2 + Vector((seed, 0, 0))) + 0.1 * noise.noise(v * 3.1 + Vector((0, seed, 0)))
                v.y *= 0.72
                if v.y < -0.3:
                    v.y = -0.3 + (v.y + 0.3) * 0.25
                return v
            g.ico(1.0, 'roca', 2, deform=d)
        objs.append(part('roca_%d' % (i + 1), root, (i * 4.0, 0, 0), rock, sharp=38))
    bake_ao(0.8, rays=24, ground=-0.36)
    for o in objs:
        o.location.x = 0.0
    export('rocas.glb')
    for i, o in enumerate(objs):
        o.location.x = i * 2.6
    preview('rocas.png', (2.6, 0.1, 0), 7.5, elev=0.3, azim=0.2, size=(560, 360))


# ================================================================ FAUNA
def build_fauna():
    """Delfín, cangrejo, mariposa (alas articuladas) y pez; todos miran a +Z."""
    reset()
    roots = []

    def delfin(g):
        secs = [(-1.02, 0.03, 0.02, 0, 0.02), (-0.84, 0.09, 0.075, 0, 0.02), (-0.5, 0.19, 0.18, 0, 0.0), (-0.12, 0.26, 0.26, 0, 0.0),
                (0.28, 0.25, 0.26, 0, 0.0), (0.6, 0.18, 0.19, 0, -0.02), (0.8, 0.12, 0.12, 0, -0.04), (0.92, 0.07, 0.055, 0, -0.07),
                (1.1, 0.045, 0.034, 0, -0.085), (1.19, 0.0, 0.0, 0, -0.085)]
        _, fs = g.loft(secs, 'delfin', seg=18, axis='z')
        g.recolor(fs, lambda c: 'delfin_vientre' if c.y < -0.07 and c.z > -0.7 else None)
        g.tube([(0, 0.2, 0.12), (0, 0.36, -0.02), (0, 0.5, -0.2)], [0.12, 0.07, 0.008], 'delfin', 8, flat=0.18)
        for sd in (1, -1):
            g.tube([(sd * 0.18, -0.1, 0.45), (sd * 0.36, -0.2, 0.3), (sd * 0.45, -0.26, 0.15)], [0.07, 0.045, 0.008], 'delfin', 8, flat=0.2)
            g.tube([(0, 0.0, -0.95), (sd * 0.22, 0.0, -1.1), (sd * 0.36, 0.0, -1.2)], [0.08, 0.06, 0.01], 'delfin', 8, flat=0.15)
            g.sphere(0.018, 'ojo', 8, 6, M4((sd * 0.13, 0.03, 0.78)))
        g.tube([(-0.05, -0.07, 1.05), (0.0, -0.075, 1.12), (0.05, -0.07, 1.05)], 0.005, 'ojo', 4)

    def cangrejo(g):
        g.sphere(0.13, 'cangrejo', 16, 10, M4((0, 0.08, 0), scale=(1.25, 0.5, 0.95)), deform=lambda p: fnoise(p, 8, 0.03, 5))
        for sd in (1, -1):
            for k in range(4):
                z = 0.07 - k * 0.05
                g.tube([(sd * 0.13, 0.08, z), (sd * 0.24, 0.13, z - 0.01), (sd * 0.3, 0.0, z - 0.03)], [0.018, 0.014, 0.008], 'cangrejo', 5)
            g.tube([(sd * 0.1, 0.08, 0.1), (sd * 0.18, 0.12, 0.2), (sd * 0.14, 0.12, 0.28)], [0.025, 0.022, 0.02], 'cangrejo', 6)
            g.sphere(0.055, 'cangrejo', 10, 8, M4((sd * 0.14, 0.12, 0.31), scale=(0.8, 0.6, 1.2)))
            g.tube([(sd * 0.04, 0.12, 0.1), (sd * 0.05, 0.18, 0.12)], 0.008, 'cangrejo', 4)
            g.sphere(0.016, 'ojo', 6, 5, M4((sd * 0.05, 0.19, 0.12)))

    def pez(g):
        g.loft([(-0.14, 0.0, 0.0), (-0.1, 0.02, 0.012), (0.0, 0.045, 0.025), (0.1, 0.03, 0.02), (0.15, 0.0, 0.0)], 'pez', seg=10, axis='z')
        g.tube([(0, 0, -0.12), (0, 0.05, -0.2)], [0.03, 0.004], 'pez', 5, flat=0.2)
        g.tube([(0, 0, -0.12), (0, -0.05, -0.2)], [0.03, 0.004], 'pez', 5, flat=0.2)

    for i, (name, fn) in enumerate((('delfin', delfin), ('cangrejo', cangrejo), ('pez', pez))):
        r = joint(name, None, (i * 5.0, 0, 0))
        part(name + '_malla', r, (0, 0, 0), fn, sharp=0 if name != 'cangrejo' else 40)
        roots.append(r)
    # mariposa: cuerpo y dos alas que aletean (articulaciones mariposa_alaL / mariposa_alaR)
    mr = joint('mariposa', None, (15.0, 0, 0))
    part('mariposa_cuerpo', mr, (0, 0, 0), lambda g: g.loft([(-0.035, 0.0, 0.0), (-0.02, 0.006, 0.006), (0.02, 0.007, 0.007), (0.03, 0.0, 0.0)],
                                                            'ala_borde', seg=6, axis='z'))
    for sd, nm in ((1, 'L'), (-1, 'R')):
        wj = joint('mariposa_ala' + nm, mr, (0, 0, 0))

        def wing(g, sd=sd):
            pts = [(0, 0, 0.02), (sd * 0.05, 0, 0.055), (sd * 0.075, 0, 0.03), (sd * 0.06, 0, -0.005), (sd * 0.07, 0, -0.035), (sd * 0.035, 0, -0.045), (0, 0, -0.02)]
            g.mesh(pts, [tuple(range(len(pts)))], 'ala')
            g.tube([(sd * 0.012, 0.0005, 0.03), (sd * 0.05, 0.0005, 0.05), (sd * 0.072, 0.0005, 0.03)], 0.003, 'ala_borde', 3, flat=0.3)
        part('mariposa_malla' + nm, wj, (0, 0, 0), wing, sharp=0)
    roots.append(mr)
    bake_ao(0.3, rays=16, ground=None, min_ao=0.55)
    for r in roots:
        r.location = (0, 0, 0)
    export('fauna.glb')
    for i, r in enumerate(roots):
        r.location = (i * 1.3 - 2.0, 0.4 if i != 1 else 0.0, 0)
    preview('fauna.png', (0, 0.3, 0), 6.0, elev=0.35, azim=0.5, size=(560, 360))


# ---------------------------------------------------------------- muestrario
def contact_sheet(names, out='muestrario_modelos.jpg'):
    tiles = []
    for n in names:
        path = os.path.join(PREV, n)
        if not os.path.exists(path):
            continue
        img = bpy.data.images.load(path, check_existing=False)
        w, h = img.size
        a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
        bpy.data.images.remove(img)
        ys = np.linspace(0, h - 1, 300).astype(int)
        xs = np.linspace(0, w - 1, int(300 * w / h)).astype(int)
        tiles.append(a[ys][:, xs])
    if not tiles:
        return
    width = sum(t.shape[1] + 6 for t in tiles)
    sheet = np.full((306, width, 4), 0.08, dtype=np.float32)
    sheet[..., 3] = 1
    x = 3
    for t in tiles:
        sheet[3:303, x:x + t.shape[1]] = t
        x += t.shape[1] + 6
    img = bpy.data.images.new('hoja', width, 306)
    img.pixels[:] = sheet.reshape(-1)
    img.filepath_raw = os.path.join(HERE, out)
    img.file_format = 'JPEG'
    img.save()


def main():
    os.makedirs(OUT, exist_ok=True)
    jobs = {'augusto': build_augusto, 'lobo': build_lobo, 'espantapajaros': build_espantapajaros,
            'santuario': build_santuario, 'arboles': build_arboles, 'rocas': build_rocas, 'fauna': build_fauna}
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    wanted = [a for a in args if a in jobs] or list(jobs)
    for name in wanted:
        print('Modelando', name)
        jobs[name]()
    contact_sheet([n + '.png' for n in jobs])


if __name__ == '__main__':
    main()

"""
Texturas de "Campos Dorados" generadas con Blender (Cycles).

Cada textura es un plano con un material procedural (nodos de Blender) que se
renderiza con una cámara ortográfica y sombreado de emisión pura, de modo que
el color del píxel es exactamente el color del material. Las texturas que se
repiten usan ruido/Voronoi 4D sobre un toro (u,v -> cos/sin) para que no tengan
costuras.

Uso (cualquiera de las dos):
    blender -b --python tools/blender/texturas_campos_dorados.py
    python tools/blender/texturas_campos_dorados.py      # con el módulo `bpy`

Salida: assets/campos-dorados/*.jpg|png  (+ tools/blender/muestrario_texturas.jpg)
Para regenerar solo algunas:  python tools/blender/texturas_campos_dorados.py leaves cape
"""
import math
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, 'assets', 'campos-dorados')
TAU = 2 * math.pi
SAMPLES = 24


def lin(hexstr):
    """#rrggbb (sRGB) -> RGBA lineal para los nodos."""
    h = hexstr.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (c[0], c[1], c[2], 1.0)


# ---------------------------------------------------------------- escena
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = SAMPLES
    sc.cycles.use_adaptive_sampling = False
    sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 0
    sc.cycles.filter_width = 1.0
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    world = bpy.data.worlds.new('W')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (0, 0, 0, 1)
    sc.world = world
    cd = bpy.data.cameras.new('Cam')
    cd.type = 'ORTHO'
    cd.ortho_scale = 2
    cam = bpy.data.objects.new('Cam', cd)
    cam.location = (0, 0, 5)
    sc.collection.objects.link(cam)
    sc.camera = cam
    return sc


def add_mesh(name, verts, faces, mat, z=0.0):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new(name, me)
    ob.location.z = z
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(mat)
    return ob


def plane(mat, hw=1.25, hh=1.25):
    return add_mesh('plano', [(-hw, -hh, 0), (hw, -hh, 0), (hw, hh, 0), (-hw, hh, 0)], [(0, 1, 2, 3)], mat)


def disk(mat, cx, cy, r, z, seg=96):
    v = [(cx, cy, 0)] + [(cx + r * math.cos(a), cy + r * math.sin(a), 0) for a in (TAU * i / seg for i in range(seg))]
    f = [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)]
    return add_mesh('disco', v, f, mat, z)


def ellipse(mat, cx, cy, rx, ry, rot, z, seg=40):
    cr, sr = math.cos(rot), math.sin(rot)
    v = [(cx, cy, 0)]
    for i in range(seg):
        a = TAU * i / seg
        x, y = rx * math.cos(a), ry * math.sin(a)
        v.append((cx + x * cr - y * sr, cy + x * sr + y * cr, 0))
    f = [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)]
    return add_mesh('elipse', v, f, mat, z)


def ring(mat, cx, cy, r0, r1, z, seg=96):
    v, f = [], []
    for i in range(seg):
        a = TAU * i / seg
        v += [(cx + r0 * math.cos(a), cy + r0 * math.sin(a), 0), (cx + r1 * math.cos(a), cy + r1 * math.sin(a), 0)]
    for i in range(seg):
        a, b, c, d = 2 * i, 2 * i + 1, 2 * ((i + 1) % seg) + 1, 2 * ((i + 1) % seg)
        f.append((a, b, c, d))
    return add_mesh('anillo', v, f, mat, z)


def stroke(mat, pts, width, z):
    """Trazo (línea gruesa) como curva con bisel."""
    cu = bpy.data.curves.new('trazo', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = width / 2
    cu.bevel_resolution = 3
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for p, (x, y) in zip(sp.points, pts):
        p.co = (x, y, 0, 1)
    ob = bpy.data.objects.new('trazo', cu)
    ob.location.z = z
    bpy.context.scene.collection.objects.link(ob)
    cu.materials.append(mat)
    return ob


def render(sc, name, w, h, transparent=False):
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = transparent
    st = sc.render.image_settings
    if name.endswith('.jpg'):
        st.file_format, st.color_mode, st.quality = 'JPEG', 'RGB', 90
    else:
        st.file_format, st.color_mode, st.compression = 'PNG', 'RGBA' if transparent else 'RGB', 90
    sc.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)
    print('  ->', name)


# ---------------------------------------------------------------- nodos
class NB:
    """Pequeño constructor de árboles de nodos para materiales de emisión."""

    def __init__(self, name, frame=(-1.0, -1.0, 2.0, 2.0)):
        self.mat = bpy.data.materials.new(name)
        self.mat.use_nodes = True
        self.nt = self.mat.node_tree
        self.nt.nodes.clear()
        self.out = self.nt.nodes.new('ShaderNodeOutputMaterial')
        tc = self.nt.nodes.new('ShaderNodeTexCoord')
        sep = self.nt.nodes.new('ShaderNodeSeparateXYZ')
        self.link(tc.outputs['Object'], sep.inputs[0])
        x0, y0, w, h = frame
        self.x, self.y = sep.outputs[0], sep.outputs[1]
        self.u = self.math('DIVIDE', self.math('SUBTRACT', self.x, x0), w)
        self.v = self.math('DIVIDE', self.math('SUBTRACT', self.y, y0), h)

    def link(self, a, b):
        self.nt.links.new(a, b)

    def _set(self, sock, v):
        if isinstance(v, (int, float)):
            sock.default_value = v
        elif isinstance(v, tuple):
            sock.default_value = v
        elif isinstance(v, str):
            sock.default_value = lin(v)
        else:
            self.link(v, sock)

    def math(self, op, a, b=None, c=None, clamp=False):
        n = self.nt.nodes.new('ShaderNodeMath')
        n.operation, n.use_clamp = op, clamp
        for i, val in enumerate((a, b, c)):
            if val is not None:
                self._set(n.inputs[i], val)
        return n.outputs[0]

    def add(self, a, b): return self.math('ADD', a, b)
    def mul(self, a, b): return self.math('MULTIPLY', a, b)
    def sub(self, a, b): return self.math('SUBTRACT', a, b)

    def smooth(self, e0, e1, x):
        n = self.nt.nodes.new('ShaderNodeMapRange')
        n.interpolation_type = 'SMOOTHSTEP'
        self._set(n.inputs['Value'], x)
        n.inputs['From Min'].default_value, n.inputs['From Max'].default_value = e0, e1
        return n.outputs['Result']

    def torus(self, a=(1, 0), b=(0, 1), ra=1.0, rb=1.0, seed=0.0):
        """Coordenadas 4D periódicas: ángulos 2π(a·uv) y 2π(b·uv) con coeficientes enteros."""
        def ang(k):
            s = self.add(self.mul(self.u, k[0]), self.mul(self.v, k[1]))
            return self.mul(s, TAU)
        aa, bb = ang(a), ang(b)
        comb = self.nt.nodes.new('ShaderNodeCombineXYZ')
        self.link(self.add(self.mul(self.math('COSINE', aa), ra), seed * 1.7), comb.inputs[0])
        self.link(self.add(self.mul(self.math('SINE', aa), ra), seed * 2.3), comb.inputs[1])
        self.link(self.add(self.mul(self.math('COSINE', bb), rb), seed * 0.9), comb.inputs[2])
        w = self.add(self.mul(self.math('SINE', bb), rb), seed * 1.3)
        return comb.outputs[0], w

    def noise(self, co, scale, detail=4.0, rough=0.55, distortion=0.0, lac=2.0):
        n = self.nt.nodes.new('ShaderNodeTexNoise')
        n.noise_dimensions = '4D'
        self.link(co[0], n.inputs['Vector'])
        self.link(co[1], n.inputs['W'])
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = rough
        n.inputs['Lacunarity'].default_value = lac
        n.inputs['Distortion'].default_value = distortion
        return n.outputs['Fac']

    def voronoi(self, co, scale, feature='F1', rand=1.0, out='Distance'):
        n = self.nt.nodes.new('ShaderNodeTexVoronoi')
        n.voronoi_dimensions = '4D'
        n.feature = feature
        self.link(co[0], n.inputs['Vector'])
        self.link(co[1], n.inputs['W'])
        n.inputs['Scale'].default_value = scale
        n.inputs['Randomness'].default_value = rand
        return n.outputs[out]

    def ramp(self, fac, stops, interp='LINEAR'):
        n = self.nt.nodes.new('ShaderNodeValToRGB')
        cr = n.color_ramp
        cr.interpolation = interp
        els = cr.elements
        els[0].position, els[0].color = stops[0][0], lin(stops[0][1])
        els[1].position, els[1].color = stops[-1][0], lin(stops[-1][1])
        for p, c in stops[1:-1]:
            e = els.new(p)
            e.color = lin(c)
        self._set(n.inputs['Fac'], fac)
        return n.outputs['Color']

    def mix(self, fac, a, b, blend='MIX'):
        n = self.nt.nodes.new('ShaderNodeMix')
        n.data_type, n.blend_type, n.clamp_result = 'RGBA', blend, True
        self._set(n.inputs[0], fac)
        self._set(n.inputs[6], a)
        self._set(n.inputs[7], b)
        return n.outputs[2]

    def scale(self, col, s):
        n = self.nt.nodes.new('ShaderNodeVectorMath')
        n.operation = 'SCALE'
        self._set(n.inputs[0], col)
        self._set(n.inputs[3], s)
        return n.outputs[0]

    def emit(self, col, alpha=None):
        em = self.nt.nodes.new('ShaderNodeEmission')
        self._set(em.inputs['Color'], col)
        em.inputs['Strength'].default_value = 1.0
        if alpha is None:
            self.link(em.outputs[0], self.out.inputs['Surface'])
        else:
            tr = self.nt.nodes.new('ShaderNodeBsdfTransparent')
            mx = self.nt.nodes.new('ShaderNodeMixShader')
            self._set(mx.inputs[0], alpha)
            self.link(tr.outputs[0], mx.inputs[1])
            self.link(em.outputs[0], mx.inputs[2])
            self.link(mx.outputs[0], self.out.inputs['Surface'])
        return self.mat


def flat(hexstr, name='plano'):
    b = NB(name)
    return b.emit(hexstr)


# ---------------------------------------------------------------- texturas
def tex_field():
    """Pradera dorada vista desde lejos: hebras de trigo en varias direcciones."""
    sc = reset_scene()
    b = NB('field')
    s1 = b.noise(b.torus((1, 1), (1, -1), 0.35, 6.0, 1), 3.0, 8, 0.6)
    s2 = b.noise(b.torus((1, 0), (0, 1), 0.3, 5.0, 2), 3.2, 8, 0.6)
    s3 = b.noise(b.torus((2, 1), (1, -2), 0.25, 4.0, 3), 2.6, 6, 0.6)
    strands = b.math('MAXIMUM', b.math('MAXIMUM', s1, b.mul(s2, 0.97)), b.mul(s3, 0.95))
    col = b.ramp(strands, [(0.36, '#4f3a1a'), (0.47, '#8c6a2e'), (0.56, '#c09343'), (0.64, '#dcb869'), (0.74, '#f0dca4')])
    big = b.noise(b.torus((1, 0), (0, 1), 0.7, 0.7, 7), 1.6, 3, 0.5)
    tint = b.ramp(big, [(0.3, '#c9b7a0'), (0.5, '#ffffff'), (0.72, '#fff2d6')])
    col = b.mix(1.0, col, tint, 'MULTIPLY')
    heads = b.voronoi(b.torus((1, 0), (0, 1), 1, 1, 5), 22, 'F1')
    col = b.mix(b.smooth(0.12, 0.05, heads), col, '#f6e7b8')
    b.emit(col)
    plane(b.mat)
    render(sc, 'field.jpg', 1024, 1024)


def tex_ground():
    """Tierra seca con piedrecillas y paja: suelo bajo el pasto y senderos."""
    sc = reset_scene()
    b = NB('ground')
    co = b.torus(seed=11)
    base = b.noise(co, 4.0, 8, 0.6)
    col = b.ramp(base, [(0.3, '#3e2c18'), (0.5, '#6a4f2e'), (0.68, '#8d7048')])
    cracks = b.voronoi(b.torus(seed=12), 5, 'DISTANCE_TO_EDGE')
    col = b.mix(b.mul(b.smooth(0.03, 0.0, cracks), 0.6), col, '#2a1d10')
    straw = b.noise(b.torus((1, 1), (1, -1), 0.4, 7, 13), 3.0, 6, 0.6)
    col = b.mix(b.smooth(0.62, 0.7, straw), col, '#b89354')
    peb = b.voronoi(b.torus(seed=14), 16, 'F1')
    pc = b.ramp(b.voronoi(b.torus(seed=14), 16, 'F1', out='Color'), [(0.0, '#7d7468'), (1.0, '#b3a894')])
    col = b.mix(b.smooth(0.2, 0.14, peb), col, pc)
    col = b.mix(b.mul(b.smooth(0.2, 0.26, peb), b.smooth(0.3, 0.2, peb)), col, '#2f2416')
    b.emit(col)
    plane(b.mat)
    render(sc, 'ground.jpg', 512, 512)


def tex_forest():
    """Suelo de bosque: musgo y hojarasca."""
    sc = reset_scene()
    b = NB('forest')
    moss = b.noise(b.torus(seed=21), 5.0, 8, 0.65)
    col = b.ramp(moss, [(0.32, '#262b14'), (0.5, '#3f4822'), (0.66, '#5d6431')])
    leaves = b.voronoi(b.torus(seed=22), 14, 'F1', out='Color')
    lc = b.ramp(leaves, [(0.0, '#6b5a33'), (0.35, '#7a4a2a'), (0.6, '#4b4020'), (1.0, '#8a6a3a')], 'CONSTANT')
    ld = b.voronoi(b.torus(seed=22), 14, 'F1')
    mask = b.mul(b.smooth(0.34, 0.26, ld), b.smooth(0.45, 0.6, b.noise(b.torus(seed=23), 3, 3)))
    col = b.mix(mask, col, lc)
    b.emit(col)
    plane(b.mat)
    render(sc, 'forest.jpg', 512, 512)


def tex_rock():
    """Roca gris con grietas y líquenes."""
    sc = reset_scene()
    b = NB('rock')
    n = b.noise(b.torus(seed=31), 3.0, 10, 0.62, 0.3)
    col = b.ramp(n, [(0.3, '#57524a'), (0.5, '#827c70'), (0.7, '#a39d90')])
    cr = b.voronoi(b.torus(seed=32), 3.5, 'DISTANCE_TO_EDGE')
    col = b.mix(b.smooth(0.035, 0.0, cr), col, '#2f2c28')
    col = b.mix(b.mul(b.smooth(0.03, 0.07, cr), 0.18), col, '#c9c2b2')
    lich = b.noise(b.torus(seed=33), 6.0, 6, 0.7)
    col = b.mix(b.smooth(0.6, 0.66, lich), col, '#a9a25e')
    lich2 = b.noise(b.torus(seed=34), 9.0, 5, 0.7)
    col = b.mix(b.smooth(0.66, 0.7, lich2), col, '#c28d45')
    b.emit(col)
    plane(b.mat)
    render(sc, 'rock.jpg', 512, 512)


def tex_stone():
    """Sillares irregulares para la base de los santuarios."""
    sc = reset_scene()
    b = NB('stone')
    co = b.torus(seed=41)
    edge = b.voronoi(co, 3.2, 'DISTANCE_TO_EDGE', 0.85)
    cellc = b.voronoi(co, 3.2, 'F1', 0.85, out='Color')
    blk = b.ramp(cellc, [(0.0, '#7a7466'), (0.5, '#958e7e'), (1.0, '#aaa391')])
    det = b.noise(b.torus(seed=42), 8.0, 8, 0.6)
    blk = b.mix(1.0, blk, b.ramp(det, [(0.3, '#b8b8b8'), (0.55, '#ffffff'), (0.8, '#ffffff')]), 'MULTIPLY')
    col = b.mix(b.smooth(0.05, 0.02, edge), blk, '#3a362f')
    col = b.mix(b.mul(b.smooth(0.05, 0.09, edge), b.smooth(0.16, 0.09, edge)), col, '#bdb6a4')
    moss = b.noise(b.torus(seed=43), 4, 6, 0.7)
    col = b.mix(b.mul(b.smooth(0.58, 0.68, moss), b.smooth(0.08, 0.02, edge)), col, '#5d6a32')
    b.emit(col)
    plane(b.mat)
    render(sc, 'stone.jpg', 512, 512)


def tex_bark():
    """Corteza con surcos verticales."""
    sc = reset_scene()
    b = NB('bark')
    ridges = b.voronoi(b.torus((1, 0), (0, 1), 5.0, 0.7, 51), 1.4, 'DISTANCE_TO_EDGE')
    n = b.noise(b.torus((1, 0), (0, 1), 3.0, 0.8, 52), 2.5, 8, 0.6)
    col = b.ramp(n, [(0.35, '#3b2d20'), (0.55, '#5c4a38'), (0.7, '#76634e')])
    col = b.mix(b.smooth(0.06, 0.0, ridges), col, '#1d150e')
    col = b.mix(b.mul(b.smooth(0.12, 0.25, ridges), 0.3), col, '#8b7963')
    b.emit(col)
    plane(b.mat)
    render(sc, 'bark.jpg', 512, 512)


def tex_wood():
    """Madera curtida (postes y mangos)."""
    sc = reset_scene()
    b = NB('wood')
    grain = b.noise(b.torus((1, 0), (0, 1), 6.0, 0.35, 61), 2.2, 6, 0.6, 0.8)
    rings = b.math('SINE', b.mul(grain, 40.0))
    g = b.add(b.mul(rings, 0.5), 0.5)
    col = b.ramp(g, [(0.0, '#4a331f'), (0.5, '#6e5134'), (1.0, '#8d6d4a')])
    wear = b.noise(b.torus(seed=62), 3, 4)
    col = b.mix(b.mul(b.smooth(0.5, 0.75, wear), 0.45), col, '#8e867a')
    knots = b.voronoi(b.torus((1, 0), (0, 1), 2.0, 0.6, 63), 2.0, 'F1')
    col = b.mix(b.smooth(0.08, 0.03, knots), col, '#2e1f12')
    b.emit(col)
    plane(b.mat)
    render(sc, 'wood.jpg', 512, 512)


def tex_straw():
    """Paja trenzada para el sombrero (tejido sobre/bajo)."""
    sc = reset_scene()
    b = NB('straw')
    n_cells = 14.0
    cu, cv = b.mul(b.u, n_cells), b.mul(b.v, n_cells)
    fu, fv = b.math('FRACT', cu), b.math('FRACT', cv)
    checker = b.math('FLOORED_MODULO', b.add(b.math('FLOOR', cu), b.math('FLOOR', cv)), 2.0)
    # perfil redondeado de cada tira: claro al centro, oscuro en los bordes
    prof_h = b.math('SINE', b.mul(fv, math.pi))
    prof_v = b.math('SINE', b.mul(fu, math.pi))
    fib_h = b.noise(b.torus((1, 0), (0, 1), 0.3, 30.0, 71), 1.5, 3, 0.5)
    fib_v = b.noise(b.torus((1, 0), (0, 1), 30.0, 0.3, 72), 1.5, 3, 0.5)
    sh_h = b.mul(prof_h, b.add(0.7, b.mul(fib_h, 0.6)))
    sh_v = b.mul(prof_v, b.add(0.7, b.mul(fib_v, 0.6)))
    shade = b.math('MAXIMUM', b.mul(sh_h, b.sub(1.0, checker)), b.mul(sh_v, checker))
    col = b.ramp(shade, [(0.0, '#4a3312'), (0.35, '#9c7433'), (0.7, '#d4b060'), (1.0, '#f0d78e')])
    tone = b.noise(b.torus(seed=73), 2.0, 3)
    col = b.mix(1.0, col, b.ramp(tone, [(0.3, '#d9cdb8'), (0.6, '#ffffff')]), 'MULTIPLY')
    b.emit(col)
    plane(b.mat)
    render(sc, 'straw.jpg', 512, 512)


def tex_cloth():
    """Tela neutra de sarga (se tiñe con el color del material)."""
    sc = reset_scene()
    b = NB('cloth')
    tw = b.math('SINE', b.mul(b.add(b.u, b.v), TAU * 72))
    thr = b.noise(b.torus((1, 1), (1, -1), 0.4, 40.0, 81), 1.5, 3)
    fuzz = b.noise(b.torus(seed=82), 10, 8, 0.7)
    g = b.add(b.add(0.72, b.mul(tw, 0.08)), b.add(b.mul(thr, 0.12), b.mul(fuzz, 0.14)))
    col = b.ramp(g, [(0.55, '#9a9a9a'), (0.8, '#dedede'), (1.0, '#f4f4f4')])
    wear = b.noise(b.torus(seed=83), 2.5, 4)
    col = b.mix(b.mul(b.smooth(0.55, 0.8, wear), 0.35), col, '#ffffff')
    b.emit(col)
    plane(b.mat)
    render(sc, 'cloth.jpg', 512, 512)


def tex_coat():
    """Abrigo remendado del espantapájaros."""
    sc = reset_scene()
    b = NB('coat')
    co = b.torus(seed=91)
    cells = b.voronoi(co, 2.6, 'F1', 0.9, out='Color')
    edge = b.voronoi(co, 2.6, 'DISTANCE_TO_EDGE', 0.9)
    patch = b.ramp(cells, [(0.0, '#4b4a30'), (0.3, '#5b4430'), (0.55, '#3f4a44'), (0.8, '#6a5a3a'), (1.0, '#4b4a30')], 'CONSTANT')
    tw = b.math('SINE', b.mul(b.sub(b.u, b.v), TAU * 60))
    fuzz = b.noise(b.torus(seed=92), 9, 8, 0.7)
    shade = b.add(0.8, b.add(b.mul(tw, 0.07), b.mul(fuzz, 0.3)))
    col = b.scale(patch, shade)
    # puntadas a lo largo de los bordes de los parches
    dash = b.math('SINE', b.mul(b.add(b.u, b.mul(b.v, 1.0)), TAU * 70))
    stitch = b.mul(b.smooth(0.03, 0.012, edge), b.smooth(0.2, 0.6, dash))
    col = b.mix(b.smooth(0.012, 0.0, edge), col, '#1b1812')
    col = b.mix(stitch, col, '#b59a64')
    dirt = b.noise(b.torus(seed=93), 3, 5)
    col = b.mix(b.mul(b.smooth(0.55, 0.75, dirt), 0.4), col, '#2b2618')
    b.emit(col)
    plane(b.mat)
    render(sc, 'coat.jpg', 512, 512)


def tex_fur():
    """Pelaje de lobo de ceniza (gris claro, se tiñe con el material)."""
    sc = reset_scene()
    b = NB('fur')
    s1 = b.noise(b.torus((1, 0), (0, 1), 18.0, 0.8, 101), 1.2, 6, 0.6, 0.4)
    s2 = b.noise(b.torus((3, 1), (1, 0), 14.0, 0.6, 102), 1.2, 6, 0.6, 0.4)
    g = b.math('MAXIMUM', s1, b.mul(s2, 0.95))
    col = b.ramp(g, [(0.3, '#5e5a55'), (0.5, '#a9a39b'), (0.7, '#e2ddd5'), (0.8, '#f5f2ec')])
    patches = b.noise(b.torus(seed=103), 2.2, 4)
    col = b.mix(b.mul(b.smooth(0.5, 0.7, patches), 0.5), col, '#57524c')
    b.emit(col)
    plane(b.mat)
    render(sc, 'fur.jpg', 512, 512)


def tex_leaves():
    """Follaje en gris (el color de cada árbol lo pone la instancia)."""
    sc = reset_scene()
    b = NB('leaves')
    co = b.torus(seed=111)
    e1 = b.voronoi(co, 6.0, 'DISTANCE_TO_EDGE')
    c1 = b.voronoi(co, 6.0, 'F1', out='Color')
    l1 = b.scale(b.ramp(c1, [(0.0, '#8e8e8e'), (1.0, '#f2f2f2')]), b.add(0.35, b.mul(b.smooth(0.0, 0.16, e1), 0.65)))
    co2 = b.torus(seed=112)
    e2 = b.voronoi(co2, 10.0, 'DISTANCE_TO_EDGE')
    c2 = b.voronoi(co2, 10.0, 'F1', out='Color')
    l2 = b.scale(b.ramp(c2, [(0.0, '#a8a8a8'), (1.0, '#ffffff')]), b.add(0.4, b.mul(b.smooth(0.0, 0.14, e2), 0.6)))
    top = b.smooth(0.45, 0.6, b.noise(b.torus(seed=113), 4.0, 4))
    col = b.mix(b.mul(top, b.smooth(0.02, 0.06, e2)), l1, l2)
    sh = b.noise(b.torus(seed=114), 2.5, 5)
    col = b.mix(1.0, col, b.ramp(sh, [(0.3, '#8c8c8c'), (0.65, '#ffffff')]), 'MULTIPLY')
    b.emit(col)
    plane(b.mat)
    render(sc, 'leaves.jpg', 512, 512)


def tex_burlap():
    """Saco de arpillera con la cara cosida (la cara queda en u≈0.25 de la esfera)."""
    sc = reset_scene()
    b = NB('burlap')
    wu = b.math('SINE', b.mul(b.u, TAU * 44))
    wv = b.math('SINE', b.mul(b.v, TAU * 44))
    jit = b.noise(b.torus(seed=121), 12, 4)
    weave = b.add(b.mul(b.math('ABSOLUTE', b.mul(wu, wv)), 0.6), b.mul(jit, 0.4))
    col = b.ramp(weave, [(0.1, '#5f4f32'), (0.45, '#9a8558'), (0.8, '#c2ad7c')])
    stain = b.noise(b.torus(seed=122), 2.5, 5)
    col = b.mix(b.mul(b.smooth(0.55, 0.75, stain), 0.45), col, '#4b3c24')
    b.emit(col)
    plane(b.mat)
    thread = flat('#241709', 'hilo')
    # boca en zigzag
    pts = [(-0.72 + i * 0.06, -0.31 + (0.022 if i % 2 else -0.018)) for i in range(9)]
    stroke(thread, pts, 0.028, 0.02)
    for i in range(8):
        x = -0.69 + i * 0.058
        stroke(thread, [(x - 0.01, -0.38), (x + 0.012, -0.24)], 0.02, 0.03)
    # costura de la frente
    stroke(thread, [(-0.9 + i * 0.05, 0.42 + 0.03 * math.sin(i * 0.5)) for i in range(17)], 0.018, 0.02)
    for i in range(8):
        x = -0.86 + i * 0.1
        stroke(thread, [(x, 0.38), (x + 0.03, 0.5)], 0.014, 0.03)
    render(sc, 'burlap.jpg', 512, 512)


def tex_cape():
    """Capa de lana carmesí con el emblema del sol y la espiga y borde rasgado."""
    sc = reset_scene()
    fr = (-0.8, -1.0, 1.6, 2.0)
    b = NB('cape', fr)
    tw = b.math('SINE', b.mul(b.add(b.mul(b.u, 0.8), b.v), TAU * 110))
    folds = b.noise(b.torus((1, 0), (0, 1), 3.0, 0.25, 131), 1.4, 3, 0.5)
    fuzz = b.noise(b.torus(seed=132), 14, 8, 0.7)
    base = b.ramp(b.v, [(0.0, '#6c0f19'), (0.35, '#8c1722'), (1.0, '#a8212c')])
    shade = b.add(b.add(0.78, b.mul(tw, 0.05)), b.add(b.mul(folds, 0.3), b.mul(fuzz, 0.12)))
    col = b.scale(base, shade)
    worn = b.noise(b.torus(seed=133), 4, 6)
    col = b.mix(b.mul(b.smooth(0.6, 0.75, worn), 0.35), col, '#c24a47')
    # ribete inferior
    col = b.mix(b.mul(b.smooth(0.125, 0.13, b.v), b.smooth(0.165, 0.16, b.v)), col, '#3a0409')
    col = b.mix(b.mul(b.smooth(0.112, 0.115, b.v), b.smooth(0.127, 0.124, b.v)), col, '#d8b877')
    # borde rasgado
    rip = b.noise((b.nt.nodes.new('ShaderNodeCombineXYZ').outputs[0], b.mul(b.u, 9.0)), 1.0, 3, 0.7)
    edge = b.add(0.035, b.mul(rip, 0.07))
    alpha = b.math('GREATER_THAN', b.v, edge)
    b.emit(col, alpha)
    plane(b.mat, 1.0, 1.25)
    # emblema
    cy, px = 0.425, 0.00625
    cream, dark = flat('#efe6d3', 'crema'), flat('#861621', 'carmesi')
    disk(cream, 0, cy, 44 * px, 0.01)
    ring(dark, 0, cy, 35.5 * px, 38.5 * px, 0.02)
    stalk = [(0.0 + 0.012 * math.sin(t * math.pi), cy - 30 * px + t * 58 * px) for t in (i / 12 for i in range(13))]
    stroke(dark, stalk, 4 * px, 0.03)
    for k in range(4):
        yy = cy + (18 - k * 11) * px
        for s in (-1, 1):
            ellipse(dark, s * 6 * px, yy, 4 * px, 8 * px, -s * 0.6, 0.04)
    ellipse(dark, 0, cy + 30 * px, 3.5 * px, 7 * px, 0, 0.04)
    render(sc, 'cape.png', 512, 640, transparent=True)


def tex_rune():
    """Glifo original de los santuarios (blanco sobre transparente, con halo)."""
    sc = reset_scene()
    white = flat('#ffffff', 'blanco')
    px, stw = 0.0125, 4 * 0.0125
    def P(x, y): return ((x - 32) * px, 1 - y * px)
    circ = [P(32 + 14 * math.cos(a), 28 + 14 * math.sin(a)) for a in (TAU * i / 48 for i in range(49))]
    stroke(white, circ, stw, 0)
    disk(white, *P(32, 28), 4 * px, 0)
    stroke(white, [P(32, 46), P(32, 146)], stw, 0)
    for k in range(3):
        y = 66 + k * 24
        stroke(white, [P(14, y + 10), P(32, y), P(50, y + 10)], stw, 0)
    disk(white, *P(16, 140), 3 * px, 0)
    disk(white, *P(48, 140), 3 * px, 0)
    render(sc, 'rune.png', 128, 320, transparent=True)
    add_glow(os.path.join(OUT, 'rune.png'), radius=6, strength=0.55)


# ---------------------------------------------------------------- posproceso
def load_px(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(img)
    return a


def save_px(path, a, alpha=True):
    h, w = a.shape[:2]
    img = bpy.data.images.new('tmp', w, h, alpha=alpha)
    img.pixels[:] = a.reshape(-1)
    img.filepath_raw = path
    img.file_format = 'JPEG' if path.endswith('.jpg') else 'PNG'
    img.save()
    bpy.data.images.remove(img)


def blur(ch, r):
    k = np.exp(-np.linspace(-2, 2, 2 * r + 1) ** 2)
    k /= k.sum()
    out = np.apply_along_axis(lambda m: np.convolve(m, k, 'same'), 0, ch)
    return np.apply_along_axis(lambda m: np.convolve(m, k, 'same'), 1, out)


def add_glow(path, radius, strength):
    a = load_px(path)
    halo = blur(a[..., 3], radius) * strength
    a[..., 3] = np.maximum(a[..., 3], halo)
    a[..., :3] = 1.0
    save_px(path, a)


def contact_sheet(names):
    tiles = []
    for n in names:
        a = load_px(os.path.join(OUT, n))
        h, w = a.shape[:2]
        # reducir a 192 px de alto por muestreo simple
        ys = np.linspace(0, h - 1, 192).astype(int)
        xs = np.linspace(0, w - 1, max(1, int(192 * w / h))).astype(int)
        t = a[ys][:, xs]
        t[..., :3] = t[..., :3] * t[..., 3:4] + 0.15 * (1 - t[..., 3:4])
        t[..., 3] = 1
        tiles.append(t)
    width = sum(t.shape[1] + 8 for t in tiles)
    sheet = np.full((200, width, 4), 0.1, dtype=np.float32)
    sheet[..., 3] = 1
    x = 4
    for t in tiles:
        sheet[4:196, x:x + t.shape[1]] = t
        x += t.shape[1] + 8
    save_px(os.path.join(HERE, 'muestrario_texturas.jpg'), sheet, alpha=False)


def main():
    os.makedirs(OUT, exist_ok=True)
    jobs = [tex_field, tex_ground, tex_forest, tex_rock, tex_stone, tex_bark, tex_wood, tex_straw,
            tex_cloth, tex_coat, tex_fur, tex_leaves, tex_burlap, tex_cape, tex_rune]
    # permite regenerar solo algunas:  ... texturas_campos_dorados.py -- leaves cape
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    wanted = {a for a in args if not a.startswith('-')}
    for job in jobs:
        if wanted and job.__name__[4:] not in wanted:
            continue
        print(job.__doc__.strip().splitlines()[0])
        job()
    contact_sheet(['field.jpg', 'ground.jpg', 'forest.jpg', 'rock.jpg', 'stone.jpg', 'bark.jpg', 'wood.jpg', 'straw.jpg',
                   'cloth.jpg', 'coat.jpg', 'fur.jpg', 'leaves.jpg', 'burlap.jpg', 'cape.png', 'rune.png'])


if __name__ == '__main__':
    main()

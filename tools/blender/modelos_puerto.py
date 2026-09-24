"""
Modelos del puerto y el pueblo de "Campos Dorados", hechos con Blender.

Usa las mismas herramientas que modelos_campos_dorados.py (bmesh, oclusión
horneada en colores de vértice, exportación glTF sin texturas) y genera:

    pueblo.glb    casas, armería, sastrería, taberna, faro, fuente, puestos,
                  muelle, norays, barriles, cajas, faroles, bancos, bote y cartel
    barcos.glb    bergantín (amarrado y con velas desplegadas) y balandra
    aldeanos.glb  vecinos articulados con las mismas articulaciones que Augusto
                  (armero, sastra, tabernero, capitana, marinero, aldeano, aldeana)

Cada modelo cuelga de un nodo raíz con su nombre; los vecinos llevan el prefijo
en cada articulación (p. ej. "marinero_hips").

Uso:
    python tools/blender/modelos_puerto.py              # con el módulo `bpy`
    blender -b --python tools/blender/modelos_puerto.py
    python tools/blender/modelos_puerto.py barcos       # solo uno
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modelos_campos_dorados as mc  # noqa: E402  (importa bpy)
import bpy  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402

TAU, M4, Geo = mc.TAU, mc.M4, mc.Geo
joint, part, bake_ao, export, preview, bands, ellipse, fnoise = (
    mc.joint, mc.part, mc.bake_ao, mc.export, mc.preview, mc.bands, mc.ellipse, mc.fnoise)


def RY(a):
    return Euler((0, a, 0)).to_matrix().to_4x4()


def T(x, y, z):
    return Matrix.Translation(Vector((x, y, z)))


FACE_RY = {'+z': 0.0, '-z': math.pi, '+x': math.pi / 2, '-x': -math.pi / 2}


def wall_frame(w, d, face, along, y, out=0.0):
    """Marco local sobre una pared: +z sale de la pared, x recorre la pared."""
    if face == '+z':
        pos = (along, y, d / 2 + out)
    elif face == '-z':
        pos = (-along, y, -d / 2 - out)
    elif face == '+x':
        pos = (w / 2 + out, y, -along)
    else:
        pos = (-w / 2 - out, y, along)
    return T(*pos) @ RY(FACE_RY[face])


# ---------------------------------------------------------------- piezas de arquitectura
def window(g, F, ww=0.8, wh=1.1, shutter='contraventana', flowers=False):
    g.box('vidrio', F @ M4((0, 0, 0.0), scale=(ww, wh, 0.06)))
    for cx, cy, sx, sy in ((0, wh / 2 + 0.04, ww + 0.16, 0.08), (0, -wh / 2 - 0.04, ww + 0.16, 0.08),
                           (ww / 2 + 0.04, 0, 0.08, wh), (-ww / 2 - 0.04, 0, 0.08, wh), (0, 0, 0.04, wh), (0, 0, ww, 0.04)):
        g.box('viga', F @ M4((cx, cy, 0.05), scale=(sx, sy, 0.07)))
    g.box('piedra', F @ M4((0, -wh / 2 - 0.12, 0.1), scale=(ww + 0.3, 0.08, 0.22)))
    if shutter:
        for sd in (1, -1):
            g.box(shutter, F @ M4((sd * (ww * 0.75 + 0.12), 0, 0.14), rot=(0, sd * 0.4, 0), scale=(ww / 2, wh + 0.04, 0.05)))
    if flowers:
        g.box('madera', F @ M4((0, -wh / 2 - 0.24, 0.22), scale=(ww + 0.1, 0.18, 0.22)))
        for k in range(5):
            g.ico(0.075, 'flor' if k % 2 == 0 else 'hojas', 1, F @ M4((-ww / 2 + 0.1 + k * (ww - 0.2) / 4, -wh / 2 - 0.1, 0.24)))


def door(g, F, dw=1.1, dh=2.15, step=True):
    g.box('puerta', F @ M4((0, dh / 2, 0.02), scale=(dw, dh, 0.08)))
    for k in range(3):
        g.box('viga', F @ M4((0, 0.45 + k * 0.65, 0.07), scale=(dw - 0.12, 0.06, 0.03)))
    g.box('viga', F @ M4((0, dh + 0.07, 0.05), scale=(dw + 0.24, 0.14, 0.12)))
    for sd in (1, -1):
        g.box('viga', F @ M4((sd * (dw / 2 + 0.06), dh / 2, 0.05), scale=(0.12, dh, 0.12)))
    g.sphere(0.04, 'hierro', 8, 6, F @ M4((dw * 0.33, dh * 0.48, 0.1)))
    if step:
        g.box('piedra', F @ M4((0, 0.06, 0.3), scale=(dw + 0.4, 0.12, 0.5)))


def house_body(g, w, d, hw, base=0.6):
    g.box('piedra', M4((0, base / 2, 0), scale=(w + 0.16, base, d + 0.16)))
    g.box('yeso', M4((0, hw / 2, 0), scale=(w, hw, d)))


def gable_roof(g, w, d, y0, h, over=0.4, axis='x', rows=7, B=None):
    B = B if B is not None else Matrix()
    if axis == 'z':
        B = B @ RY(math.pi / 2)
        w, d = d, w
    half_in = d / 2
    tan = h / half_in
    ang = math.atan(tan)
    half = half_in + over
    L = w + 2 * over
    slab = half / math.cos(ang)
    yr = y0 + h
    for sd in (1, -1):
        g.box('teja', B @ M4((0, yr - (half / 2) * tan, sd * half / 2), rot=(sd * ang, 0, 0), scale=(L, 0.12, slab)))
        for k in range(rows):
            f = (k + 0.7) / rows
            g.box('teja', B @ M4((0, yr - half * f * tan + 0.075, sd * half * f), rot=(sd * ang, 0, 0), scale=(L, 0.06, 0.1)))
    for sx in (1, -1):
        x = sx * w / 2
        g.mesh([(x, y0, -half_in), (x, y0, half_in), (x, yr, 0)], [(0, 1, 2)], 'yeso', M=B)
    g.box('viga', B @ M4((0, yr + 0.03, 0), scale=(L + 0.1, 0.2, 0.22)))


def timber(g, F, width, y0, y1, posts=4):
    g.box('viga', F @ M4((0, y0, 0.03), scale=(width, 0.14, 0.06)))
    g.box('viga', F @ M4((0, y1, 0.03), scale=(width, 0.14, 0.06)))
    for k in range(posts):
        x = -width / 2 + 0.07 + k * (width - 0.14) / (posts - 1)
        g.box('viga', F @ M4((x, (y0 + y1) / 2, 0.03), scale=(0.14, y1 - y0, 0.06)))


def chimney(g, x, z, y0, h):
    g.box('piedra', M4((x, y0 + h / 2, z), scale=(0.7, h, 0.7)))
    g.box('piedra', M4((x, y0 + h + 0.06, z), scale=(0.9, 0.12, 0.9)))


def barrel(g, M, h=0.95, r=0.34, m='madera'):
    g.loft([(0.0, r * 0.84, r * 0.84), (h * 0.5, r, r), (h, r * 0.84, r * 0.84)], m, seg=14, M=M)
    for y in (0.12, 0.5, 0.88):
        rr = r * (0.87 + 0.13 * math.sin(math.pi * y))
        g.tube(ellipse(rr + 0.012, rr + 0.012, y * h, 16), 0.018, 'hierro', 4, closed=True, M=M)


def crate(g, M, s=0.8):
    g.box('madera', M @ M4((0, s / 2, 0), scale=(s * 0.96, s * 0.96, s * 0.96)))
    e = s * 0.08
    for a in (-1, 1):
        for b in (-1, 1):
            g.box('viga', M @ M4((a * (s / 2 - e / 2), s / 2, b * (s / 2 - e / 2)), scale=(e, s, e)))
            g.box('viga', M @ M4((a * (s / 2 - e / 2), s / 2 + b * (s / 2 - e / 2), 0), scale=(e, e, s)))
            g.box('viga', M @ M4((0, s / 2 + a * (s / 2 - e / 2), b * (s / 2 - e / 2)), scale=(s, e, e)))


def hanging_sign(g, x, y, z, icon):
    """Letrero colgante perpendicular a la fachada (+z), con un icono en relieve en ambas caras."""
    g.box('hierro', M4((x, y + 0.55, z + 0.45), scale=(0.06, 0.06, 0.95)))
    g.box('hierro', M4((x, y + 0.3, z + 0.1), rot=(0.7, 0, 0), scale=(0.05, 0.05, 0.6)))
    for dz in (0.2, 0.75):
        g.box('hierro', M4((x, y + 0.4, z + dz), scale=(0.02, 0.28, 0.02)))
    g.box('tablas', M4((x, y, z + 0.48), scale=(0.07, 0.62, 0.95)))
    g.box('viga', M4((x, y, z + 0.48), scale=(0.075, 0.7, 1.03)), deform=None)
    for sx in (1, -1):
        icon(g, T(x + sx * 0.05, y, z + 0.48) @ RY(sx * math.pi / 2))


def icon_swords(g, F):
    for a in (0.75, -0.75):
        g.box('acero', F @ M4((0, 0, 0), rot=(0, 0, a), scale=(0.05, 0.55, 0.02)))
        g.box('oro', F @ M4((0, 0, 0), rot=(0, 0, a), scale=(0.2, 0.035, 0.03)) @ M4((0, -4.5, 0)))
    g.box('oro', F @ M4((0, -0.05, 0.01), scale=(0.12, 0.12, 0.02)))


def icon_hat(g, F):
    g.loft([(0.0, 0.26, 0.1), (0.02, 0.26, 0.1), (0.03, 0.12, 0.08), (0.18, 0.1, 0.07), (0.2, 0.0, 0.0)], 'tela_azul', seg=16,
           M=F @ M4((0, -0.1, 0.0), rot=(math.pi / 2, 0, 0), scale=(1, 1, 1)) @ M4(rot=(-math.pi / 2, 0, 0)))
    g.loft([(0.0, 0.006, 0.006), (0.5, 0.004, 0.004)], 'acero', seg=6, M=F @ M4((0.12, -0.25, 0.02), rot=(0, 0, -0.5)))
    g.tube([(0.2, -0.05, 0.03), (0.28, 0.05, 0.03), (0.2, 0.15, 0.03), (0.1, 0.12, 0.03)], 0.008, 'rojo', 5, M=F)


def icon_mug(g, F):
    g.loft([(-0.18, 0.13, 0.13), (0.18, 0.13, 0.13)], 'madera', seg=14, M=F)
    for y in (-0.12, 0.12):
        g.tube(ellipse(0.135, 0.135, y, 14), 0.012, 'hierro', 4, closed=True, M=F)
    g.tube([(0.13, 0.1, 0), (0.24, 0.08, 0), (0.25, -0.05, 0), (0.13, -0.08, 0)], 0.022, 'madera', 6, M=F)
    g.ico(0.14, 'camisa', 1, F @ M4((0, 0.2, 0), scale=(1.0, 0.45, 1.0)))


# ---------------------------------------------------------------- edificios
def casa_a(g):
    w, d, hw = 6.0, 5.0, 5.4
    house_body(g, w, d, hw)
    gable_roof(g, w, d, hw, 2.4, 0.45, 'x')
    F = lambda face, a, y: wall_frame(w, d, face, a, y, 0.02)
    door(g, F('+z', 0.6, 0.0))
    for a in (-1.8, 2.2):
        window(g, F('+z', a, 1.6))
    for a in (-1.9, 0.25, 2.2):
        window(g, F('+z', a, 4.0), flowers=True)
    for a in (-1.5, 1.5):
        window(g, F('-z', a, 1.6))
        window(g, F('-z', a, 4.0))
    for face in ('+x', '-x'):
        window(g, F(face, 0, 1.6), ww=0.7)
        window(g, F(face, 0, 4.0), ww=0.7)
    timber(g, wall_frame(w, d, '+z', 0, 0, 0.0), w, 2.85, hw - 0.08, 4)
    timber(g, wall_frame(w, d, '-z', 0, 0, 0.0), w, 2.85, hw - 0.08, 4)
    chimney(g, -1.8, -1.2, 6.0, 2.2)


def casa_b(g):
    w, d, hw = 7.0, 5.0, 3.2
    house_body(g, w, d, hw)
    gable_roof(g, w, d, hw, 2.2, 0.5, 'x')
    F = lambda face, a, y: wall_frame(w, d, face, a, y, 0.02)
    door(g, F('+z', -0.5, 0.0))
    for a in (-2.5, 1.7):
        window(g, F('+z', a, 1.6), ww=0.9, flowers=True)
    for a in (-2.0, 0.0, 2.0):
        window(g, F('-z', a, 1.6))
    for face in ('+x', '-x'):
        window(g, F(face, 0, 1.6), ww=0.8)
    chimney(g, 2.3, -1.0, 4.2, 2.0)


def casa_c(g):
    w, d, hw = 4.4, 5.2, 7.6
    house_body(g, w, d, hw)
    gable_roof(g, w, d, hw, 2.6, 0.4, 'z')
    F = lambda face, a, y: wall_frame(w, d, face, a, y, 0.02)
    door(g, F('+z', -0.9, 0.0))
    window(g, F('+z', 1.0, 1.6))
    door(g, F('+z', 0.0, 2.95), step=False)
    g.box('tablas', M4((0, 2.95, d / 2 + 0.55), scale=(2.8, 0.14, 1.1)))
    for k in range(8):
        g.box('hierro', M4((-1.35 + k * 2.7 / 7, 3.45, d / 2 + 1.05), scale=(0.04, 0.9, 0.04)))
    g.box('hierro', M4((0, 3.9, d / 2 + 1.05), scale=(2.8, 0.06, 0.06)))
    for sx in (1, -1):
        g.box('hierro', M4((sx * 1.38, 3.45, d / 2 + 0.55), scale=(0.04, 0.9, 1.0)))
    for a in (-0.9, 0.9):
        window(g, F('+z', a, 5.9), ww=0.7)
        window(g, F('-z', a, 1.6), ww=0.7)
        window(g, F('-z', a, 4.2), ww=0.7)
    for face in ('+x', '-x'):
        for y in (1.6, 4.2, 6.2):
            window(g, F(face, 0, y), ww=0.7)
    chimney(g, 1.2, -1.6, 9.2, 1.6)


def armeria(g):
    w, d, hw = 7.0, 6.0, 4.0
    g.box('tablas', M4((0, 0.05, 0), scale=(w, 0.1, d)))
    g.box('yeso', M4((0, hw / 2, -d / 2 + 0.15), scale=(w, hw, 0.3)))
    for sx in (1, -1):
        g.box('yeso', M4((sx * (w / 2 - 0.15), hw / 2, 0), scale=(0.3, hw, d)))
        g.box('yeso', M4((sx * (w / 2 - 0.75), hw / 2, d / 2 - 0.15), scale=(1.5, hw, 0.3)))
        g.box('piedra', M4((sx * (w / 2 - 0.75), 0.3, d / 2 - 0.1), scale=(1.6, 0.6, 0.45)))
    g.box('yeso', M4((0, 2.9 + (hw - 2.9) / 2, d / 2 - 0.15), scale=(w, hw - 2.9, 0.3)))
    g.box('viga', M4((0, 2.9, d / 2 - 0.02), scale=(w - 2.6, 0.22, 0.26)))
    g.box('tablas', M4((0, hw - 0.05, 0), scale=(w - 0.5, 0.1, d - 0.5)))
    gable_roof(g, w, d, hw, 2.2, 0.4, 'x')
    g.box('tablas', M4((0, 2.62, d / 2 + 0.85), rot=(0.33, 0, 0), scale=(w - 2.2, 0.08, 1.85)))
    for sx in (1, -1):
        g.loft([(0.0, 0.07, 0.07, sx * (w / 2 - 1.25), d / 2 + 1.6), (2.4, 0.07, 0.07, sx * (w / 2 - 1.25), d / 2 + 1.6)], 'viga', seg=6)
    g.box('tablas', M4((0, 0.5, d / 2 - 0.65), scale=(w - 3.2, 1.0, 0.6)))
    g.box('madera', M4((0, 1.04, d / 2 - 0.65), scale=(w - 3.0, 0.08, 0.76)))
    for k, x in enumerate((-0.9, 0.5)):
        g.box('acero', M4((x, 1.1, d / 2 - 0.65), rot=(0, 0.3 * (1 - 2 * k), 0), scale=(0.9, 0.012, 0.05)))
        g.box('cuero', M4((x + 0.55 * math.cos(0.3 * (1 - 2 * k)), 1.11, d / 2 - 0.65 - 0.55 * math.sin(0.3 * (1 - 2 * k))), rot=(0, 0.3 * (1 - 2 * k), 0), scale=(0.2, 0.04, 0.04)))
    g.box('viga', M4((0, 2.25, -d / 2 + 0.36), scale=(w - 1.2, 0.12, 0.12)))
    for k in range(6):
        x = -2.4 + k * 0.96
        g.box('acero', M4((x, 1.45, -d / 2 + 0.37), scale=(0.055, 0.85, 0.015)))
        g.box('oro', M4((x, 1.9, -d / 2 + 0.37), scale=(0.22, 0.04, 0.04)))
        g.box('cuero', M4((x, 2.05, -d / 2 + 0.37), scale=(0.04, 0.24, 0.04)))
    for x in (-1.7, 1.7):
        g.loft([(0.0, 0.36, 0.36, x, 3.15), (0.05, 0.36, 0.36, x, 3.15)], 'madera', seg=18, axis='z', M=T(0, 0, -d / 2 + 0.33))
        g.tube(ellipse(0.36, 0.36, 0, 18), 0.025, 'hierro', 5, closed=True, M=T(x, 3.15, -d / 2 + 0.38) @ M4(rot=(math.pi / 2, 0, 0)))
        g.sphere(0.08, 'hierro', 10, 8, M4((x, 3.15, -d / 2 + 0.4), scale=(1, 1, 0.6)))
    ax = -w / 2 - 0.9
    g.loft([(0.0, 0.3, 0.3, ax, d / 2 - 0.4), (0.5, 0.28, 0.28, ax, d / 2 - 0.4)], 'madera', seg=12)
    g.box('hierro', M4((ax, 0.62, d / 2 - 0.4), scale=(0.5, 0.2, 0.24)))
    g.box('hierro', M4((ax, 0.53, d / 2 - 0.4), scale=(0.28, 0.12, 0.18)))
    g.loft([(0.0, 0.08, 0.08, 0.66, d / 2 - 0.4), (0.32, 0.0, 0.0, 0.66, d / 2 - 0.4)], 'hierro', seg=8, axis='x', M=T(ax + 0.25, 0, 0))
    barrel(g, T(w / 2 + 0.7, 0, d / 2 - 0.3))
    for k in range(4):
        a = k * 1.6
        g.box('acero', M4((w / 2 + 0.7 + 0.12 * math.cos(a), 1.2, d / 2 - 0.3 + 0.12 * math.sin(a)), rot=(0.12 * math.sin(a), 0, 0.12 * math.cos(a)), scale=(0.05, 0.8, 0.012)))
        g.box('cuero', M4((w / 2 + 0.7 + 0.16 * math.cos(a), 1.65, d / 2 - 0.3 + 0.16 * math.sin(a)), scale=(0.04, 0.22, 0.04)))
    hanging_sign(g, w / 2 - 0.25, 3.0, d / 2, icon_swords)


def sastreria(g):
    w, d, hw = 7.0, 6.0, 4.0
    house_body(g, w, d, hw, base=0.4)
    gable_roof(g, w, d, hw, 2.2, 0.4, 'x')
    F = lambda face, a, y: wall_frame(w, d, face, a, y, 0.02)
    window(g, F('+z', -1.3, 1.55), ww=2.6, wh=1.7, shutter=None)
    door(g, F('+z', 2.0, 0.0))
    for a in (-1.5, 1.5):
        window(g, F('-z', a, 1.6))
    g.box('toldo', M4((0, 3.0, d / 2 + 0.75), rot=(0.38, 0, 0), scale=(w + 0.2, 0.05, 1.6)))
    for k in range(14):
        x = -w / 2 + 0.25 + k * (w - 0.5) / 13
        g.loft([(0.0, 0.26, 0.26), (0.03, 0.26, 0.26)], 'toldo', seg=12, axis='z', arc=(math.pi, TAU),
               M=T(x, 2.72, d / 2 + 1.5))
    for sx in (1, -1):
        g.loft([(0.0, 0.05, 0.05, sx * (w / 2 + 0.05), d / 2 + 1.45), (2.7, 0.05, 0.05, sx * (w / 2 + 0.05), d / 2 + 1.45)], 'hierro', seg=6)
    tx, tz = -1.0, d / 2 + 1.7
    g.box('madera', M4((tx, 0.8, tz), scale=(1.8, 0.08, 0.8)))
    for a in (-1, 1):
        for b in (-1, 1):
            g.box('viga', M4((tx + a * 0.8, 0.4, tz + b * 0.33), scale=(0.07, 0.8, 0.07)))
    for k, m in enumerate(('tela_azul', 'tela_verde', 'toldo', 'camisa', 'vestido')):
        g.loft([(-0.35, 0.1, 0.1, 0.94 + 0.13 * (k % 2), tz - 0.15 + 0.12 * (k // 2)),
                (0.35, 0.1, 0.1, 0.94 + 0.13 * (k % 2), tz - 0.15 + 0.12 * (k // 2))], m, seg=10, axis='x', M=T(tx, 0, 0))
    mx, mz = 2.9, d / 2 + 0.9
    g.loft([(0.0, 0.25, 0.25, mx, mz), (0.05, 0.25, 0.25, mx, mz)], 'madera', seg=12)
    g.loft([(0.0, 0.03, 0.03, mx, mz), (1.0, 0.03, 0.03, mx, mz)], 'madera', seg=6)
    g.loft([(0.95, 0.15, 0.11, mx, mz), (1.1, 0.19, 0.13, mx, mz), (1.4, 0.2, 0.14, mx, mz), (1.62, 0.19, 0.13, mx, mz), (1.72, 0.07, 0.07, mx, mz)],
           'tela_azul', seg=14)
    g.sphere(0.1, 'madera', 10, 8, M4((mx, 1.85, mz)))
    for y in (1.5, 1.35, 1.2):
        g.sphere(0.018, 'oro', 6, 5, M4((mx, y, mz + 0.14)))
    hanging_sign(g, -w / 2 + 0.25, 3.0, d / 2, icon_hat)


def taberna(g):
    w, d, hw = 9.0, 7.0, 5.6
    house_body(g, w, d, hw)
    gable_roof(g, w, d, hw, 2.6, 0.45, 'x')
    F = lambda face, a, y: wall_frame(w, d, face, a, y, 0.02)
    door(g, F('+z', 0.0, 0.0), dw=1.7, dh=2.3)
    for a in (-2.9, 2.9):
        window(g, F('+z', a, 1.6), ww=1.1)
    for a in (-2.9, 0.0, 2.9):
        window(g, F('+z', a, 4.1), flowers=True)
        window(g, F('-z', a, 1.6))
        window(g, F('-z', a, 4.1))
    for face in ('+x', '-x'):
        for a in (-1.4, 1.4):
            window(g, F(face, a, 1.6))
            window(g, F(face, a, 4.1))
    timber(g, wall_frame(w, d, '+z', 0, 0, 0.0), w, 2.9, hw - 0.08, 5)
    chimney(g, -3.0, -1.6, 7.0, 2.4)
    chimney(g, 3.2, -1.6, 7.0, 2.2)
    hanging_sign(g, 1.3, 3.1, d / 2, icon_mug)
    for k, (x, z) in enumerate(((-2.2, d / 2 + 0.7), (-2.9, d / 2 + 0.55), (-2.55, d / 2 + 1.3))):
        barrel(g, T(x, 0, z) @ RY(k))
    tx, tz = 3.0, d / 2 + 1.8
    g.box('madera', M4((tx, 0.78, tz), scale=(1.8, 0.08, 0.9)))
    for a in (-1, 1):
        g.box('viga', M4((tx + a * 0.75, 0.39, tz), scale=(0.1, 0.78, 0.7)))
        g.box('madera', M4((tx, 0.45, tz + a * 0.75), scale=(1.8, 0.07, 0.3)))
        g.box('viga', M4((tx, 0.22, tz + a * 0.75), scale=(1.5, 0.44, 0.08)))
    g.loft([(0.0, 0.05, 0.05), (0.2, 0.05, 0.05)], 'madera', seg=10, M=T(tx - 0.3, 0.82, tz))
    g.loft([(0.0, 0.05, 0.05), (0.2, 0.05, 0.05)], 'madera', seg=10, M=T(tx + 0.4, 0.82, tz - 0.1))


def faro(g):
    g.loft([(0.0, 3.1, 3.1), (0.9, 3.1, 3.1), (1.0, 2.9, 2.9), (1.0, 0.0, 0.0)], 'piedra', seg=8, a0=math.pi / 8)
    ys = [1.0, 3.6, 5.2, 7.8, 9.4, 12.0]
    rad = lambda y: 2.4 - 0.8 * (y - 1.0) / 11.0
    for k in range(len(ys) - 1):
        g.loft([(ys[k], rad(ys[k]), rad(ys[k])), (ys[k + 1], rad(ys[k + 1]), rad(ys[k + 1]))], 'faro_rojo' if k % 2 else 'yeso',
               seg=28, cap0=False, cap1=False)
    door(g, T(0, 1.0, rad(1.5) - 0.05), dw=1.0, dh=2.0, step=False)
    for k, y in enumerate((4.2, 6.6, 8.8)):
        a = 1.2 + k * 2.1
        r = rad(y)
        F = T(math.cos(a) * r, y, math.sin(a) * r) @ RY(math.pi / 2 - a)
        g.box('vidrio', F @ M4(scale=(0.45, 0.8, 0.12)))
        g.box('viga', F @ M4((0, 0.45, 0.04), scale=(0.6, 0.1, 0.1)))
    g.loft([(12.0, 2.5, 2.5), (12.25, 2.5, 2.5)], 'piedra', seg=24)
    for k in range(16):
        a = TAU * k / 16
        g.box('hierro', M4((math.cos(a) * 2.35, 12.7, math.sin(a) * 2.35), scale=(0.05, 0.9, 0.05)))
    g.tube(ellipse(2.35, 2.35, 13.15, 32), 0.04, 'hierro', 5, closed=True)
    g.loft([(12.25, 1.3, 1.3), (14.3, 1.3, 1.3)], 'vidrio', seg=8, cap0=False, cap1=False)
    for k in range(8):
        a = TAU * k / 8
        g.box('hierro', M4((math.cos(a) * 1.3, 13.3, math.sin(a) * 1.3), scale=(0.08, 2.1, 0.08)))
    g.sphere(0.55, 'lampara', 16, 10, M4((0, 13.2, 0)))
    g.loft([(14.3, 1.6, 1.6), (14.45, 1.6, 1.6), (15.9, 0.0, 0.0)], 'faro_rojo', seg=24)
    g.sphere(0.2, 'hierro', 10, 8, M4((0, 16.0, 0)))


def fuente(g):
    g.loft([(0.0, 2.7, 2.7), (0.55, 2.7, 2.7), (0.7, 2.8, 2.8), (0.78, 2.8, 2.8), (0.78, 2.45, 2.45), (0.3, 2.4, 2.4), (0.3, 0.0, 0.0)],
           'piedra', seg=24)
    g.loft([(0.55, 2.42, 2.42), (0.56, 0.0, 0.0)], 'agua_fuente', seg=24)
    g.loft([(0.3, 0.4, 0.4), (0.5, 0.32, 0.32), (1.5, 0.26, 0.26), (1.6, 0.35, 0.35), (1.62, 0.95, 0.95), (1.85, 1.0, 1.0),
            (1.85, 0.85, 0.85), (1.7, 0.8, 0.8), (1.7, 0.0, 0.0)], 'piedra', seg=18)
    g.loft([(1.8, 0.84, 0.84), (1.81, 0.0, 0.0)], 'agua_fuente', seg=18)
    g.loft([(1.7, 0.18, 0.18), (2.3, 0.12, 0.12), (2.45, 0.2, 0.2), (2.7, 0.0, 0.0)], 'piedra', seg=12)


def puesto(g, fruits=('fruta_roja', 'fruta_verde', 'fruta_naranja')):
    for a, h in ((-1.4, 2.4), (1.4, 2.4)):
        for b, hh in ((0.8, 2.3), (-0.8, 2.75)):
            g.loft([(0.0, 0.05, 0.05, a, b), (hh, 0.05, 0.05, a, b)], 'madera', seg=6)
    g.box('toldo', M4((0, 2.55, 0), rot=(0.27, 0, 0), scale=(3.2, 0.05, 1.95)))
    g.box('tablas', M4((0, 0.45, 0.2), scale=(3.0, 0.9, 1.0)))
    for k, m in enumerate(fruits):
        cx = -0.95 + k * 0.95
        g.box('madera', M4((cx, 0.98, 0.25), scale=(0.8, 0.16, 0.7)))
        for i in range(9):
            g.ico(0.085, m, 1, M4((cx - 0.25 + (i % 3) * 0.25, 1.1 + 0.03 * (i % 2), 0.05 + (i // 3) * 0.2)))


def muelle(g):
    for k in range(12):
        g.box('tablas', M4((0, -0.05, -2.75 + k * 0.5), scale=(4.0, 0.1, 0.46)))
    for x in (-1.6, 0.0, 1.6):
        g.box('viga', M4((x, -0.25, 0), scale=(0.2, 0.3, 6.0)))
    for x in (-1.9, 1.9):
        for z in (-2.7, 2.7):
            g.loft([(-5.0, 0.16, 0.16, x, z), (0.25, 0.15, 0.15, x, z)], 'viga', seg=8)
        g.box('viga', M4((x + (0.06 if x > 0 else -0.06), 0.05, 0), scale=(0.16, 0.16, 6.0)))


def noray(g):
    g.loft([(0.0, 0.2, 0.2), (0.08, 0.2, 0.2), (0.12, 0.13, 0.13), (0.38, 0.12, 0.12), (0.44, 0.2, 0.2), (0.52, 0.2, 0.2), (0.56, 0.0, 0.0)], 'hierro', seg=12)


def farol(g):
    g.loft([(0.0, 0.14, 0.14), (0.25, 0.12, 0.12), (0.3, 0.06, 0.06), (3.0, 0.05, 0.05), (3.05, 0.0, 0.0)], 'hierro', seg=8)
    g.box('hierro', M4((0.3, 2.95, 0), scale=(0.6, 0.05, 0.05)))
    g.loft([(0.0, 0.16, 0.16), (0.05, 0.16, 0.16)], 'hierro', seg=4, a0=math.pi / 4, M=T(0.55, 2.35, 0))
    g.loft([(0.0, 0.14, 0.14), (0.45, 0.17, 0.17)], 'vidrio', seg=4, a0=math.pi / 4, cap0=False, cap1=False, M=T(0.55, 2.4, 0))
    g.loft([(0.0, 0.2, 0.2), (0.22, 0.0, 0.0)], 'hierro', seg=4, a0=math.pi / 4, M=T(0.55, 2.85, 0))
    g.box('lampara', M4((0.55, 2.6, 0), scale=(0.14, 0.22, 0.14)))


def banco(g):
    for k in range(3):
        g.box('madera', M4((0, 0.46, -0.15 + k * 0.15), scale=(1.8, 0.05, 0.13)))
    for a in (-0.75, 0.75):
        g.box('viga', M4((a, 0.22, 0), scale=(0.08, 0.44, 0.42)))
    g.box('madera', M4((0, 0.85, -0.25), rot=(-0.2, 0, 0), scale=(1.8, 0.3, 0.05)))


def cartel(g):
    g.loft([(0.0, 0.07, 0.07), (2.6, 0.06, 0.06)], 'madera', seg=8)
    for y, a, sd in ((2.25, 0.2, 1), (1.8, -0.4, -1)):
        F = T(0, y, 0) @ RY(a)
        g.box('tablas', F @ M4((sd * 0.55, 0, 0), scale=(1.0, 0.28, 0.05)))
        g.mesh([(sd * 1.05, 0.2, 0), (sd * 1.3, 0.0, 0), (sd * 1.05, -0.2, 0), (sd * 1.05, 0.2, 0.03), (sd * 1.3, 0.0, 0.03), (sd * 1.05, -0.2, 0.03)],
               [(0, 1, 2), (3, 5, 4)], 'tablas', M=F @ T(0, 0, -0.015))


# ---------------------------------------------------------------- cascos de barco
def hull(g, L, B, draft, sheer0, amp, stations=18, mats=('casco', 'casco_color', 'casco_franja', 'casco_fondo'), transom=0.72, deck=True):
    prof = [(1.0, 0.0), (1.03, -0.28), (0.99, -0.52), (0.87, -0.72), (0.62, -0.88), (0.28, -0.97), (0.0, -1.0)]

    def width(t):
        if t <= 0.45:
            return B * (transom + (1 - transom) * math.sin(t / 0.45 * math.pi / 2))
        return B * max(0.02, math.cos((t - 0.45) / 0.55 * math.pi / 2) ** 0.85)

    def sheer(t):
        return sheer0 + amp * ((t - 0.5) * 2) ** 2
    rings = []
    for k in range(stations + 1):
        t = k / stations
        z = -L / 2 + t * L
        w, S = width(t), sheer(t)
        keel = -draft * (1 - 0.35 * max(0.0, (t - 0.75) / 0.25))
        H = S - keel
        half = [(w * xf, S + yf * H) for xf, yf in prof]
        rings.append([(-x, y, z) for x, y in half] + [(x, y, z) for x, y in reversed(half[:-1])])
    _, fs = g.rings(rings, mats[0], closed=False)

    def paint(c):
        t = (c.z + L / 2) / L
        S = sheer(t)
        if c.y < 0.0:
            return mats[3]
        if c.y > S - 0.45:
            return mats[1]
        return None
    g.recolor(fs, paint)
    g.mesh(rings[0], [tuple(range(len(rings[0])))], mats[0])
    # moldura dorada a lo largo del costado (una franja 3D continua)
    for sd in (1, -1):
        wale = []
        for k in range(stations + 1):
            t = min(k / stations, 0.97)
            wale.append((sd * width(t) * 1.005, sheer(t) - 0.62, -L / 2 + t * L))
        g.tube(wale, B * 0.018, mats[2], 5)
    if deck:
        dk = []
        for k in range(stations + 1):
            t = k / stations
            dk.append([(-width(t) * 0.99, sheer(t) - 0.55, -L / 2 + t * L), (width(t) * 0.99, sheer(t) - 0.55, -L / 2 + t * L)])
        g.rings(dk, 'cubierta', closed=False)
    return width, sheer


def sail(g, corners, bulge, nu=6, nv=5, m='vela'):
    """Vela como malla bilineal entre 4 esquinas (sup-izq, sup-der, inf-der, inf-izq) con panza."""
    a, b, c, d = [Vector(p) for p in corners]
    n = (b - a).cross(d - a).normalized()
    rings = []
    for j in range(nv + 1):
        v = j / nv
        row = []
        for i in range(nu + 1):
            u = i / nu
            p = (a.lerp(b, u)).lerp(d.lerp(c, u), v)
            p = p + n * bulge * math.sin(math.pi * u) * math.sin(math.pi * min(1.0, v * 1.1))
            row.append(p)
        rings.append(row)
    g.rings(rings, m, closed=False)


def build_bergantin(name, sails):
    root = joint(name, None, (0, 0, 0))
    L, B = 24.0, 3.3
    masts = ((5.5, 17.0, (7.5, 11.8, 15.0), (10.0, 8.0, 5.5)), (-2.5, 18.5, (8.0, 12.4, 15.8), (11.0, 8.5, 6.0)))

    def body(g):
        width, sheer = hull(g, L, B, 2.0, 2.0, 0.9)
        dy = lambda z: sheer((z + L / 2) / L) - 0.55
        g.box('casco', M4((0, dy(-9.6) + 0.85, -9.4), scale=(5.4, 1.7, 5.0)))
        g.box('cubierta', M4((0, dy(-9.6) + 1.75, -9.4), scale=(5.6, 0.12, 5.2)))
        for k in range(4):
            x = -1.8 + k * 1.2
            g.box('vidrio', M4((x, dy(-9.6) + 1.0, -11.92), scale=(0.7, 0.7, 0.06)))
            g.box('casco_franja', M4((x, dy(-9.6) + 1.0, -11.95), scale=(0.84, 0.84, 0.03)))
        for sx in (1, -1):
            g.loft([(0.0, 0.05, 0.05, sx * 2.6, -11.8), (1.2, 0.05, 0.05, sx * 2.6, -11.8)], 'madera', seg=6, M=T(0, dy(-9.6) + 1.8, 0))
            g.sphere(0.2, 'lampara', 10, 8, M4((sx * 2.6, dy(-9.6) + 3.1, -11.8)))
            for k in range(5):
                g.box('madera', M4((sx * 2.72, dy(-9.6) + 2.1, -11.6 + k * 1.1), scale=(0.08, 0.6, 0.08)))
            g.box('madera', M4((sx * 2.72, dy(-9.6) + 2.42, -9.4), scale=(0.1, 0.08, 5.0)))
        for sx in (1, -1):
            for z in (-4.0, -0.5, 3.0, 6.5):
                w = width((z + L / 2) / L)
                g.box('casco_fondo', M4((sx * (w + 0.02), dy(z) + 0.55, z), scale=(0.1, 0.5, 0.6)))
                g.loft([(0.0, 0.13, 0.13), (0.9, 0.1, 0.1)], 'hierro', seg=10, axis='x', M=T(sx * (w - 0.4), dy(z) + 0.55, z) @ M4(scale=(sx, 1, 1)))
        g.loft([(0.0, 0.2, 0.2), (6.5, 0.08, 0.08)], 'madera', seg=8, axis='z', M=T(0, sheer(1.0) - 0.2, L / 2 - 0.8) @ M4(rot=(-0.4, 0, 0)))
        spiral = [(0.0, sheer(1.0) - 0.9 + 0.35 * math.sin(a) * (1 - a / 12), L / 2 + 0.1 + 0.35 * math.cos(a) * (1 - a / 12)) for a in [k * 0.5 for k in range(20)]]
        g.tube(spiral, [0.1 * (1 - k / 22) for k in range(20)], 'casco_franja', 6)
        for zm, h, ys, ls in masts:
            y0 = dy(zm)
            g.loft([(y0 - 0.3, 0.3, 0.3, 0, zm), (y0 + 2, 0.28, 0.28, 0, zm), (h, 0.12, 0.12, 0, zm), (h + 0.3, 0.0, 0.0, 0, zm)], 'madera', seg=10)
            g.loft([(10.8, 1.1, 1.1, 0, zm), (11.0, 1.1, 1.1, 0, zm)], 'cubierta', seg=12)
            for y, ln in zip(ys, ls):
                g.loft([(-ln / 2, 0.13, 0.13, y, zm), (ln / 2, 0.13, 0.13, y, zm)], 'madera', seg=8, axis='x')
                if not sails:
                    g.loft([(-ln / 2 + 0.3, 0.24, 0.24, y - 0.25, zm + 0.05), (ln / 2 - 0.3, 0.24, 0.24, y - 0.25, zm + 0.05)], 'vela', seg=8, axis='x',
                           fn=lambda p, a, i: (p[0], p[1] + 0.05 * math.sin(p[0] * 3), p[2]))
            for sx in (1, -1):
                for dz in (-1.0, 0.0, 1.0):
                    w = width((zm + dz + L / 2) / L)
                    g.tube([(0.3 * sx, h * 0.72, zm), (sx * w, dy(zm + dz) + 0.6, zm + dz)], 0.025, 'cuerda', 4)
            if sails:
                prev = None
                for y, ln in zip(ys, ls):
                    top = (y - 0.1, ln)
                    if prev is None:
                        bot = (y0 + 1.8, ln * 1.08)
                    else:
                        bot = prev
                    sail(g, [(-top[1] / 2, top[0], zm + 0.3), (top[1] / 2, top[0], zm + 0.3), (bot[1] / 2 * 0.98, bot[0] + 0.2, zm + 0.3),
                             (-bot[1] / 2 * 0.98, bot[0] + 0.2, zm + 0.3)], 0.9)
                    prev = (y, ln)
        g.tube([(0, 17.0, 5.5), (0, sheer(1.0) + 2.3, L / 2 + 5.2)], 0.035, 'cuerda', 4)
        g.tube([(0, 18.5, -2.5), (0, 16.0, 5.5)], 0.035, 'cuerda', 4)
        g.tube([(0, 11.0, -2.5), (0, 3.0, -11.6)], 0.03, 'cuerda', 4)
        if sails:
            sail(g, [(0, 15.5, 5.7), (0, 15.5, 5.7), (0, sheer(1.0) + 2.0, L / 2 + 4.8), (0, sheer(1.0) + 0.6, L / 2 - 0.5)], 0.6, 5, 4)
        g.loft([(0.0, 0.06, 0.06, 0, -11.6), (4.4, 0.04, 0.04, 0, -11.6)], 'madera', seg=6, M=T(0, dy(-9.6) + 1.8, 0))
    part(name + '_casco', root, (0, 0, 0), body, sharp=40)
    joint(name + '_bandera_mayor', root, (0, 18.6, -2.5))
    joint(name + '_bandera_proa', root, (0, 17.1, 5.5))
    return root


def build_balandra(name):
    root = joint(name, None, (0, 0, 0))
    L = 10.0

    def body(g):
        width, sheer = hull(g, L, 1.6, 1.1, 1.1, 0.4, stations=14, mats=('casco', 'casco_verde', 'casco_franja', 'casco_fondo'))
        dy = lambda z: sheer((z + L / 2) / L) - 0.55
        g.box('casco_verde', M4((0, dy(-1.5) + 0.5, -1.6), scale=(1.8, 1.0, 2.6)))
        g.box('cubierta', M4((0, dy(-1.5) + 1.02, -1.6), scale=(1.95, 0.08, 2.75)))
        for x in (-0.5, 0.5):
            g.box('vidrio', M4((x, dy(-1.5) + 0.55, -0.28), scale=(0.4, 0.3, 0.05)))
        zm = 1.0
        g.loft([(dy(zm), 0.14, 0.14, 0, zm), (11.0, 0.07, 0.07, 0, zm), (11.2, 0.0, 0.0, 0, zm)], 'madera', seg=8)
        g.loft([(0.0, 0.07, 0.07, 2.2, 0.0), (5.2, 0.06, 0.06, 2.2, 0.0)], 'madera', seg=6, axis='z', M=T(0, 0, zm) @ M4(scale=(1, 1, -1)))
        g.tube([(0, 8.2, zm - 0.1), (0, 10.2, zm - 4.1)], 0.055, 'madera', 6)
        sail(g, [(0, 8.1, zm - 0.2), (0, 10.1, zm - 4.05), (0, 2.35, zm - 5.0), (0, 2.35, zm - 0.25)], 0.45, 5, 5)
        sail(g, [(0, 9.4, zm + 0.15), (0, 9.4, zm + 0.15), (0, 1.5, L / 2 - 0.1), (0, 1.9, zm + 0.5)], 0.35, 4, 4)
        for sx in (1, -1):
            g.tube([(0.05 * sx, 9.0, zm), (sx * 0.85, dy(zm) + 0.5, zm)], 0.02, 'cuerda', 4)
        g.tube([(0, 10.8, zm), (0, 1.3, L / 2)], 0.02, 'cuerda', 4)
    part(name + '_casco', root, (0, 0, 0), body, sharp=40)
    joint(name + '_bandera', root, (0, 11.2, 1.0))
    return root


def bote(g):
    hull(g, 3.8, 0.75, 0.32, 0.4, 0.16, stations=10, mats=('casco', 'casco_color', 'casco_color', 'casco_fondo'), transom=0.55, deck=False)
    for z in (-1.1, 0.0, 0.9):
        g.box('tablas', M4((0, 0.25, z), scale=(1.3 if z < 0.5 else 0.9, 0.05, 0.25)))
    g.box('tablas', M4((0, -0.02, 0), scale=(0.9, 0.04, 3.0)))
    for sd in (1, -1):
        g.tube([(sd * 0.3, 0.3, -0.9), (sd * 0.45, 0.32, 1.2)], 0.025, 'madera', 5)
        g.box('madera', M4((sd * 0.46, 0.32, 1.35), rot=(0, sd * 0.07, 0), scale=(0.06, 0.02, 0.45)))


# ---------------------------------------------------------------- vecinos
def human(prefix, x_off, o):
    """Vecino articulado (mismas articulaciones y pivotes que Augusto)."""
    skin, shirt, pants = o.get('skin', 'piel'), o.get('shirt', 'camisa'), o.get('pants', 'pantalon')
    hair, belly, bulk = o.get('hair', 'pelo'), o.get('belly', 0.0), o.get('bulk', 1.0)
    P = lambda n: prefix + '_' + n
    root = joint(prefix, None, (x_off, 0, 0))
    hips = joint(P('hips'), root, (0, 0.95, 0))

    def pelvis(g):
        g.loft([(-0.1, 0.15, 0.12), (-0.02, 0.16, 0.13)], pants, seg=18)
        g.loft([(-0.03, 0.16, 0.13), (0.08, 0.158 + belly * 0.05, 0.127 + belly * 0.08), (0.2, 0.166 + belly * 0.08, 0.132 + belly * 0.12),
                (0.33, 0.172, 0.13)], shirt, seg=18)
        g.loft([(-0.05, 0.168 + belly * 0.02, 0.138 + belly * 0.03), (-0.01, 0.168 + belly * 0.02, 0.138 + belly * 0.03)], o.get('belt', 'cuero'), seg=18)
        if o.get('skirt'):
            g.loft([(0.05, 0.18, 0.16), (-0.2, 0.25, 0.22), (-0.55, 0.3, 0.27), (-0.86, 0.33, 0.3)], o['skirt'], seg=24, cap0=False, cap1=False,
                   fn=lambda p, a, i: (p[0] * (1 + 0.05 * math.sin(a * 8) * i / 3), p[1], p[2] * (1 + 0.05 * math.sin(a * 8) * i / 3)))
        if o.get('coat'):
            for a0, a1 in ((36, 86), (94, 144), (216, 266), (274, 324)):
                g.loft([(0.03, 0.172, 0.142), (-0.2, 0.22, 0.19), (-0.55, 0.27, 0.24)], o['coat'], seg=6,
                       arc=(math.radians(a0), math.radians(a1)))
        if o.get('apron'):
            base_r = 0.3 if o.get('skirt') else 0.2
            g.loft([(0.1, 0.19 + belly * 0.08, 0.16 + belly * 0.12), (-0.25, base_r + 0.03, base_r), (-0.62, base_r + 0.06, base_r + 0.03)],
                   o['apron'], seg=8, arc=(math.radians(45), math.radians(135)))
    part(P('pelvis'), hips, (0, 0, 0), pelvis)
    chest = joint(P('chest'), hips, (0, 0.52, 0))

    def torso(g):
        bl = lambda y: 1 + belly * 0.35 * math.exp(-((y + 0.25) / 0.12) ** 2)
        secs = [(-0.28, 0.168, 0.13), (-0.18, 0.185, 0.14), (-0.08, 0.212, 0.148), (-0.02, 0.212, 0.14), (0.03, 0.17, 0.115), (0.07, 0.09, 0.08)]
        g.loft([(y, a * bl(y) * (0.95 + 0.05 * bulk), b * bl(y) * (0.95 + 0.05 * bulk)) for y, a, b in secs], shirt, seg=20)
        if o.get('vest'):
            g.loft([(y, a * bl(y) * 1.06, b * bl(y) * 1.08) for y, a, b in secs[:5]], o['vest'], seg=24, arc=(math.radians(112), math.radians(428)))
        if o.get('coat'):
            g.loft([(y, a * bl(y) * 1.08, b * bl(y) * 1.1) for y, a, b in secs[:5]], o['coat'], seg=24, arc=(math.radians(104), math.radians(436)))
            g.tube(ellipse(0.11, 0.1, 0.05, 16), 0.03, o['coat'], 6, closed=True)
            for y in (-0.06, -0.14, -0.22):
                for sd in (1, -1):
                    g.sphere(0.013, 'oro', 6, 5, M4((0.06 * sd, y, 0.165)))
        if o.get('apron'):
            g.loft([(-0.28, 0.2 + belly * 0.07, 0.16 + belly * 0.06), (-0.05, 0.215, 0.152)], o['apron'], seg=6, arc=(math.radians(55), math.radians(125)))
            for sd in (1, -1):
                g.tube([(0.07 * sd, -0.05, 0.14), (0.1 * sd, 0.04, 0.08), (0.08 * sd, 0.06, -0.05)], 0.01, o['apron'], 4)
        g.tube(ellipse(0.085, 0.072, 0.055, 16), 0.016, shirt, 6, closed=True)
        if o.get('tape'):
            g.tube([(0.07, 0.06, 0.02), (0.1, -0.05, 0.1), (0.1, -0.22, 0.15)], 0.012, 'cinta', 4, flat=0.3)
            g.tube([(-0.07, 0.06, 0.02), (-0.09, -0.05, 0.1), (-0.08, -0.18, 0.15)], 0.012, 'cinta', 4, flat=0.3)
    part(P('torso'), chest, (0, 0, 0), torso)
    neck = joint(P('neck'), chest, (0, 0.06, 0))
    part(P('cuello'), neck, (0, 0, 0), lambda g: g.loft([(-0.02, 0.05, 0.05), (0.1, 0.047, 0.047)], skin, seg=12))

    def head(g):
        def jaw(p):
            x, y, z = p
            dy = y - 0.15
            if dy < 0:
                k = min(1.0, -dy / 0.12)
                x *= 1 - 0.2 * k
                z = z * (1 - 0.08 * k) + (0.012 * k if z > 0 else 0.0)
            return (x, y, z)
        g.sphere(0.12, skin, 20, 14, M4((0, 0.15, 0), scale=(0.93, 1.06, 1.0)), deform=jaw)
        g.ico(1.0, skin, 1, M4((0, 0.135, 0.118), scale=(0.02, 0.028, 0.024)))
        for s in (1, -1):
            g.sphere(1.0, skin, 8, 6, M4((0.112 * s, 0.15, -0.005), scale=(0.014, 0.034, 0.026)))
            g.sphere(0.014, 'ojo', 8, 6, M4((0.04 * s, 0.165, 0.104)))
            g.box(hair, M4((0.043 * s, 0.188, 0.108), rot=(0.2, 0, -0.18 * s), scale=(0.036, 0.01, 0.012)))
        g.box('ojo', M4((0, 0.1, 0.106), scale=(0.028, 0.004, 0.006)))
        style = o.get('hair_style', 'corto')
        if style in ('corto', 'mono', 'coleta', 'largo'):
            g.sphere(0.127, hair, 18, 12, M4((0, 0.172, -0.016), scale=(1.0, 0.85, 1.02)))
        if style == 'calvo':
            g.sphere(0.124, hair, 18, 10, M4((0, 0.14, -0.02), scale=(1.0, 0.55, 1.0)), deform=lambda p: (p[0], min(p[1], 0.17), p[2]))
        if style == 'mono':
            g.sphere(0.06, hair, 12, 8, M4((0, 0.25, -0.1)))
        if style == 'coleta':
            g.tube([(0, 0.17, -0.13), (0, 0.08, -0.17), (0, -0.05, -0.16)], [0.035, 0.03, 0.01], hair, 8)
        if style == 'largo':
            g.loft([(0.2, 0.12, 0.1, 0, -0.03), (0.05, 0.13, 0.1, 0, -0.05), (-0.08, 0.14, 0.08, 0, -0.07)], hair, seg=16,
                   arc=(math.radians(180), math.radians(360)), cap0=False, cap1=False)
        beard = o.get('beard')
        if beard == 'barba':
            g.sphere(0.1, hair, 14, 10, M4((0, 0.08, 0.035), scale=(1.0, 0.9, 0.95)), deform=lambda p: (p[0], min(p[1], 0.11), p[2]))
        if beard in ('barba', 'bigote'):
            g.tube([(-0.05, 0.11, 0.108), (0.0, 0.118, 0.122), (0.05, 0.11, 0.108)], [0.01, 0.016, 0.01], hair, 6)
        if o.get('glasses'):
            for s in (1, -1):
                g.tube(ellipse(0.022, 0.018, 0, 12), 0.003, 'hierro', 4, closed=True, M=T(0.04 * s, 0.165, 0.118) @ M4(rot=(math.pi / 2, 0, 0)))
            g.box('hierro', M4((0, 0.168, 0.12), scale=(0.035, 0.004, 0.004)))
        hat = o.get('hat')
        hm = o.get('hat_mat', 'fieltro')
        if hat == 'gorra':
            g.sphere(0.135, hm, 18, 10, M4((0, 0.21, -0.005), scale=(1.05, 0.55, 1.08)), deform=lambda p: (p[0], max(p[1], 0.2), p[2]))
            g.box(hm, M4((0, 0.205, 0.14), rot=(0.15, 0, 0), scale=(0.2, 0.02, 0.1)))
        if hat == 'panuelo':
            g.sphere(0.133, hm, 18, 10, M4((0, 0.175, -0.012), scale=(1.0, 0.82, 1.04)),
                     deform=lambda p: (p[0], max(p[1], 0.15 - 0.05 * max(0.0, -p[2]) / 0.13), p[2]))
            g.sphere(0.028, hm, 8, 6, M4((0, 0.16, -0.14)))
            g.tube([(0.01, 0.155, -0.145), (0.03, 0.08, -0.17), (0.04, 0.02, -0.16)], [0.022, 0.018, 0.01], hm, 6, flat=0.35)
        if hat == 'tricornio':
            def lift(p, a, i):
                corner = sum(max(0.0, math.cos(1.5 * (a - math.pi / 2 - c))) ** 6 for c in (0.0, TAU / 3, -TAU / 3))
                L = max(0.0, 1.0 - 1.4 * corner) * (i / 3)
                r = math.hypot(p[0], p[2])
                k = (r - 0.07 * L) / max(r, 1e-6)
                return (p[0] * k, p[1] + 0.13 * L, p[2] * k)
            g.loft([(0.0, 0.15, 0.15), (0.004, 0.22, 0.22), (0.008, 0.28, 0.28), (0.014, 0.31, 0.31)], hm, seg=40, cap0=False, cap1=False,
                   fn=lift, M=T(0, 0.24, 0))
            g.sphere(0.15, hm, 16, 10, M4((0, 0.27, 0), scale=(1.0, 0.85, 1.05)))
            edge = [lift((math.cos(TAU * k / 40) * 0.31, 0.016, math.sin(TAU * k / 40) * 0.31), TAU * k / 40, 3) for k in range(40)]
            g.tube([(p[0], p[1] + 0.24, p[2]) for p in edge], 0.009, 'oro', 5, closed=True)
    part(P('cabeza'), neck, (0, 0, 0), head)

    short = o.get('sleeves') == 'cortas'
    for side, nm in ((-1, 'R'), (1, 'L')):
        sh = joint(P('sh' + nm), chest, (0.25 * side, -0.03, 0))
        ub = bulk

        def upper(g, ub=ub):
            g.sphere(0.052 * ub, shirt, 12, 8, M4((0, -0.015, 0)))
            g.loft([(0.0, 0.057 * ub, 0.055 * ub), (-0.12, 0.056 * ub, 0.054 * ub), (-0.2 if short else -0.305, 0.052 * ub, 0.05 * ub)], shirt, seg=12)
            if short:
                g.loft([(-0.19, 0.046 * ub, 0.045 * ub), (-0.305, 0.045 * ub, 0.044 * ub)], skin, seg=12)
            if o.get('coat'):
                g.loft([(0.0, 0.062 * ub, 0.06 * ub), (-0.305, 0.055 * ub, 0.054 * ub)], o['coat'], seg=12)
        part(P('brazo' + nm), sh, (0, 0, 0), upper)
        el = joint(P('el' + nm), sh, (0, -0.3, 0))

        def fore(g, ub=ub):
            g.sphere(0.047 * ub, skin if short else shirt, 10, 8, M4((0, 0.005, 0)))
            g.loft([(0.0, 0.046 * ub, 0.045 * ub), (-0.235, 0.039 * ub, 0.036 * ub)], skin if short else (o.get('coat') or shirt), seg=12)
            if not short:
                g.loft([(-0.2, 0.048 * ub, 0.046 * ub), (-0.245, 0.048 * ub, 0.046 * ub)], shirt, seg=12)
        part(P('antebrazo' + nm), el, (0, 0, 0), fore)
        hand = joint(P('hand' + nm), el, (0, -0.29, 0))
        part(P('mano' + nm), hand, (0, 0, 0), lambda g: g.sphere(0.045, skin, 12, 8, M4((0, 0.0, 0.0), scale=(0.85, 1.12, 0.95))))

    for side, nm in ((1, 'L'), (-1, 'R')):
        hip = joint(P('hip' + nm), hips, (0.1 * side, -0.02, 0))

        def thigh(g):
            g.loft([(0.04, 0.085, 0.082), (-0.12, 0.084, 0.08), (-0.3, 0.072, 0.07), (-0.46, 0.064, 0.062)], pants, seg=12)
            g.sphere(0.063, pants, 12, 8, M4((0, -0.46, 0.005)))
        part(P('muslo' + nm), hip, (0, 0, 0), thigh)
        knee = joint(P('knee' + nm), hip, (0, -0.46, 0))
        barefoot = o.get('feet') == 'descalzo'

        def shin(g, barefoot=barefoot):
            if barefoot:
                g.loft([(0.0, 0.062, 0.06), (-0.18, 0.058, 0.056)], pants, seg=12)
                g.loft([(-0.17, 0.05, 0.05), (-0.42, 0.042, 0.042)], skin, seg=12)
                g.loft([(-0.06, 0.045, 0.028, 0.0, -0.44), (0.12, 0.04, 0.022, 0.0, -0.45), (0.15, 0.0, 0.0, 0.0, -0.452)], skin, seg=10, axis='z')
            else:
                g.loft([(0.0, 0.062, 0.06), (-0.31, 0.052, 0.05)], pants, seg=12)
                g.loft([(-0.28, 0.056, 0.058), (-0.44, 0.06, 0.064)], o.get('shoes', 'cuero'), seg=12)
                g.loft([(-0.075, 0.054, 0.042, 0.0, -0.432), (0.06, 0.056, 0.042, 0.0, -0.438), (0.13, 0.046, 0.032, 0.0, -0.446),
                        (0.165, 0.0, 0.0, 0.0, -0.45)], o.get('shoes', 'cuero'), seg=12, axis='z')
                g.box('vaina', M4((0, -0.462, 0.045), scale=(0.115, 0.018, 0.25)))
        part(P('pierna' + nm), knee, (0, 0, 0), shin)
    return root


NPCS = [
    ('armero', dict(hair='pelo_gris', hair_style='calvo', beard='barba', shirt='camisa', pants='pantalon', apron='cuero', bulk=1.25, belly=0.3,
                    sleeves='cortas', skin='piel_osc')),
    ('sastra', dict(hair='pelo_gris', hair_style='mono', skirt='vestido', shirt='vestido', pants='vestido', glasses=True, tape=True, skin='piel_clara')),
    ('tabernero', dict(hair='pelo', hair_style='calvo', beard='bigote', belly=1.0, shirt='camisa', pants='pantalon', apron='delantal', sleeves='cortas')),
    ('capitana', dict(hair='pelo_rojo', hair_style='coleta', coat='tela_azul', shirt='camisa', pants='pantalon', hat='tricornio', hat_mat='fieltro',
                      skin='piel_clara')),
    ('marinero', dict(hair='pelo', hair_style='corto', beard='barba', shirt='rayas', pants='pantalon_azul', hat='panuelo', hat_mat='rojo_osc',
                      feet='descalzo', sleeves='cortas', skin='piel_osc')),
    ('aldeano', dict(hair='pelo_rubio', hair_style='corto', shirt='camisa', vest='chaleco_v', pants='pantalon', hat='gorra', hat_mat='tela_verde')),
    ('aldeana', dict(hair='pelo_rojo', hair_style='largo', skirt='tela_verde', shirt='camisa', pants='tela_verde', apron='delantal', hat='panuelo',
                     hat_mat='tela_azul')),
]


# ---------------------------------------------------------------- construcción y exportación
PUEBLO = [('casa_a', casa_a), ('casa_b', casa_b), ('casa_c', casa_c), ('armeria', armeria), ('sastreria', sastreria), ('taberna', taberna),
          ('faro', faro), ('fuente', fuente), ('puesto', puesto), ('muelle', muelle), ('noray', noray), ('barril', lambda g: barrel(g, Matrix())),
          ('caja', lambda g: crate(g, Matrix())), ('farol', farol), ('banco', banco), ('cartel', cartel), ('bote', bote)]


def build_pueblo():
    mc.reset()
    roots = []
    for i, (name, fn) in enumerate(PUEBLO):
        root = joint(name, None, (i * 40.0, 8.0 if name == 'muelle' else 0.0, 0))
        part(name + '_malla', root, (0, 0, 0), fn, sharp=40)
        roots.append(root)
    joint('armeria_npc', roots[3], (0, 0, 1.7))
    joint('sastreria_npc', roots[4], (1.3, 0, 4.4))
    joint('taberna_npc', roots[5], (1.8, 0, 4.9))
    bake_ao(0.9, rays=20, ground=0.0, min_ao=0.35)
    for r in roots:
        r.location = (0, 0, 0)
    export('pueblo.glb')
    for i, r in enumerate(roots[:9]):
        r.location = ((i % 3) * 12.0 - 12.0, 0, (i // 3) * -13.0)
    for r in roots[9:]:
        r.location = (0, -50, 0)
    preview('pueblo.png', (0, 3.0, -12.0), 44.0, elev=0.42, azim=0.35, size=(640, 420))


def build_barcos():
    mc.reset()
    a = build_bergantin('bergantin', False)
    b = build_bergantin('bergantin_velas', True)
    c = build_balandra('balandra')
    b.location = (40, 0, 0)
    c.location = (80, 0, 0)
    bake_ao(1.5, rays=20, ground=None, min_ao=0.4)
    for r in (a, b, c):
        r.location = (0, 0, 0)
    export('barcos.glb')
    a.location = (-9, 0, 0)
    b.location = (9, 0, -4)
    c.location = (24, 0, 6)
    preview('barcos.png', (7, 7, 0), 62.0, elev=0.2, azim=1.05, size=(640, 420))


def build_aldeanos():
    mc.reset()
    roots = [human(name, i * 3.0, o) for i, (name, o) in enumerate(NPCS)]
    bake_ao(0.14, rays=24, ground=0.0)
    for r in roots:
        r.location = (0, 0, 0)
    export('aldeanos.glb')
    for i, r in enumerate(roots):
        r.location = (i * 0.9 - 2.7, 0, 0)
    preview('aldeanos.png', (0, 0.95, 0), 7.5, elev=0.15, azim=0.0, size=(640, 360))


def main():
    os.makedirs(mc.OUT, exist_ok=True)
    jobs = {'pueblo': build_pueblo, 'barcos': build_barcos, 'aldeanos': build_aldeanos}
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    wanted = [a for a in args if a in jobs] or list(jobs)
    for name in wanted:
        print('Modelando', name)
        jobs[name]()
    mc.contact_sheet([n + '.png' for n in jobs], out='muestrario_puerto.jpg')


if __name__ == '__main__':
    main()

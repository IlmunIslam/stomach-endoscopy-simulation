"""Stage 1 of the hypopharynx: build PART_W0_Oropharynx (mouth, tongue, palate, uvula, pharynx walls, floor around the
laryngeal slab). Run inside Blender with exec(open(path).read()); builds a NEW object, touches no existing mesh.

Axes (scene): z up (superior), anterior = +y (epiglottis side of PART_W0_Hypopharynx), esophagus axis ~ (13.42, -7.93).
The tube runs from the mouth (y=+10.5, z=72) back along -y, bends down at the oropharynx and ends at z=65.0 around the
slab outline; a floor ring with a hole at the esophagus closes the gap between the tube wall and the slab.
Tongue side of every ring is B = N x T (floor in the mouth, anterior wall in the vertical part).
"""
import bpy, bmesh, numpy as np
from mathutils import Vector

NAME = "PART_W0_Oropharynx"
CX = 13.45
NRING = 72

# centerline (y, z); x is CX everywhere
PTS = np.array([(11.5, 72.0), (8.0, 72.0), (4.0, 72.0), (0.0, 72.0), (-3.0, 71.9), (-5.3, 70.6),
                (-6.5, 68.6), (-6.75, 66.5), (-6.75, 65.0)])


def catmull(P, n=400):
    P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1) ** 0.5)]
    ts = np.linspace(d[1], d[-2], n)
    out = []
    for t in ts:
        i = min(max(np.searchsorted(d, t) - 1, 1), len(P) - 3)
        t0, t1, t2, t3 = d[i - 1], d[i], d[i + 1], d[i + 2]
        a1 = (t1 - t) / (t1 - t0) * P[i - 1] + (t - t0) / (t1 - t0) * P[i]
        a2 = (t2 - t) / (t2 - t1) * P[i] + (t - t1) / (t2 - t1) * P[i + 1]
        a3 = (t3 - t) / (t3 - t2) * P[i + 1] + (t - t2) / (t3 - t2) * P[i + 2]
        b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
        b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
        out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    return np.array(out)


def interp(table, s):
    xs = [a for a, *_ in table]
    return [float(np.interp(s, xs, [row[k] for row in table])) for k in range(1, len(table[0]))]


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def build():
    C = catmull(PTS, 360)
    seg = np.linalg.norm(np.diff(C, axis=0), axis=1)
    S = np.r_[0, np.cumsum(seg)]
    L = S[-1]
    # tangent (y,z)
    T = np.gradient(C, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    rings_s = np.linspace(0, L, 150)
    # (s, ax, b_tongue_side, b_other_side)
    table = [(0, 1.45, 1.25, 1.25), (1.8, 1.5, 1.3, 1.3), (4.2, 2.3, 2.0, 2.1), (11, 2.35, 2.0, 2.1),
             (L - 9.0, 2.4, 2.0, 2.05), (L - 4.5, 2.55, 2.05, 2.05), (L, 2.55, 2.05, 2.05)]
    verts, tongue_w, uv, slab_w = [], [], [], []
    phis = np.linspace(0, 2 * np.pi, NRING, endpoint=False)
    for s in rings_s:
        cy = np.interp(s, S, C[:, 0]); cz = np.interp(s, S, C[:, 1])
        ty = np.interp(s, S, T[:, 0]); tz = np.interp(s, S, T[:, 1])
        t3 = np.array([0.0, ty, tz]); t3 /= np.linalg.norm(t3)
        N = np.array([1.0, 0, 0]); B = np.cross(N, t3)
        ax, bp, bn = interp(table, s)
        tongue_h = 1.05 * smooth((s - 1.8) / 2.6) * (1 - 0.85 * smooth((s - (L - 11.0)) / 6.0))
        palate_h = 1.1 * smooth((s - 9.0) / 3.0) * (1 - smooth((s - (L - 8.0)) / 3.0))
        for phi in phis:
            c, sn = np.cos(phi), np.sin(phi)
            if sn > 0:
                b = bp - tongue_h * (1 - abs(c) ** 2.0) ** 1.2 * sn ** 0.5
                b = b if b > 0.35 else 0.35
                w = smooth((sn + 0.1) / 0.9) * smooth((s - 1.8) / 1.2) * (1 - smooth((s - (L - 12.0)) / 4.0))
            else:
                b = bn - palate_h * (1 - abs(c) ** 2.0) ** 1.0 * (-sn) ** 0.5 - 0.45 * smooth((s - (L - 15.0)) / 2.5) * (1 - smooth((s - (L - 9.0)) / 2.5)) * np.exp(-((abs(c) - 0.72) / 0.13) ** 2) * (-sn)
                w = 0.0
            rad = np.array([ax * c, 0, 0]) + B * (b * sn)
            p = np.array([CX, cy, cz]) + rad
            # slight organic wobble
            p += 0.025 * np.array([np.sin(3 * phi + s), np.sin(2 * phi + 0.7 * s), np.sin(5 * phi - s)])
            verts.append(p); tongue_w.append(w); slab_w.append(float(smooth((s - (L - 9.0)) / 6.0)))
            uv.append((phi / (2 * np.pi), s / L))
    verts = np.array(verts)
    me = bpy.data.meshes.new("MESH_W0_Oropharynx")
    bm = bmesh.new()
    wl = bm.verts.layers.float.new("tongue_w")
    sl = bm.verts.layers.float.new("slab_w")
    uvl = bm.loops.layers.uv.new("UVMap")
    bv = [bm.verts.new(v) for v in verts]
    nr = len(rings_s)
    faces = []
    for i in range(nr - 1):
        for j in range(NRING):
            a = i * NRING + j; b = i * NRING + (j + 1) % NRING
            c = (i + 1) * NRING + (j + 1) % NRING; d = (i + 1) * NRING + j
            faces.append(bm.faces.new((bv[a], bv[b], bv[c], bv[d])))
    # material index: 2 = bite block (s<2.6), else 0
    for k, f in enumerate(faces):
        i = k // NRING
        f.material_index = 2 if rings_s[i] < 1.8 else 0
    # floor: bridge the end ring (z=65.0) to a hole circle at the esophagus
    end_loop = [e for e in bm.edges if all(abs(v.co.z - 65.0) < 1e-4 for v in e.verts) and len(e.link_faces) == 1]
    hole = []
    hc = Vector((13.42, -7.93, 65.0)); r = 0.8
    # hole ring ordered like the end ring (same angle sweep, start phi=0 on the +x side)
    for j in range(NRING):
        a = phis[j]
        hole.append(bm.verts.new(hc + Vector((r * np.cos(a), r * np.sin(a), 0))))
    hole_edges = [bm.edges.new((hole[j], hole[(j + 1) % NRING])) for j in range(NRING)]
    bmesh.ops.bridge_loops(bm, edges=end_loop + hole_edges)
    # uvula
    uvr = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.5)
    uverts = uvr["verts"]
    near = [v for v in verts if abs(v[1] + 3.4) < 0.3 and abs(v[0] - CX) < 0.3 and v[2] > 72.0]
    ceil_z = max(v[2] for v in near)
    bmesh.ops.scale(bm, vec=(0.36, 0.36, 0.62), verts=uverts)
    bmesh.ops.translate(bm, vec=(CX, -3.4, ceil_z - 0.27), verts=uverts)
    bm.normal_update()
    # tongue weight attribute and uv layer
    for v in hole:
        v[sl] = 1.0
    for v in uverts:
        for f in v.link_faces:
            f.material_index = 1
    index_of = {v: i for i, v in enumerate(bv)}
    for i, v in enumerate(bv):
        v[wl] = tongue_w[i]; v[sl] = slab_w[i]
    for f in bm.faces:
        for lp in f.loops:
            v = lp.vert
            if v in index_of:
                lp[uvl].uv = uv[index_of[v]]
            else:
                lp[uvl].uv = (0.5 + 0.3 * v.co.x % 1.0, 0.5 + 0.3 * v.co.y % 1.0)
    # normals: face the inside (towards the centerline)
    # flip as a full set only if a clear majority of tube faces face away from the centerline (floor and uvula excluded)
    votes = []
    for f in faces:
        cen = f.calc_center_median()
        d = np.linalg.norm(C - np.array([cen.y, cen.z]), axis=1); k = int(d.argmin())
        axp = Vector((CX, C[k][0], C[k][1]))
        votes.append(f.normal.dot(axp - cen) > 0)
    if sum(votes) < len(votes) / 2:
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    bm.to_mesh(me)
    bm.free()
    return me, dict(L=L, rings=nr, votes_inward=int(sum(votes)), faces=len(faces))


def materials():
    mats = {}
    m = bpy.data.materials.new("MAT_W0_Oral"); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    attr = nt.nodes.new("ShaderNodeAttribute"); attr.attribute_name = "tongue_w"; attr.attribute_type = 'GEOMETRY'
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'
    mix.inputs[6].default_value = (0.70, 0.24, 0.19, 1)      # mucosa (A)
    mix.inputs[7].default_value = (0.72, 0.40, 0.35, 1)      # tongue (B)
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 45; nz.inputs["Detail"].default_value = 6
    vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.feature = 'SMOOTH_F1'; vor.inputs["Smoothness"].default_value = 1.0; vor.inputs["Scale"].default_value = 120
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.0; bump.inputs["Distance"].default_value = 0.012
    mulb = nt.nodes.new("ShaderNodeMath"); mulb.operation = 'MULTIPLY_ADD'; mulb.inputs[1].default_value = 0.3; mulb.inputs[2].default_value = 0.16
    nt.links.new(attr.outputs["Fac"], mix.inputs[0])
    nt.links.new(vor.outputs["Distance"], bump.inputs["Height"])
    nt.links.new(nz.outputs["Fac"], vor.inputs["Vector"]) if False else None
    nt.links.new(attr.outputs["Fac"], mulb.inputs[0])
    nt.links.new(mulb.outputs[0], bump.inputs["Strength"])
    attr2 = nt.nodes.new("ShaderNodeAttribute"); attr2.attribute_name = "slab_w"; attr2.attribute_type = 'GEOMETRY'
    mix2 = nt.nodes.new("ShaderNodeMix"); mix2.data_type = 'RGBA'
    mix2.inputs[7].default_value = (0.78, 0.27, 0.21, 1)   # tone of the laryngeal texture next to the wall
    mulc = nt.nodes.new("ShaderNodeMath"); mulc.operation = 'MULTIPLY'; mulc.inputs[1].default_value = 0.85
    nt.links.new(attr2.outputs["Fac"], mulc.inputs[0]); nt.links.new(mulc.outputs[0], mix2.inputs[0])
    nt.links.new(mix.outputs[2], mix2.inputs[6])
    nt.links.new(mix2.outputs[2], bs.inputs["Base Color"])
    nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    bs.inputs["Roughness"].default_value = 0.35
    bs.inputs["Subsurface Weight"].default_value = 0.15
    bs.inputs["Coat Weight"].default_value = 0.5; bs.inputs["Coat Roughness"].default_value = 0.08
    nt.links.new(bs.outputs[0], out.inputs[0])
    mats[0] = m
    u = bpy.data.materials.new("MAT_W0_Uvula"); u.use_nodes = True
    ub = u.node_tree.nodes["Principled BSDF"]
    ub.inputs["Base Color"].default_value = (0.66, 0.26, 0.22, 1); ub.inputs["Roughness"].default_value = 0.55
    ub.inputs["Coat Weight"].default_value = 0.15; ub.inputs["Subsurface Weight"].default_value = 0.1
    mats[1] = u
    p = bpy.data.materials.new("MAT_W0_BiteBlock"); p.use_nodes = True
    pb = p.node_tree.nodes["Principled BSDF"]
    pb.inputs["Base Color"].default_value = (0.22, 0.12, 0.42, 1); pb.inputs["Roughness"].default_value = 0.25
    mats[2] = p
    return mats


def run():
    if NAME in bpy.data.objects:
        return {"error": NAME + " already exists"}
    for mn in ("MAT_W0_Oral", "MAT_W0_BiteBlock", "MAT_W0_Uvula"):
        if mn in bpy.data.materials and bpy.data.materials[mn].users == 0:
            bpy.data.materials.remove(bpy.data.materials[mn])
    me, info = build()
    ms = materials()
    me.materials.append(ms[0]); me.materials.append(ms[1]); me.materials.append(ms[2])
    me.shade_smooth()
    ob = bpy.data.objects.new(NAME, me)
    bpy.data.collections["Collection"].objects.link(ob)
    return info


result = run()

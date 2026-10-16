"""Tint the Stomach mucosa toward the Antrum's redder colour near the Antrum rim, so the seam disappears.
Creates vertex group 'Antrum_Blend' on Stomach only (1 at the rim -> 0 at `radius` units, geodesic) and inserts a MULTIPLY mix
between COL_VALLEY and the Principled Base Color in MAT_W3_Fundus_Mucosa. The material is shared with PART_W3_Fundus, but
that object has no such group, so the Attribute node reads 0 there and the Fundus is unchanged. Object Mode. Never saves.
"""
import bpy, numpy as np, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import extend_smooth_antrum as E

GROUP = 'Antrum_Blend'


def run(pylorus=(13.68, -7.79, 27.97), radius=9.0, strength=0.75, tint=(0.74, 0.44, 0.40, 1.0), apply=True):
    so = bpy.data.objects['Stomach']
    _, co, ed, bv, fa = E._read(so); n = len(co)
    W = np.array(so.matrix_world); wc = co[bv] @ W[:3, :3].T + W[:3, 3]
    seeds = bv[np.linalg.norm(wc - np.array(pylorus), axis=1) < 3.0]
    d = E.geodesic(ed, co, seeds, n, radius)
    s = np.clip((radius - d) / (radius - 0.5), 0, 1); w = s * s * (3 - 2 * s)
    if not apply: return dict(nonzero=int((w > 0).sum()))
    vg = so.vertex_groups.get(GROUP) or so.vertex_groups.new(name=GROUP)
    vg.remove(list(range(n)))
    q = np.round(w, 2)
    for val in np.unique(q[q > 0]):
        vg.add(np.where(q == val)[0].tolist(), float(val), 'REPLACE')
    nt = bpy.data.materials['MAT_W3_Fundus_Mucosa'].node_tree
    if 'AB_ATTR' not in nt.nodes:
        pb = nt.nodes['Principled BSDF']; src = pb.inputs['Base Color'].links[0].from_node  # COL_VALLEY
        at = nt.nodes.new('ShaderNodeAttribute'); at.name = at.label = 'AB_ATTR'; at.attribute_type = 'GEOMETRY'; at.attribute_name = GROUP
        sc = nt.nodes.new('ShaderNodeMath'); sc.name = sc.label = 'AB_FAC'; sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = strength
        mx = nt.nodes.new('ShaderNodeMix'); mx.name = mx.label = 'AB_TINT'; mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
        mx.inputs[7].default_value = tint
        nt.links.new(at.outputs['Fac'], sc.inputs[0]); nt.links.new(sc.outputs[0], mx.inputs[0])
        nt.links.new(src.outputs[2], mx.inputs[6])   # [2] = colour result of the Mix node
        nt.links.new(mx.outputs[2], pb.inputs['Base Color'])
        for nd, dx, dy in ((at, -420, -330), (sc, -240, -330), (mx, -60, -300)): nd.location = (pb.location.x + dx, pb.location.y + dy)
    return dict(nonzero=int((w > 0).sum()), full=int((w >= 0.99).sum()))

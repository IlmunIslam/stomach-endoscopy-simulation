"""Re-skin the front of the Antrum skirt around the pyloric ring with one clean height-field sheet (live scene, never saves).

Why: the skirt is a double sheet with cracks, a recessed V lobe and pale ring-material petals; patching the cracks one by one failed
(PLAYBOOK 13). Instead: ray-cast down the pyloric axis (-A) on a polar grid (rad .085-.46, 240 angles), take the first hit height,
median-filter 5x5 (removes the through-slit outliers), lift by 0.0025 (+0.005 faded to 0 at both rims) and build a new quad sheet in the
same mesh. New verts get the same position in every shape key (the keys differ only at rad < .1). Faces are reversed so normals face +A.
Then ring-material faces with rad > 0.035 are moved to the mucosa slot so no pale ragged petal border remains.
Take mesh.copy() backups first (PLAYBOOK 11); the grid is built once, rerunning adds a second sheet.
"""
import bpy, bmesh, numpy as np
from mathutils import Vector
import rebuild_pyloric_canal as RC

R0, R1, DR, NT, LIFT, EXTRA = 0.085, 0.46, 0.005, 240, 0.0025, 0.005


def heights(ant, ax0=0.9):
    NR = int((R1 - R0) / DR) + 1; rads = np.linspace(R0, R1, NR); ths = np.linspace(-np.pi, np.pi, NT, endpoint=False)
    H = np.full((NR, NT), np.nan)
    for i, r in enumerate(rads):
        for j, t in enumerate(ths):
            o = RC.C_ + RC.A_ * ax0 + RC.OFF + r * (np.cos(t) * RC.E1 + np.sin(t) * RC.E2)
            ok, loc, _, _ = ant.ray_cast(Vector(o.tolist()), Vector((-RC.A_).tolist()))
            if ok: H[i, j] = (np.array(loc) - RC.C_) @ RC.A_
    H = np.where(np.isnan(H), np.nanmedian(H), H)
    P = np.pad(H, ((2, 2), (0, 0)), mode='edge'); P = np.pad(P, ((0, 0), (2, 2)), mode='wrap')
    Hm = np.median(np.stack([P[2 + a:2 + a + NR, 2 + b:2 + b + NT] for a in range(-2, 3) for b in range(-2, 3)]), axis=0)
    return rads, ths, Hm


def build(ant):
    me = ant.data; names = [k.name for k in me.shape_keys.key_blocks]
    rads, ths, Hm = heights(ant); NR = len(rads)
    ss = lambda x: (lambda y: y * y * (3 - 2 * y))(np.clip(x, 0, 1))
    bm = bmesh.new(); bm.from_mesh(me); lay = [bm.verts.layers.shape[n] for n in names]
    V = [[None] * NT for _ in range(NR)]
    for i, r in enumerate(rads):
        w = float(ss((r - R0) / 0.05) * (1 - ss((r - 0.40) / 0.05)))
        for j, t in enumerate(ths):
            p = RC.C_ + RC.A_ * (Hm[i, j] + LIFT + EXTRA * w) + RC.OFF + r * (np.cos(t) * RC.E1 + np.sin(t) * RC.E2)
            v = bm.verts.new(p.tolist())
            for L in lay: v[L] = p.tolist()
            V[i][j] = v
    F = [bm.faces.new([V[i][j], V[i][(j + 1) % NT], V[i + 1][(j + 1) % NT], V[i + 1][j]]) for i in range(NR - 1) for j in range(NT)]
    bm.normal_update()
    bad = [f for f in F if np.array(f.normal) @ RC.A_ < 0]
    if bad: bmesh.ops.reverse_faces(bm, faces=bad)
    for f in F: f.material_index = 0; f.smooth = True
    bm.to_mesh(me); bm.free(); me.update()
    return dict(faces=len(F), flipped=len(bad))


def soften_ring_material(ant, rad_min=0.035):
    me = ant.data; n = 0
    for p in me.polygons:
        if p.material_index == 1 and RC.axrt(p.center)[1] > rad_min: p.material_index = 0; n += 1
    me.update(); return n

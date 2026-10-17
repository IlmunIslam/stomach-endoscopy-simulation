"""Round 5: rebuild the pyloric canal between the ring and the duodenal bulb, and close the gap around it in the bulb wall. Never saves.

Measured problems (see docs/LESSONS.md): the tube of PART_W5_Antrum is a funnel 0.4 local units long that PROTRUDES into the bulb
(its mouth is at axial coordinate ax=0, the bulb wall hole sits at ax 0.17-0.25 with radius 0.075-0.23, i.e. far wider than the tube),
so from the bulb side it reads as a pipe sticking out of the wall, the hole leaves a gap through which the Stomach is visible
(the 'ragged flap'), the hole's ragged edge has glossy slivers (the 'shards'), and the tube wall has 3-4-face seam edges.

Steps (axial frame: c=(-0.447,0.079,0.599) local, a=(1,0.006,-0.016) normalised, lumen centre offset -0.003 e1 + 0.007 e2):
 1. rebuild_tube(): delete the old tube faces (all verts ax in [-0.05, 0.41], radius < 0.07) and build a clean single-layer canal
    from ax=AX_START (inside the bulb hole) to the remaining wall (junction loop of 79 verts), same radius profile +12% and gentle
    5-fold folds, material slot 0 (mucosa). The protruding part (ax < AX_START) is gone. Same positions in every shape key
    (the keys only differ at ax > 0.40).
 2. close_bulb_hole(): in PART_9_Duodenal bulb, map radius about the canal axis so the ragged hole edge lands on the canal wall:
    r' = r - (rb(theta) - Rt)*(1 - smoothstep((r - rb(theta))/DELTA)); monotonic, so no triangle flips.
"""
import bpy, bmesh, numpy as np

A_ = np.array([1.0, 0.006, -0.016]); A_ /= np.linalg.norm(A_); C_ = np.array([-0.447, 0.079, 0.599])
E1 = np.cross(A_, [0, 0, 1.0]); E1 /= np.linalg.norm(E1); E2 = np.cross(A_, E1); OFF = -0.003 * E1 + 0.007 * E2
AX_START, AX_END, DELTA, AX_DEL_HI = 0.16, 0.375, 0.35, 0.41   # canal is rebuilt up to the skirt (flare starts at ax~0.42)
PROF = np.array([(0.10, 0.028), (0.14, 0.022), (0.18, 0.018), (0.22, 0.0155), (0.26, 0.0140), (0.30, 0.0132), (0.34, 0.0125), (0.40, 0.012)])


def ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def axrt(p):
    r = np.asarray(p) - C_; ax = r @ A_; q = r - ax * A_ - OFF
    return ax, float(np.hypot(q @ E1, q @ E2)), float(np.arctan2(q @ E2, q @ E1))


def canal_radius(ax, th):
    base = np.interp(ax, PROF[:, 0], PROF[:, 1]); b = np.sin(np.pi * np.clip((ax - AX_START) / (0.33 - AX_START), 0, 1))
    return base * (1 + 0.12 * b + 0.08 * b * np.cos(5 * th + 0.6))


def canal_point(ax, th, r=None):
    r = canal_radius(ax, th) if r is None else r
    return C_ + A_ * ax + OFF + r * (np.cos(th) * E1 + np.sin(th) * E2)


def rebuild_tube(apply=True):
    ob = bpy.data.objects['PART_W5_Antrum']; me = ob.data
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    names = [k.name for k in me.shape_keys.key_blocks]; sk = bm.verts.layers.shape; lay = [sk[n] for n in names]
    axr = {v.index: axrt(v.co) for v in bm.verts}
    inz = lambda v: -0.05 <= axr[v.index][0] <= AX_DEL_HI and axr[v.index][1] < 0.07
    old = [f for f in bm.faces if all(inz(v) for v in f.verts)]
    oldset = set(old)
    jset = {v for f in old for v in f.verts if any(g not in oldset for g in v.link_faces)}
    # walk the boundary of the deleted region as a cyclic loop (the junction zig-zags in ax, so sorting by angle would twist it)
    jedges = [e for e in bm.edges if e.verts[0] in jset and e.verts[1] in jset and len(e.link_faces) >= 1 and
              any(g in oldset for g in e.link_faces) and any(g not in oldset for g in e.link_faces)]
    adj = {}
    for e in jedges:
        for v in e.verts: adj.setdefault(v, []).append(e.other_vert(v))
    start = min(jset, key=lambda v: axr[v.index][2]); loop = [start]; prev = None; cur = start
    while True:
        nxt = [w for w in adj.get(cur, []) if w is not prev and w not in loop[1:]]
        if not nxt: break
        nxt = nxt[0]
        if nxt is start: break
        loop.append(nxt); prev, cur = cur, nxt
    junction = loop if (len(loop) == len(jset) and len(loop) > 20) else sorted(jset, key=lambda v: axr[v.index][2])
    # make the loop run in increasing angle
    if len(junction) > 3 and axr[junction[1].index][2] < axr[junction[0].index][2] and axr[junction[2].index][2] < axr[junction[1].index][2]: junction = junction[::-1]
    # orientation of the old tube faces relative to the axis (+1 = normals point away from the axis)
    sgn = np.sign(np.mean([np.dot(np.array(f.normal), np.array(f.calc_center_median()) - C_ - OFF - A_ * ((np.array(f.calc_center_median()) - C_) @ A_)) for f in old]))
    info = dict(old_faces=len(old), junction=len(junction), orientation=float(sgn),
                junction_ax=[min(axr[v.index][0] for v in junction), max(axr[v.index][0] for v in junction)], loop_walk=(junction is loop))
    if not apply: bm.free(); return info
    ths = np.array([axr[v.index][2] for v in junction]); M = len(junction)
    bmesh.ops.delete(bm, geom=old, context='FACES')
    ax_rings = np.linspace(AX_START, AX_END, 8)
    rings = []
    for ax in ax_rings:
        ring = []
        for th in ths:
            p = canal_point(ax, th); v = bm.verts.new(p.tolist())
            for L in lay: v[L] = p.tolist()
            ring.append(v)
        rings.append(ring)
    rings.append(list(junction))
    new = []
    for k in range(len(rings) - 1):
        for j in range(M):
            j2 = (j + 1) % M
            try: new.append(bm.faces.new([rings[k][j], rings[k][j2], rings[k + 1][j2], rings[k + 1][j]]))
            except ValueError: pass
    bm.normal_update()
    # orient like the old faces: reverse EVERY new face whose normal disagrees (old faces point toward the axis here)
    flip = []
    for f in new:
        cc = np.array(f.calc_center_median()); rad = cc - C_ - OFF - A_ * ((cc - C_) @ A_)
        if np.dot(np.array(f.normal), rad) * sgn < 0: flip.append(f)
    if flip: bmesh.ops.reverse_faces(bm, faces=flip)
    for f in new: f.material_index = 0; f.smooth = True
    bm.to_mesh(me); bm.free(); me.update()
    info.update(new_faces=len(new), rings=len(ax_rings), flipped=len(flip)); return info


def close_bulb_hole(apply=True, hops=60):
    bulb = bpy.data.objects['PART_9_Duodenal bulb']; ant = bpy.data.objects['PART_W5_Antrum']; me = bulb.data; n = len(me.vertices)
    Wb = np.array(bulb.matrix_world); Wa = np.array(ant.matrix_world); Wai = np.linalg.inv(Wa)
    V = np.empty(n * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    Vl = ((V @ Wb[:3, :3].T + Wb[:3, 3]) @ Wai[:3, :3].T) + Wai[:3, 3]            # bulb verts in Antrum local coords
    r = Vl - C_; ax = r @ A_; q = r - ax[:, None] * A_ - OFF; rad = np.hypot(q @ E1, q @ E2); th = np.arctan2(q @ E2, q @ E1)
    lf = {}
    for p in me.polygons:
        v = list(p.vertices)
        for k in range(len(v)): lf.setdefault(tuple(sorted((v[k], v[(k + 1) % len(v)]))), []).append(p.index)
    bd = [e for e, f in lf.items() if len(f) == 1]
    hole = sorted({v for e in bd for v in e if rad[v] < 0.25 and abs(ax[v]) < 0.3})
    hole = np.array(hole)
    # rb(theta): boundary radius as a smooth periodic function
    nb = 72; bins = np.linspace(-np.pi, np.pi, nb + 1); rb = np.full(nb, np.nan)
    for i in range(nb):
        m = (th[hole] >= bins[i]) & (th[hole] < bins[i + 1])
        if m.any(): rb[i] = rad[hole][m].mean()
    idx = np.arange(nb); good = ~np.isnan(rb); rb = np.interp(idx, idx[good], rb[good], period=nb)
    k = np.array([1, 4, 6, 4, 1], float); k /= k.sum(); rb = np.convolve(np.concatenate([rb[-2:], rb, rb[:2]]), k, mode='valid')
    rb_of = lambda t: np.interp((t + np.pi) / (2 * np.pi) * nb - 0.5, np.arange(-1, nb + 1), np.concatenate([rb[-1:], rb, rb[:1]]))
    Rt = np.array([canal_radius(float(np.clip(ax[v], AX_START + 0.005, AX_END)), th[v]) * 1.02 for v in hole])
    info = dict(hole_verts=len(hole), rb_range=[float(rb.min()), float(rb.max())], ax_range=[float(ax[hole].min()), float(ax[hole].max())])
    # graph hops from the hole
    ed = np.array([e for e in lf.keys()]); d = np.full(n, 10 ** 6); d[hole] = 0
    for h in range(1, hops + 1):
        m1 = (d[ed[:, 0]] == h - 1) & (d[ed[:, 1]] > h); d[ed[m1, 1]] = h
        m2 = (d[ed[:, 1]] == h - 1) & (d[ed[:, 0]] > h); d[ed[m2, 0]] = h
    # harmonic (implicit-smoothed, near-Laplace) displacement: the ragged hole edge moves radially onto the canal wall (Dirichlet),
    # the wall within `hops` edges follows smoothly, everything else is fixed. Avoids the long spikes a per-vertex radial map makes.
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) if '__file__' in globals() else None
    import close_pylorus_slot as CS
    ishole = np.zeros(n, bool); ishole[hole] = True
    band = (ax > ax[hole].min() - 0.12) & (ax < ax[hole].max() + 0.12)
    free = (d <= hops) & (~ishole) & band
    q_dir = np.stack([np.cos(th), np.sin(th)], 1)
    D = np.zeros((n, 3)); drh = Rt - rad[hole]
    D[hole] = drh[:, None] * (q_dir[hole][:, :1] * E1 + q_dir[hole][:, 1:] * E2)
    Ds = CS._smooth(ed, n, free, D, t=40.0, iters=600)
    info.update(affected=int((np.linalg.norm(Ds, axis=1) > 1e-6).sum()), max_move_local=float(np.linalg.norm(Ds, axis=1).max()), free=int(free.sum()))
    if not apply: return info
    newl = Vl + Ds
    # new local positions -> back to bulb local
    Wbi = np.linalg.inv(Wb)
    world_old = Vl @ Wa[:3, :3].T + Wa[:3, 3]; world_new = newl @ Wa[:3, :3].T + Wa[:3, 3]
    out = (V + ((world_new - world_old) @ Wbi[:3, :3].T)).ravel()
    me.vertices.foreach_set('co', out); me.update()
    return info

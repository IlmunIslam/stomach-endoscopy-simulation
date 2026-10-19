"""Fill the V-shaped notch above the pyloric ring in PART_W5_Antrum (live scene, never saves).

Why: the skirt of the Antrum is a two-sheet slab (stomach-facing 'front' sheet and bulb-facing 'back' sheet) with a wedge-shaped
bite missing above the ring (tip at radius 0.08, theta -90 deg, opening to theta -153..-27 at radius 0.43; axial frame as in
rebuild_pyloric_canal.py). Through the bite the camera saw the dark back of the Stomach wall (the 'black V').

Steps (all shape keys are written per vertex, so Basis / Pylorus_Close / Pylorus_Open stay consistent):
 1. restore the pre-patch topology from the mesh copy ANTRUM_BACKUP_r10;
 2. delete the notch wall faces (|normal . axis| < 0.5 within 6 deg of the empty wedge);
 3. build one patch per sheet whose first/last column are the flank boundary vertices themselves (interior columns interpolated in
    polar coordinates), weld coincident vertices;
 4. close the remaining hairline cracks with mutual-nearest pair welds (0.015) and vertex merges (0.008, then 0.010/0.014/0.020 on
    the open boundary only). Do NOT go above 0.02: 0.025 merged 422 vertices and shredded the flanks.
Data needed in %TEMP%/antrum_fix/r4: notch_rows2.npy (flank angle/axial profile per radius, per key).
"""
import bpy, bmesh, numpy as np
import rebuild_pyloric_canal as RC

A = RC.A_
RR = np.arange(0.075, 0.4301, 0.006)
NC = 16


def pol1(p):
    r = np.asarray(p) - RC.C_; ax = r @ A; q = r - ax * A - RC.OFF
    return ax, float(np.hypot(q @ RC.E1, q @ RC.E2)), float(np.arctan2(q @ RC.E2, q @ RC.E1))


def run(R, backup='ANTRUM_BACKUP_r10'):
    ob = bpy.data.objects['PART_W5_Antrum']; me = ob.data; bkm = bpy.data.meshes[backup]
    bm0 = bmesh.new(); bm0.from_mesh(bkm); bm0.to_mesh(me); bm0.free(); me.update()
    names = [k.name for k in me.shape_keys.key_blocks]
    K = {nm: np.array([x.co[:] for x in me.shape_keys.key_blocks[nm].data]) for nm in names}
    data = np.load(R + r"\notch_rows2.npy"); RADS = np.arange(0.07, 0.431, 0.01)
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.verts.ensure_lookup_table()
    lay = [bm.verts.layers.shape[nm] for nm in names]
    kill = []
    for f in bm.faces:
        c = f.calc_center_median(); ax, rad, th = RC.axrt(c); th = np.degrees(th)
        if not (0.07 < rad < 0.45 and ax > 0.42): continue
        if abs(np.array(f.normal) @ A) > 0.5: continue
        k = int(np.clip(round((rad - 0.07) / 0.01), 0, len(RADS) - 1)); d = data[0, k]
        if min(abs(th - d[0]), abs(th - d[1])) < 6 or d[0] < th < d[1]: kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context='FACES_ONLY'); bm.edges.ensure_lookup_table(); bm.verts.ensure_lookup_table()

    def kinfo(v):
        ax, rad, th = RC.axrt(v.co); return ax, rad, np.degrees(th)

    def zone(v):
        ax, rad, th = kinfo(v)
        if not (0.06 < rad < 0.46 and ax > 0.42): return False
        k = int(np.clip(round((rad - 0.07) / 0.01), 0, len(RADS) - 1)); d = data[0, k]; return d[0] - 10 < th < d[1] + 10
    bverts = set()
    for e in bm.edges:
        if len(e.link_faces) == 1 and zone(e.verts[0]) and zone(e.verts[1]): bverts.add(e.verts[0]); bverts.add(e.verts[1])

    def isfront(v, left):
        ax, rad, th = kinfo(v); k = int(np.clip(round((rad - 0.07) / 0.01), 0, len(RADS) - 1)); d = data[0, k]
        return ax > (((d[2] + d[3]) / 2) if left else ((d[4] + d[5]) / 2))
    left = [v for v in bverts if kinfo(v)[2] < -90]; right = [v for v in bverts if kinfo(v)[2] >= -90]

    def chain(side, left_, front): return sorted([v for v in side if isfront(v, left_) == front], key=lambda v: kinfo(v)[1])
    CH = {('L', 1): chain(left, True, True), ('L', 0): chain(left, True, False), ('R', 1): chain(right, False, True), ('R', 0): chain(right, False, False)}

    def nearest(ch, r0):
        rs = np.array([kinfo(v)[1] for v in ch]); i = int(np.abs(rs - r0).argmin()); return ch[i] if abs(rs[i] - r0) < 0.012 else None
    nfaces = 0
    for front in (1, 0):
        rowsV = []
        for r0 in RR:
            vl = nearest(CH[('L', front)], r0); vr = nearest(CH[('R', front)], r0)
            if vl is None or vr is None: rowsV.append(None); continue
            row = [vl]; pk = []
            for nm in names:
                al, rl, tl = pol1(K[nm][vl.index]); ar, rr_, tr = pol1(K[nm][vr.index]); pk.append((al, rl, tl, ar, rr_, tr))
            for c in range(1, NC - 1):
                f = c / (NC - 1); pts = []
                for (al, rl, tl, ar, rr_, tr) in pk:
                    t = tl + f * (tr - tl); rad = rl + f * (rr_ - rl); ax = al + f * (ar - al)
                    pts.append(RC.C_ + A * ax + RC.OFF + rad * (np.cos(t) * RC.E1 + np.sin(t) * RC.E2))
                nv = bm.verts.new(pts[0].tolist())
                for L, p in zip(lay, pts): nv[L] = p.tolist()
                row.append(nv)
            row.append(vr); rowsV.append(row)
        faces = []
        for i in range(len(rowsV) - 1):
            a_, b_ = rowsV[i], rowsV[i + 1]
            if a_ is None or b_ is None: continue
            for c in range(NC - 1):
                vs = [a_[c], a_[c + 1], b_[c + 1], b_[c]]
                if len(set(vs)) < 3: continue
                try: faces.append(bm.faces.new(vs if len(set(vs)) == 4 else list(dict.fromkeys(vs))))
                except ValueError: pass
        bm.normal_update(); want = 1 if front else -1
        bad = [f for f in faces if (np.array(f.normal) @ A) * want < 0]
        if len(bad) > len(faces) / 2: bad = [f for f in faces if f not in bad]
        if bad: bmesh.ops.reverse_faces(bm, faces=bad)
        for f in faces: f.material_index = 0; f.smooth = True
        nfaces += len(faces)
    bm.verts.ensure_lookup_table()
    zone_v = [v for v in bm.verts if (lambda a: 0.06 < a[1] < 0.47 and a[0] > 0.42)(RC.axrt(v.co))]
    bmesh.ops.remove_doubles(bm, verts=zone_v, dist=1e-5)
    bm.to_mesh(me); bm.free(); me.update()
    return dict(killed=len(kill), patch_faces=nfaces, nv=len(me.vertices), nf=len(me.polygons))


def open_boundary(bm, rmax=0.47):
    def inz(v):
        q = RC.axrt(v.co); return 0.07 < q[1] < rmax and q[0] > 0.42 and abs(np.degrees(q[2]) + 90) < 85
    return [v for v in bm.verts if inz(v) and any(len(e.link_faces) == 1 for e in v.link_edges)]


def weld_cracks(me):
    names = [k.name for k in me.shape_keys.key_blocks]; log = []
    for rnd in range(5):                      # mutual nearest pairs across the cracks, midpoint in every key
        bm = bmesh.new(); bm.from_mesh(me); bm.edges.ensure_lookup_table(); bm.verts.ensure_lookup_table()
        lay = [bm.verts.layers.shape[nm] for nm in names]
        bnd = open_boundary(bm); m = len(bnd); P = np.array([v.co for v in bnd]); conn = [{e.other_vert(v) for e in v.link_edges} for v in bnd]
        nn = []
        for i in range(m):
            d = np.linalg.norm(P - P[i], axis=1); d[i] = 9
            for j in range(m):
                if bnd[j] in conn[i]: d[j] = 9
            nn.append(int(d.argmin()) if d.min() < 0.015 else -1)
        pairs = [(i, nn[i]) for i in range(m) if nn[i] >= 0 and nn[nn[i]] == i and i < nn[i]]
        for i, j in pairs:
            for L in lay:
                mid = (bnd[i][L] + bnd[j][L]) * 0.5; bnd[i][L] = mid.copy(); bnd[j][L] = mid.copy()
            mid = (bnd[i].co + bnd[j].co) * 0.5; bnd[i].co = mid; bnd[j].co = mid.copy()
        bmesh.ops.remove_doubles(bm, verts=[bnd[i] for p in pairs for i in p], dist=1e-6)
        bm.to_mesh(me); bm.free(); me.update(); log.append((m, len(pairs)))
        if not pairs: break
    for thr in (0.008, 0.010, 0.014, 0.020):  # vertex merges on the open boundary only
        bm = bmesh.new(); bm.from_mesh(me); bm.edges.ensure_lookup_table(); bm.verts.ensure_lookup_table()
        n0 = len(bm.verts); bmesh.ops.remove_doubles(bm, verts=open_boundary(bm), dist=thr); log.append((thr, n0 - len(bm.verts)))
        bm.to_mesh(me); bm.free(); me.update()
    return log

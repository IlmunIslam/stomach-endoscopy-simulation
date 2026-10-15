"""Remove spike/fin anomalies on Stomach WITHOUT opening a gap to PART_W5_Antrum.

Object-mode, numpy only. Does not touch selection flags or save.
Membrane: the anomaly region (bool mask) is solved as a harmonic surface, everything else pinned (open-boundary
verts and the pylorus lumen cylinder are pinned too, optional). Then the Stomach hole rim is snapped onto the nearest
point of the Antrum surface; the move fades out over `warp_hops` rings as a displacement field (detail preserved).
Writes coordinates to the mesh AND the Basis shape key. Backs up originals to backup_path (npy).
"""
import bpy, bmesh, numpy as np, mathutils


def _cg(matvec, b, x0, iters=400, tol=1e-7):
    x = x0.copy(); r = b - matvec(x); p = r.copy(); rs = (r * r).sum()
    for _ in range(iters):
        Ap = matvec(p); a = rs / max((p * Ap).sum(), 1e-30)
        x += a * p; r -= a * Ap; rs2 = (r * r).sum()
        if rs2 < tol * tol * max(b.size, 1): break
        p = r + (rs2 / rs) * p; rs = rs2
    return x


class Mesh:
    def __init__(self, me):
        self.n = len(me.vertices)
        co = np.empty(self.n * 3); me.vertices.foreach_get("co", co); self.co = co.reshape(-1, 3)
        ed = np.empty(len(me.edges) * 2, int); me.edges.foreach_get("vertices", ed); self.ed = ed.reshape(-1, 2)
        self.deg = np.maximum(np.bincount(self.ed.ravel(), minlength=self.n), 1).astype(float)
        order = np.argsort(np.concatenate([self.ed[:, 0], self.ed[:, 1]]))
        a = np.concatenate([self.ed[:, 0], self.ed[:, 1]])[order]; b = np.concatenate([self.ed[:, 1], self.ed[:, 0]])[order]
        self.nbr_ptr = np.searchsorted(a, np.arange(self.n + 1)); self.nbr = b
        pc = np.empty(len(me.polygons), int); me.polygons.foreach_get("loop_total", pc)

    def nb(self, v): return self.nbr[self.nbr_ptr[v]:self.nbr_ptr[v + 1]]

    def lap(self, p):
        a = np.zeros_like(p); np.add.at(a, self.ed[:, 0], p[self.ed[:, 1]]); np.add.at(a, self.ed[:, 1], p[self.ed[:, 0]])
        return a / self.deg[:, None] - p

    def rings(self, mask, k):
        m = mask.copy()
        for _ in range(k):
            idx = np.where(m)[0]
            if idx.size == 0: break
            nxt = np.concatenate([self.nb(v) for v in idx]); m[nxt] = True
        return m

    def taubin_dev(self, co, it=20, mask=None):
        """Deviation from a Taubin-smoothed copy; with `mask`, only that sub-mesh is processed (fast)."""
        if mask is None: mask = np.ones(self.n, bool)
        ea, eb = self.ed[:, 0], self.ed[:, 1]; keep = mask[ea] & mask[eb]
        ea, eb = ea[keep], eb[keep]
        deg = np.maximum(np.bincount(np.concatenate([ea, eb]), minlength=self.n), 1).astype(float)

        def lap(p):
            a = np.zeros_like(p); np.add.at(a, ea, p[eb]); np.add.at(a, eb, p[ea]); return a / deg[:, None] - p
        p = co.copy()
        for _ in range(it): p = p + 0.5 * lap(p); p = p - 0.53 * lap(p)
        out = np.zeros(self.n); out[mask] = np.linalg.norm(co - p, axis=1)[mask]
        return out

    def harmonic(self, free, co, fixed_override=None, iters=600):
        """Solve free verts as the average of neighbours; all other verts are fixed at `co`."""
        P = co.copy()
        F = np.where(free)[0]
        # CG on  (D - A) x = A_fixed * x_fixed  restricted to free
        pos = -np.ones(self.n, int); pos[F] = np.arange(F.size)
        ea, eb = self.ed[:, 0], self.ed[:, 1]
        ff = free[ea] & free[eb]
        fa, fb = pos[ea[ff]], pos[eb[ff]]
        rhs = np.zeros((F.size, 3))
        m1 = free[ea] & ~free[eb]; np.add.at(rhs, pos[ea[m1]], co[eb[m1]])
        m2 = free[eb] & ~free[ea]; np.add.at(rhs, pos[eb[m2]], co[ea[m2]])
        d = self.deg[F]

        def mv(x):
            y = d[:, None] * x
            np.add.at(y, fa, -x[fb]); np.add.at(y, fb, -x[fa]); return y
        x = _cg(mv, rhs, co[F], iters=iters)
        P[F] = x
        return P


def boundary_loops(me):
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    adj = {}
    for e in bm.edges:
        if len(e.link_faces) == 1:
            a, b = e.verts[0].index, e.verts[1].index
            adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    seen, loops = set(), []
    for s in adj:
        if s in seen: continue
        order = [s]; seen.add(s)
        prev = None; cur = s
        while True:
            nx = [y for y in adj[cur] if y != prev and y not in seen]
            if not nx: break
            prev, cur = cur, nx[0]; seen.add(cur); order.append(cur)
        loops.append(order)
    bm.free()
    return loops


def nearest_on_polyline(pts, poly):
    """pts (m,3); poly (k,3) closed. Return nearest point on the polyline for each pt."""
    a = poly; b = np.roll(poly, -1, axis=0); ab = b - a; l2 = np.maximum((ab * ab).sum(1), 1e-12)
    out = np.empty_like(pts)
    for i, p in enumerate(pts):
        t = np.clip(((p - a) * ab).sum(1) / l2, 0, 1)
        q = a + t[:, None] * ab
        out[i] = q[np.argmin(((q - p) ** 2).sum(1))]
    return out


def run(region, backup_path=None, lumen_radius=0.0, pin_boundary=False, warp_hops=10, apply=True):
    """region: bool mask (len = verts) of the anomaly vertices to flatten."""
    s = bpy.data.objects["Stomach"]; a = bpy.data.objects["PART_W5_Antrum"]
    me = s.data; M = Mesh(me)
    mwS = np.array(s.matrix_world); mwA = np.array(a.matrix_world)
    aco = np.array([list(v.co) for v in a.data.vertices]) @ mwA[:3, :3].T + mwA[:3, 3]
    apoly = aco[max(boundary_loops(a.data), key=len)]
    scw = lambda l: M.co[l] @ mwS[:3, :3].T + mwS[:3, 3]
    srim = min([l for l in boundary_loops(me) if len(l) > 50],
               key=lambda l: np.linalg.norm(scw(l).mean(0) - apoly.mean(0)))
    rim_mask = np.zeros(M.n, bool); rim_mask[srim] = True
    # 1. membrane over the anomaly region (everything else pinned). Open-boundary verts (holes such as the pylorus
    #    opening) are pinned too, otherwise the membrane collapses and fills those holes.
    bnd = np.zeros(M.n, bool)
    for l in boundary_loops(me): bnd[l] = True
    if pin_boundary: region = region & ~bnd
    # keep the pylorus lumen open: pin Stomach verts inside a cylinder around the Antrum axis (open end -> outlet)
    outlet = aco[min(boundary_loops(a.data), key=len)].mean(0)
    ax0 = apoly.mean(0); ax = outlet - ax0; axl = np.linalg.norm(ax); ax /= axl
    wco = M.co @ mwS[:3, :3].T + mwS[:3, 3]
    t = (wco - ax0) @ ax; rad = np.linalg.norm(wco - (ax0 + t[:, None] * ax), axis=1)
    if lumen_radius > 0: region = region & ~((t > -0.5) & (t < axl + 1.0) & (rad < lumen_radius))
    co1 = M.harmonic(region, M.co)
    # 2. close the gap: snap the Stomach hole rim onto the Antrum SURFACE (nearest point), fading out over warp_hops rings
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromObject(a, bpy.context.evaluated_depsgraph_get())
    invA = a.matrix_world.inverted(); invS3 = np.linalg.inv(mwS[:3, :3])
    tgt = np.empty((len(srim), 3)); gap = np.empty(len(srim))
    for k, vi in enumerate(srim):
        pw = mathutils.Vector(co1[vi] @ mwS[:3, :3].T + mwS[:3, 3])
        loc, nrm, idx, dist = bvh.find_nearest(invA @ pw)
        qw = np.array(a.matrix_world @ loc); tgt[k] = (qw - mwS[:3, 3]) @ invS3.T; gap[k] = np.linalg.norm(qw - np.array(pw))
    zone = M.rings(rim_mask, warp_hops)
    delta = np.zeros_like(M.co); delta[srim] = tgt - co1[srim]
    co2 = co1 + M.harmonic(zone & ~rim_mask, delta)
    info = {"region": int(region.sum()), "rim_verts": len(srim), "gap_before_max": float(gap.max()), "gap_before_mean": float(gap.mean()),
            "max_move": float(np.linalg.norm(co2 - M.co, axis=1).max())}
    if apply:
        if backup_path: np.save(backup_path, M.co)
        me.vertices.foreach_set("co", co2.ravel())
        if me.shape_keys:
            for kb in me.shape_keys.key_blocks:
                if kb.relative_key == kb: kb.data.foreach_set("co", co2.ravel())
        me.update()
    return info, co2

"""Refine the vein-like strand that already exists in PART_W5_Antrum (the vertices the user selected; saved as an index
list tools/antrum_vein_idx.npy). Object Mode, numpy, data API; selection flags are not touched. Never saves.

 1. Under-surface S = Laplacian smoothing of the strand verts with the ring of neighbours fixed (flattens the jagged fin).
 2. New height = gaussian cross-section (sigma, height) around the strand centreline (binned PCA path), added along the
    vertex normal of S. Weight fades to 0 over the 2 outermost vertex rings so no seam is cut into the wall.
 3. The same displacement is added to every shape key (Close/Open animation stays consistent).
 4. Float POINT attribute 'Antrum_Vein' (gaussian, wider than the geometry) for the shader to tint the vessel.
"""
import bpy, numpy as np


def run(idx, sigma=0.017, height=0.012, tint_sigma=0.026, iters=60, backup_npz=None, apply=True):
    ob = bpy.data.objects['PART_W5_Antrum']; me = ob.data; nv = len(me.vertices)
    keys = [k.data for k in me.shape_keys.key_blocks]
    co = []
    for kd in keys:
        x = np.empty(nv * 3); kd.foreach_get('co', x); co.append(x.reshape(-1, 3))
    if backup_npz: np.savez(backup_npz, *co)
    idx = np.asarray(idx); n = len(idx); pos = -np.ones(nv, int); pos[idx] = np.arange(n)
    ed = np.empty(len(me.edges) * 2, int); me.edges.foreach_get('vertices', ed); ed = ed.reshape(-1, 2)
    a, b = ed[:, 0], ed[:, 1]
    P = co[0][idx]
    nrm = np.empty(nv * 3); me.vertex_normals.foreach_get('vector', nrm); nrm = nrm.reshape(-1, 3)
    # neighbour lists
    nbr = [[] for _ in range(nv)]
    for u, v in ed:
        if pos[u] >= 0 or pos[v] >= 0: nbr[u].append(v); nbr[v].append(u)
    depth = np.full(n, 99.0)
    for i, v in enumerate(idx):
        if any(pos[w] < 0 for w in nbr[v]): depth[i] = 0
    for h in range(1, 4):
        for i, v in enumerate(idx):
            if depth[i] > h and any(pos[w] >= 0 and depth[pos[w]] == h - 1 for w in nbr[v]): depth[i] = h
    w_fade = np.clip(depth / 2.0, 0, 1)
    S = P.copy()
    for _ in range(iters):
        new = S.copy()
        for i, v in enumerate(idx):
            acc = [S[pos[w]] if pos[w] >= 0 else co[0][w] for w in nbr[v]]
            new[i] = 0.5 * S[i] + 0.5 * np.mean(acc, 0)
        S = new
    c = S.mean(0); u, sv, vt = np.linalg.svd(S - c); ax = vt[0]
    # crest verts = the most raised part of the original fin (relative to the smoothed under-surface)
    Nn = nrm[idx] / np.maximum(np.linalg.norm(nrm[idx], axis=1, keepdims=True), 1e-9)
    dev = ((P - S) * Nn).sum(1); crest = dev >= np.percentile(dev, 60)
    t = (S - c) @ ax; edges = np.linspace(t.min(), t.max(), 22); cl = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (t >= lo) & (t <= hi) & crest
        if m.any(): cl.append(P[m].mean(0))
    cl = np.array(cl)
    for _ in range(2): cl[1:-1] = 0.25 * cl[:-2] + 0.5 * cl[1:-1] + 0.25 * cl[2:]

    def dist(p):
        best = 1e9
        for q0, q1 in zip(cl[:-1], cl[1:]):
            ab = q1 - q0; s = np.clip(np.dot(p - q0, ab) / max(np.dot(ab, ab), 1e-12), 0, 1); best = min(best, np.linalg.norm(p - (q0 + s * ab)))
        return best
    d = np.array([dist(p) for p in S])
    prof = height * np.exp(-d ** 2 / (2 * sigma ** 2))
    N = nrm[idx]; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    delta = w_fade[:, None] * ((S + N * prof[:, None]) - P)
    tint = np.exp(-d ** 2 / (2 * tint_sigma ** 2))
    info = dict(n=n, max_move=float(np.linalg.norm(delta, axis=1).max()), mean_move=float(np.linalg.norm(delta, axis=1).mean()),
                strand_len_local=float(np.linalg.norm(np.diff(cl, axis=0), axis=1).sum()))
    if apply:
        for kd, arr in zip(keys, co):
            q = arr.copy(); q[idx] += delta; kd.foreach_set('co', q.ravel())
        q0 = co[0].copy(); q0[idx] += delta; me.vertices.foreach_set('co', q0.ravel())
        att = me.attributes.get('Antrum_Vein') or me.attributes.new('Antrum_Vein', 'FLOAT', 'POINT')
        arr = np.zeros(nv, np.float32); arr[idx] = tint; att.data.foreach_set('value', arr)
        me.update()
    return info

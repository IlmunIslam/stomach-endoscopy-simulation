"""Antrum is the pivot (never moved). Blend the Stomach wall into PART_W5_Antrum:
 1. smooth the Stomach hole rim along its own loop, re-project onto the Antrum surface (removes sawtooth),
 2. bend the wall near the rim so it flows tangentially into the Antrum: implicit smoothing of the band where the rim and
    'ghost' points (Antrum surface points a little beyond each rim vertex, along the wall's direction of travel) are fixed.
Object Mode, numpy; writes Stomach coords + Basis key. Never saves.
"""
import bpy, bmesh, numpy as np, mathutils
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import extend_smooth_antrum as E


def run(pylorus=(13.68, -7.79, 27.97), band=4.0, full=1.0, t=15.0, ghost=0.7, max_move=0.8, rim_iters=4, backup_npy=None, apply=True):
    so = bpy.data.objects['Stomach']; ao = bpy.data.objects['PART_W5_Antrum']
    _, co, ed, bv, fa = E._read(so); n = len(co)
    if backup_npy: np.save(backup_npy, co)
    W = np.array(so.matrix_world); Wi = np.linalg.inv(W)
    w2l = lambda p: p @ Wi[:3, :3].T + Wi[:3, 3]
    wco = co @ W[:3, :3].T + W[:3, 3]
    seeds = bv[np.linalg.norm(wco[bv] - np.array(pylorus), axis=1) < 3.0]
    seed_set = set(seeds.tolist())
    # Antrum BVH (world)
    ab = bmesh.new(); ab.from_mesh(ao.data); ab.transform(ao.matrix_world); ab.faces.ensure_lookup_table()
    bvh = mathutils.bvhtree.BVHTree.FromBMesh(ab)
    near = lambda p: bvh.find_nearest(mathutils.Vector(p))
    # adjacency
    nbrs = [[] for _ in range(n)]
    for a, b in ed: nbrs[a].append(b); nbrs[b].append(a)
    # 1. rim loop smoothing + reprojection
    rim = np.array(sorted(seed_set)); rpos = wco[rim].copy()
    ridx = {v: i for i, v in enumerate(rim)}
    rn = [[ridx[u] for u in nbrs[v] if u in ridx] for v in rim]   # boundary neighbours (loop adjacency)
    for _ in range(rim_iters):
        new = rpos.copy()
        for i, l in enumerate(rn):
            if l: new[i] = 0.5 * rpos[i] + 0.5 * rpos[l].mean(0)
        rpos = new
        for i in range(len(rim)): rpos[i] = np.array(near(rpos[i])[0])
    rim_move = np.linalg.norm(rpos - wco[rim], axis=1)
    wco2 = wco.copy(); wco2[rim] = rpos
    # 2. ghost points
    ghosts = []
    for i, v in enumerate(rim):
        inner = [u for u in nbrs[v] if u not in seed_set]
        m = wco2[inner].mean(0) if inner else wco2[v]
        dv = wco2[v] - m; dv /= max(np.linalg.norm(dv), 1e-9)
        loc, nrm, _, _ = near(wco2[v])
        nrm = np.array(nrm); td = dv - dv.dot(nrm) * nrm; td /= max(np.linalg.norm(td), 1e-9)
        g = near(np.array(loc) + ghost * td)[0]
        ghosts.append(w2l(np.array(g)))
    ghosts = np.array(ghosts)
    # geodesic weight from rim (original graph)
    d = E.geodesic(ed, co, rim, n, band + 1)
    s = np.clip((band - d) / (band - full), 0, 1); w = s * s * (3 - 2 * s)
    co2 = co.copy(); co2[rim] = w2l(rpos)
    free = (w > 0) & ~np.isin(np.arange(n), rim)
    # extended graph with ghosts (fixed)
    gi = n + np.arange(len(rim))
    ed_x = np.vstack([ed, np.stack([rim, gi], 1)])
    co_x = np.vstack([co2, ghosts]); free_x = np.concatenate([free, np.zeros(len(rim), bool)])
    S = E._implicit_smooth(ed_x, n + len(rim), free_x, co_x, t)[:n]
    dl = w[:, None] * (S - co2); ln = np.linalg.norm(dl, axis=1, keepdims=True)
    new = co2 + dl * np.minimum(1.0, max_move / np.maximum(ln, 1e-12))
    new[rim] = co2[rim]
    info = dict(rim=len(rim), rim_move_mean=float(rim_move.mean()), rim_move_max=float(rim_move.max()),
                band_verts=int((w > 0).sum()), max_move=float(np.linalg.norm(new - co, axis=1).max()),
                mean_move_band=float(np.linalg.norm(new - co, axis=1)[w > 0.5].mean()))
    if apply:
        so.data.vertices.foreach_set("co", new.ravel())
        if so.data.shape_keys: so.data.shape_keys.key_blocks[0].data.foreach_set("co", new.ravel())
        so.data.update()
    return info

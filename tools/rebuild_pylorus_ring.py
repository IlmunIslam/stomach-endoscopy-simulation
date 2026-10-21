"""Rebuild the pyloric ring (funnel, lips, throat, short canal to the bulb) as one clean polar sheet with analytic shape keys.

Why: the old ring was a non-manifold two-sheet lump (84 non-manifold edges): lobed 'volcano' lips when open, spikes inside the tube,
ragged back sheet. Here every old face with centre ax > 0.30 and rad < 0.44 (that is the ring core, old skirt rest, canal, back sheet)
is deleted, and a single sheet is built that starts at the first row of the cover sheet (cover_antrum_front.py, rad 0.087) and ends at
the smoothed bulb hole profile (hole_prof_smooth.npy). Profile per angle: funnel (rim -> lip top), quarter-circle lip, throat that
widens into the canal radius. Three states (Basis half open, Pylorus_Close pursed rosette that protrudes, Pylorus_Open round funnel)
are written to the matching shape keys. Run with the live scene; take a mesh.copy() and a keys .npz first. Never saves.
"""
import bpy, bmesh, numpy as np
import rebuild_pyloric_canal as RC

NT = 240
N_F, N_L, N_T = 12, 6, 14
STATES = {  # r0 aperture radius, rl lip radius, a_lip axial plane of the lip, am lobing, pl pleat amplitude
    'Basis': dict(r0=0.011, rl=0.007, a_lip=0.505, am=0.10, pl=0.004),
    'Pylorus_Close': dict(r0=0.0035, rl=0.005, a_lip=0.520, am=0.06, pl=0.010),
    'Pylorus_Open': dict(r0=0.034, rl=0.012, a_lip=0.490, am=0.12, pl=0.003),
}
ss = lambda x: (lambda y: y * y * (3 - 2 * y))(np.clip(x, 0, 1))


def pt(ax, rho, th):
    ax, rho, th = (np.asarray(x, float)[:, None] for x in (ax, rho, th))
    return RC.C_ + RC.A_ * ax + RC.OFF + rho * (np.cos(th) * RC.E1 + np.sin(th) * RC.E2)


def sheet(S, rim_ax, rim_rho, ths, hole_ax):
    """rows x NT x 3 positions for one state; row 0 is the rim (given)."""
    r_ap = S['r0'] * (1 + S['am'] * (0.6 * np.cos(3 * ths + 0.4) + 0.4 * np.cos(5 * ths + 1.3)))
    rl = S['rl']; a_lip = S['a_lip'] + 0.002 * np.cos(2 * ths + 0.8)
    rho_c = r_ap + rl; ax_top = a_lip + rl
    rows = []
    for k in range(N_F + 1):
        t = k / N_F; rho = rim_rho + (rho_c - rim_rho) * t
        ax = rim_ax + (ax_top - rim_ax) * t ** 1.5
        ax = ax + S['pl'] * np.sin(np.pi * t) * np.cos(7 * ths + 0.7) * (1 - 0.5 * t)
        rho = rho * (1 + 0.04 * S['pl'] / 0.01 * np.sin(np.pi * t) * np.cos(7 * ths + 0.7))
        rows.append(pt(ax, rho, ths) if k else None)
    for m in range(1, N_L + 1):
        phi = np.pi / 2 + (np.pi / 2) * m / N_L
        rows.append(pt(a_lip + rl + rl * (np.sin(phi) - 1), rho_c + rl * np.cos(phi), ths))
    for q in range(1, N_T + 1):
        d = (q / N_T)
        ax = a_lip + (hole_ax - a_lip) * d ** 0.85
        rcan = np.array([RC.canal_radius(float(a), float(t)) for a, t in zip(ax, ths)]) * 1.02
        w = ss((a_lip - ax) / np.maximum(a_lip - 0.39, 1e-6))
        rows.append(pt(ax, r_ap + (rcan - r_ap) * w, ths))
    return rows


def rebuild(hole_prof_path, n_old=20903, cover_nt=NT):
    ant = bpy.data.objects['PART_W5_Antrum']; me = ant.data; names = [k.name for k in me.shape_keys.key_blocks]
    sm = np.load(hole_prof_path); nb = len(sm)
    hole_of = lambda t: np.interp((t + np.pi) / (2 * np.pi) * nb - 0.5, np.arange(-1, nb + 1), np.concatenate([sm[-1:], sm, sm[:1]]))
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    lay = {n: bm.verts.layers.shape[n] for n in names}
    rim = [bm.verts[n_old + j] for j in range(cover_nt)]
    ths = np.linspace(-np.pi, np.pi, cover_nt, endpoint=False)
    cov = set(v for v in bm.verts if v.index >= n_old)
    kill = []
    for f in bm.faces:
        if any(v in cov for v in f.verts): continue
        ax, rad, _ = RC.axrt(f.calc_center_median())
        if ax > 0.30 and rad < 0.44: kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context='FACES_ONLY')
    loose = [v for v in bm.verts if not v.link_faces and v not in cov]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    rows_v = [rim]; per_state = {}
    hole_ax = hole_of(ths)
    for nm in names:
        S = STATES[nm]
        K = np.array([v[lay[nm]] for v in rim]); r = K - RC.C_; ax = r @ RC.A_; q = r - ax[:, None] * RC.A_ - RC.OFF
        per_state[nm] = sheet(S, ax, np.hypot(q @ RC.E1, q @ RC.E2), ths, hole_ax)
    nrows = len(per_state['Basis'])
    for i in range(1, nrows):
        row = []
        for j in range(cover_nt):
            v = bm.verts.new(per_state['Basis'][i][j].tolist())
            for nm in names: v[lay[nm]] = per_state[nm][i][j].tolist()
            row.append(v)
        rows_v.append(row)
    F = []
    for i in range(len(rows_v) - 1):
        for j in range(cover_nt):
            f = bm.faces.new([rows_v[i][j], rows_v[i][(j + 1) % cover_nt], rows_v[i + 1][(j + 1) % cover_nt], rows_v[i + 1][j]])
            f.material_index = 0 if i < N_F else 1; f.smooth = True; F.append(f)
    bm.normal_update()
    # funnel faces must look toward the camera (+axis); flip the whole sheet when they do not
    ref = F[len(F) // 2 % cover_nt]
    flip = sum(np.array(f.normal) @ RC.A_ > 0 for f in F[:cover_nt * (N_F // 2)]) < cover_nt * (N_F // 2) / 2
    if flip: bmesh.ops.reverse_faces(bm, faces=F)
    bm.to_mesh(me); bm.free(); me.update()
    return dict(deleted=len(kill), loose=len(loose), rows=nrows, faces=len(F), flipped=bool(flip))

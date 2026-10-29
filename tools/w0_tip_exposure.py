"""Auto-exposure bake for the endoscope tip light, frames 1..341 (stage 1 of the hypopharynx).

Frames 1..F_JOIN-1 get energy = K * D^2 (D = geometric-mean forward hit distance, 9 rays within +-25 deg, against the scene
meshes), smoothed over +-5 frames like a camera's auto exposure; frames F_JOIN..341 take the old bake (time-warped from
old frames OLD_JOIN..341), so everything from frame 341 on is untouched. Backup of the old action is in
backups_w0/w0_stage1_backup.blend (BK_W0_TipLight_action). Run inside Blender with exec(open(path).read()).
"""
import bpy, numpy as np
from mathutils import Vector

K = 20.0
F_JOIN, OLD_JOIN, F_END = 224, 121, 341
CAP = (6.0, 700.0)
# measured correction from low-res test renders (target mean luminance ~0.36): frame -> multiplier
MULT = [(1, 0.8), (28, 0.8), (50, 0.65), (70, 0.75), (88, 0.9), (104, 0.95), (128, 1.0), (172, 1.0), (186, 0.9), (198, 0.45), (206, 0.3), (214, 0.3), (224, 1.0)]


def fcurves(idb):
    out = []
    for l in idb.animation_data.action.layers:
        for s in l.strips:
            for cb in s.channelbags:
                out += list(cb.fcurves)
    return out


def run():
    sc = bpy.context.scene
    cam = bpy.data.objects['Cam_Endoscope']
    tip = bpy.data.lights['Light_Endoscope_Tip_Data']
    fc = fcurves(tip)[0]
    import os
    npy = os.path.join("E:/works/Blender creations/Stomach all parts/backups_w0", "tip_old_energy.npy")
    if os.path.exists(npy):
        old = np.load(npy)
    else:
        old = np.array([kp.co[1] for kp in fc.keyframe_points])
        np.save(npy, old)
    f0 = sc.frame_current
    names = ['PART_W0_Oropharynx', 'PART_W0_Hypopharynx', 'Esophagus Tube']
    dg = bpy.context.evaluated_depsgraph_get()
    evs = [(bpy.data.objects[n].evaluated_get(dg)) for n in names]
    D = np.zeros(F_JOIN)
    offs = [(0, 0), (0.43, 0), (-0.43, 0), (0, 0.25), (0, -0.25), (0.4, 0.23), (-0.4, 0.23), (0.4, -0.23), (-0.4, -0.23)]
    for f in range(1, F_JOIN + 1):
        sc.frame_set(f)
        mw = cam.matrix_world; o = mw.translation; q = mw.to_quaternion()
        ds = []
        for ox, oy in offs:
            d = (q @ Vector((ox, oy, -1))).normalized()
            best = 30.0
            for ev in evs:
                inv = ev.matrix_world.inverted()
                ok, loc, nrm, idx = ev.ray_cast(inv @ o, (inv.to_3x3() @ d).normalized())
                if ok:
                    best = min(best, (ev.matrix_world @ loc - o).length)
            ds.append(best)
        D[f - 1] = float(np.exp(np.mean(np.log(np.maximum(ds, 0.2)))))  # geometric mean of 9 forward hits
    sc.frame_set(f0)
    E = np.clip(K * np.maximum(D, 0.25) ** 2, *CAP)
    # smooth in log space over +-5 frames
    k = np.ones(11) / 11
    pad = np.r_[np.full(5, E[0]), E, np.full(5, E[-1])]
    Es = np.exp(np.convolve(np.log(pad), k, mode='valid'))[:F_JOIN]
    Es = Es * np.interp(np.arange(1, F_JOIN + 1), [m[0] for m in MULT], [m[1] for m in MULT])
    new = old.copy()
    new[:F_JOIN - 1] = Es[:F_JOIN - 1]
    for f in range(F_JOIN, F_END + 1):
        g = OLD_JOIN + (f - F_JOIN) * (F_END - OLD_JOIN) / (F_END - F_JOIN)
        i0 = int(np.floor(g)); w = g - i0
        new[f - 1] = old[i0 - 1] * (1 - w) + old[min(i0, len(old) - 1)] * w
    # blend over the last 8 frames before F_JOIN
    for j in range(8):
        f = F_JOIN - 8 + j; w = (j + 1) / 9
        new[f - 1] = np.exp(np.log(Es[f - 1]) * (1 - w) + np.log(new[F_JOIN - 1]) * w)
    for f in range(1, F_END + 1):
        kp = fc.keyframe_points[f - 1]
        assert int(round(kp.co[0])) == f
        kp.co[1] = new[f - 1]; kp.handle_left[1] = new[f - 1]; kp.handle_right[1] = new[f - 1]
        kp.interpolation = 'LINEAR'
    fc.update()
    return D, new


D, new = run()
result = {'D_samples': {str(f): round(float(D[f - 1]), 2) for f in (1, 16, 40, 62, 78, 96, 112, 124, 156, 172, 194, 203, 212)},
          'E_samples': {str(f): round(float(new[f - 1]), 1) for f in (1, 16, 40, 62, 78, 96, 112, 124, 156, 172, 194, 203, 212, 230, 300, 341)}}

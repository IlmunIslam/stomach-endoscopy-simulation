"""Stage 1 camera for the hypopharynx: new keys for frames 1..F_JOIN (mouth, tongue, uvula, tip bend, larynx hover,
pyriform/UES passage, first esophagus) and a time warp of the old esophagus keys (old frames 121..341 -> F_JOIN..341) so
that everything from frame 341 on is untouched. Run inside Blender with exec(open(path).read()).

Backups first (rule: datablocks in a side .blend, never deleted without approval):
  backups_w0/w0_stage1_backup.blend  (copies of the camera action and tip light action)
  backups_w0/cam_old_keys.npy        (old camera loc+quat per frame 1..1630)
"""
import bpy, os, numpy as np
from mathutils import Vector, Matrix, Quaternion

ROOT = r"E:\works\Blender creations\Stomach all parts\backups_w0"
F_JOIN = 212
OLD_JOIN = 121
F_END = 341

WP = [  # frame, (x, y, z), pitch deg, yaw deg, roll deg, hold
    (1,   (13.45, 9.8, 71.6), 6, 0, 0, True),
    (16,  (13.45, 9.6, 71.6), 6, 0, 0, True),
    (40,  (13.50, 5.5, 71.5), 9, -2, 0, False),
    (62,  (13.45, 0.5, 71.9), 4, 2, 0, False),
    (78,  (13.45, -2.3, 71.8), 8, 0, 0, False),
    (96,  (13.45, -4.4, 71.2), 38, 0, 0, False),
    (112, (13.45, -5.7, 70.2), 78, 0, 0, False),
    (124, (13.50, -6.5, 69.3), 90, 0, 0, True),
    (156, (13.50, -6.7, 68.7), 90, 0, 0, True),
    (172, (13.45, -7.5, 67.6), 90, 0, 0, False),
    (186, (13.40, -7.9, 66.6), 90, 0, 0, False),
    (194, (13.40, -7.9, 66.2), 90, 0, 0, True),
    (203, (13.45, -7.9, 65.0), 90, 0, 0, False),
]


def fcurves(idb):
    out = []
    for l in idb.animation_data.action.layers:
        for s in l.strips:
            for cb in s.channelbags:
                out += list(cb.fcurves)
    return out


def get_curves(ob):
    d = {}
    for fc in fcurves(ob):
        d[(fc.data_path, fc.array_index)] = fc
    return d


def hermite(t, t0, t1, p0, p1, m0, m1):
    h = t1 - t0; s = (t - t0) / h
    h00 = 2 * s**3 - 3 * s**2 + 1; h10 = s**3 - 2 * s**2 + s; h01 = -2 * s**3 + 3 * s**2; h11 = s**3 - s**2
    return h00 * p0 + h10 * h * m0 + h01 * p1 + h11 * h * m1


def waypoint_track(frames):
    wf = np.array([w[0] for w in WP], float)
    vals = np.array([list(w[1]) + [w[2], w[3], w[4]] for w in WP], float)
    hold = [w[5] for w in WP]
    n = len(WP)
    tang = np.zeros_like(vals)
    for i in range(n):
        if hold[i]:
            continue
        a = max(i - 1, 0); b = min(i + 1, n - 1)
        tang[i] = (vals[b] - vals[a]) / (wf[b] - wf[a])
    out = []
    for f in frames:
        i = min(max(np.searchsorted(wf, f, side='right') - 1, 0), n - 2)
        out.append(hermite(f, wf[i], wf[i + 1], vals[i], vals[i + 1], tang[i], tang[i + 1]))
    return np.array(out)


def pose_quat(pitch, yaw, roll):
    a, b, g = np.radians([pitch, yaw, roll])
    f = np.array([0, -np.cos(a), -np.sin(a)]); u = np.array([0, np.sin(a), -np.cos(a)])
    cy, sy = np.cos(b), np.sin(b)
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    f, u = Rz @ f, Rz @ u
    cg, sg = np.cos(g), np.sin(g)
    u = u * cg + np.cross(f, u) * sg
    x = np.cross(f, u)
    m = Matrix(((x[0], u[0], -f[0]), (x[1], u[1], -f[1]), (x[2], u[2], -f[2])))
    return m.to_quaternion()


def run(write=True):
    os.makedirs(ROOT, exist_ok=True)
    cam = bpy.data.objects['Cam_Endoscope']
    cur = get_curves(cam)
    keys = [('location', 0), ('location', 1), ('location', 2), ('rotation_quaternion', 0), ('rotation_quaternion', 1),
            ('rotation_quaternion', 2), ('rotation_quaternion', 3)]
    n_old = len(cur[keys[0]].keyframe_points)
    old = np.array([[cur[k].keyframe_points[i].co[1] for k in keys] for i in range(n_old)])
    bk = os.path.join(ROOT, 'w0_stage1_backup.blend')
    if write and not os.path.exists(bk):
        np.save(os.path.join(ROOT, 'cam_old_keys.npy'), old)
        a1 = cam.animation_data.action.copy(); a1.name = 'BK_W0_Cam_Endoscope_action'
        tip = bpy.data.objects['Light_Endoscope_Tip'].data
        a2 = tip.animation_data.action.copy(); a2.name = 'BK_W0_TipLight_action'
        a1.use_fake_user = True; a2.use_fake_user = True
        bpy.data.libraries.write(bk, {a1, a2}, fake_user=True)
        bpy.data.actions.remove(a1); bpy.data.actions.remove(a2)

    frames = np.arange(1, F_END + 1)
    new = np.zeros((len(frames), 7))
    wf = frames[frames <= 203]
    tr = waypoint_track(wf)
    for k, f in enumerate(wf):
        new[k, :3] = tr[k, :3]
        q = pose_quat(*tr[k, 3:6])
        new[k, 3:] = [q.w, q.x, q.y, q.z]
    # old esophagus part, time-warped, plus blend frames 203..F_JOIN
    def old_at(g):
        g = min(max(g, 1), n_old)
        i0 = int(np.floor(g)); i1 = min(i0 + 1, n_old); w = g - i0
        v = old[i0 - 1] * (1 - w) + old[i1 - 1] * w
        v[3:] /= np.linalg.norm(v[3:])
        return v
    for k, f in enumerate(frames):
        if f <= 203:
            continue
        if f < F_JOIN:
            w = (f - 203) / (F_JOIN - 203); w = w * w * (3 - 2 * w)
            a = np.r_[tr[len(wf) - 1][:3], [pose_quat(*tr[len(wf) - 1][3:6]).w, *list(pose_quat(*tr[len(wf) - 1][3:6]))[1:]]]
            b = old_at(OLD_JOIN)
            v = a * (1 - w) + b * w; v[3:] /= np.linalg.norm(v[3:])
            new[k] = v
        else:
            g = OLD_JOIN + (f - F_JOIN) * (F_END - OLD_JOIN) / (F_END - F_JOIN)
            new[k] = old_at(g)
    # keep quaternion sign continuous
    for k in range(1, len(new)):
        if np.dot(new[k, 3:], new[k - 1, 3:]) < 0:
            new[k, 3:] *= -1
    if write:
        for c, key in enumerate(keys):
            fc = cur[key]
            for k, f in enumerate(frames):
                kp = fc.keyframe_points[f - 1]
                assert int(round(kp.co[0])) == f
                kp.co[1] = new[k, c]
                kp.handle_left[1] = new[k, c]; kp.handle_right[1] = new[k, c]
                kp.interpolation = 'LINEAR'
            fc.update()
        bpy.context.scene.frame_set(bpy.context.scene.frame_current)
    return new


res = run(write=True)
result = {'frames_written': int(len(res)), 'sample': {str(f): [round(float(x), 3) for x in res[f - 1][:3]] for f in (1, 40, 96, 124, 156, 194, 212, 341)}}

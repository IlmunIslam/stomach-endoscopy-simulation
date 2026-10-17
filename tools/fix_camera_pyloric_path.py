"""Re-author Cam_Endoscope's baked keys around the pylorus (frames ~481-1150) in the live scene. Never saves.

Problems found by measuring (docs/LESSONS.md / PLAYBOOK 12):
 * Roll: from frame ~521 to ~921 the camera's roll is ~165 deg, i.e. world +Z shows on screen as DOWN. The pylorus is higher
   (world +Z) than the approach path, so the ring appeared below the centre of the view.
 * Passage: the camera crosses the pyloric aperture/tube with 0.06-0.6 world units of radial offset, but the tube's narrowest
   lumen radius is ~0.028 world (0.012 local), so it flew through the walls (and the ring was halved after the original path
   was made). The return pass had the same problem (radial 0.14-0.24 at the aperture).

Fix (all as per-frame values written into the existing location / rotation_quaternion F-curves; interpolation stays LINEAR):
 * roll = 0 (world +Z up on screen) for frames ROLL_FROM..ROLL_TO, blending back to the original roll afterwards;
 * approach: the camera's axial progress s(f) along the pyloric axis u is kept (timing, dwell frames 780-840 unchanged) but it
   is placed BELOW the axis by h(s) (ring appears above centre), h = 0.16*|s| far away, easing to 0 by s = -0.3, so the
   camera rises to the axis just before the aperture, then follows the lumen centreline through aperture and tube;
 * tube: forward = +u (out) or -u (back) and radial offset 0 in the windows OUT_IN..OUT_OUT and BACK_IN..BACK_OUT, with smooth
   blends to the original path before and after.
Frame numbers: out crossing aperture ~863, mouth ~881; back mouth ~1039, aperture ~1061 (measured from the original keys).
"""
import bpy, numpy as np
from mathutils import Matrix, Vector, Quaternion

ROLL_FROM, ROLL_FULL, ROLL_TO, ROLL_FADE = 486, 620, 1110, 40   # forward points straight down at frame ~490: roll is eased in AFTER it, not flipped
OUT_BLEND_IN, OUT_IN, OUT_OUT, OUT_BLEND_OUT = 640, 700, 881, 910
BACK_BLEND_IN, BACK_IN, BACK_OUT, BACK_BLEND_OUT = 1010, 1030, 1070, 1100
H_K, H_END = 0.16, -0.3


def ss(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def geometry():
    ant = bpy.data.objects['PART_W5_Antrum']; W = ant.matrix_world
    a = np.array([1.0, 0.006, -0.016]); a /= np.linalg.norm(a); c = np.array([-0.447, 0.079, 0.599])
    e1 = np.cross(a, [0, 0, 1.0]); e1 /= np.linalg.norm(e1); e2 = np.cross(a, e1)
    off = -0.003 * e1 + 0.007 * e2                         # measured lumen centre offset from the axis line
    Aloc = c + a * 0.47 + off; Mloc = c + off
    A = np.array(W @ Vector(Aloc)); M = np.array(W @ Vector(Mloc)); u = M - A; L = float(np.linalg.norm(u)); u /= L
    return A, u, L


def curves(cam):
    out = {}
    for l in cam.animation_data.action.layers:
        for s in l.strips:
            for cb in s.channelbags:
                for f in cb.fcurves: out[(f.data_path, f.array_index)] = f
    return out


def read(cam):
    fc = curves(cam); n = len(fc[('location', 0)].keyframe_points)
    pos = np.array([[fc[('location', i)].keyframe_points[k].co[1] for i in range(3)] for k in range(n)])
    q = np.array([[fc[('rotation_quaternion', i)].keyframe_points[k].co[1] for i in range(4)] for k in range(n)])
    return fc, pos, q


def basis(fw, up_ref=np.array([0, 0, 1.0])):
    fw = fw / np.linalg.norm(fw); r = np.cross(fw, up_ref); r /= np.linalg.norm(r); up = np.cross(r, fw)
    return r, up, -fw


def quat_from_fw(fw):
    r, up, back = basis(fw)
    return Matrix(((r[0], up[0], back[0]), (r[1], up[1], back[1]), (r[2], up[2], back[2]))).to_quaternion()


def fw_of(q):
    return np.array(Quaternion(q).to_matrix() @ Vector((0, 0, -1)))


def roll_of(q):
    m = np.array(Quaternion(q).to_matrix()); fw = -m[:, 2]; rt = m[:, 0]; up = m[:, 1]
    zp = np.array([0, 0, 1.0]); zp = zp - (zp @ fw) * fw; nz = np.linalg.norm(zp)
    if nz < 0.15: return None
    zp /= nz; return float(np.degrees(np.arctan2(zp @ rt, zp @ up)))


def plan():
    cam = bpy.context.scene.camera; fc, P0, Q0 = read(cam); n = len(P0)
    A, u, L = geometry()
    zdir = np.array([0, 0, 1.0]); zp = zdir - (zdir @ u) * u; zp /= np.linalg.norm(zp)    # screen-up direction when facing along the axis
    P = P0.copy(); Q = Q0.copy()
    s0 = (P0 - A) @ u
    fw0 = np.array([fw_of(q) for q in Q0])
    # 1) roll-corrected original orientation: rotate the ORIGINAL orientation about its own forward axis by -w*roll, with the roll
    #    unwrapped (continuous) while it is eased in, so there is no flip and no slerp shortcut through 180 degrees.
    rollU = np.zeros(n); last = 0.0
    seg = [f for f in range(494, 701)]
    raw = []
    for f in seg:
        r = roll_of(Q0[f - 1]); raw.append(np.radians(r if r is not None else np.degrees(raw[-1]) if raw else 0.0))
    un = np.degrees(np.unwrap(np.array(raw)))
    for f in range(1, n + 1):
        if f < 494: v = un[0]
        elif f <= 700: v = un[f - 494]
        else:
            r = roll_of(Q0[f - 1]); v = r if r is not None else last
        rollU[f - 1] = v; last = v
    Qr = Q0.copy()
    for f in range(ROLL_FROM, ROLL_TO + 40):
        i = f - 1
        w = ss((f - ROLL_FROM) / (ROLL_FULL - ROLL_FROM)) if f < ROLL_FULL else (1.0 if f <= ROLL_TO else 1 - ss((f - ROLL_TO) / ROLL_FADE))
        Qr[i] = np.array(Quaternion(Q0[i]) @ Quaternion((0, 0, 1), np.radians(-w * rollU[i])))
    # 2) outbound path
    def hfun(s):
        if s >= H_END: return 0.0
        if s <= -1.0: return H_K * (-s)
        return H_K * 1.0 * (1 - ss((s + 1.0) / (H_END + 1.0)))
    for f in range(OUT_BLEND_IN, OUT_BLEND_OUT + 1):
        i = f - 1; s = s0[i]
        pos_tube = A + u * s - zp * hfun(min(s, 0.0))                       # on/below the axis, centreline once inside
        wp = ss((f - OUT_BLEND_IN) / (OUT_IN - OUT_BLEND_IN)) if f < OUT_IN else (1.0 if f <= OUT_OUT else 1 - ss((f - OUT_OUT) / (OUT_BLEND_OUT - OUT_OUT)))
        P[i] = P0[i] * (1 - wp) + pos_tube * wp
        wq = ss((f - 700) / 22.0) if f < 722 else (1.0 if f <= OUT_OUT else 1 - ss((f - OUT_OUT) / (OUT_BLEND_OUT - OUT_OUT)))
        qa = Quaternion(Qr[i]); qb = quat_from_fw(u)
        if qa.dot(qb) < 0: qb.negate()
        Q[i] = np.array(qa.slerp(qb, wq))
    # 3) return path
    for f in range(BACK_BLEND_IN, BACK_BLEND_OUT + 1):
        i = f - 1; s = s0[i]
        pos_tube = A + u * s
        if f < BACK_IN: wp = ss((f - BACK_BLEND_IN) / (BACK_IN - BACK_BLEND_IN))
        elif f <= BACK_OUT: wp = 1.0
        else: wp = 1 - ss((f - BACK_OUT) / (BACK_BLEND_OUT - BACK_OUT))
        # camera is exactly on the centreline only while s in the tube; leaving through the aperture it eases to the original
        P[i] = P0[i] * (1 - wp) + pos_tube * wp
        qa = Quaternion(Qr[i]); qb = quat_from_fw(-u)
        if qa.dot(qb) < 0: qb.negate()
        Q[i] = np.array(qa.slerp(qb, wp))
    # frames with only the roll fix (no tube blend) keep their roll-corrected quaternion
    for f in range(ROLL_FROM, ROLL_TO + 40):
        i = f - 1
        if not (OUT_BLEND_IN <= f <= OUT_BLEND_OUT or BACK_BLEND_IN <= f <= BACK_BLEND_OUT): Q[i] = Qr[i]
    # quaternion sign continuity
    for i in range(ROLL_FROM, ROLL_TO + 60):
        if np.dot(Q[i], Q[i - 1]) < 0: Q[i] = -Q[i]
    return dict(fc=fc, P0=P0, Q0=Q0, P=P, Q=Q, A=A, u=u, L=L, s0=s0)


def apply(pl):
    fc = pl['fc']
    for k in range(len(pl['P'])):
        for i in range(3): fc[('location', i)].keyframe_points[k].co[1] = float(pl['P'][k][i])
        for i in range(4): fc[('rotation_quaternion', i)].keyframe_points[k].co[1] = float(pl['Q'][k][i])
    for f in fc.values(): f.update()


if __name__ == '__main__' or True:
    pass   # usage in the live session: pl = plan(); apply(pl)  (originals saved beforehand to %TEMP%\antrum_fix\cam\cam_backup_original.npz)

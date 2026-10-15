"""One-shot: close the Antrum notch, flatten the Stomach spike region, snap the Stomach hole rim onto the Antrum surface.
Usage (inside Blender): exec(open('tools/fix_stomach_antrum.py').read()); run(region_idx_npy, backup_npy)
"""
import bpy, numpy as np, os
_T = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else r"E:\works\Blender creations\Stomach all parts\tools"


def _load(name):
    ns = {}; exec(open(os.path.join(_T, name)).read(), ns); return ns


def run(region_idx_npy, backup_npy=None):
    bpy.context.scene.frame_set(732)
    out = {"weld": _load("weld_antrum_slit.py")["run"]()}
    me = bpy.data.objects["Stomach"].data
    reg = np.zeros(len(me.vertices), bool); reg[np.load(region_idx_npy)] = True
    out["membrane"] = _load("clean_spikes_no_gap.py")["run"](reg, backup_path=backup_npy)[0]
    return out

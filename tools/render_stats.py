"""Numeric image statistics. Prints numbers only.

Usage:
    blender -b --factory-startup --python tools/render_stats.py -- <image_path>

Luminance is Rec.709 weights on the image's stored (display-referred) pixel
values, in 0..1. Fireflies = pixels whose luminance exceeds 4x the brightest of
their 8 neighbours and is at least 0.5.
"""
import os
import sys

import bpy
import numpy as np


def stats(path):
    path = os.path.abspath(path)
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    lum = 0.2126 * px[..., 0] + 0.7152 * px[..., 1] + 0.0722 * px[..., 2]
    p1, p50, p99, p999 = np.percentile(lum, [1, 50, 99, 99.9])
    pad = np.pad(lum, 1, mode="edge")
    neigh = np.stack([pad[y:y + h, x:x + w] for y in range(3) for x in range(3) if (y, x) != (1, 1)])
    fire = (lum >= 0.5) & (lum > 4.0 * neigh.max(axis=0))
    out = {
        "width": int(w), "height": int(h),
        "mean_luminance": float(lum.mean()),
        "p1": float(p1), "p50": float(p50), "p99": float(p99), "p99_9": float(p999),
        "share_ge_0.98": float((lum >= 0.98).mean()),
        "share_le_0.02": float((lum <= 0.02).mean()),
        "firefly_proxy_count": int(fire.sum()),
        "file_size_bytes": os.path.getsize(path),
    }
    bpy.data.images.remove(img)
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not argv:
        print("usage: blender -b --python tools/render_stats.py -- <image_path>")
        return
    for k, v in stats(argv[0]).items():
        print("{}: {}".format(k, round(v, 6) if isinstance(v, float) else v))


main()

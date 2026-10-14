"""Post lab: apply endoscope-style camera/sensor looks to an existing frame.

Usage:
    blender -b --factory-startup --python tools/post_lab.py -- <input> <outdir>

Writes <outdir>/<input stem>/{original,A_subtle,B_balanced,C_strong_mask}.png and
sheet.png (original | A | B | C at the same scale), plus C_round, C_round_small and
sheet_round.png (original | C | C_round | C_round_small) when those presets exist. Prints numbers only.
Presets live in tools/post_lab_presets.json. Standalone: it does not touch any
scene or .blend; Blender is used only for image I/O, numpy for the maths.

Pipeline (linear light unless noted):
 1 barrel distortion (k1, k2, bilinear, auto-scaled so no empty corners)
 2 vignette  3 highlight bloom  4 sensor noise (seeded from the file name)
 5 unsharp mask  -> sRGB encode -> 6 S-curve -> highlight ceiling -> 7 mask (C only)
Metrics use Rec.709 weights on the stored (sRGB-encoded) 8-bit values.
"""
import ctypes
import json
import os
import sys
import time
import zlib
from ctypes import wintypes

import bpy
import numpy as np

W709 = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


# ---------------------------------------------------------------- colour
def srgb_to_linear(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(np.float32)


def linear_to_srgb(x):
    x = np.clip(x, 0.0, None)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055).astype(np.float32)


def lum(a):
    return a @ W709


# ---------------------------------------------------------------- image I/O
def load_image(path):
    img = bpy.data.images.load(path, check_existing=False)
    img.colorspace_settings.name = "Non-Color"  # raw stored values, no conversion
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)[..., :3].copy()  # rows are bottom-up; all ops are symmetric


def save_image(path, rgb):
    h, w, _ = rgb.shape
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=False, float_buffer=False)
    img.colorspace_settings.name = "Non-Color"
    out = np.ones((h, w, 4), dtype=np.float32)
    out[..., :3] = rgb
    img.pixels.foreach_set(out.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def quantize(a):
    return np.round(np.clip(a, 0, 1) * 255.0).astype(np.float32) / 255.0


def metrics(enc):
    y = lum(enc)
    return float(y.mean()), float((y >= 0.98).mean())


# ---------------------------------------------------------------- operations
def bilinear(img, sx, sy):
    h, w, _ = img.shape
    sx = np.clip(sx, 0, w - 1.0001)
    sy = np.clip(sy, 0, h - 1.0001)
    x0 = sx.astype(np.int32)
    y0 = sy.astype(np.int32)
    fx = (sx - x0)[..., None]
    fy = (sy - y0)[..., None]
    top = img[y0, x0] * (1 - fx) + img[y0, x0 + 1] * fx
    bot = img[y0 + 1, x0] * (1 - fx) + img[y0 + 1, x0 + 1] * fx
    return (top * (1 - fy) + bot * fy).astype(np.float32)


def coords(h, w):
    """Normalised coords in units of the half-diagonal; returns dx, dy, r, and the half extents."""
    R = 0.5 * np.hypot(w, h)
    xs = (np.arange(w, dtype=np.float32) + 0.5 - w / 2) / R
    ys = (np.arange(h, dtype=np.float32) + 0.5 - h / 2) / R
    dx, dy = np.meshgrid(xs, ys)
    return dx, dy, np.sqrt(dx * dx + dy * dy), (w / 2) / R, (h / 2) / R, R


def barrel(img, k1, k2, zoom=None):
    h, w, _ = img.shape
    dx, dy, r, hw, hh, R = coords(h, w)
    if zoom is not None:
        g = 1 + k1 * r ** 2 + k2 * r ** 4
        return bilinear(img, dx * zoom * g * R + w / 2 - 0.5, dy * zoom * g * R + h / 2 - 0.5)
    if k1 == 0 and k2 == 0:
        return img
    # border samples decide the zoom so that every output pixel samples inside the source
    t = np.linspace(-1, 1, 1024, dtype=np.float32)
    bx = np.concatenate([t * hw, t * hw, np.full_like(t, hw), np.full_like(t, -hw)])
    by = np.concatenate([np.full_like(t, hh), np.full_like(t, -hh), t * hh, t * hh])
    br = np.sqrt(bx * bx + by * by)
    g = 1 + k1 * br ** 2 + k2 * br ** 4
    s = float(np.min(np.minimum(hw / (np.abs(bx * g) + 1e-9), hh / (np.abs(by * g) + 1e-9))))
    s = min(s, 1.0)
    g = 1 + k1 * r ** 2 + k2 * r ** 4
    sx = dx * s * g * R + w / 2 - 0.5
    sy = dy * s * g * R + h / 2 - 0.5
    return bilinear(img, sx, sy)


def vignette(img, strength, power):
    h, w, _ = img.shape
    r = coords(h, w)[2]
    gain = 1.0 - strength * np.clip(r, 0, 1) ** power
    return img * gain[..., None]


def box_sizes(sigma, n=3):
    wi = np.sqrt(12 * sigma * sigma / n + 1)
    wl = int(np.floor(wi))
    if wl % 2 == 0:
        wl -= 1
    wu = wl + 2
    m = int(round((12 * sigma * sigma - n * wl * wl - 4 * n * wl - 3 * n) / (-4 * wl - 4)))
    return [wl if i < m else wu for i in range(n)]


def box_axis(a, size, axis):
    r = size // 2
    if r < 1:
        return a
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r + 1, r)
    p = np.pad(a, pad, mode="edge").astype(np.float64)
    c = np.cumsum(p, axis=axis)
    n = a.shape[axis]
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return ((hi - lo) / (2 * r + 1)).astype(np.float32)


def gauss(a, sigma):
    if sigma < 0.4:
        return a
    for size in box_sizes(sigma):
        a = box_axis(box_axis(a, size, 0), size, 1)
    return a


def bloom(img, threshold, sigmas, weights, intensity):
    h = img.shape[0]
    excess = np.maximum(img - threshold, 0.0)
    acc = np.zeros_like(img)
    for s, wt in zip(sigmas, weights):
        acc += wt * gauss(excess, s * h)
    return img + intensity * acc


def noise(img, name, shot_gain, read_std, luma_w, chroma_w):
    rng = np.random.default_rng(zlib.crc32(name.encode("utf-8")))
    h, w, _ = img.shape
    n_l = rng.standard_normal((h, w, 1), dtype=np.float32)
    n_c = rng.standard_normal((h, w, 3), dtype=np.float32)
    n_c -= n_c.mean(axis=2, keepdims=True)  # chroma noise carries no luminance
    std = np.sqrt(shot_gain * np.clip(lum(img), 0, None) + read_std ** 2)[..., None]
    return np.clip(img + std * (luma_w * n_l + chroma_w * n_c), 0, None)


def sharpen(img, sigma, amount):
    y = lum(img)[..., None]
    detail = y - gauss(y, sigma)
    return img + amount * detail


def s_curve(enc, amount):
    return enc - amount * np.sin(2 * np.pi * enc) / (2 * np.pi)  # monotonic for amount < 1


def ceiling(enc, ceil):
    """Soft-knee cap on luminance (hue-preserving) so no highlight exceeds `ceil`."""
    y = lum(enc)
    k = 0.8 * ceil
    over = y > k
    yc = np.where(over, k + (ceil - k) * np.tanh((y - k) / max(ceil - k, 1e-6)), y)
    return enc * (yc / np.maximum(y, 1e-6))[..., None]


def rounded_mask(h, w, mx, my, radius, feather):
    cx, cy = w / 2, h / 2
    hx = w / 2 - mx * w
    hy = h / 2 - my * h
    rad = radius * min(w, h)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    qx = np.abs(xs + 0.5 - cx) - (hx - rad)
    qy = np.abs(ys + 0.5 - cy) - (hy - rad)
    d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - rad
    return np.clip(0.5 - d / max(feather, 1e-3), 0, 1).astype(np.float32)[..., None]


def circle_zoom(h, w, k1, k2, diameter, feather, border):
    """Largest zoom (<=1) at which every sample for pixels inside the circle (plus feather) stays in the source."""
    R = 0.5 * np.hypot(w, h)
    rad = diameter / 2 + feather / 2
    a = np.linspace(0, 2 * np.pi, 8192, dtype=np.float64)
    bx, by = rad * np.cos(a), rad * np.sin(a)
    br = np.hypot(bx, by) / R
    g = 1 + k1 * br ** 2 + k2 * br ** 4
    sx = np.abs(bx) * g / (w / 2 - border)
    sy = np.abs(by) * g / (h / 2 - border)
    return float(min(1.0, 1.0 / max(sx.max(), sy.max())))


def circle_masks(h, w, diameter, feather):
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.hypot(xs + 0.5 - w / 2, ys + 0.5 - h / 2) - diameter / 2
    soft = np.clip(0.5 - d / max(feather, 1e-3), 0, 1).astype(np.float32)[..., None]
    return soft, d <= 0


def run_round(enc_in, name, p):
    h, w, _ = enc_in.shape
    m, ex = p["mask"], p["exposure_match"]
    diameter = m["diameter_frac_of_height"] * h
    soft, inside = circle_masks(h, w, diameter, m["feather_px"])
    zoom = circle_zoom(h, w, p["distortion"]["k1"], p["distortion"]["k2"], diameter, m["feather_px"], p["zoom"]["border_px"])
    y_in = lum(enc_in)
    mean_in, share_in = float(y_in[inside].mean()), float((y_in[inside] >= 0.98).mean())
    in_max = float(y_in[inside].max())
    lin = barrel(srgb_to_linear(enc_in), p["distortion"]["k1"], p["distortion"]["k2"], zoom)
    lin = vignette(lin, p["vignette"]["strength"], p["vignette"]["power"])
    b = p["bloom"]
    lin = bloom(lin, b["threshold_linear"], b["sigmas"], b["weights"], b["intensity"])
    n = p["noise"]
    lin = noise(lin, name, n["shot_gain"], n["read_std"], n["luma_weight"], n["chroma_weight"])
    lin = sharpen(lin, p["sharpen"]["sigma_px"], p["sharpen"]["amount"])
    enc = s_curve(np.clip(np.clip(linear_to_srgb(lin), 0, None), 0, 1), p["s_curve"]["amount"])
    ceil = min(in_max if share_in > 0 else min(in_max, 0.975), 1.0)

    def build(gain, c):
        return quantize(np.clip(ceiling(enc * gain, c), 0, 1) * soft)

    lo, hi = ex["gain_search"]
    for _ in range(ex["iterations"]):  # bisection on a monotone mean
        mid = np.sqrt(lo * hi)
        if lum(build(mid, ceil))[inside].mean() < mean_in:
            lo = mid
        else:
            hi = mid
    gain = float(np.sqrt(lo * hi))
    out = build(gain, ceil)
    while (float((lum(out)[inside] >= 0.98).mean()) > share_in + 1e-12 or float(lum(out).max()) > in_max) and ceil > 0.3:
        ceil -= 0.001
        out = build(gain, ceil)
    y_out = lum(out)
    return out, dict(zoom=zoom, gain=gain, ceil=ceil, mean_in=mean_in, share_in=share_in,
                     mean_out=float(y_out[inside].mean()), share_out=float((y_out[inside] >= 0.98).mean()),
                     max_in=in_max, max_out=float(y_out.max()),
                     outside_max=float(out[~inside & (soft[..., 0] == 0)].max()) if (~inside & (soft[..., 0] == 0)).any() else 0.0)


# ---------------------------------------------------------------- pipeline
def run_preset(enc_in, name, p, share_in, in_max):
    lin = srgb_to_linear(enc_in)
    lin = barrel(lin, p["distortion"]["k1"], p["distortion"]["k2"])
    lin = vignette(lin, p["vignette"]["strength"], p["vignette"]["power"])
    b = p["bloom"]
    lin = bloom(lin, b["threshold_linear"], b["sigmas"], b["weights"], b["intensity"])
    n = p["noise"]
    lin = noise(lin, name, n["shot_gain"], n["read_std"], n["luma_weight"], n["chroma_weight"])
    lin = sharpen(lin, p["sharpen"]["sigma_px"], p["sharpen"]["amount"])
    enc = np.clip(linear_to_srgb(lin), 0, None)
    enc = s_curve(np.clip(enc, 0, 1), p["s_curve"]["amount"])
    m = p["mask"]
    mask = rounded_mask(*enc.shape[:2], m["margin_x"], m["margin_y"], m["corner_radius"], m["feather_px"]) if m.get("enabled") else None
    # highlight ceiling: never more clipped highlights than the input
    ceil = max(in_max, 0.5) if share_in > 0 else min(in_max, 0.975)
    ceil = min(ceil, 1.0)
    out = None
    for _ in range(40):
        out = np.clip(ceiling(enc, ceil), 0, 1)
        if mask is not None:
            out = out * mask
        out = quantize(out)
        if metrics(out)[1] <= share_in + 1e-12:
            break
        ceil -= 0.005
    return out, ceil


def peak_working_set_mib():
    class PMC(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    ps = ctypes.WinDLL("psapi", use_last_error=True)
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    ps.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
    pmc = PMC()
    pmc.cb = ctypes.sizeof(pmc)
    ps.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb)
    return pmc.PeakWorkingSetSize / 2 ** 20, pmc.WorkingSetSize / 2 ** 20


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) < 2:
        print("usage: blender -b --factory-startup --python tools/post_lab.py -- <input> <outdir>")
        return
    src, outroot = os.path.abspath(argv[0]), os.path.abspath(argv[1])
    stem = os.path.splitext(os.path.basename(src))[0]
    outdir = os.path.join(outroot, stem)
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
    presets = json.load(open(os.path.join(here, "post_lab_presets.json"), encoding="utf-8"))

    enc_in = quantize(load_image(src))
    mean_in, share_in = metrics(enc_in)
    in_max = float(lum(enc_in).max())
    print("input {} {}x{} mean_lum={:.4f} share_ge_0.98={:.6f} max_lum={:.4f}".format(
        stem, enc_in.shape[1], enc_in.shape[0], mean_in, share_in, in_max))
    save_image(os.path.join(outdir, "original.png"), enc_in)
    tiles = [enc_in]
    for key in ("A", "B", "C"):
        p = presets[key]
        t0 = time.perf_counter()
        out, ceil = run_preset(enc_in, os.path.basename(src), p, share_in, in_max)
        t1 = time.perf_counter()
        save_image(os.path.join(outdir, "{}_{}.png".format(key, p["name"])), out)
        t2 = time.perf_counter()
        mean_o, share_o = metrics(out)
        print("preset {} ({}) process_s={:.2f} save_s={:.2f} mean_lum={:.4f} share_ge_0.98={:.6f} ceiling={:.3f}".format(
            key, p["name"], t1 - t0, t2 - t1, mean_o, share_o, ceil))
        tiles.append(out)
    save_image(os.path.join(outdir, "sheet.png"), np.concatenate(tiles, axis=1))
    round_tiles = [enc_in, tiles[3]]
    for key in ("C_round", "C_round_small"):
        if key not in presets:
            continue
        p = presets[key]
        t0 = time.perf_counter()
        out, info = run_round(enc_in, os.path.basename(src), p)
        t1 = time.perf_counter()
        save_image(os.path.join(outdir, key + ".png"), out)
        t2 = time.perf_counter()
        print("preset {} process_s={:.2f} save_s={:.2f} zoom={:.4f} gain={:.3f} ceiling={:.3f} circle_mean_in={:.4f} circle_mean_out={:.4f} "
              "circle_share_ge_0.98_in={:.6f} out={:.6f} circle_max_in={:.4f} out={:.4f} outside_max_value={:.4f}".format(
                  key, t1 - t0, t2 - t1, info["zoom"], info["gain"], info["ceil"], info["mean_in"], info["mean_out"],
                  info["share_in"], info["share_out"], info["max_in"], info["max_out"], info["outside_max"]))
        round_tiles.append(out)
    if len(round_tiles) > 2:
        save_image(os.path.join(outdir, "sheet_round.png"), np.concatenate(round_tiles, axis=1))
    peak, cur = peak_working_set_mib()
    print("process peak_working_set_MiB={:.0f} working_set_MiB={:.0f}".format(peak, cur))


main()

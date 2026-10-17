"""Round 5 helpers recorded from the live session (never saves).

1. Pylorus_Motion keys: ring CLOSED from frame 1 until the camera is close, and closed again after the camera has left.
   Pylorus_Open  = [(1,0),(700,0),(755,0),(772,0),(782,0),(793,0),(803,.3),(813,.3),(823,0),(833,0),(843,.55),(852,1),(885,1),(930,.55),(1040,.55),(1060,.85),(1085,.2),(1100,0),(1630,0)]
   Pylorus_Close = [(1,1),(700,1),(755,1),(772,1),(782,1),(793,1),(803,0),(813,0),(823,1),(833,1),(843,0),(852,0),(885,0),(930,0),(1040,0),(1060,0),(1085,.6),(1100,1),(1630,1)]
   (the old 755-772 half-open pulse was removed; later pulses and the fully open window 852-885 are unchanged). Originals: %TEMP%\antrum_fix\r4\pyl_keys_backup.pkl
2. Camera 'outside the skin' (frames ~1094-1136): the original path left the Stomach wall (signed distance to the closest Stomach
   face > 0 up to 0.4). Fix = per-frame displacement along -normal so the signed distance stays <= -0.35, gaussian-smoothed (sigma 4)
   and tapered over 8 frames at both ends of frames 1076-1146 (max shift 0.8 world, max step 0.088/frame). Positions only.
   Originals: %TEMP%\antrum_fix\r4\cam_before_skin_fix.npz
3. Canal/bulb: tools/rebuild_pyloric_canal.py (rebuild_tube, close_bulb_hole) followed by:
   * flip the new canal faces (they come out facing away from the axis; the old ones face inward),
   * channel faces (ax 0.14-0.415, radius < 0.03) -> material slot 0 so there is no white/red seam line,
   * implicit smoothing of the channel end (ax 0.355-0.43, t=3, clamp 0.006) in every shape key,
   * bulb: three relax passes around the collar (ax -0.16..0.06, rad 0.06-0.28; t=8 / 25 / 80, hops 3-4, clamp 0.06-0.12).
"""

"""Shorten the way from the pyloric ring to the duodenal bulb, bring the camera closer to the ring and add auto-exposure (live scene, never saves).

Order used (2026-10-22), each step with a mesh/npz backup first:
 1. Move PART_9_Duodenal bulb 0.15 local units (0.355 world) toward the ring: location -= u * 0.15 * antrum.scale (u from fix_camera_pyloric_path.geometry()).
 2. Re-fit the bulb's hole edge: smooth its axial profile around the circle (gaussian, 72 bins) and put the edge on the canal wall
    (canal_point at the smoothed ax, radius canal_radius * 1.02), harmonic-smoothed over 40 hops with close_pylorus_slot._smooth.
    The smoothed profile (ax 0.337-0.391) is what rebuild_pylorus_ring.rebuild() uses as the end of the throat.
 3. rebuild_pylorus_ring.rebuild() builds funnel + lips + throat + short canal as one sheet with three analytic shape keys.
 4. Camera: fix_camera_pyloric_path.plan() with s0 replaced by SPRE(): s(700)=original, s(795)=-0.50, s(850)=-0.42 (dwell about 0.4 world
    from the ring instead of 1.08), s(872)=original again; then frames 860-1110 with camera s > 0.05 are shifted by -u*0.355*clip((s-0.05)/0.5, 0, 1)
    so the bulb-side path follows the moved bulb and the canal pass is short.
 6. Delete the old canal stub left inside the moved bulb: Antrum faces with centre ax < 0.335 and rad < 0.07 (395 faces). It showed from the
    bulb side as ten flat white 'pebbles' around the tube mouth (found by ray-casting the white pixels of the render to face ids).
 5. Light_Endoscope_Tip energy is baked per frame: for frames 744-884 and 1030-1060 set E = 41 * d^2 (d = median forward ray distance over a
    +-18 deg cone, capped 1.2, 5-tap smoothed in log space, 8-frame blends), x(0.4..1) when closer than 0.5, capped 8 around the exit.
"""

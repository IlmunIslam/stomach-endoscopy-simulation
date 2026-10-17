"""Round 2 of the Antrum crack fix (recorded from the live session, applied in this order; all coords on every shape key).
Method: measure, don't guess. Ray-cast the camera at frames 820/850 across the crack, read depth steps and face normals.
 1. holes_fill on small closed boundary loops near (0.07,0.09,0.67) local: 6 faces (no visible change).
 2. Depth scan across the crack found grooves/steps; implicit smoothing (close_pylorus_slot._smooth) seeded on the faces whose
    depth jumps >0.004..0.01 vs neighbours: t=2..3 (clamp 0.015), then t=6 hops 4 (clamp 0.02), then t=15 hops 5 (clamp 0.03).
 3. Delete faces visible from behind (normal.view > 0.1) in the pixel boxes around the crack at 820/850: 3 + 3 faces.
 4. Weld open boundary chains across the slit: mutual-nearest boundary verts <0.012 apart, shape-key coords averaged per key,
    bmesh.ops.weld_verts (removed the red dart).
Backups (npz of all keys) in %TEMP%\antrum_fix. Frames 361/531/731/971 and 700-900 means identical before/after (nothing else moved).
"""
# Open after round 2 (not fixed): a vertical chain of small through-holes in the funnel wall below the pyloric aperture
# (about local x 0..0.08, z 0.60-0.61 at frame 850, pixels ~(489-501, 313-337) of 960x540). Rays pass through to the Stomach (red).
# The wall there is a very low-poly double-layer slab: rim vertices are sparse and the rim edges are shared by 3-4 faces, so
# boundary-edge detection, weld pairs, holes_fill and a hand-made ngon patch (looked like a flat sticker, reverted) did not work.
# Needs a local rebuild of that wall patch (e.g. remesh/re-bridge the two lips), not smoothing.

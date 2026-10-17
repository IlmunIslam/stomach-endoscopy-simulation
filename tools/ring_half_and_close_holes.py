"""Round 3: pyloric ring 50% smaller + close the chain of through-holes below the aperture. Object Mode, all shape keys. Never saves.
1. Ring: shrink_pylorus_ring.run(scale=0.5, apply=True) (ring perp radius p95 0.106 -> 0.053 local), then implicit smoothing
   (close_pylorus_slot._smooth, t=4, clamp 0.05) of the moved non-ring band so the sheet around the smaller ring stays smooth.
2. Holes (rays pass through to the Stomach): at frame 850 ray-cast a grid at 0.25 px, label non-Antrum pixels (comps 2+3 of
   the box x 465-530, y 245-335, aperture is comp 1), dilate 1 px, take 16 ring points around the hole, ray-cast each to get the
   Antrum face + barycentric weights, and build new vertices whose position in EVERY shape key is the same barycentric blend
   of that face's vertices (so the patch follows Close/Open). Fan of 16 triangles to a centre vertex (mean per key), material of
   the rim faces (slot 1), smooth shading. 16 faces / 17 verts added; nothing deleted.
Why not use existing vertices: the wall is a very low-poly double layer whose rim edges are shared by 3-4 faces (see
antrum_crack_round2.py), so rim vertices were sparse and boundary-edge methods failed.
Backups: %TEMP%\antrum_fix\r3\backup_*.npz. Frames 361/531/971 means unchanged; 731 -0.4; antrum frames 780-850 -1.3..-3.8 (smaller bright ring).
"""

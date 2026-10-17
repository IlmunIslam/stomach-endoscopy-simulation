"""Round 6 (live scene, never saves). Steps applied through execute_blender_code; recorded here so they can be repeated.

1. PART_W5_Antrum: delete the 16-face loose strip of ring material (verts with only strip faces, ax .44-.51, theta -90) that
   showed as glassy white shards at frames 866/1056; reverse junction faces 17902-17908 (normal pointing away from the axis);
   relax vertex 17333 and its two neighbours (12 mm off its neighbours in every key); weld 27 mutual-nearest pairs of
   boundary verts across the theta -90 slit (all keys set to the pair midpoint first); delete the 5 ring-material faces
   that formed the remaining wedge (more deletions only expose the next layer of the double-layered column: do not).
2. Scope shaft (GN_Scope_Shaft): GATE_OUT From Min/Max 1420/1380 -> 1475/1440 so the shaft stays threaded through the cardia hole
   (SH_HOLE) while the camera pulls away; it leaves the frame by ~1428 and is hidden at 1430 (hide keys unchanged).
"""

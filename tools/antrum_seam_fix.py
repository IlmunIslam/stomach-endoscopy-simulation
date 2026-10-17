"""Seam / Y-crack / strand-highlight fix on PART_W5_Antrum, recorded from the live session (steps were applied in this order).
All coordinate edits go to every shape key. Object Mode. Never saves. Backups: scratchpad antrum_backup_t4*.npz.

 1. Local implicit smoothing (close_pylorus_slot._smooth) around the slot seam, in two passes:
      pass A seed |y-0.09|<0.012, 0.03<x<0.13, 0.60<z<0.72, 3 hops, t=2, move clamp 0.01
      pass B seed |y-0.09|<0.02,  0.03<x<0.15, 0.58<z<0.80, 4 hops, t=3, move clamp 0.012
    (removes the long sliver triangles left by the earlier vertex welds.)
 2. Delete mat-1 faces in that region that face away from the camera at frames 800/850 (51 faces; slot-wall backfaces that
    showed as white glints). bmesh.ops.delete(context='FACES_ONLY').
 3. Strand highlight: the glint came from base specular (Specular IOR Level 0.28), not the coat.
    Float attribute Antrum_Vein_W (blurred Antrum_Vein) drives a Math node VEIN_SPEC = 0.28 - 0.24*W into Specular IOR Level.
    The ridge was also relaxed (implicit smoothing on verts with Antrum_Vein>0.05, t=1.5, clamp 0.006).
 Failed earlier: remove_doubles at 1e-4..1.2e-3, material reassignment, coat changes (see docs/LESSONS.md).
"""

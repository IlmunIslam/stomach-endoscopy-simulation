# Scout index: everything evaluated

| Name | Link | Date | Verdict | Reason |
|---|---|---|---|---|
| Blender Lab MCP (official) | https://projects.blender.org/lab/blender_mcp | 2026-10-19 | try / verify | Confirm whether it is the server in use, pin the version, install its add-on in Blender 5.2.2. |
| MCP for Blender (ahujasid, community, renamed Sept 2026) | n/a | 2026-10-19 | watch | Four 2026 CVEs per a vendor security guide (low-medium confidence); relevant only if it is in use. |
| blender-mcp-ultra | https://github.com/carlosh7/blender-mcp | 2026-10-19 | reject for now | 223 tools, unknown maintainer, large attack surface. Idea noted: visual feedback loop (we already use image review and render_stats). |
| VR-Caps | https://github.com/CapsuleEndoscope/VirtualCapsuleEndoscopy , https://arxiv.org/pdf/2008.12949 | 2026-10-19 | try (idea only) | Vessels as texture extracted from real endoscopy images, Unity HDRP coat mask for specular, SOFA + Unity for deformation; relevant to the vessel question and the Unity phase. |
| Blender Randomiser (UCL, BSD-3) | n/a | 2026-10-19 | watch | Scene-property randomisation, later. |
| MeshBrush | https://arxiv.org/abs/2404.02999 | 2026-10-19 | watch | Neural stylization research, code status unclear. |
| EndoPBR | n/a | 2026-10-19 | watch | Neural stylization research, code status unclear. |
| kevinbadi/blender-skills | n/a | 2026-10-19 | reject | Product turntables, not our bottleneck. |
| hkuds/cli-anything | n/a | 2026-10-19 | reject | Headless CLI, not our bottleneck. |

Seeded from the Director's first sweep of 2026-10-19.

# Hypopharynx tempo: mouth to first esophagus (from the reference video, 2026-10-29)

Source: `references/Upper Gastrointestinal Endoscopy Examination Technique and Standard Findings.mp4` (453 s, 656x480, 25 fps, burned-in captions, no subtitle file). Frames and contact sheets live in `references/_frames/` (git-ignored). View-only reference.
Numbers are from 5 fps grey frames: brightness = mean luminance 0..1 over the whole picture (about 24 % is the black mask round the round endoscope image, so it is a relative number), motion = mean abs frame difference x100. Video seconds x 24 = frames at our fps. The burned-in clock (16:54:xx) equals video seconds + about 0 (16:54:41 shows at 41 s).

## Captions (what the examiner does, in order)
1. "First put the tip of the endoscope on the patient's tongue under direct vision" (about 14-18 s)
2. "guide the scope through the mouth, you can see the uvula at the 6:00" (about 18-24 s; tongue at the top of the picture, uvula at the bottom)
3. "when the epiglottis, cricoid [arytenoid] cartilage and vocal cords appear, guide the tip of the instrument behind the cricoid cartilage" (about 31-44 s)
4. "and instruct the patient to swallow while you apply gentle pressure" (about 44-52 s)
5. "[once] passed, advance the endoscope slowly to allow careful examination of the esophageal contour" (about 58 s on)

## Stages
| Stage | Video s | Frames @24 | What the picture shows | Motion | Notes |
|---|---|---|---|---|---|
| Title card | 0-4 | - | Elsevier title | 0 | skip |
| Tongue hold | 4-9 | 96-216 | tongue dorsum (pale pink, rough papillae) filling the top, purple bite block and teeth edge at the bottom | 2.6 (still) | scope parked about 4-5 s |
| Palate / tongue-base touch | 9-12 | 216-288 | lens touches mucosa: flat orange frames at 9, 11; white tongue-base rim at the top | 8.3 | first push-in |
| Posterior pharyngeal wall | 12-16 | 288-384 | dark brown-pink wall below a pale tongue-base rim, tiny saliva bubbles | 5.0 | slow dark drift, mean brightness 0.29 |
| Uvula / oropharynx | 16-25 | 384-600 | pink wall brightening, uvula tip as a V at the bottom (18.5 s), pharyngeal wall folds, wet specular spots | 5.9 | tongue base stays at the top edge |
| Tip bends down | 25-31 | 600-744 | view turns from the oral cavity to the hypopharynx: dark airway to one side, bright grazing light, wall close-ups at 28-30 s | 5.8 | the up direction rotates (pitch down over the tongue base) |
| Larynx | 31-42 | 744-1008 | arytenoid / corniculate mounds with the glottis opening behind them (V-shaped dark gap, cords visible 35-36.5 s), inter-arytenoid ridge, wet shiny pink mucosa | 6.0 | slow hover: the clearest 11 s of the clip; 37.5 s lens touch |
| Pyriform / retro-cricoid | 42-52 | 1008-1248 | sweeps sideways and down past the sinus, soft pink walls, lens touches (43.5, 47-47.5, 51.5 s are flat orange), swallow with gentle pressure 44-52 s | 6.9 (highest) | motion blur at 38 s and 50 s |
| UES opening | 52-57 | 1248-1368 | a small dark off-centre opening (53.5 s dot, 54.5-55 s oval, 56 s smaller), light wall around it | 6.0 | opening is small, round, not a slit; 55.5 s lens touch |
| First esophagus | 57-62 | 1368-1488 | pale pink wall with fine red vessels, a small dark closed lumen at the centre (58-59.5 s), then the lumen opens round (60-61.5 s) | 4.6 then 2-3 | speed drops: slow reading of the tube |

Whole mouth-to-esophagus span: 4 to 57.5 s = 53.5 s = about 1,290 frames. After 62 s the esophagus runs to about 78-80 s; the stomach (cardia, folds) starts around 82-84 s, and the rest to 453 s was not reviewed (stomach and duodenum, ignore for now).

## Exposure
Auto-exposure keeps the picture steady: mean brightness 0.27-0.40 all the way, no dark tunnel effect. The brightest frames are lens touches (flat orange, nothing else visible) and pale tongue-base rims (up to 11 % near white at 4 s). The darkest stretch is the posterior wall at 12-16 s (0.29). There is no blackout between the mouth and the throat; the light stays at the tip and the walls are always close (a few centimetres).

## Camera behaviour to copy
- Orientation: tongue at the top while looking back along the mouth; after the dive over the tongue base the up direction turns anterior (epiglottis / larynx at the top).
- Holds: about 4-5 s on the tongue, about 11 s hovering at the larynx, about 5 s at the UES, slow reading of the first esophagus. Between holds the tip moves with short pushes and small sideways corrections, not a steady glide.
- The tip touches mucosa several times (orange flashes); do not copy as a feature, but never leave more than about 1-2 cm between lens and the wall.
- UES: a small dark round opening off-centre in a smooth wall, not a clean tube mouth.

## Our current fly-through compared (frames 1-121, before Stage 1)
- Starts 7 units above a floating slab in a flat brown void: no mouth, tongue, palate, uvula or pharyngeal walls at all.
- Crosses the slab (the whole laryngeal region) in about 18 frames (0.75 s); the real clip spends 11 s at the larynx and 25 s from tongue to UES.
- Constant speed 0.13 units/frame, no hold anywhere; the real scope parks for seconds.
- Path is 0.5-1.25 units off the channel and runs into the esophagus tube, not the larynx.
- Exposure jumps from mean luminance 0.114 (void) to 0.379 (esophagus wall) instead of staying steady.
- 90 degree lens, no distortion; the real image is a round mask with a wide, slightly barrel-distorted field.
- No saliva highlights; mucosa reads matte.

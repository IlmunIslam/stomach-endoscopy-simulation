# Hypopharynx and upper endoscopy, mouth to UES: for PART_W0_Hypopharynx (research card, 2026-10-29)

**Use when:** modelling, texturing or animating PART_W0_Hypopharynx, or deciding whether a structure belongs in the first seconds of the scope path. Prevents the "invented feature" error of LESSONS 2026-10-17 (antrum vein): add nothing that a cited image does not show.

**EVIDENCE WARNING.** `references/` (GastroHUN, HyperKvasir, GastroVision) and the five photo folders (Antrum + Pylorus ring, Duodenal bulb, Duodenum 2nd part, Fundus, GEJ Z-line) contain NO hypopharynx or oropharynx images. Every statement below comes from the web (text only; I could not view pixels) and none was checked against a photo. Status: PARTIAL.

## What the web sources support
Order of view, scope entering from the mouth, image top = tongue side (the scope's anterior):
1. **Tongue base / vallecula / epiglottis.** Tongue at the top of the frame; the epiglottis is the first landmark below it. The hypopharynx runs from the lower edge of the epiglottis to the esophageal entrance. Sources do not describe the vallecula itself (not confirmed).
2. **Larynx seen from above.** A standard pass typically shows the vocal cords, the inner (laryngeal) surface of the epiglottis, the corniculate and arytenoid cartilages, and the pyriform sinus. Aryepiglottic folds join epiglottis to arytenoids (anatomical knowledge, not in the fetched snippets). Structures are visible only transiently. Adds ~35 s when inspected on purpose (Stevens 2014, n=111, white light and NBI).
3. **Pyriform sinuses** flank the larynx; during a swallow, contrast-stained water pools in the "swallowing crescent" (parts of the pyriform sinuses plus the post-arytenoid space).
4. **Postcricoid region and UES.** The UES is ~3 to 5 cm long, with the cricopharyngeus forming lateral and posterior walls and the cricoid lamina anterior. At rest it appears as a squeezed-shut slit (the muscle is nearly always contracted, even asleep). It opens when the larynx rises and moves forward and the cricopharyngeus relaxes (swallow), and an older study saw it open under air insufflation. The scope passes with gentle pressure.
5. **Mucosa:** squamous, whitish-pink to silver-red, smooth, fine vascular markings, little pooled secretion. Mild glycogenic acanthosis (pale tiny plaques) is normal in the cervical esophagus.
6. Image of "larynx at intubation of the esophagus during gastroscopy" exists (Commons "Larynx endo 2.jpg": cords and cricopharyngeal fossa). Licence conflicting between mirrors; verify on Commons before any use.

## Not found / unverified [low confidence]
Wetness and gloss description, colour values, lens distortion at this site, proportions (UES slit width vs frame), exact UES opening duration, how the esophagus first segment looks (ring folds, collapsed star). Typical expectations (glossy saliva film, strong specular on epiglottis, dark airway behind cords) are my common-knowledge assumptions only.

## How to build (suggested, untested)
1. **Geometry layers** for large forms: tongue-base mound at top, epiglottis as a curved leaf, two arytenoid mounds with aryepiglottic folds, a flat cord pair as a V slit, two pyriform pockets, then a posterior wall funnelling to the UES. These are shape, so geometry, not texture.
2. **Displacement/normal** only for fine surface (mucosal grain, fold wrinkle). **Texture** for pink-white colour and faint vessels; keep vessels blurred and low-contrast (see queued vessels card).
3. **UES motion:** one shape key "UES_open" (Basis = closed slit, key = round-ish opening, larynx edge lifted forward), driven by a custom property or driver (value 0 to 1) so Unity can export a blendshape. Closed rest state is the default frame; open only on swallow/insufflation input.
4. **Lens and light:** same wide-angle scope look and light-guide setup as other parts (see queued exposure card); wet-surface roughness ~0.2 to 0.4 as per antrum card, [unverified for this site].

## Pitfalls
- Modelling the UES as an always-open tube; sources say closed at rest.
- Treating hand-drawn atlas or Science Photo Library pictures as free: they are rights-restricted.
- Inventing cord detail or cartilage texture without an image.

## Sources and licences
- Visualization of larynx/hypopharynx at EGD (Stevens et al., feasibility, 111 patients): https://read.qxmd.com/read/25303903/visual-evaluation-of-the-larynx-and-hypopharynx-during-esophagogastroduodenoscopy-a-safety-and-feasibility-study (abstract; cite only). Related PMC pages PMC3678057 and PMC7952122 appeared in search but fetch was blocked; their content is via search summary only.
- Cricopharyngeus at rest/swallow: https://laryngopedia.com/cricopharyngeus-muscle/ (All rights reserved; cite only, do not copy images).
- UES opening mechanics: https://vivo.colorado.edu/display/pubid_125186 (abstract only).
- Commons image mirror: https://en.wikipedia.com/wiki/File:Larynx_endo_2.jpg (licence unclear).
- SAGES normal vocal cords video: https://sages.org/video/normal-vocal-cords (licence unconfirmed).

**Confidence:** order of structures and UES closed-at-rest behaviour medium-high (several sources agree). Everything about look (colour, wetness, lens) low. Nothing seen by eye.

## Missing references (needed from Ilmun, real endoscopy stills or video with usable licence)
1. Transoral view of the tongue base and epiglottis (with vallecula) as the scope enters.
2. Larynx from above with cords open (inspiration) and closed.
3. Aryepiglottic folds and arytenoids, close view.
4. Both pyriform sinuses, empty and with saliva pooled.
5. Postcricoid region and UES entry, closed slit at rest.
6. UES opening on swallow and on air insufflation (video or frame sequence).
7. First segment of the cervical esophagus just past the UES (fold pattern, colour, wetness).
8. One full-frame example showing the scope's lens vignette at this site.

# Normal-stomach endoscopy reference sources (licences, sizes, proposed board)

Date: 2026-10-15. Researcher session, no Blender, nothing downloaded. Ilmun may sell the simulation commercially.

## TL;DR
- Best fit by content and quality: **GastroHUN** (1080x1350, Olympus EXERA III, 22 stomach landmarks incl. incisura/antrum/body/fundus, 10 s clips). Figshare says **CC BY**, but its GitHub README badge says CC BY-NC 4.0, so it is not cleared for commercial use yet.
- **HyperKvasir** has z-line (932), pylorus (999), retroflex-stomach (764) images and 373 videos. Paper, repo, OSF and the zip's `license.txt` say CC BY 4.0, but the GitHub README says commercial use needs prior written permission: conflict.
- **GastroVision** has 969 normal-stomach, 393 pylorus, 330 normal z-line, 140 normal esophagus images (94+33+37+13 of them at 1920x1072); no licence file; OSF licence record says CC BY 4.0.
- Wikimedia Commons has only two usable stills (CC BY-SA 3.0). NIH Open-i was not checked.
- Subsets can be fetched without the full zips (HTTP range requests work). ffmpeg 8.1.1 is installed. Own-photo candidate folders are listed in section 7.

## Facts

### 1. HyperKvasir (Simula / Baerum Hospital, Norway)
- Size: 110,079 images; 373 videos per the [Simula page](https://datasets.simula.no/hyper-kvasir/) (11.62 h) but 374 per the [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7455694/) (conflict of 1). 10,662 labeled images in 23 classes. Confidence high.
- Upper-GI landmark classes, counted from the zip's central directory (range request, no image data read; [labeled-images zip](https://datasets.simula.no/downloads/hyper-kvasir/hyper-kvasir-labeled-images.zip)): `z-line` 932, `pylorus` 999, `retroflex-stomach` 764 images, avg 0.71-0.78 MB each. The upper-GI landmarks folder holds 2,695 images in total. Confidence high. The classes are landmarks; "normal" is not stated per image.
- Image resolution: **could not check** (given only in a figure; I did not read image headers). Video resolution: **could not check**.
- Videos: 373 .avi files, 4 MB to 633 MB each. Stomach-related labels in `video-annotations.csv`: "stomach" x6 (55-196 MB), "gastric" x1 (60 MB), "retroflexed stomach," x1 (29 MB), "z-line distal oesophagus" x1 (35 MB), "upper GI" x1 (70 MB), "duodenum" x4 (42-179 MB). Labels are free text; "normal" is not stated. Confidence medium. Equipment Olympus/Pentax (paper); HD not confirmed.
- Download sizes: Simula page lists whole set 58.6 GB, labeled images 3.9 GB, labeled videos "25.2 GB", segmentation 46 MB, unlabeled 29.4 GB. The videos zip measured 30,074,941,115 bytes (HTTP range header), so the page's 25.2 GB is wrong; the paper says 32,539 MB. Confidence high for the measured value.
- Subset without full zip: **yes**. Server answers `206 Partial Content` with `Accept-Ranges: bytes`; the zip central directory is at the end (1.97 MB read for the image zip, 46 KB for the video zip), so single members can be extracted. OSF also holds per-file downloads ([OSF](https://osf.io/mh9sj/)); I could not finish listing OSF (timed out).
- **Licence (conflict):**
  - CC BY 4.0: paper ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7455694/)); `license.txt` inside both zips; GitHub licence field CC-BY-4.0 ([GitHub API](https://api.github.com/repos/simula/hyper-kvasir)); OSF licence record "CC-By Attribution 4.0 International".
  - Restrictive: [GitHub README](https://github.com/simula/hyper-kvasir) "Terms of Use": "released fully open for research and educational purposes. The use of the dataset for purposes such as competitions and commercial purposes needs prior written permission."
  - The Simula page itself only asks for a citation.
  - The Hugging Face mirror card has YAML `license: mit` and body text CC BY 4.0 (mirror, not primary).
  - Attribution: Borgli et al., "HyperKvasir, a comprehensive multi-class image and video dataset for gastrointestinal endoscopy", Scientific Data 7:283 (2020), doi 10.1038/s41597-020-00622-y, CC BY 4.0.
- Consent: anonymous data, exempt from patient consent and regional ethics review (paper). Confidence high.

### 2. GastroVision (Baerum Hospital NO + Karolinska SE)
- Size/classes: **conflict**. OSF, arXiv, GitHub README and the [metadata CSV](https://raw.githubusercontent.com/DebeshJha/GastroVision/main/GastroVision_metadata.csv) (8,000 rows): 8,000 images, 27 classes. The [Simula page](https://datasets.simula.no/gastrovision/) says 6,169 images, 36 classes (updated June 2026). I could not tell which version the OSF download serves. Confidence high for the CSV.
- Normal upper-GI classes in the CSV (images; resolutions): Normal stomach 969 (768x576: 575; 1280x1024: 265; 1920x1072: 94; 720x576: 35); Pylorus 393 (1920x1072: 33); Gastroesophageal_junction_normal z-line 330 (1920x1072: 37); Normal esophagus 140 (1920x1072: 13); Duodenal bulb 205. Average file 216-323 kB. Confidence high.
- No video, no retroflex-stomach class (only "Retroflex rectum"), no fluid or bubble class.
- Download size: **could not check** (OSF listing shows folders without sizes; Google Drive mirror not opened). Subset download: not tested.
- **Licence:** the OSF project licence record is "CC-By Attribution 4.0 International", copyright holder empty, year 2023 ([OSF API](https://api.osf.io/v2/nodes/84e7f/)). The arXiv page shows CC BY 4.0 for the article only ([arXiv](https://arxiv.org/abs/2307.08140)). GitHub repo has no licence file (API `license: null`); the Simula page states none. Confidence medium. Attribution: Jha et al., GastroVision, ICML ML4MHD 2023.

### 3. GastroHUN (Hospital Universitario Nacional de Colombia)
- Content: 8,834 labeled images (387 patients), 4,729 labeled 10 s sequences (223 procedures), 237 full videoendoscopies; 22 stomach landmarks (A/L/P/G views of antrum, lower body, middle-upper body, fundus/cardia, incisura) plus one "NA" class ([paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11742658/), [GitHub README](https://github.com/Cimalab-unal/GastroHUN)). Confidence high. There is no esophagus/Z-line and no pylorus class among the landmarks listed.
- Resolution: images 1080x1350 (91%) or 720x900; sequences the same; Olympus EVIS EXERA III CV-190; 15 or 30 fps (paper). The most modern footage found. Confidence high.
- Download sizes ([figshare file list](https://springernature.figshare.com/articles/dataset/GastroHUN_an_Endoscopy_Dataset_of_Complete_Systematic_Screening_Protocol_for_the_Stomach/27308133), via [API](https://api.figshare.com/v2/articles/27308133)): Labeled Images.zip 2.63 GiB (9,221 entries); Labeled_Sequences Group1-7 1.28-4.86 GiB each; Videoendoscopies Group1-7 5.9-9.7 GiB each; metadata.zip 2 MB; about 96.9 GB total. Images sit in patient-ID folders, so class labels need `metadata.zip` (not read). Sequences are mp4, 8.7-10.4 MB each in the group I listed.
- Subset: **yes**. The figshare file URL redirects to storage that answers range requests with 206 and `Accept-Ranges: bytes` (central directory read 1.1 MB).
- **Licence (conflict):** figshare record CC BY (`license.name = CC BY`, creativecommons.org/licenses/by/4.0). Paper article CC BY 4.0. GitHub README: badge "CC BY-NC 4.0" and text "released fully open for research and educational purposes" with competitions needing permission. Patient consent covers "research and education" (paper). Commercial reuse is therefore unclear. Confidence medium.
- Attribution: Bravo et al., "GastroHUN...", Scientific Data 12:102 (2025), doi 10.1038/s41597-025-04401-5; dataset doi 10.6084/m9.figshare.27308133.

### 4. Wikimedia Commons
- Two stills of a "normal stomach" (pylorus; body), 1300x1000, CC BY-SA 3.0, patient permission stated ([File 1](https://commons.wikimedia.org/wiki/File:Stomach_endoscopy_1.jpg), [File 2](https://commons.wikimedia.org/wiki/File:Stomach_endoscopy_2.jpg), read through the Commons API). Author field is not machine-readable. Searches for gastroscopy/EGD found no video of a normal stomach. Commons coverage beyond these: **I could not find this** (three API searches only). Share-alike applies to distributed adaptations.

### 5. Others
- NIH Open-i: **not checked**.
- SAGES Video Atlas "normal stomach" video: no licence in the search result; the site asks users to contact SAGES ([page](https://sages.org/video/normal-stomach)). Not usable without permission. Confidence medium.
- GIM-ENDO (gastric intestinal metaplasia, upper-GI video): CC BY-NC 4.0 per a search summary ([arXiv](https://arxiv.org/pdf/2606.20919)); excluded. [unverified, not opened]
- GastroNet-5M: described as CC BY 4.0 in a search result but "scientific use"; not opened. [unverified]

### 6. ffmpeg and video to frames
- `where ffmpeg`: `C:\Users\ilmun\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe` (also `ffprobe.exe`). ffmpeg 8.1.1 full build (gyan.dev), configured with `--enable-gpl --enable-version3`; decoders h264, hevc, mpeg4, mjpeg, wmv3 present. Nothing installed.
- Frames: `ffmpeg -i clip.mp4 -vf fps=2 frames/%04d.png`, or `-vf "select=eq(n\,120)" -vframes 1` for one frame; `ffprobe` for resolution and fps. Blender alternative: load the clip as a Movie Clip or Video Sequencer strip and render a frame range as PNG. ffmpeg is simpler. The codec of the HyperKvasir .avi files was not checked.

### 7. Folders in the project (file counts only, no image opened)
- Candidates for Ilmun's own endoscopic photos (untracked image folders): `Antrum + Pylorus ring images` 5 (jpg); `Duodenal bulb images` 1 (jpg); `Duodenum 2nd part images` 1 (jpg); `Fundus Images` 4 (jpg); `GEJ Z-line images` 10 (8 jpg, 1 png, 1 webp). Total 21.
- Other folders with images (file names suggest textures or renders, not photos): `W0_Hypopharynx` 3, `W1_GEJ_ZLine` 3, `W2_Cardia_Retroflexed` 3, `W5_Antrum` 1, `W6_Pylorus` 3 (names `Color_/NormalGL_/ORM_`, 3D AI Studio maps); `renders/` 51 (6 in `renders/stills`); `render_v17/` 1,440 PNG frames.

## Opinions and proposals (not facts)
- Commercial use: I am not a lawyer. The cleanest route is a short written email to the dataset contacts (HyperKvasir: contacts on the Simula page; GastroHUN: the paper's authors) asking them to confirm that CC BY covers commercial use. A private comparison board that is never shipped or published carries less risk than anything bundled in the product, but that is Ilmun's call.
- Proposed board (about 30 stills, 5 clips). Exact files cannot be chosen from metadata; that needs looking at candidates after a yes.
  - GastroHUN stills (16, ~0.3 MB each): incisura 3 (A6/L6/P6), antrum 3, lower body 3, middle-upper body (rugae) 3, fundus/cardia 3, 1 from the "NA" class hoping for fluid or bubbles (unverified that it has any).
  - HyperKvasir stills (10, ~0.75 MB each): z-line 4, retroflex-stomach 4, pylorus 2.
  - GastroVision stills (4, ~0.25 MB each, 1920x1072): normal stomach 2 (close mucosa), pylorus 1, normal esophagus 1.
  - Pooled fluid and bubbles: no dataset labels this; pick by eye.
  - Clips (5): GastroHUN labeled sequences x3 (incisura, body, antrum; ~9-10 MB each, chosen via the metadata labels); HyperKvasir "retroflexed stomach," (29 MB) and "z-line distal oesophagus" (35 MB).
  - Estimated total about 100 MB; every single file is under 50 MB.
- Method for a small download: read each zip's central directory over HTTP range and extract only the chosen members, plus GastroHUN `metadata.zip` (2 MB). I would write a one-off script in `tools/` using only the Python standard library; nothing to install.

## Open questions for Ilmun
1. Accept the licence conflicts, or should I draft permission emails first (HyperKvasir, GastroHUN, GastroVision)?
2. Yes to downloading the ~100 MB board into `references/` (git-ignored)?
3. May I view the candidate images to curate the board, or will you pick?
4. Which folder holds your own photos (section 7)?

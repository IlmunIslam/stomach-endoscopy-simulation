# Permission email drafts (DRAFTS ONLY, nothing has been sent)

Status: not sent. Ilmun or the supervisor decides who sends, from which address, and whether to copy the supervisor.
Placeholders in [square brackets] must be filled in before sending.

Why these three: each dataset has a licence conflict on the primary pages (see `docs/research/2026-10-15-endoscopy-reference-sources.md` and `docs/security/LICENSES.md`).

| Dataset | The conflict | Contacts listed on the source pages |
|---|---|---|
| HyperKvasir | CC BY 4.0 in the paper, `license.txt` and repo, but the GitHub README says commercial use needs prior written permission | steven@simula.no, michael@simula.no, paalh@simula.no ([Simula page](https://datasets.simula.no/hyper-kvasir/)) |
| GastroHUN | Figshare says CC BY; the GitHub README badge says CC BY-NC 4.0 and "research and educational purposes" | Corresponding author address: I did not read it from the paper, so take it from the [Scientific Data article](https://www.nature.com/articles/s41597-025-04401-5) |
| GastroVision | OSF record says CC BY 4.0; no licence file on GitHub; the Simula page says nothing | debesh.jha@northwestern.edu, vanshalisharma@iitg.ac.in, ulas.bagci@northwestern.edu ([GitHub README](https://github.com/DebeshJha/GastroVision)) |

---

## Draft 1: HyperKvasir

**To:** steven@simula.no, michael@simula.no, paalh@simula.no
**Cc:** [supervisor, optional]
**Subject:** Question about commercial use of HyperKvasir (CC BY 4.0 vs README terms)

Dear Dr. [surname] and colleagues,

My name is Ilmun Islam and I am a computer science student at [university], supervised by [supervisor name]. I am building a non-clinical, visual 3D simulation of a gastroscopy (a stomach interior as seen by an endoscope) in Blender. The simulation is not a medical device and is not used for diagnosis or training of diagnostic software. I may sell it in the future.

I would like to use a small number of HyperKvasir images and video clips (about 10 images and 2 short clips, from the z-line, pylorus and retroflex-stomach classes) only as visual references, to compare how real mucosa, highlights and lighting look against my own rendering. I will not copy them into my textures, my scene or my final video, and I will not redistribute them. I would credit your dataset and cite the Scientific Data paper (Borgli et al., 2020, doi 10.1038/s41597-020-00622-y).

I noticed two statements that seem to differ:
1. The paper, the `license.txt` file in the download and the GitHub repository licence say the dataset is CC BY 4.0.
2. The "Terms of Use" in the GitHub README says the data is released for research and educational purposes and that commercial use needs prior written permission.

Could you please confirm in writing which one applies, and whether my use described above is allowed for a product that may be sold? If written permission is needed, please tell me what I should do to obtain it.

Thank you very much for making the dataset available.

Kind regards,
Ilmun Islam
[email] · [university] · [supervisor name]

---

## Draft 2: GastroHUN

**To:** [corresponding author email from the paper]
**Cc:** [supervisor, optional]
**Subject:** Question about commercial use of GastroHUN (CC BY on figshare vs CC BY-NC on GitHub)

Dear Dr. [surname] and colleagues,

My name is Ilmun Islam and I am a computer science student at [university], supervised by [supervisor name]. I am building a non-clinical, visual 3D simulation of a gastroscopy in Blender. It is not a medical device and not meant for diagnosis. I may sell it in the future.

I would like to use a small number of GastroHUN images and 10-second sequences (about 16 images and 3 clips of normal stomach landmarks) only as visual references for comparing real mucosa, folds, highlights and lighting with my own rendering. I will not copy them into my textures, my scene or my final video, and I will not redistribute them. I would credit your dataset and cite the paper (Bravo et al., Scientific Data 12:102, 2025, doi 10.1038/s41597-025-04401-5).

I noticed that the licence information differs:
1. The figshare record and the article say CC BY (4.0).
2. The GitHub README shows a "CC BY-NC 4.0" badge and says the data is released for research and educational purposes.

I also read that patient consent covered research and education. Could you please confirm in writing which licence applies and whether my use described above is allowed for a product that may be sold? If it is not, please let me know whether you can grant permission for this reference-only use.

Thank you very much for sharing this dataset.

Kind regards,
Ilmun Islam
[email] · [university] · [supervisor name]

---

## Draft 3: GastroVision

**To:** debesh.jha@northwestern.edu, vanshalisharma@iitg.ac.in, ulas.bagci@northwestern.edu
**Cc:** [supervisor, optional]
**Subject:** Question about the licence of GastroVision (commercial use)

Dear Dr. Jha, Dr. Sharma and Dr. Bagci,

My name is Ilmun Islam and I am a computer science student at [university], supervised by [supervisor name]. I am building a non-clinical, visual 3D simulation of a gastroscopy in Blender. It is not a medical device and not meant for diagnosis. I may sell it in the future.

I would like to use a handful of GastroVision images (about 4 images of normal stomach, pylorus and z-line) only as visual references, to compare real mucosa and highlights with my own rendering. I will not copy them into my textures, my scene or my final video, and I will not redistribute them. I would credit the dataset and cite your paper (Jha et al., GastroVision, ICML ML4MHD 2023).

I could not find a clear licence for the dataset itself. The OSF project page shows a CC BY 4.0 licence record, the arXiv page shows CC BY 4.0 for the article only, the GitHub repository has no licence file, and the Simula page does not name one. I also noticed that the Simula page describes 6,169 images in 36 classes, while the OSF files and the GitHub metadata list 8,000 images in 27 classes.

Could you please confirm in writing which licence applies to the images, and whether my use described above is allowed for a product that may be sold? Please also tell me which version of the dataset is the current one.

Thank you very much for making the dataset available.

Kind regards,
Ilmun Islam
[email] · [university] · [supervisor name]

---

## Notes for the sender
- Keep the replies; they are the written confirmation. File them in `docs/security/` (text only, no personal data beyond the sender's name).
- Some GastroVision and HyperKvasir images carry on-screen text fields from the recording system (dates, times, labels). I would mention this to the dataset owners only if you want to ask whether those overlays were meant to stay.
- Until written answers arrive, I treat all three as view-only and not cleared for anything that ships.

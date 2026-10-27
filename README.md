# SIMETRIC — Pre- and post-task surveys

Analysis code and de-identified outputs for the survey measures of the SIMETRIC study
(Simulation and Imaging Methods using Eye Tracking for the Recording of Peripheral Intravenous
Catheter Insertion).

Companion repositories:
[eye tracking, procedural success and duration](https://github.com/JW-999-IE/SIMETRIC-Eye-tracking) ·
[hand motion and grip](https://github.com/JW-999-IE/SIMETRIC-Hand-motion)

Manuscript: *Ultrasound-guided long peripheral catheter configurations differ in procedural
performance, gaze-event rates and hand kinematics in the SIMETRIC simulation study*
(submitted to *Scientific Reports*).

## Study context

Twenty-seven clinicians completed five ultrasound-guided insertions with each of three 8-cm long
peripheral catheter configurations on a vascular-access phantom: catheter-over-needle (CON),
accelerated technique with guidewire (ATG) and direct Seldinger technique (DST). Surveys were
completed before and after the simulation session.

The analysis script reads the original survey workbook, in which DST is labelled `MST`. The
deposited outputs in `results/` use DST throughout.

## Measures

| Outcome | Scale | Analysis |
|---|---|---|
| Device-specific stress | 1–5, one score per clinician and configuration | Friedman test; Holm-adjusted Wilcoxon signed-rank pairwise tests |
| Adapted LPC usability index | Ten items scored 0–4 following System Usability Scale polarity, rescaled to 0–100; not a validated SUS | Clinician-clustered GEE; item-level Friedman tests with Holm correction |
| Device preference | Favourite, most comfortable, least stressful; general preference for a guidewire device | Descriptive |

## Results

**Usability.** Means 69.7 (CON), 50.3 (ATG), 69.8 (DST). CON was 19.4 points higher than ATG
(95% CI 7.1–31.8, Holm P = 0.006); DST was 19.5 points higher than ATG (6.6–32.4, Holm P = 0.006);
CON and DST did not differ (0.1 points, P = 0.988).

**Stress.** Means 2.00 (CON), 2.85 (ATG), 1.96 (DST). Friedman P < 0.001; ATG higher than CON and
than DST (Holm P = 0.006 each); CON and DST did not differ (P = 0.978).

**Preference.** Favourite device: DST 10/27, CON 8/27, ATG 5/27, no preference 4/27. Twenty of 27
clinicians (74.1%) stated a general preference for a catheter with a guidewire.

Stress values are means of clinician-level scores, not medians of individual Likert responses.

## Repository structure

```
├── README.md
├── DEIDENTIFICATION.md
├── data/README.md                         # why raw responses are not deposited
├── scripts/
│   └── analyse_lpc_pre_post_surveys.py
└── results/
    ├── lpc_adapted_usability_scores.csv      # clinician × configuration index (0–100)
    ├── lpc_adapted_usability_items.csv       # item-level responses and 0–4 scores
    ├── lpc_usability_descriptives.csv
    ├── lpc_usability_pairwise_gee.csv
    ├── lpc_device_stress_scores.csv
    ├── lpc_stress_descriptives.csv
    ├── lpc_stress_pairwise_wilcoxon.csv
    ├── lpc_post_preferences.csv
    ├── lpc_guidewire_preference.csv
    ├── lpc_post_global_simulation_outcomes.csv
    └── lpc_survey_inference_summary.txt
```

To rerun: `python scripts/analyse_lpc_pre_post_surveys.py --survey-workbook <workbook.xlsx> --output-dir results`

## Data availability

Raw survey responses and free-text answers are not deposited, because the combination of age band,
gender, profession, clinical setting and years of experience could allow re-identification of
participants. Clinician-level scores in `results/` use pseudonymous codes (P1–P30) and are
sufficient to reproduce every reported survey statistic. Raw responses may be requested from the
corresponding author, subject to institutional and ethical approval.

## Ethics

Approved by the Clinical Research Ethics Committee at the University of Galway (C.A. 3392) before
recruitment. Written informed consent was obtained from all participants.

## Requirements

Python ≥ 3.9 with numpy, pandas, scipy, statsmodels and openpyxl.

## Citation

Manuscript reference to be added on acceptance.

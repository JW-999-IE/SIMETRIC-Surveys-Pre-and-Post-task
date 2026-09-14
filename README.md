# SIMETRIC — Pre- and Post-Task Surveys

Analysis code and aggregate outputs for the pre- and post-simulation survey measures of the
SIMETRIC study (Simulation and Imaging Methods for Eye Tracking and Recording Intravenous
Catheter Insertion).

Companion repositories:
[eye tracking](https://github.com/JW-999-IE/SIMETRIC-Eye-tracking) ·
[hand motion](https://github.com/JW-999-IE/SIMETRIC-Hand-motion)

## Study context

Twenty-seven hospital clinicians each performed five ultrasound-guided long peripheral catheter
(LPC) insertions with each of three configurations — catheter-over-needle (CON), accelerated
technique with guidewire (ATG), and modified Seldinger technique (MST) — on a vascular-access
phantom. Surveys were administered before and after the simulation session.

**Terminology.** The parent protocol refers to these devices as midline catheters, reflecting the
nomenclature current when it was written. At 8 cm insertable length they fall within the long
peripheral catheter category under current definitions. LPC is used throughout.

## Measures

**Pre-simulation.** Demographics, professional background, prior LPC and ultrasound training,
self-reported LPC insertion volume, knowledge items, clinical attitudes (0–10 Likert), and
current practice.

**Post-simulation.** Three device-specific outcomes:

| Outcome | Scale | Analysis |
|---|---|---|
| Self-reported stress during the procedure | 1–5 Likert, per attempt | Aggregated to one score per participant per configuration; Friedman test with Holm-adjusted Wilcoxon signed-rank pairwise comparisons |
| Adapted LPC usability index | 0–100, derived from multiple items on ease of use, control and confidence | Participant-clustered GEE with configuration as predictor |
| Device preference | Categorical (favourite, most comfortable, least stressful) | Descriptive |

## Headline results

**Usability.** Mean index 50.3 (ATG), 69.7 (CON), 69.8 (MST). Omnibus Wald χ²(2) = 11.65,
P = 0.003. ATG rated 19.4 points below CON (95% CI 7.1–31.8, Holm P = 0.006) and 19.5 points
below MST (6.6–32.4, P = 0.006); CON and MST did not differ (0.1 points, P = 0.988).

**Stress.** Mean 2.85 (SD 1.20) ATG, 2.00 (0.78) CON, 1.96 (1.06) MST; medians 3, 2, 2.
Friedman χ²(2) = 14.26, P < 0.001. Holm-adjusted Wilcoxon: ATG higher than CON (P = 0.006) and
than MST (P = 0.006); CON and MST did not differ (P = 0.978).

**Preference.** Favourite: MST 10/27 (37.0%), CON 8 (29.6%), ATG 5 (18.5%), no preference 4
(14.8%). Most comfortable: MST 14 (51.9%). Least stressful: MST 12 (44.4%).

Note that the stress summary statistics are **means and medians across participants of
participant-level aggregate scores**, not medians of raw Likert responses. Values such as 2.85
and 1.96 are not attainable as medians of an integer 1–5 scale.

## Repository structure

```
├── README.md
├── scripts/
│   └── analyse_lpc_pre_post_surveys.py   # survey analysis pipeline
├── results/
│   ├── lpc_usability_descriptives.csv
│   ├── lpc_usability_pairwise_gee.csv
│   ├── lpc_adapted_usability_scores.csv
│   ├── lpc_adapted_usability_items.csv
│   ├── lpc_stress_descriptives.csv
│   ├── lpc_stress_pairwise_wilcoxon.csv
│   ├── lpc_device_stress_scores.csv
│   ├── lpc_post_preferences.csv
│   ├── lpc_guidewire_preference.csv
│   └── lpc_survey_inference_summary.txt
└── figures/
    └── figure5_surveys_composite.png
```

## Data availability

**Raw participant-level survey responses are not deposited here.** They combine age band, gender,
job title, clinical setting and years of experience for 27 clinicians recruited through named
Irish hospital networks, and that combination could permit re-identification. Aggregate outputs
sufficient to reproduce every reported statistic are included in `results/`.

Raw responses may be requested from the corresponding author, subject to ethical approval and
institutional data-sharing agreements.

## Ethics

Approved by the Clinical Research Ethics Committee at the University of Galway (C.A. 3392) before
data collection began. Written informed consent was obtained from all participants.

## Requirements

```
Python >= 3.9
numpy, pandas, scipy, statsmodels, openpyxl
matplotlib, seaborn   # figures
```

## Citation

Manuscript reference to be added on acceptance.

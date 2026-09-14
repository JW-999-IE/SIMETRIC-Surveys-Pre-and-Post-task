from __future__ import annotations

import argparse
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.stats.multitest import multipletests
from scipy.stats import friedmanchisquare, wilcoxon, chi2, norm


EXCLUDED = {"P7", "P8", "P14"}
HIGHER = {"P1", "P3", "P9", "P12", "P29"}
SOME = {"P2", "P4", "P5", "P6", "P10", "P11", "P16", "P24", "P28"}

LIKERT = {
    "strongly disagree": 1,
    "disagree": 2,
    "neither agree nor disagree": 3,
    "agree": 4,
    "strongly agree": 5,
}
STRESS = {
    "not at all": 1,
    "slightly": 2,
    "moderately": 3,
    "very": 4,
    "very much": 4,
    "extremely": 5,
}


def pnorm(v):
    m = re.search(r"(\d+)", str(v))
    return f"P{int(m.group(1))}" if m else str(v).strip()


def experience(p):
    p = pnorm(p)
    if p in HIGHER: return "Higher"
    if p in SOME: return "Some"
    return "None"


def norm_text(v):
    return " ".join(str(v).replace("\xa0", " ").strip().lower().split())


def score_likert(v):
    return LIKERT.get(norm_text(v), np.nan)


def score_stress(v):
    s = norm_text(v)
    for k, val in STRESS.items():
        if s == k:
            return val
    return np.nan


def excel_col_index(ref):
    m = re.match(r"([A-Z]+)", ref)
    n = 0
    for ch in m.group(1):
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def strict_sheet(path: Path, wanted: str) -> pd.DataFrame:
    ns = "htt<SET_YOUR_ANALYSIS_ROOT>"
    relns = "htt<SET_YOUR_ANALYSIS_ROOT>"
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall(f"{{{ns}}}si"):
                shared.append("".join((t.text or "") for t in si.iter(f"{{{ns}}}t")))

        wb = ET.fromstring(z.read("xl/workbook.xml"))
        sheets = wb.find(f"{{{ns}}}sheets")
        rid = None
        for s in sheets:
            if s.attrib.get("name") == wanted:
                rid = s.attrib[f"{{{relns}}}id"]
                break
        if rid is None:
            raise KeyError(wanted)

        relroot = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = None
        for r in relroot:
            if r.attrib.get("Id") == rid:
                target = "xl/" + r.attrib["Target"]
                break
        root = ET.fromstring(z.read(target))

        rows = []
        width = 0
        for row in root.findall(f".//{{{ns}}}sheetData/{{{ns}}}row"):
            vals = {}
            for c in row.findall(f"{{{ns}}}c"):
                idx = excel_col_index(c.attrib["r"])
                typ = c.attrib.get("t")
                v = c.find(f"{{{ns}}}v")
                val = None
                if typ == "s" and v is not None:
                    val = shared[int(v.text)]
                elif typ == "inlineStr":
                    t = c.find(f".//{{{ns}}}t")
                    val = t.text if t is not None else ""
                elif v is not None:
                    val = v.text
                vals[idx] = val
                width = max(width, idx + 1)
            arr = [None] * width
            for i, val in vals.items():
                if i >= len(arr):
                    arr.extend([None] * (i - len(arr) + 1))
                arr[i] = val
            rows.append(arr)

        width = max([len(r) for r in rows], default=0)
        rows = [r + [None] * (width - len(r)) for r in rows]
        if not rows:
            return pd.DataFrame()
        header = rows[0]
        return pd.DataFrame(rows[1:], columns=header)


def read_sheet(path: Path, sheet: str):
    try:
        x = pd.read_excel(path, sheet_name=sheet, dtype=object)
        if len(x.columns):
            return x
    except Exception:
        pass
    return strict_sheet(path, sheet)


def find_col(df, include, exclude=()):
    """
    Match descriptive words by substring, but match LPC configuration labels
    (CON/ATG/MST) as standalone tokens. This prevents 'CON' from falsely
    matching the 'con' inside words such as 'inconsistency'.
    """
    include = [str(x).lower() for x in include]
    exclude = [str(x).lower() for x in exclude]
    device_tokens = {"con", "atg", "mst"}

    def has_term(s, term):
        if term in device_tokens:
            return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", s) is not None
        return term in s

    hits = []
    for c in df.columns:
        s = norm_text(c)
        if all(has_term(s, x) for x in include) and not any(has_term(s, x) for x in exclude):
            hits.append(c)

    if len(hits) != 1:
        raise RuntimeError(
            f"Column match failed include={include} exclude={exclude}: {hits}"
        )
    return hits[0]


def omnibus_device(result):
    names = list(result.params.index)
    idx = [
        i for i, n in enumerate(names)
        if "C(device" in str(n) and ("[T.ATG]" in str(n) or "[T.MST]" in str(n))
    ]
    b = result.params.to_numpy(float)[idx]
    cov = np.asarray(result.cov_params(), float)[np.ix_(idx, idx)]
    stat = float(b.T @ np.linalg.pinv(cov) @ b)
    return stat, float(chi2.sf(stat, len(idx)))


def pairwise_device(result):
    names = list(result.params.index)
    def term(level):
        h = [x for x in names if "C(device" in str(x) and f"[T.{level}]" in str(x)]
        return h[0] if len(h) == 1 else None
    rows = []
    for label, high, low in [
        ("MST_vs_CON", "MST", "CON"),
        ("ATG_vs_CON", "ATG", "CON"),
        ("MST_vs_ATG", "MST", "ATG"),
    ]:
        c = np.zeros(len(names))
        if high != "CON": c[names.index(term(high))] += 1
        if low != "CON": c[names.index(term(low))] -= 1
        b = float(c @ result.params.to_numpy(float))
        cov = np.asarray(result.cov_params(), float)
        se = np.sqrt(max(float(c @ cov @ c), 0))
        z = b / se if se > 0 else np.nan
        p = 2 * norm.sf(abs(z)) if np.isfinite(z) else np.nan
        rows.append({
            "contrast": label,
            "mean_difference_score_points": b,
            "ci95_low": b - 1.95996398454 * se,
            "ci95_high": b + 1.95996398454 * se,
            "p_raw": p,
        })
    q = pd.DataFrame(rows)
    _, adj, _, _ = multipletests(q["p_raw"], method="holm")
    q["p_holm"] = adj
    return q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--survey-workbook", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = Path(args.survey_workbook)

    demo = read_sheet(path, "demographic")
    pre = read_sheet(path, "pre-survey")
    post = read_sheet(path, "post-survey")

    for d in [demo, pre, post]:
        d["participant"] = d["Id"].map(pnorm)
        d.drop(d[d["participant"].isin(EXCLUDED)].index, inplace=True)
        d["experience_stratum"] = d["participant"].map(experience)

    # Post-survey device stress.
    stress_cols = {
        dev: find_col(post, ["stressed", dev.lower()])
        for dev in ["CON", "ATG", "MST"]
    }
    stress_long = []
    for _, r in post.iterrows():
        for dev, c in stress_cols.items():
            stress_long.append({
                "participant": r["participant"],
                "experience_stratum": r["experience_stratum"],
                "device": dev,
                "stress_score_1_5": score_stress(r[c]),
            })
    stress = pd.DataFrame(stress_long)

    # Adapted LPC usability index: 10 device-specific SUS-style items.
    concepts = [
        (["like", "frequently"], True),
        (["unnecessarily", "complex"], False),
        (["easy", "use"], True),
        (["support", "technical"], False),
        (["well", "integrated"], True),
        (["too", "much", "inconsistency"], False),
        (["learn", "very", "quickly"], True),
        (["cumbersome", "use"], False),
        (["confident", "using"], True),
        (["learn", "lot", "before"], False),
    ]

    usability_rows = []
    item_rows = []
    for _, r in post.iterrows():
        for dev in ["CON", "ATG", "MST"]:
            contributions = []
            for item_no, (words, positive) in enumerate(concepts, 1):
                c = find_col(post, words + [dev.lower()])
                response = score_likert(r[c])
                if np.isfinite(response):
                    contribution = response - 1 if positive else 5 - response
                else:
                    contribution = np.nan
                contributions.append(contribution)
                item_rows.append({
                    "participant": r["participant"],
                    "device": dev,
                    "item_number": item_no,
                    "response_1_5": response,
                    "positive_worded": positive,
                    "scored_0_4": contribution,
                })
            score = sum(contributions) * 2.5 if all(np.isfinite(contributions)) else np.nan
            usability_rows.append({
                "participant": r["participant"],
                "experience_stratum": r["experience_stratum"],
                "device": dev,
                "adapted_lpc_usability_index_0_100": score,
            })
    usability = pd.DataFrame(usability_rows)
    items = pd.DataFrame(item_rows)

    # GEE for usability.
    ud = usability.dropna().copy()
    model = smf.gee(
        'adapted_lpc_usability_index_0_100 ~ C(device, Treatment(reference="CON"))'
        ' + C(experience_stratum, Treatment(reference="None"))',
        groups="participant", data=ud,
        family=sm.families.Gaussian(), cov_struct=Exchangeable()
    )
    try:
        ur = model.fit(cov_type="bias_reduced")
        cov_type = "bias_reduced"
    except Exception:
        ur = model.fit(cov_type="robust")
        cov_type = "robust_fallback"
    ustat, up = omnibus_device(ur)
    upair = pairwise_device(ur)

    # Friedman sensitivity for usability and ordinal stress.
    upiv = usability.pivot(index="participant", columns="device", values="adapted_lpc_usability_index_0_100").dropna()
    uf = friedmanchisquare(upiv["CON"], upiv["ATG"], upiv["MST"]) if len(upiv) else None

    spiv = stress.pivot(index="participant", columns="device", values="stress_score_1_5").dropna()
    sf = friedmanchisquare(spiv["CON"], spiv["ATG"], spiv["MST"]) if len(spiv) else None
    spair_rows = []
    for label, a, b in [("MST_vs_CON", "MST", "CON"), ("ATG_vs_CON", "ATG", "CON"), ("MST_vs_ATG", "MST", "ATG")]:
        try:
            z = wilcoxon(spiv[a], spiv[b], zero_method="wilcox", alternative="two-sided")
            p = z.pvalue
        except Exception:
            p = np.nan
        spair_rows.append({"contrast": label, "p_raw": p})
    spair = pd.DataFrame(spair_rows)
    valid = spair["p_raw"].notna()
    if valid.any():
        _, adj, _, _ = multipletests(spair.loc[valid, "p_raw"], method="holm")
        spair.loc[valid, "p_holm"] = adj

    # Preferences.
    pref_fields = {
        "most_comfortable": "post_most_comfortable",
        "least_stressful": "post_least_stressful",
        "favourite": "post_favourite",
    }
    pref_rows = []
    for label, col in pref_fields.items():
        for value, n in post[col].fillna("").astype(str).value_counts().items():
            pref_rows.append({
                "question": label,
                "response": value,
                "n": int(n),
                "percent_of_27": 100 * n / len(post),
            })
    pref = pd.DataFrame(pref_rows)

    guide_col = find_col(post, ["prefer", "catheter", "guidewire"])
    guide = (
        post[guide_col].fillna("").astype(str).value_counts()
        .rename_axis("response").reset_index(name="n")
    )
    guide["percent_of_27"] = 100 * guide["n"] / len(post)

    # Four global post-simulation items.
    global_cols = {
        "more_confident_after_simulation": find_col(post, ["after", "simulation", "more", "confident"]),
        "improved_understanding": find_col(post, ["improved", "understanding", "differences"]),
        "enhanced_ultrasound_ability": find_col(post, ["enhanced", "ability", "ultrasound"]),
        "prepared_for_clinical_insertion": find_col(post, ["prepared", "perform"]),
    }
    global_rows = []
    for label, c in global_cols.items():
        vals = post[c].map(score_likert)
        global_rows.append({
            "outcome": label,
            "n": int(vals.notna().sum()),
            "mean_1_5": vals.mean(),
            "median_1_5": vals.median(),
            "agree_or_strongly_agree_n": int(vals.ge(4).sum()),
            "agree_or_strongly_agree_percent": 100 * vals.ge(4).mean(),
        })
    global_summary = pd.DataFrame(global_rows)

    # Baseline LPC experience / attitudes, renamed to LPC-facing outputs.
    baseline = pd.DataFrame({
        "participant": pre["participant"],
        "experience_stratum": pre["experience_stratum"],
        "age": pre.get("age", ""),
        "gender": pre.get("gender", ""),
        "clinical_experience": pre.get("clinical_experience", ""),
        "vascular_access_experience": pre.get("va_exp", ""),
        "prior_lpc_insertions_last_year": pre.get("Approximately how many MLC catheters have you inserted in the last year?", pre.get("n_mlc", "")),
        "usual_lpc_technique": pre.get("Which MLC catheter insertion technique do you most commonly use?", ""),
        "ultrasound_confidence": pre.get("How confident are you in using ultrasound machine?", ""),
    })

    usability_desc = (
        usability.groupby("device")["adapted_lpc_usability_index_0_100"]
        .agg(["count", "mean", "std", "median"])
        .reset_index()
    )
    stress_desc = (
        stress.groupby("device")["stress_score_1_5"]
        .agg(["count", "mean", "std", "median"])
        .reset_index()
    )

    usability.to_csv(out / "lpc_adapted_usability_scores.csv", index=False)
    items.to_csv(out / "lpc_adapted_usability_items.csv", index=False)
    stress.to_csv(out / "lpc_device_stress_scores.csv", index=False)
    pref.to_csv(out / "lpc_post_preferences.csv", index=False)
    guide.to_csv(out / "lpc_guidewire_preference.csv", index=False)
    global_summary.to_csv(out / "lpc_post_global_simulation_outcomes.csv", index=False)
    baseline.to_csv(out / "lpc_pre_simulation_baseline.csv", index=False)
    usability_desc.to_csv(out / "lpc_usability_descriptives.csv", index=False)
    stress_desc.to_csv(out / "lpc_stress_descriptives.csv", index=False)
    upair.to_csv(out / "lpc_usability_pairwise_gee.csv", index=False)
    spair.to_csv(out / "lpc_stress_pairwise_wilcoxon.csv", index=False)

    with open(out / "lpc_survey_inference_summary.txt", "w", encoding="utf-8") as f:
        f.write(f"Usability GEE covariance: {cov_type}\n")
        f.write(f"Usability omnibus device Wald chi2={ustat:.6g}, p={up:.6g}\n")
        if uf:
            f.write(f"Usability Friedman chi2={uf.statistic:.6g}, p={uf.pvalue:.6g}\n")
        if sf:
            f.write(f"Stress Friedman chi2={sf.statistic:.6g}, p={sf.pvalue:.6g}\n")
        f.write("The adapted LPC usability index uses SUS-style polarity/scoring but is not claimed to be a formally validated SUS instrument.\n")
        f.write("The questionnaire does not directly measure acceptability of the eye-tracking technology itself.\n")

    print("=== LPC PRE/POST SURVEY ANALYSIS COMPLETE ===")
    print("Included clinicians:", len(post))
    print()
    print("Adapted LPC usability descriptives:")
    print(usability_desc.to_string(index=False))
    print(f"Usability device omnibus: chi2={ustat:.3f}, p={up:.6g}")
    print(upair.to_string(index=False))
    print()
    print("Stress descriptives:")
    print(stress_desc.to_string(index=False))
    if sf:
        print(f"Stress Friedman: chi2={sf.statistic:.3f}, p={sf.pvalue:.6g}")
    print(spair.to_string(index=False))
    print()
    print("Global post-simulation outcomes:")
    print(global_summary.to_string(index=False))
    print()
    print("NOTE: outputs use LPC terminology; legacy wording is accessed only internally to read the source workbook.")

if __name__ == "__main__":
    main()

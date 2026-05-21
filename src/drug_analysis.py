import pandas as pd
import numpy as np
import warnings as pywarnings
from scipy.optimize import OptimizeWarning, curve_fit

from src.validation import validate_drug_response_df
from src.llm_helper import call_llm

EXPLANATION_LEVEL_OPTIONS = [
    "Simple",
    "Undergraduate Biochemistry",
    "Research Assistant",
    "Lab Report Style",
    "Poster Caption",
]


def load_drug_response_csv(file_path) -> pd.DataFrame:
    return pd.read_csv(file_path)


def summarize_drug_response(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["drug_name", "concentration_uM"])
          .agg(
              mean_viability=("cell_viability_percent", "mean"),
              sd_viability=("cell_viability_percent", "std"),
              n=("cell_viability_percent", "count"),
          )
          .reset_index()
    )

    summary["sem_viability"] = summary["sd_viability"] / (summary["n"] ** 0.5)
    return summary


def build_drug_response_cards(df: pd.DataFrame, summary_df: pd.DataFrame) -> dict:
    if summary_df.empty:
        return {}

    strongest_row = summary_df.sort_values("mean_viability").iloc[0]

    return {
        "drugs_detected": int(df["drug_name"].nunique()),
        "concentrations_tested": int(df["concentration_uM"].nunique()),
        "total_samples": int(len(df)),
        "strongest_observed_response": (
            f"{strongest_row['drug_name']} at {strongest_row['concentration_uM']} uM"
        ),
        "missing_values": int(df.isna().sum().sum()),
    }


def build_summary_markdown(summary_df: pd.DataFrame, warnings: list[str]) -> str:
    md = "## Drug Response Summary\n\n"
    md += summary_df.to_markdown(index=False)
    md += "\n\n## Data Quality Warnings\n\n"

    if warnings:
        for warning in warnings:
            md += f"- {warning}\n"
    else:
        md += "- No major data quality warnings detected.\n"

    return md


def _four_parameter_logistic(x, bottom, top, ic50, hill_slope):
    return bottom + (top - bottom) / (1 + (x / ic50) ** hill_slope)


def fit_ic50_curves(summary_df: pd.DataFrame) -> tuple[pd.DataFrame, list[str], pd.DataFrame]:
    if summary_df.empty:
        return pd.DataFrame(), [], pd.DataFrame()

    fit_rows: list[dict] = []
    fit_warnings: list[str] = []
    fit_curve_rows: list[dict] = []

    for drug_name, group in summary_df.groupby("drug_name"):
        ordered = group.sort_values("concentration_uM")
        positive_group = ordered[ordered["concentration_uM"] > 0].copy()

        if positive_group["concentration_uM"].nunique() < 4:
            fit_warnings.append(
                f"{drug_name}: IC50 fit skipped because fewer than 4 positive concentrations were available."
            )
            continue

        x = positive_group["concentration_uM"].to_numpy(dtype=float)
        y = positive_group["mean_viability"].to_numpy(dtype=float)

        if np.ptp(y) < 20:
            fit_warnings.append(
                f"{drug_name}: dynamic range is small, so IC50 estimates may be unstable."
            )

        if np.any(np.diff(y) > 5):
            fit_warnings.append(
                f"{drug_name}: response is not consistently decreasing across concentrations, so fit quality should be reviewed manually."
            )

        initial_guess = [max(0.0, float(y.min())), min(150.0, float(y.max())), float(np.median(x)), 1.0]
        lower_bounds = [-20.0, 0.0, max(float(x.min()) * 0.01, 1e-6), 0.1]
        upper_bounds = [150.0, 200.0, float(x.max()) * 100.0, 5.0]

        try:
            with pywarnings.catch_warnings(record=True) as caught_warnings:
                pywarnings.simplefilter("always", OptimizeWarning)
                params, covariance = curve_fit(
                    _four_parameter_logistic,
                    x,
                    y,
                    p0=initial_guess,
                    bounds=(lower_bounds, upper_bounds),
                    maxfev=20000,
                )
        except Exception as exc:
            fit_warnings.append(f"{drug_name}: IC50 fit failed ({exc}).")
            continue

        if any(issubclass(w.category, OptimizeWarning) for w in caught_warnings):
            fit_warnings.append(
                f"{drug_name}: optimizer reported uncertain parameter covariance; treat the IC50 estimate as provisional."
            )

        bottom, top, ic50, hill_slope = [float(value) for value in params]
        predictions = _four_parameter_logistic(x, *params)
        ss_res = float(np.sum((y - predictions) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r_squared = 1.0 - ss_res / ss_tot if ss_tot else np.nan
        rmse = float(np.sqrt(np.mean((y - predictions) ** 2)))

        if np.isfinite(r_squared) and r_squared < 0.85:
            fit_warnings.append(
                f"{drug_name}: IC50 fit has low R^2 ({r_squared:.2f}); inspect the curve before reporting it."
            )

        if ic50 < float(x.min()) or ic50 > float(x.max()):
            fit_warnings.append(
                f"{drug_name}: fitted IC50 ({ic50:.3g} uM) falls outside the tested concentration range."
            )

        if not np.all(np.isfinite(np.diag(covariance))):
            fit_warnings.append(
                f"{drug_name}: fit covariance could not be estimated reliably; parameter uncertainty may be high."
            )

        fit_rows.append(
            {
                "drug_name": drug_name,
                "ic50_uM": ic50,
                "hill_slope": hill_slope,
                "top_response": top,
                "bottom_response": bottom,
                "r_squared": r_squared,
                "rmse": rmse,
            }
        )

        curve_x = np.geomspace(float(x.min()), float(x.max()), 120)
        curve_y = _four_parameter_logistic(curve_x, *params)
        for curve_conc, curve_value in zip(curve_x, curve_y):
            fit_curve_rows.append(
                {
                    "drug_name": drug_name,
                    "concentration_uM": curve_conc,
                    "predicted_viability": float(curve_value),
                }
            )

    return pd.DataFrame(fit_rows), fit_warnings, pd.DataFrame(fit_curve_rows)


def build_ic50_markdown(fit_df: pd.DataFrame, fit_warnings: list[str]) -> str:
    md = "## IC50 Fit Summary\n\n"
    if fit_df.empty:
        md += "No IC50 fits were generated.\n"
    else:
        rounded_df = fit_df.copy()
        for column in ["ic50_uM", "hill_slope", "top_response", "bottom_response", "r_squared", "rmse"]:
            rounded_df[column] = rounded_df[column].round(3)
        md += rounded_df.to_markdown(index=False)
        md += "\n"

    md += "\n## IC50 Fit Warnings\n\n"
    if fit_warnings:
        for warning in fit_warnings:
            md += f"- {warning}\n"
    else:
        md += "- No major IC50 fit warnings detected.\n"

    return md


def _default_next_experiment_suggestions() -> list[str]:
    return [
        "Add more biological replicates to improve confidence in the observed trend.",
        "Confirm that vehicle, untreated, and assay-specific controls behave as expected.",
        "Test intermediate concentrations around the apparent transition region to refine the response curve.",
    ]


def _default_challenge_questions() -> list[str]:
    return [
        "What is the independent variable in this experiment?",
        "What is the dependent variable being measured?",
        "Why are biological or technical replicates important for interpretation?",
        "What does the error bar represent in this plot?",
        "Why should we avoid claiming a drug is effective based only on this dataset?",
        "What additional control or follow-up experiment would strengthen the conclusion?",
    ]


def _normalize_explanation_level(explanation_level: str | None) -> str:
    if explanation_level in EXPLANATION_LEVEL_OPTIONS:
        return explanation_level
    return "Undergraduate Biochemistry"


def _explanation_level_instruction(explanation_level: str) -> str:
    instructions = {
        "Simple": "Use short sentences, minimal jargon, and student-friendly wording.",
        "Undergraduate Biochemistry": "Use clear undergraduate biochemistry language with moderate scientific vocabulary.",
        "Research Assistant": "Use more technical wording appropriate for a new research assistant while staying cautious.",
        "Lab Report Style": "Write in a concise, formal style suitable for a lab report draft.",
        "Poster Caption": "Keep the wording compact, presentation-friendly, and suitable for a poster or slide handout.",
    }
    return instructions[_normalize_explanation_level(explanation_level)]


def generate_rule_based_interpretation(
    summary_df: pd.DataFrame,
    warnings: list[str],
    explanation_level: str | None = None,
) -> str:
    if summary_df.empty:
        return "No interpretation is available because the summary table is empty."

    normalized_level = _normalize_explanation_level(explanation_level)
    lines = ["## Plain-English Summary", ""]
    drugs = list(summary_df["drug_name"].dropna().unique())

    if len(drugs) >= 2:
        final_rows = (
            summary_df.sort_values(["drug_name", "concentration_uM"])
            .groupby("drug_name", as_index=False)
            .tail(1)
            .sort_values("mean_viability")
        )
        strongest = final_rows.iloc[0]
        weakest = final_rows.iloc[-1]
        lines.append(
            f"In this dataset, {strongest['drug_name']} shows the strongest reduction in cell viability at the highest tested concentration."
        )
        lines.append(
            f"Compared with {weakest['drug_name']}, the response appears stronger overall for {strongest['drug_name']}."
        )
    else:
        drug_name = drugs[0] if drugs else "the drug"
        lines.append(
            f"In this dataset, {drug_name} shows a concentration-dependent pattern that can be reviewed in the summary statistics and plot."
        )

    lines.extend(
        [
            "",
            "## Key Observations",
            "",
        ]
    )

    for drug_name, group in summary_df.groupby("drug_name"):
        ordered = group.sort_values("concentration_uM")
        start_viability = ordered.iloc[0]["mean_viability"]
        end_viability = ordered.iloc[-1]["mean_viability"]
        delta = start_viability - end_viability
        lines.append(
            f"- {drug_name}: mean viability changes from {start_viability:.1f}% to {end_viability:.1f}% across the tested range, a decrease of {delta:.1f} percentage points."
        )

    lines.extend(
        [
            "",
            "## Results Paragraph Draft",
            "",
        ]
    )

    if len(drugs) >= 2:
        final_rows = (
            summary_df.sort_values(["drug_name", "concentration_uM"])
            .groupby("drug_name", as_index=False)
            .tail(1)
            .sort_values("mean_viability")
        )
        strongest = final_rows.iloc[0]
        weakest = final_rows.iloc[-1]
        lines.append(
            f"In this dataset, mean cell viability decreases across the tested concentration range, with {strongest['drug_name']} showing the lowest viability at the highest tested concentration compared with {weakest['drug_name']}. These summary-level results are consistent with a stronger apparent dose-response pattern for {strongest['drug_name']}, although the findings still require manual review of assay quality, controls, and replicate behavior."
        )
    else:
        drug_name = drugs[0] if drugs else "the drug"
        ordered = summary_df.sort_values("concentration_uM")
        lines.append(
            f"In this dataset, {drug_name} shows a change in mean cell viability across the tested concentration range. The summary-level pattern is consistent with an apparent dose-response trend, but the result should be treated as a preliminary observation until controls, replicate quality, and assay conditions are checked manually."
        )

    if normalized_level == "Simple":
        lines.extend(
            [
                "",
                "Use this as a simple study note: describe the pattern first, then mention at least one limitation before making any claim.",
            ]
        )
    elif normalized_level == "Research Assistant":
        lines.extend(
            [
                "",
                "Use this as a technical practice draft: separate observations from interpretation and keep assay limitations visible.",
            ]
        )
    elif normalized_level == "Lab Report Style":
        lines.extend(
            [
                "",
                "Use this as a formal draft that can be revised into a Results or Discussion section.",
            ]
        )
    elif normalized_level == "Poster Caption":
        lines.extend(
            [
                "",
                "Use this as compact presentation support and trim wording further if space is limited.",
            ]
        )

    lines.extend(
        [
            "",
            "## Possible Biological Interpretation",
            "",
            "The pattern is consistent with a dose-dependent response in this assay, but it should be treated as an initial observation rather than a biological conclusion.",
            "",
            "## Discussion Paragraph Draft",
            "",
            "A cautious discussion should note that the observed trend may reflect a drug-associated response, while also emphasizing that summary-level patterns alone do not establish mechanism, selectivity, or reproducibility. Interpretation should stay tied to the assay context, replicate quality, and the need for proper controls and follow-up validation.",
            "",
            "## Limitations",
            "",
        ]
    )

    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.extend(
            [
                "- This project uses summary-level analysis only and does not fit an IC50 curve.",
                "- Replicate counts are small, so apparent differences may not be stable.",
                "- Experimental controls and assay conditions still need manual review.",
            ]
        )

    lines.extend(
        [
            "",
            "## Next Experiment Suggestions",
            "",
        ]
    )

    for suggestion in _default_next_experiment_suggestions():
        lines.append(f"- {suggestion}")

    lines.extend(
        [
            "",
            "## What to Verify Manually",
            "",
            "- Confirm that concentration units and viability units are correct.",
            "- Check whether the dataset is synthetic or experimental.",
            "- Review replicate quality, outliers, and assay controls before reporting conclusions.",
            "",
            "## Challenge Questions",
            "",
        ]
    )

    for question in _default_challenge_questions():
        lines.append(f"- {question}")

    return "\n".join(lines)


def generate_rule_based_figure_caption(summary_df: pd.DataFrame) -> str:
    if summary_df.empty:
        return "Figure caption unavailable because the summary table is empty."

    parts = [
        "Dose-response plot showing mean cell viability across tested concentrations for each drug."
    ]

    final_rows = (
        summary_df.sort_values(["drug_name", "concentration_uM"])
        .groupby("drug_name", as_index=False)
        .tail(1)
        .sort_values("mean_viability")
    )

    if not final_rows.empty:
        strongest = final_rows.iloc[0]
        parts.append(
            f"At the highest tested concentration, {strongest['drug_name']} shows the lowest mean viability ({strongest['mean_viability']:.1f}%)."
        )

    if "sem_viability" in summary_df.columns:
        parts.append("Error bars represent the standard error of the mean.")

    parts.append(
        "This figure supports an initial review of dose-dependent trends but should not be treated as conclusive biological evidence without manual validation."
    )

    return " ".join(parts)


def analyze_drug_response(file_path) -> dict:
    df = load_drug_response_csv(file_path)
    warnings = validate_drug_response_df(df)

    if any(w.startswith("Missing required columns") for w in warnings):
        return {
            "df": df,
            "summary_df": pd.DataFrame(),
            "fit_df": pd.DataFrame(),
            "fit_warnings": [],
            "fit_curve_df": pd.DataFrame(),
            "warnings": warnings,
            "cards": {},
            "summary_markdown": "",
        }

    summary_df = summarize_drug_response(df)
    fit_df, fit_warnings, fit_curve_df = fit_ic50_curves(summary_df)
    cards = build_drug_response_cards(df, summary_df)
    summary_markdown = build_summary_markdown(summary_df, warnings)
    summary_markdown += "\n\n" + build_ic50_markdown(fit_df, fit_warnings)

    return {
        "df": df,
        "summary_df": summary_df,
        "fit_df": fit_df,
        "fit_warnings": fit_warnings,
        "fit_curve_df": fit_curve_df,
        "warnings": warnings,
        "cards": cards,
        "summary_markdown": summary_markdown,
    }


def generate_ai_drug_response_explanation(summary_markdown: str, explanation_level: str | None = None) -> str:
    normalized_level = _normalize_explanation_level(explanation_level)
    system_prompt = '''
You are an AI assistant helping a third-year undergraduate Biochemistry student.
Explain drug response results clearly and cautiously.
Do not overstate conclusions.
If the dataset is synthetic, say so clearly.
Separate observations from interpretations.
Always include limitations and what to verify manually.
Do not give clinical or medical advice.
'''

    user_prompt = f'''
The following summary statistics come from a drug response / cell viability dataset:

{summary_markdown}

Explanation level: {normalized_level}
Style instruction: {_explanation_level_instruction(normalized_level)}

Please write:

## Plain-English Summary
## Key Observations
## Results Paragraph Draft
## Possible Biological Interpretation
## Discussion Paragraph Draft
## Limitations
## Next Experiment Suggestions
## What to Verify Manually
## Challenge Questions
'''

    return call_llm(system_prompt, user_prompt)


def generate_rule_based_interpretation_feedback(
    student_interpretation: str,
    summary_df: pd.DataFrame,
    warnings: list[str],
) -> str:
    interpretation_text = student_interpretation.strip()
    if not interpretation_text:
        return "Please enter your interpretation first."

    lower_text = interpretation_text.lower()
    strengths: list[str] = []
    suggestions: list[str] = []

    final_rows = (
        summary_df.sort_values(["drug_name", "concentration_uM"])
        .groupby("drug_name", as_index=False)
        .tail(1)
        .sort_values("mean_viability")
        if not summary_df.empty
        else pd.DataFrame()
    )

    if any(term in lower_text for term in ["dose-dependent", "dose dependent", "concentration-dependent", "concentration dependent"]):
        strengths.append("You identified a possible dose-response pattern instead of describing the data as random.")
    else:
        suggestions.append("Mention whether the pattern appears dose-dependent across the tested concentrations.")

    if any(term in lower_text for term in ["limitation", "caution", "however", "preliminary"]):
        strengths.append("You used cautious language rather than presenting the result as final proof.")
    else:
        suggestions.append("Add a caution statement or limitation so the interpretation stays scientifically responsible.")

    if "synthetic" in lower_text:
        strengths.append("You acknowledged that the built-in teaching scenarios are synthetic when that is relevant.")
    else:
        suggestions.append("State whether the dataset is synthetic or user-supplied so the reader understands the evidence context.")

    if any(term in lower_text for term in ["replicate", "replicates", "control", "controls", "assay"]):
        strengths.append("You connected the interpretation to experimental design details such as controls, replicates, or assay context.")
    else:
        suggestions.append("Refer to controls, replicates, or assay context to show what still needs verification.")

    if any(term in lower_text for term in ["effective", "cure", "safe", "proves", "proven"]):
        suggestions.append("Avoid strong words like 'effective', 'safe', or 'proves' unless the evidence really supports them.")
    else:
        strengths.append("You avoided obviously over-claiming language.")

    if warnings:
        suggestions.append("Incorporate the data-quality warnings into your interpretation before treating the result as strong evidence.")

    if not final_rows.empty:
        lead_drug = str(final_rows.iloc[0]["drug_name"])
        if lead_drug.lower() in lower_text:
            strengths.append(f"You referenced the apparent lead compound ({lead_drug}) instead of staying too vague.")
        else:
            suggestions.append(f"Name the apparent lead compound ({lead_drug}) if you want the interpretation to feel more specific.")

    strengths = strengths[:4]
    suggestions = suggestions[:5]

    lines = ["## Strengths", ""]
    if strengths:
        lines.extend(f"- {item}" for item in strengths)
    else:
        lines.append("- You made a start by drafting an interpretation that can now be revised more scientifically.")

    lines.extend(["", "## Suggestions", ""])
    if suggestions:
        lines.extend(f"- {item}" for item in suggestions)
    else:
        lines.append("- Your draft already covers the main teaching points; the next step is tightening wording for clarity.")

    return "\n".join(lines)


def generate_ai_interpretation_feedback(
    summary_markdown: str,
    student_interpretation: str,
    explanation_level: str | None = None,
) -> str:
    normalized_level = _normalize_explanation_level(explanation_level)
    system_prompt = '''
You are an AI assistant helping a third-year undergraduate Biochemistry student improve their own written interpretation.
Give feedback that is supportive, specific, and scientifically cautious.
Do not rewrite the whole interpretation unless needed.
Focus on strengths first, then clear suggestions.
Do not give clinical or medical advice.
'''

    user_prompt = f'''
The following summary statistics come from a drug response / cell viability dataset:

{summary_markdown}

The student wrote this interpretation:

{student_interpretation}

Explanation level: {normalized_level}
Style instruction: {_explanation_level_instruction(normalized_level)}

Please respond with:

## Strengths
## Suggestions

Keep the feedback encouraging and specific.
'''

    return call_llm(system_prompt, user_prompt)


def generate_rule_based_lab_assistant_message(
    summary_df: pd.DataFrame,
    warnings: list[str],
    is_synthetic: bool = True,
) -> str:
    if summary_df.empty:
        return "BioDose Assistant says: Run the Python analysis first so I can comment on the current dataset."

    final_rows = (
        summary_df.sort_values(["drug_name", "concentration_uM"])
        .groupby("drug_name", as_index=False)
        .tail(1)
        .sort_values("mean_viability")
    )

    if final_rows.empty:
        return "BioDose Assistant says: I could not identify a clear end-point comparison from the current summary table yet."

    lead_row = final_rows.iloc[0]
    lead_drug = str(lead_row["drug_name"])
    lead_viability = float(lead_row["mean_viability"])
    concentration = lead_row["concentration_uM"]

    caution = (
        "This built-in scenario is synthetic, so treat the pattern as practice evidence only."
        if is_synthetic
        else "If this is a real dataset, confirm controls, units, and assay conditions before using this wording in a report."
    )

    if warnings:
        review_note = "Data-quality review is still important because the current dataset triggered one or more warnings."
    else:
        review_note = "The dataset passed the main automatic checks, but manual review is still important before drawing stronger conclusions."

    return (
        f"BioDose Assistant says: {lead_drug} appears to show the strongest reduction in viability at the highest tested concentration "
        f"({lead_viability:.1f}% at {concentration} uM). {caution} {review_note}"
    )


def generate_ai_lab_assistant_message(
    summary_markdown: str,
    is_synthetic: bool = True,
) -> str:
    system_prompt = '''
You are BioDose Assistant, a friendly and professional scientific helper for a third-year undergraduate Biochemistry student.
Write one short paragraph.
Keep the tone calm, encouraging, and scientifically responsible.
Do not sound childish.
Do not give clinical or medical advice.
'''

    user_prompt = f'''
The following summary statistics come from a drug response / cell viability dataset:

{summary_markdown}

Dataset context: {"Synthetic teaching scenario" if is_synthetic else "User-supplied dataset"}

Please write a short assistant message starting with:
BioDose Assistant says:

The message should:
- mention the most important observed pattern
- include one caution about interpretation
- suggest one thing to verify manually
'''

    return call_llm(system_prompt, user_prompt)


def generate_ai_figure_caption(summary_markdown: str) -> str:
    system_prompt = '''
You are an AI assistant helping a third-year undergraduate Biochemistry student.
Write a short, cautious scientific figure caption.
Do not overstate conclusions.
If the dataset is synthetic, say so clearly when relevant.
Do not give clinical or medical advice.
'''

    user_prompt = f'''
The following summary statistics come from a drug response / cell viability dataset:

{summary_markdown}

Please write a concise figure caption for a dose-response plot.
Mention the overall pattern, clarify that the figure is summary-level, and use cautious scientific wording.
'''

    return call_llm(system_prompt, user_prompt)

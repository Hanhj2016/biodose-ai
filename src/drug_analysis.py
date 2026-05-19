import pandas as pd
import numpy as np
import warnings as pywarnings
from scipy.optimize import OptimizeWarning, curve_fit

from src.validation import validate_drug_response_df
from src.llm_helper import call_llm


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


def generate_rule_based_interpretation(summary_df: pd.DataFrame, warnings: list[str]) -> str:
    if summary_df.empty:
        return "No interpretation is available because the summary table is empty."

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
            "## Possible Biological Interpretation",
            "",
            "The pattern is consistent with a dose-dependent response in this assay, but it should be treated as an initial observation rather than a biological conclusion.",
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
            "## What to Verify Manually",
            "",
            "- Confirm that concentration units and viability units are correct.",
            "- Check whether the dataset is synthetic or experimental.",
            "- Review replicate quality, outliers, and assay controls before reporting conclusions.",
        ]
    )

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


def generate_ai_drug_response_explanation(summary_markdown: str) -> str:
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

Please write:

## Plain-English Summary
## Key Observations
## Possible Biological Interpretation
## Limitations
## What to Verify Manually
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

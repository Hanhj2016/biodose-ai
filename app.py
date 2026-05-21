from datetime import date
from pathlib import Path

import gradio as gr
import pandas as pd

from src.assay_templates import (
    ASSAY_TEMPLATE_OPTIONS,
    get_assay_template_guidance,
    save_assay_template_csv,
)
from src.drug_analysis import (
    EXPLANATION_LEVEL_OPTIONS,
    analyze_drug_response,
    generate_ai_figure_caption,
    generate_ai_drug_response_explanation,
    generate_ai_interpretation_feedback,
    generate_ai_lab_assistant_message,
    generate_rule_based_figure_caption,
    generate_rule_based_interpretation,
    generate_rule_based_interpretation_feedback,
    generate_rule_based_lab_assistant_message,
)
from src.export_utils import (
    save_academic_sections_bundle,
    save_markdown_section,
    save_markdown_summary,
    save_report_bundle,
    save_summary_csv,
)
from src.plots import create_dose_response_plot

EXAMPLE_FILE = Path("data/examples/drug_response_sample.csv")
SCENARIO_DATASETS = {
    "Clear Dose-Response": {
        "path": EXAMPLE_FILE,
        "teaches": "Basic interpretation with a clean synthetic two-compound screening pattern.",
    },
    "Weak Response": {
        "path": Path("data/examples/drug_response_weak_response.csv"),
        "teaches": "Avoid overclaiming when viability changes are small across the tested range.",
    },
    "Noisy Assay": {
        "path": Path("data/examples/drug_response_noisy_assay.csv"),
        "teaches": "Replicate variability can make a trend harder to trust even when a signal seems present.",
    },
    "Missing Replicate": {
        "path": Path("data/examples/drug_response_missing_replicate.csv"),
        "teaches": "A missing replicate should lower confidence and trigger data-quality review.",
    },
    "Similar Effect": {
        "path": Path("data/examples/drug_response_similar_effect.csv"),
        "teaches": "When compounds look close together, ranking should stay cautious and uncertainty should be discussed.",
    },
}
DEFAULT_SCENARIO = "Clear Dose-Response"
ACADEMIC_EXPORT_OPTIONS = [
    "Plain-English Summary",
    "Results Paragraph Draft",
    "Discussion Paragraph Draft",
    "Limitations",
    "Next Experiment Suggestions",
    "What to Verify Manually",
    "Challenge Questions",
]
ACADEMIC_SECTION_TITLES = [
    "Results Paragraph Draft",
    "Discussion Paragraph Draft",
    "Limitations",
    "Next Experiment Suggestions",
    "What to Verify Manually",
    "Challenge Questions",
]


def _final_response_rows(summary_df: pd.DataFrame) -> pd.DataFrame:
    if summary_df.empty:
        return pd.DataFrame()

    return (
        summary_df.sort_values(["drug_name", "concentration_uM"])
        .groupby("drug_name", as_index=False)
        .tail(1)
        .sort_values("mean_viability")
        .reset_index(drop=True)
    )


def get_scenario_details(scenario_name: str) -> dict:
    return SCENARIO_DATASETS.get(scenario_name, SCENARIO_DATASETS[DEFAULT_SCENARIO])


def format_cards(cards: dict) -> str:
    if not cards:
        return "<div class='metric-grid'><div class='metric-card'><p>No summary cards available.</p></div></div>"

    metric_items = [
        ("Drugs detected", cards.get("drugs_detected")),
        ("Concentrations tested", cards.get("concentrations_tested")),
        ("Total samples", cards.get("total_samples")),
        ("Strongest response", cards.get("strongest_observed_response")),
        ("Missing values", cards.get("missing_values")),
    ]

    card_html = []
    for label, value in metric_items:
        card_html.append(
            f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """
        )

    return f"<div class='metric-grid'>{''.join(card_html)}</div>"


def format_fit_warnings(warnings: list[str]) -> str:
    if not warnings:
        return """
<div class="callout callout-ok">
    <strong>IC50 Fit Review</strong>
    <p>No major IC50 fit warnings were detected.</p>
</div>
"""

    warning_items = "".join(f"<li>{warning}</li>" for warning in warnings)
    return f"""
<div class="callout callout-warn">
    <strong>IC50 Fit Review</strong>
    <p>Review these fit-quality warnings before reporting IC50 values:</p>
    <ul>{warning_items}</ul>
</div>
"""


def format_warnings(warnings: list[str]) -> str:
    if not warnings:
        return """
<div class="callout callout-ok">
    <strong>Quality Check</strong>
    <p>No major data-quality warnings were detected.</p>
</div>
"""

    warning_items = "".join(f"<li>{warning}</li>" for warning in warnings)
    return f"""
<div class="callout callout-warn">
    <strong>Quality Check</strong>
    <p>Review these items before interpreting the result:</p>
    <ul>{warning_items}</ul>
</div>
"""


def format_dataset_guidance(file_input) -> str:
    dataset_name = Path(normalize_file_path(file_input)).name if file_input else EXAMPLE_FILE.name
    is_sample = not file_input or dataset_name == EXAMPLE_FILE.name

    if is_sample:
        return f"""
<div class="callout callout-info">
    <strong>Dataset Context</strong>
    <p><code>{dataset_name}</code> is the built-in teaching dataset. Treat all findings as synthetic practice results, not real experimental evidence.</p>
</div>
"""

    return f"""
<div class="callout callout-info">
    <strong>Dataset Context</strong>
    <p><code>{dataset_name}</code> appears to be a user-supplied file. Confirm units, controls, assay conditions, and privacy expectations before using AI-generated text in a report.</p>
</div>
"""


def format_assay_guidance(assay_type: str) -> str:
    guidance = get_assay_template_guidance(assay_type)
    return (
        "<div class='callout callout-info'>"
        f"<strong>Assay Template</strong><div>{guidance.replace(chr(10), '<br>')}</div>"
        "</div>"
    )


def format_scenario_guidance(scenario_name: str) -> str:
    details = get_scenario_details(scenario_name)
    return "\n".join(
        [
            f"## Scenario: {scenario_name}",
            "",
            f"Teaching focus: {details['teaches']}",
            "",
            "For learning purposes only. These built-in scenarios use synthetic assay-style data and should be interpreted cautiously.",
        ]
    )


def format_badges(badges: list[str]) -> str:
    if not badges:
        return "<div class='metric-grid'><div class='metric-card'><p>No mission badges yet.</p></div></div>"

    badge_html = "".join(f"<span class='badge-chip'>{badge}</span>" for badge in badges)
    return f"<div class='badge-row'>{badge_html}</div>"


def normalize_file_path(file_input):
    if file_input is None:
        return str(EXAMPLE_FILE)

    if isinstance(file_input, dict) and file_input.get("name"):
        return file_input["name"]

    if hasattr(file_input, "name"):
        return file_input.name

    return str(file_input)


def resolve_analysis_file_path(file_input, scenario_name: str) -> str:
    if file_input is not None:
        return normalize_file_path(file_input)
    return str(get_scenario_details(scenario_name)["path"])


def empty_academic_outputs():
    return ("", "", "", "", "", "", "", "")


def split_markdown_sections(markdown_text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_title = None

    for line in markdown_text.splitlines():
        if line.startswith("## "):
            current_title = line[3:].strip()
            sections[current_title] = []
            continue

        if current_title is not None:
            sections[current_title].append(line)

    return {
        title: "\n".join(lines).strip()
        for title, lines in sections.items()
    }


def build_academic_outputs(explanation_markdown: str):
    if not explanation_markdown.strip():
        return empty_academic_outputs()

    sections = split_markdown_sections(explanation_markdown)
    return (
        explanation_markdown,
        sections.get("Results Paragraph Draft", ""),
        sections.get("Discussion Paragraph Draft", ""),
        sections.get("Limitations", ""),
        sections.get("Next Experiment Suggestions", ""),
        sections.get("What to Verify Manually", ""),
        sections.get("Challenge Questions", ""),
        sections.get("Plain-English Summary", ""),
    )


def export_selected_academic_section(
    selected_section,
    plain_summary,
    results_text,
    discussion_text,
    limitations_text,
    next_steps_text,
    verify_text,
    questions_text,
):
    section_map = {
        "Plain-English Summary": plain_summary,
        "Results Paragraph Draft": results_text,
        "Discussion Paragraph Draft": discussion_text,
        "Limitations": limitations_text,
        "Next Experiment Suggestions": next_steps_text,
        "What to Verify Manually": verify_text,
        "Challenge Questions": questions_text,
    }
    content = section_map.get(selected_section, "")
    return save_markdown_section(selected_section, content)


def export_all_academic_sections(
    plain_summary,
    results_text,
    discussion_text,
    limitations_text,
    next_steps_text,
    verify_text,
    questions_text,
):
    return save_academic_sections_bundle(
        {
            "Plain-English Summary": plain_summary,
            "Results Paragraph Draft": results_text,
            "Discussion Paragraph Draft": discussion_text,
            "Limitations": limitations_text,
            "Next Experiment Suggestions": next_steps_text,
            "What to Verify Manually": verify_text,
            "Challenge Questions": questions_text,
        }
    )


def build_data_quality_score(df: pd.DataFrame, warnings: list[str]) -> tuple[int, str]:
    if df.empty:
        return 0, "No data loaded yet"

    score = 0
    required_columns = {"sample_id", "drug_name", "concentration_uM", "replicate", "cell_viability_percent"}
    if required_columns.issubset(df.columns):
        score += 20
    if df.isna().sum().sum() == 0:
        score += 20
    if required_columns.issubset(df.columns):
        replicate_counts = df.groupby(["drug_name", "concentration_uM"]).size()
        if not replicate_counts.empty and (replicate_counts >= 3).all():
            score += 20
    if "concentration_uM" in df.columns and pd.api.types.is_numeric_dtype(df["concentration_uM"]) and df["concentration_uM"].nunique() > 1:
        score += 15
        if (df["concentration_uM"] == 0).any():
            score += 10

    critical_warning_markers = ("negative", "duplicate", "should be numeric", "missing")
    if not any(marker in warning.lower() for marker in critical_warning_markers for warning in warnings):
        score += 15

    if score >= 85:
        status = "Good for exploration; still not enough for a final biological conclusion."
    elif score >= 65:
        status = "Usable for practice, but review data-quality details before interpreting trends."
    else:
        status = "Needs manual cleanup or caution before using the result for comparison."

    return score, status


def build_candidate_ranking(summary_df: pd.DataFrame) -> str:
    final_rows = _final_response_rows(summary_df)
    if final_rows.empty:
        return "No candidate ranking is available yet."

    lines = ["## Candidate Ranking", ""]
    for idx, row in enumerate(final_rows.itertuples(index=False), start=1):
        lines.append(
            f"{idx}. {row.drug_name} — mean viability {row.mean_viability:.1f}% at {row.concentration_uM} uM."
        )
    lines.extend(
        [
            "",
            "Educational ranking based on summary-level assay data. This is not an efficacy, safety, or clinical conclusion.",
        ]
    )
    return "\n".join(lines)


def build_mission_badges(df: pd.DataFrame, summary_df: pd.DataFrame, warnings: list[str], fit_df: pd.DataFrame) -> list[str]:
    badges: list[str] = []
    if not df.empty:
        badges.append("Data Loaded")
    if summary_df.empty:
        return badges
    badges.append("Dose-Response Plot Generated")
    if len(summary_df["drug_name"].dropna().unique()) >= 2:
        badges.append("Compound Comparison Ready")
    if fit_df is not None and isinstance(fit_df, pd.DataFrame) and not fit_df.empty:
        badges.append("IC50 Fit Generated")
    if warnings:
        badges.append("Quality Check Needs Review")
    else:
        badges.append("Quality Check Passed")
    return badges


def build_mission_follow_up_checks(warnings: list[str], summary_df: pd.DataFrame) -> str:
    lines = ["## Follow-up Checks", ""]

    if warnings:
        for warning in warnings:
            lines.append(f"- Review: {warning}")
    else:
        lines.append("- Review controls, replicate consistency, and concentration units before reporting conclusions.")

    final_rows = _final_response_rows(summary_df)
    if not final_rows.empty:
        top_row = final_rows.iloc[0]
        lines.append(
            f"- Check whether the apparent lead compound ({top_row['drug_name']}) stays strongest when replicate variability and assay controls are reviewed."
        )
    lines.append("- If the trend looks important, test more concentrations around the transition region before making stronger claims.")
    return "\n".join(lines)


def build_mission_brief(file_input, cards: dict, score: int, status: str) -> str:
    dataset_name = Path(normalize_file_path(file_input)).name if file_input else EXAMPLE_FILE.name
    scenario_label = "Built-in teaching scenario" if dataset_name == EXAMPLE_FILE.name else "User-uploaded screening scenario"
    drugs = cards.get("drugs_detected", 0) or 0
    concentrations = cards.get("concentrations_tested", 0) or 0
    samples = cards.get("total_samples", 0) or 0

    return "\n".join(
        [
            "## Mission 1: Compound Screening Challenge",
            "",
            "Mission: Compare compound-screening results and decide what should be checked next.",
            "",
            f"- Scenario: {scenario_label}",
            f"- Dataset: `{dataset_name}`",
            f"- Compounds detected: {drugs}",
            f"- Concentration levels: {concentrations}",
            f"- Samples reviewed: {samples}",
            f"- Data Quality Score: {score} / 100",
            f"- Status: {status}",
        ]
    )


def build_mission_outputs(file_input, scenario_name: str, df: pd.DataFrame, summary_df: pd.DataFrame, warnings: list[str], cards: dict, fit_df: pd.DataFrame):
    score, status = build_data_quality_score(df, warnings)
    scenario_note = format_scenario_guidance(scenario_name) if file_input is None else "\n".join(
        [
            "## Scenario: User Upload",
            "",
            "Teaching focus: Review your own dataset with the same mission-style checklist and compare it with the built-in scenarios when helpful.",
            "",
            "User uploads may not be synthetic, so units, controls, privacy, and assay context need manual review.",
        ]
    )
    return (
        build_mission_brief(file_input, cards, score, status),
        scenario_note,
        f"## Data Quality Score\n\n**{score} / 100**\n\n{status}",
        build_candidate_ranking(summary_df),
        format_badges(build_mission_badges(df, summary_df, warnings, fit_df)),
        build_mission_follow_up_checks(warnings, summary_df),
    )


def build_lab_notebook_entry(
    file_input,
    scenario_name: str,
    assay_type: str,
    summary_markdown: str,
    plain_summary: str,
    results_text: str,
    interpretation_text: str,
    limitations_text: str,
    next_steps_text: str,
    verify_text: str,
    mission_brief: str,
    mission_ranking: str,
    figure_caption: str,
):
    if not summary_markdown.strip():
        return "Please run Python analysis first."

    dataset_name = Path(normalize_file_path(file_input)).name if file_input else get_scenario_details(scenario_name)["path"].name
    question = "Which compound appears strongest in this screening-style dataset, and what should be checked next?"
    observation = plain_summary or "Observation notes were not generated yet."
    interpretation_block = interpretation_text or results_text or "Interpretation draft was not generated yet."
    limitations_block = limitations_text or "- Add at least one limitation before finalizing the notebook entry."
    next_step_block = next_steps_text or "- Add a follow-up experiment suggestion."
    verification_block = verify_text or "- Confirm controls, units, and replicate quality."

    return "\n".join(
        [
            "# BioDose AI Lab Notebook Entry",
            "",
            f"Date: {date.today().isoformat()}",
            f"Dataset: {dataset_name}",
            f"Scenario: {scenario_name if file_input is None else 'User Upload'}",
            f"Assay Type: {assay_type}",
            "",
            "## Question",
            "",
            question,
            "",
            "## Method",
            "",
            "Loaded a dose-response dataset in BioDose AI, validated required columns, summarized replicate viability values, reviewed the interactive plot, and checked mission-style ranking and follow-up prompts.",
            "",
            "## Observation",
            "",
            observation,
            "",
            "## Interpretation",
            "",
            interpretation_block,
            "",
            "## Limitations",
            "",
            limitations_block,
            "",
            "## Next Step",
            "",
            next_step_block,
            "",
            "## Verification Checklist",
            "",
            verification_block,
            "",
            "## Mission Snapshot",
            "",
            mission_brief or "Mission brief unavailable.",
            "",
            mission_ranking or "Candidate ranking unavailable.",
            "",
            "## Figure Caption Draft",
            "",
            figure_caption or "Figure caption not generated yet.",
        ]
    )


def build_mini_poster(
    file_input,
    scenario_name: str,
    assay_type: str,
    plain_summary: str,
    results_text: str,
    limitations_text: str,
    next_steps_text: str,
    mission_brief: str,
    figure_caption: str,
    assistant_note: str,
):
    dataset_name = Path(normalize_file_path(file_input)).name if file_input else get_scenario_details(scenario_name)["path"].name
    if not plain_summary and not results_text and not mission_brief:
        return "Please run Python analysis first."

    scenario_label = scenario_name if file_input is None else "User Upload"
    title = f"BioDose AI Mini Poster: {scenario_label}"
    background = (
        "BioDose AI is a beginner-friendly compound-screening practice workflow that helps review dose-response patterns, compare compounds, and draft cautious scientific communication."
    )
    method = (
        f"The dataset `{dataset_name}` was analyzed in BioDose AI using grouped summary statistics, an interactive dose-response plot, mission-style comparison prompts, and cautious interpretation support for the {assay_type} assay context."
    )
    key_observation = plain_summary or results_text or "Key observation not generated yet."
    limitations_block = limitations_text or "- Add at least one limitation before using the poster draft."
    next_step_block = next_steps_text or "- Add one follow-up experiment recommendation."
    what_i_learned = (
        assistant_note.replace("BioDose Assistant says:", "").strip()
        if assistant_note.strip()
        else "This poster-style summary should still be checked against the raw data, controls, and replicate quality."
    )

    return "\n".join(
        [
            f"# {title}",
            "",
            "## Background",
            "",
            background,
            "",
            "## Method",
            "",
            method,
            "",
            "## Main Figure",
            "",
            "Use the interactive dose-response plot from BioDose AI as the main visual for this poster draft.",
            "",
            "## Key Observation",
            "",
            key_observation,
            "",
            "## Limitations",
            "",
            limitations_block,
            "",
            "## Next Step",
            "",
            next_step_block,
            "",
            "## What I Learned",
            "",
            what_i_learned,
            "",
            "## Figure Caption",
            "",
            figure_caption or "Figure caption not generated yet.",
            "",
            "## Mission Snapshot",
            "",
            mission_brief or "Mission brief unavailable.",
        ]
    )


def export_lab_notebook_entry(notebook_entry: str):
    if not notebook_entry.strip() or notebook_entry.strip() == "Please run Python analysis first.":
        return None
    return save_markdown_section("Lab Notebook Entry", notebook_entry)


def export_mini_poster(poster_markdown: str):
    if not poster_markdown.strip() or poster_markdown.strip() == "Please run Python analysis first.":
        return None
    return save_markdown_section("Mini Scientific Poster", poster_markdown)


def run_interpretation_feedback(summary_markdown, summary_df, warnings_markdown, student_interpretation, explanation_level):
    if not summary_markdown:
        return "Please run Python analysis first."
    if not student_interpretation.strip():
        return "Please write your interpretation first."

    try:
        return generate_ai_interpretation_feedback(summary_markdown, student_interpretation, explanation_level)
    except Exception as exc:
        warnings = []
        if warnings_markdown and "No major data-quality warnings" not in warnings_markdown:
            warnings = ["Manual review recommended based on the uploaded dataset."]
        if isinstance(summary_df, pd.DataFrame) and not summary_df.empty:
            fallback = generate_rule_based_interpretation_feedback(student_interpretation, summary_df, warnings)
            return (
                f"{fallback}\n\n---\n\n"
                f"_AI feedback was unavailable, so this local feedback was generated instead. Reason: {exc}_"
            )
        return f"Interpretation feedback failed: {exc}"


def export_interpretation_feedback(feedback_markdown: str):
    if not feedback_markdown.strip() or feedback_markdown.startswith("Please "):
        return None
    return save_markdown_section("Interpretation Feedback", feedback_markdown)


def build_default_lab_assistant_message(file_input, summary_df, warnings):
    return generate_rule_based_lab_assistant_message(
        summary_df if isinstance(summary_df, pd.DataFrame) else pd.DataFrame(),
        warnings,
        is_synthetic=file_input is None,
    )


def run_lab_assistant(summary_markdown, summary_df, warnings_markdown, file_input):
    if not summary_markdown:
        return "BioDose Assistant says: Run the Python analysis first so I can comment on the current dataset."

    try:
        return generate_ai_lab_assistant_message(summary_markdown, is_synthetic=file_input is None)
    except Exception as exc:
        warnings = []
        if warnings_markdown and "No major data-quality warnings" not in warnings_markdown:
            warnings = ["Manual review recommended based on the uploaded dataset."]
        fallback = generate_rule_based_lab_assistant_message(
            summary_df if isinstance(summary_df, pd.DataFrame) else pd.DataFrame(),
            warnings,
            is_synthetic=file_input is None,
        )
        return f"{fallback}\n\n_AI assistant note was unavailable, so this local note was generated instead. Reason: {exc}_"


def run_analysis(file_input, assay_type, scenario_name=DEFAULT_SCENARIO):
    file_path = resolve_analysis_file_path(file_input, scenario_name)

    result = analyze_drug_response(file_path)
    df = result["df"]
    summary_df = result["summary_df"]
    cards = result["cards"]
    warnings = result["warnings"]
    fit_df = result["fit_df"]
    fit_warnings = result["fit_warnings"]
    fit_curve_df = result["fit_curve_df"]
    dataset_guidance = format_dataset_guidance(file_input)
    assay_guidance = format_assay_guidance(assay_type)
    mission_outputs = build_mission_outputs(file_input, scenario_name, df, summary_df, warnings, cards, fit_df)
    assistant_message = build_default_lab_assistant_message(file_input, summary_df, warnings)

    if summary_df.empty:
        return (
            df,
            summary_df,
            fit_df,
            format_cards(cards),
            dataset_guidance,
            assay_guidance,
            format_warnings(warnings),
            format_fit_warnings(fit_warnings),
            None,
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            mission_outputs[0],
            mission_outputs[1],
            mission_outputs[2],
            mission_outputs[3],
            mission_outputs[4],
            mission_outputs[5],
            assistant_message,
            "",
            None,
            "",
            None,
            "",
            None,
        )

    fig = create_dose_response_plot(summary_df, fit_curve_df)

    return (
        df,
        summary_df,
        fit_df,
        format_cards(cards),
        dataset_guidance,
        assay_guidance,
        format_warnings(warnings),
        format_fit_warnings(fit_warnings),
        fig,
        result["summary_markdown"],
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        mission_outputs[0],
        mission_outputs[1],
        mission_outputs[2],
        mission_outputs[3],
        mission_outputs[4],
        mission_outputs[5],
        assistant_message,
        "",
        None,
        "",
        None,
        "",
        None,
    )


def run_ai_explanation(summary_markdown, summary_df, warnings_markdown, explanation_level):
    if not summary_markdown:
        return (
            "Please run Python analysis first.",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        )

    try:
        explanation = generate_ai_drug_response_explanation(summary_markdown, explanation_level)
    except Exception as exc:
        if isinstance(summary_df, pd.DataFrame) and not summary_df.empty:
            warnings = []
            if warnings_markdown and "No major data-quality warnings" not in warnings_markdown:
                warnings = ["Manual review recommended based on the uploaded dataset."]
            fallback = generate_rule_based_interpretation(summary_df, warnings, explanation_level)
            explanation = (
                f"{fallback}\n\n---\n\n"
                f"_AI explanation was unavailable, so this {explanation_level} fallback summary was generated locally. Reason: {exc}_"
            )
        else:
            explanation = f"AI explanation failed: {exc}"

    return build_academic_outputs(explanation)


def run_figure_caption(summary_markdown, summary_df):
    if not summary_markdown:
        return "Please run Python analysis first."

    try:
        return generate_ai_figure_caption(summary_markdown)
    except Exception as exc:
        if isinstance(summary_df, pd.DataFrame) and not summary_df.empty:
            fallback = generate_rule_based_figure_caption(summary_df)
            return (
                f"{fallback}\n\n---\n\n"
                f"_AI caption generation was unavailable, so this fallback caption was generated locally. Reason: {exc}_"
            )
        return f"Figure caption generation failed: {exc}"


def use_selected_scenario(assay_type, scenario_name):
    return run_analysis(None, assay_type, scenario_name)


def export_summary(summary_markdown, ai_explanation):
    content = summary_markdown or ""
    if ai_explanation:
        content += "\n\n---\n\n# AI-assisted Explanation\n\n"
        content += ai_explanation

    if not content.strip():
        return None

    return save_markdown_summary(content)


def export_summary_table(summary_df):
    if not isinstance(summary_df, pd.DataFrame) or summary_df.empty:
        return None

    return save_summary_csv(summary_df)


def export_report_package(summary_markdown, summary_df, fit_df, ai_explanation, figure_caption, assay_type):
    if not summary_markdown:
        return None
    if not isinstance(summary_df, pd.DataFrame) or summary_df.empty:
        return None

    normalized_fit_df = fit_df if isinstance(fit_df, pd.DataFrame) else pd.DataFrame()
    return save_report_bundle(
        summary_markdown=summary_markdown,
        summary_df=summary_df,
        fit_df=normalized_fit_df,
        ai_explanation=ai_explanation or "",
        figure_caption=figure_caption or "",
        assay_type=assay_type,
    )


def download_assay_template(assay_type):
    return save_assay_template_csv(assay_type)


with gr.Blocks(title="BioDose AI") as demo:
    gr.HTML(
        """
<style>
    .app-shell {max-width: 1100px; margin: 0 auto;}
    .hero {
        background: linear-gradient(135deg, #f7f1d5 0%, #d6ebd8 55%, #cfe7f7 100%);
        border: 1px solid #d8e3d2;
        border-radius: 20px;
        padding: 24px 28px;
        margin-bottom: 18px;
    }
    .hero h1 {margin: 0 0 8px 0; font-size: 2.2rem;}
    .hero p {margin: 0; font-size: 1.05rem;}
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 12px;
    }
    .metric-card {
        background: #fbfcf8;
        border: 1px solid #d6dfcf;
        border-radius: 16px;
        padding: 14px;
    }
    .metric-label {
        color: #4e6352;
        font-size: 0.85rem;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .metric-value {
        color: #16321f;
        font-size: 1.1rem;
        font-weight: 700;
    }
    .callout {
        border-radius: 16px;
        padding: 14px 16px;
        margin: 6px 0;
    }
    .callout strong {display: block; margin-bottom: 6px;}
    .callout p {margin: 0 0 8px 0;}
    .callout ul {margin: 0; padding-left: 18px;}
    .callout-ok {
        background: #edf7ee;
        border: 1px solid #b9d9be;
        color: #204729;
    }
    .callout-warn {
        background: #fff4df;
        border: 1px solid #e8cb87;
        color: #6c4f0d;
    }
    .callout-info {
        background: #eef5fb;
        border: 1px solid #bdd3ea;
        color: #1d4669;
    }
    .badge-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 8px 0 16px 0;
    }
    .badge-chip {
        background: #16321f;
        color: #f7f5e8;
        border-radius: 999px;
        padding: 8px 12px;
        font-size: 0.9rem;
        font-weight: 600;
    }
</style>
"""
    )
    gr.Markdown(
        """
<div class="app-shell">
    <div class="hero">
        <h1>🧪 BioDose AI</h1>
        <p>AI-assisted drug response analysis for Biochemistry students.</p>
        <p>Upload a CSV from a cell-viability experiment or start with the built-in teaching dataset.</p>
    </div>
</div>
"""
    )

    with gr.Row():
        file_input = gr.File(label="Upload drug response CSV", file_types=[".csv"])
        scenario_input = gr.Dropdown(
            choices=list(SCENARIO_DATASETS.keys()),
            value=DEFAULT_SCENARIO,
            label="Built-in scenario",
        )
        assay_type_input = gr.Dropdown(
            choices=ASSAY_TEMPLATE_OPTIONS,
            value="MTT",
            label="Assay type",
        )
        analyze_btn = gr.Button("Analyze with Python", variant="primary")
        sample_btn = gr.Button("Use Selected Scenario")

    with gr.Tab("Data Preview"):
        raw_output = gr.Dataframe(label="Raw Data")

    with gr.Tab("Summary"):
        cards_output = gr.HTML(label="Result Cards")
        guidance_output = gr.HTML(label="Dataset Context")
        assay_guidance_output = gr.HTML(label="Assay Guidance")
        warnings_output = gr.HTML(label="Data Quality Warnings")
        fit_warnings_output = gr.HTML(label="IC50 Fit Warnings")
        summary_output = gr.Dataframe(label="Summary Statistics")
        fit_output = gr.Dataframe(label="IC50 Fit Table")

    with gr.Tab("Dose-Response Plot"):
        plot_output = gr.Plot(label="Interactive Dose-Response Curve")

    with gr.Tab("AI Explanation"):
        explanation_level_input = gr.Dropdown(
            choices=EXPLANATION_LEVEL_OPTIONS,
            value="Undergraduate Biochemistry",
            label="Explanation Level",
        )
        ai_btn = gr.Button("Generate AI Explanation")
        ai_output = gr.Markdown(label="AI-assisted Explanation")
        gr.Markdown(
            "Use this as a draft academic support output only. The explanation level can shift the writing style from simpler study help to more formal lab-report wording, but controls, replicate quality, units, and dataset context still need manual verification."
        )
        caption_btn = gr.Button("Generate Figure Caption")
        caption_output = gr.Markdown(label="Figure Caption")

    with gr.Tab("Academic Support"):
        gr.Markdown(
            "Turn the generated academic support text into small reusable study or report assets. Choose one section to download, or export the full academic-support bundle."
        )
        summary_support_output = gr.Markdown(label="Plain-English Summary")
        results_output = gr.Markdown(label="Results Paragraph Draft")
        discussion_output = gr.Markdown(label="Discussion Paragraph Draft")
        limitations_output = gr.Markdown(label="Limitations")
        next_steps_output = gr.Markdown(label="Next Experiment Suggestions")
        verify_output = gr.Markdown(label="What to Verify Manually")
        questions_output = gr.Markdown(label="Challenge Questions")
        with gr.Row():
            academic_export_choice = gr.Dropdown(
                choices=ACADEMIC_EXPORT_OPTIONS,
                value="Results Paragraph Draft",
                label="Academic section to download",
            )
            academic_export_btn = gr.Button("Download Selected Section")
            academic_bundle_btn = gr.Button("Download Academic Bundle")
        with gr.Row():
            academic_export_file = gr.File(label="Selected Section Download")
            academic_bundle_file = gr.File(label="Academic Bundle Download")

    with gr.Tab("Mission Mode"):
        gr.Markdown(
            "Industry-inspired framing for practice only: use this mission brief to review compound-screening patterns, rank apparent leads, and decide what follow-up checks matter next."
        )
        mission_brief_output = gr.Markdown(label="Mission Brief")
        mission_scenario_output = gr.Markdown(label="Scenario Note")
        mission_score_output = gr.Markdown(label="Data Quality Score")
        mission_ranking_output = gr.Markdown(label="Candidate Ranking")
        mission_badges_output = gr.HTML(label="Achievement Badges")
        mission_checks_output = gr.Markdown(label="Follow-up Checks")

    with gr.Tab("AI Lab Assistant"):
        gr.Markdown(
            "A short professional assistant note that highlights the main pattern, keeps the wording cautious, and points to one thing worth checking next."
        )
        assistant_btn = gr.Button("Refresh Assistant Note")
        assistant_output = gr.Markdown(label="Assistant Note")

    with gr.Tab("Mini Scientific Poster"):
        gr.Markdown(
            "Generate a compact poster-style scientific summary that can be refined into a one-page presentation or Quarto handout."
        )
        poster_btn = gr.Button("Generate Mini Poster")
        poster_output = gr.Markdown(label="Mini Poster Draft")
        poster_export_btn = gr.Button("Download Mini Poster")
        poster_export_file = gr.File(label="Mini Poster Download")

    with gr.Tab("Lab Notebook Mode"):
        gr.Markdown(
            "Generate a structured notebook-style entry that connects the dataset, question, observation, interpretation, limitations, and next step in one reusable record."
        )
        notebook_btn = gr.Button("Generate Lab Notebook Entry")
        notebook_output = gr.Markdown(label="Lab Notebook Entry")
        notebook_export_btn = gr.Button("Download Lab Notebook Entry")
        notebook_export_file = gr.File(label="Lab Notebook Download")

    with gr.Tab("Score My Interpretation"):
        gr.Markdown(
            "Write your own interpretation first, then ask BioDose AI for strengths and suggestions. This is for learning and revision support only."
        )
        student_interpretation_input = gr.Textbox(
            label="Your Interpretation Draft",
            lines=8,
            placeholder="Write your interpretation of the current dataset here.",
        )
        score_btn = gr.Button("Score My Interpretation")
        feedback_output = gr.Markdown(label="Interpretation Feedback")
        feedback_export_btn = gr.Button("Download Feedback")
        feedback_export_file = gr.File(label="Interpretation Feedback Download")

    with gr.Tab("Summary Markdown"):
        markdown_output = gr.Markdown(label="Summary Markdown")

    with gr.Tab("Templates"):
        template_guidance = gr.Markdown(value=get_assay_template_guidance("MTT"))
        template_btn = gr.Button("Download Assay Template CSV")
        template_file = gr.File(label="Template Download")

    with gr.Tab("Export"):
        export_btn = gr.Button("Download Summary Markdown")
        export_file = gr.File(label="Markdown Download")
        export_csv_btn = gr.Button("Download Summary Table CSV")
        export_csv_file = gr.File(label="CSV Download")
        export_bundle_btn = gr.Button("Download Report Package ZIP")
        export_bundle_file = gr.File(label="Report Package")

    analyze_btn.click(
        fn=run_analysis,
        inputs=[file_input, assay_type_input, scenario_input],
        outputs=[
            raw_output,
            summary_output,
            fit_output,
            cards_output,
            guidance_output,
            assay_guidance_output,
            warnings_output,
            fit_warnings_output,
            plot_output,
            markdown_output,
            ai_output,
            caption_output,
            results_output,
            discussion_output,
            limitations_output,
            next_steps_output,
            verify_output,
            questions_output,
            summary_support_output,
            mission_brief_output,
            mission_scenario_output,
            mission_score_output,
            mission_ranking_output,
            mission_badges_output,
            mission_checks_output,
            assistant_output,
            poster_output,
            poster_export_file,
            notebook_output,
            notebook_export_file,
            feedback_output,
            feedback_export_file,
        ],
    )

    sample_btn.click(
        fn=use_selected_scenario,
        inputs=[assay_type_input, scenario_input],
        outputs=[
            raw_output,
            summary_output,
            fit_output,
            cards_output,
            guidance_output,
            assay_guidance_output,
            warnings_output,
            fit_warnings_output,
            plot_output,
            markdown_output,
            ai_output,
            caption_output,
            results_output,
            discussion_output,
            limitations_output,
            next_steps_output,
            verify_output,
            questions_output,
            summary_support_output,
            mission_brief_output,
            mission_scenario_output,
            mission_score_output,
            mission_ranking_output,
            mission_badges_output,
            mission_checks_output,
            assistant_output,
            poster_output,
            poster_export_file,
            notebook_output,
            notebook_export_file,
            feedback_output,
            feedback_export_file,
        ],
    )

    ai_btn.click(
        fn=run_ai_explanation,
        inputs=[markdown_output, summary_output, warnings_output, explanation_level_input],
        outputs=[
            ai_output,
            results_output,
            discussion_output,
            limitations_output,
            next_steps_output,
            verify_output,
            questions_output,
            summary_support_output,
        ],
    )

    caption_btn.click(
        fn=run_figure_caption,
        inputs=[markdown_output, summary_output],
        outputs=[caption_output],
    )

    export_btn.click(
        fn=export_summary,
        inputs=[markdown_output, ai_output],
        outputs=[export_file],
    )

    export_csv_btn.click(
        fn=export_summary_table,
        inputs=[summary_output],
        outputs=[export_csv_file],
    )

    export_bundle_btn.click(
        fn=export_report_package,
        inputs=[markdown_output, summary_output, fit_output, ai_output, caption_output, assay_type_input],
        outputs=[export_bundle_file],
    )

    academic_export_btn.click(
        fn=export_selected_academic_section,
        inputs=[
            academic_export_choice,
            summary_support_output,
            results_output,
            discussion_output,
            limitations_output,
            next_steps_output,
            verify_output,
            questions_output,
        ],
        outputs=[academic_export_file],
    )

    academic_bundle_btn.click(
        fn=export_all_academic_sections,
        inputs=[
            summary_support_output,
            results_output,
            discussion_output,
            limitations_output,
            next_steps_output,
            verify_output,
            questions_output,
        ],
        outputs=[academic_bundle_file],
    )

    notebook_btn.click(
        fn=build_lab_notebook_entry,
        inputs=[
            file_input,
            scenario_input,
            assay_type_input,
            markdown_output,
            summary_support_output,
            results_output,
            ai_output,
            limitations_output,
            next_steps_output,
            verify_output,
            mission_brief_output,
            mission_ranking_output,
            caption_output,
        ],
        outputs=[notebook_output],
    )

    notebook_export_btn.click(
        fn=export_lab_notebook_entry,
        inputs=[notebook_output],
        outputs=[notebook_export_file],
    )

    assistant_btn.click(
        fn=run_lab_assistant,
        inputs=[markdown_output, summary_output, warnings_output, file_input],
        outputs=[assistant_output],
    )

    poster_btn.click(
        fn=build_mini_poster,
        inputs=[
            file_input,
            scenario_input,
            assay_type_input,
            summary_support_output,
            results_output,
            limitations_output,
            next_steps_output,
            mission_brief_output,
            caption_output,
            assistant_output,
        ],
        outputs=[poster_output],
    )

    poster_export_btn.click(
        fn=export_mini_poster,
        inputs=[poster_output],
        outputs=[poster_export_file],
    )

    score_btn.click(
        fn=run_interpretation_feedback,
        inputs=[
            markdown_output,
            summary_output,
            warnings_output,
            student_interpretation_input,
            explanation_level_input,
        ],
        outputs=[feedback_output],
    )

    feedback_export_btn.click(
        fn=export_interpretation_feedback,
        inputs=[feedback_output],
        outputs=[feedback_export_file],
    )

    assay_type_input.change(
        fn=get_assay_template_guidance,
        inputs=[assay_type_input],
        outputs=[template_guidance],
    )

    template_btn.click(
        fn=download_assay_template,
        inputs=[assay_type_input],
        outputs=[template_file],
    )

def main():
    demo.launch()


if __name__ == "__main__":
    main()

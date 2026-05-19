from pathlib import Path

import gradio as gr
import pandas as pd

from src.assay_templates import (
    ASSAY_TEMPLATE_OPTIONS,
    get_assay_template_guidance,
    save_assay_template_csv,
)
from src.drug_analysis import (
    analyze_drug_response,
    generate_ai_figure_caption,
    generate_ai_drug_response_explanation,
    generate_rule_based_figure_caption,
    generate_rule_based_interpretation,
)
from src.export_utils import save_markdown_summary, save_report_bundle, save_summary_csv
from src.plots import create_dose_response_plot

EXAMPLE_FILE = Path("data/examples/drug_response_sample.csv")


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


def normalize_file_path(file_input):
    if file_input is None:
        return str(EXAMPLE_FILE)

    if isinstance(file_input, dict) and file_input.get("name"):
        return file_input["name"]

    if hasattr(file_input, "name"):
        return file_input.name

    return str(file_input)


def run_analysis(file_input, assay_type):
    file_path = normalize_file_path(file_input)
    file_path = file_path if file_path else str(EXAMPLE_FILE)

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
    )


def run_ai_explanation(summary_markdown, summary_df, warnings_markdown):
    if not summary_markdown:
        return "Please run Python analysis first."

    try:
        return generate_ai_drug_response_explanation(summary_markdown)
    except Exception as exc:
        if isinstance(summary_df, pd.DataFrame) and not summary_df.empty:
            warnings = []
            if warnings_markdown and "No major data-quality warnings" not in warnings_markdown:
                warnings = ["Manual review recommended based on the uploaded dataset."]
            fallback = generate_rule_based_interpretation(summary_df, warnings)
            return (
                f"{fallback}\n\n---\n\n"
                f"_AI explanation was unavailable, so this fallback summary was generated locally. Reason: {exc}_"
            )
        return f"AI explanation failed: {exc}"


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


def use_sample_dataset(assay_type):
    return run_analysis(None, assay_type)


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
        assay_type_input = gr.Dropdown(
            choices=ASSAY_TEMPLATE_OPTIONS,
            value="MTT",
            label="Assay type",
        )
        analyze_btn = gr.Button("Analyze with Python", variant="primary")
        sample_btn = gr.Button("Use Sample Dataset")

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
        ai_btn = gr.Button("Generate AI Explanation")
        ai_output = gr.Markdown(label="AI-assisted Explanation")
        gr.Markdown(
            "Use this as a draft explanation only. Verify controls, replicate quality, units, and whether the dataset is synthetic or experimental."
        )
        caption_btn = gr.Button("Generate Figure Caption")
        caption_output = gr.Markdown(label="Figure Caption")

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
        inputs=[file_input, assay_type_input],
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
        ],
    )

    sample_btn.click(
        fn=use_sample_dataset,
        inputs=[assay_type_input],
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
        ],
    )

    ai_btn.click(
        fn=run_ai_explanation,
        inputs=[markdown_output, summary_output, warnings_output],
        outputs=[ai_output],
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


demo.launch()

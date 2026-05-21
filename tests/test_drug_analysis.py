import pandas as pd

from src.drug_analysis import (
    EXPLANATION_LEVEL_OPTIONS,
    analyze_drug_response,
    build_drug_response_cards,
    fit_ic50_curves,
    generate_ai_drug_response_explanation,
    generate_ai_interpretation_feedback,
    generate_ai_lab_assistant_message,
    generate_rule_based_figure_caption,
    generate_rule_based_interpretation,
    generate_rule_based_interpretation_feedback,
    generate_rule_based_lab_assistant_message,
    summarize_drug_response,
)
from src.validation import validate_drug_response_df


def make_sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "sample_id": "S001",
                "drug_name": "DrugA",
                "concentration_uM": 0.0,
                "replicate": 1,
                "cell_viability_percent": 100,
            },
            {
                "sample_id": "S002",
                "drug_name": "DrugA",
                "concentration_uM": 10.0,
                "replicate": 1,
                "cell_viability_percent": 40,
            },
            {
                "sample_id": "S003",
                "drug_name": "DrugB",
                "concentration_uM": 0.0,
                "replicate": 1,
                "cell_viability_percent": 100,
            },
            {
                "sample_id": "S004",
                "drug_name": "DrugB",
                "concentration_uM": 10.0,
                "replicate": 1,
                "cell_viability_percent": 70,
            },
        ]
    )


def test_validate_drug_response_df_reports_missing_columns():
    df = pd.DataFrame({"sample_id": ["S001"]})

    warnings = validate_drug_response_df(df)

    assert warnings
    assert warnings[0].startswith("Missing required columns:")


def test_summarize_drug_response_builds_expected_columns():
    df = pd.DataFrame(
        [
            {
                "sample_id": "S001",
                "drug_name": "DrugA",
                "concentration_uM": 0.0,
                "replicate": 1,
                "cell_viability_percent": 100,
            },
            {
                "sample_id": "S002",
                "drug_name": "DrugA",
                "concentration_uM": 0.0,
                "replicate": 2,
                "cell_viability_percent": 90,
            },
        ]
    )

    summary = summarize_drug_response(df)

    assert list(summary.columns) == [
        "drug_name",
        "concentration_uM",
        "mean_viability",
        "sd_viability",
        "n",
        "sem_viability",
    ]
    assert summary.iloc[0]["mean_viability"] == 95
    assert summary.iloc[0]["n"] == 2


def test_build_drug_response_cards_uses_lowest_viability_as_strongest_response():
    df = make_sample_df()
    summary = summarize_drug_response(df)

    cards = build_drug_response_cards(df, summary)

    assert cards["drugs_detected"] == 2
    assert cards["strongest_observed_response"] == "DrugA at 10.0 uM"


def test_generate_rule_based_interpretation_mentions_limitations_and_drug_strength():
    df = make_sample_df()
    summary = summarize_drug_response(df)

    interpretation = generate_rule_based_interpretation(summary, warnings=[])

    assert "DrugA shows the strongest reduction" in interpretation
    assert "## Limitations" in interpretation
    assert "## What to Verify Manually" in interpretation


def test_generate_rule_based_figure_caption_mentions_error_bars_and_strongest_drug():
    df = make_sample_df()
    summary = summarize_drug_response(df)

    caption = generate_rule_based_figure_caption(summary)

    assert "Dose-response plot" in caption
    assert "DrugA" in caption
    assert "Error bars represent the standard error of the mean." in caption


def test_validate_drug_response_df_reports_duplicate_sample_ids():
    df = pd.DataFrame(
        [
            {
                "sample_id": "S001",
                "drug_name": "DrugA",
                "concentration_uM": 1.0,
                "replicate": 1,
                "cell_viability_percent": 95,
            },
            {
                "sample_id": "S001",
                "drug_name": "DrugA",
                "concentration_uM": 1.0,
                "replicate": 2,
                "cell_viability_percent": 90,
            },
        ]
    )

    warnings = validate_drug_response_df(df)

    assert "Duplicate sample_id values detected." in warnings


def test_validate_drug_response_df_reports_negative_concentrations():
    df = pd.DataFrame(
        [
            {
                "sample_id": "S001",
                "drug_name": "DrugA",
                "concentration_uM": -0.5,
                "replicate": 1,
                "cell_viability_percent": 95,
            },
            {
                "sample_id": "S002",
                "drug_name": "DrugA",
                "concentration_uM": -0.5,
                "replicate": 2,
                "cell_viability_percent": 90,
            },
        ]
    )

    warnings = validate_drug_response_df(df)

    assert "Negative concentration values detected." in warnings


def test_fit_ic50_curves_returns_fit_table_for_monotonic_data():
    df = pd.DataFrame(
        [
            {"sample_id": "S001", "drug_name": "DrugA", "concentration_uM": 0.0, "replicate": 1, "cell_viability_percent": 100},
            {"sample_id": "S002", "drug_name": "DrugA", "concentration_uM": 0.01, "replicate": 1, "cell_viability_percent": 96},
            {"sample_id": "S003", "drug_name": "DrugA", "concentration_uM": 0.1, "replicate": 1, "cell_viability_percent": 85},
            {"sample_id": "S004", "drug_name": "DrugA", "concentration_uM": 1.0, "replicate": 1, "cell_viability_percent": 60},
            {"sample_id": "S005", "drug_name": "DrugA", "concentration_uM": 10.0, "replicate": 1, "cell_viability_percent": 30},
        ]
    )

    summary = summarize_drug_response(df)
    fit_df, fit_warnings, fit_curve_df = fit_ic50_curves(summary)

    assert not fit_df.empty
    assert "ic50_uM" in fit_df.columns
    assert not fit_curve_df.empty
    assert isinstance(fit_warnings, list)


def test_analyze_drug_response_returns_consistent_empty_fit_outputs_for_missing_columns():
    result = analyze_drug_response("data/examples/drug_response_missing_column.csv")

    assert result["summary_df"].empty
    assert result["fit_df"].empty
    assert result["fit_curve_df"].empty
    assert result["fit_warnings"] == []


def test_validate_drug_response_df_handles_non_numeric_viability_without_crashing():
    df = pd.DataFrame(
        [
            {
                "sample_id": "S001",
                "drug_name": "DrugA",
                "concentration_uM": 1.0,
                "replicate": 1,
                "cell_viability_percent": "bad",
            }
        ]
    )

    warnings = validate_drug_response_df(df)

    assert "cell_viability_percent should be numeric." in warnings


def test_generate_rule_based_interpretation_mentions_requested_explanation_level_usage():
    df = make_sample_df()
    summary = summarize_drug_response(df)

    interpretation = generate_rule_based_interpretation(summary, warnings=[], explanation_level="Poster Caption")

    assert "compact presentation support" in interpretation


def test_generate_ai_drug_response_explanation_includes_explanation_level_in_prompt(monkeypatch):
    captured = {}

    def fake_call_llm(system_prompt, user_prompt, model=None):
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        return "ok"

    monkeypatch.setattr("src.drug_analysis.call_llm", fake_call_llm)

    output = generate_ai_drug_response_explanation("## Drug Response Summary", explanation_level="Simple")

    assert output == "ok"
    assert "Explanation level: Simple" in captured["user_prompt"]
    assert "minimal jargon" in captured["user_prompt"]
    assert "Simple" in EXPLANATION_LEVEL_OPTIONS


def test_generate_rule_based_interpretation_feedback_returns_strengths_and_suggestions():
    df = make_sample_df()
    summary = summarize_drug_response(df)

    feedback = generate_rule_based_interpretation_feedback(
        "DrugA shows a dose-dependent response, but this synthetic dataset still needs more replicates.",
        summary,
        warnings=[],
    )

    assert "## Strengths" in feedback
    assert "## Suggestions" in feedback
    assert "dose-response pattern" in feedback or "dose-dependent" in feedback


def test_generate_ai_interpretation_feedback_includes_student_text_in_prompt(monkeypatch):
    captured = {}

    def fake_call_llm(system_prompt, user_prompt, model=None):
        captured["user_prompt"] = user_prompt
        return "feedback"

    monkeypatch.setattr("src.drug_analysis.call_llm", fake_call_llm)

    output = generate_ai_interpretation_feedback(
        "## Drug Response Summary",
        "My draft interpretation.",
        explanation_level="Research Assistant",
    )

    assert output == "feedback"
    assert "My draft interpretation." in captured["user_prompt"]
    assert "Explanation level: Research Assistant" in captured["user_prompt"]


def test_generate_rule_based_lab_assistant_message_mentions_lead_compound():
    df = make_sample_df()
    summary = summarize_drug_response(df)

    message = generate_rule_based_lab_assistant_message(summary, warnings=[], is_synthetic=True)

    assert message.startswith("BioDose Assistant says:")
    assert "DrugA" in message
    assert "synthetic" in message


def test_generate_ai_lab_assistant_message_includes_dataset_context(monkeypatch):
    captured = {}

    def fake_call_llm(system_prompt, user_prompt, model=None):
        captured["user_prompt"] = user_prompt
        return "assistant note"

    monkeypatch.setattr("src.drug_analysis.call_llm", fake_call_llm)

    output = generate_ai_lab_assistant_message("## Drug Response Summary", is_synthetic=False)

    assert output == "assistant note"
    assert "User-supplied dataset" in captured["user_prompt"]
    assert "BioDose Assistant says:" in captured["user_prompt"]

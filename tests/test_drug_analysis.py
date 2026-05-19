import pandas as pd

from src.drug_analysis import (
    build_drug_response_cards,
    fit_ic50_curves,
    generate_rule_based_figure_caption,
    generate_rule_based_interpretation,
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

from pathlib import Path

import pandas as pd

from src.validation import validate_drug_response_df


EXAMPLES_DIR = Path("data/examples")


def test_missing_column_example_triggers_required_column_warning():
    df = pd.read_csv(EXAMPLES_DIR / "drug_response_missing_column.csv")

    warnings = validate_drug_response_df(df)

    assert any("Missing required columns:" in warning for warning in warnings)
    assert any("cell_viability_percent" in warning for warning in warnings)


def test_duplicate_sample_example_triggers_duplicate_warning():
    df = pd.read_csv(EXAMPLES_DIR / "drug_response_duplicate_samples.csv")

    warnings = validate_drug_response_df(df)

    assert "Duplicate sample_id values detected." in warnings


def test_negative_concentration_example_triggers_negative_concentration_warning():
    df = pd.read_csv(EXAMPLES_DIR / "drug_response_negative_concentration.csv")

    warnings = validate_drug_response_df(df)

    assert "Negative concentration values detected." in warnings

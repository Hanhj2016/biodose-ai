import pandas as pd

REQUIRED_DRUG_RESPONSE_COLUMNS = {
    "sample_id",
    "drug_name",
    "concentration_uM",
    "replicate",
    "cell_viability_percent",
}


def validate_drug_response_df(df: pd.DataFrame) -> list[str]:
    warnings: list[str] = []

    missing = REQUIRED_DRUG_RESPONSE_COLUMNS - set(df.columns)
    if missing:
        warnings.append(f"Missing required columns: {', '.join(sorted(missing))}")
        return warnings

    if df.empty:
        warnings.append("The dataset is empty.")

    if df["cell_viability_percent"].isna().any():
        warnings.append("Missing cell viability values detected.")

    if df["concentration_uM"].isna().any():
        warnings.append("Missing concentration values detected.")

    if not pd.api.types.is_numeric_dtype(df["concentration_uM"]):
        warnings.append("concentration_uM should be numeric.")

    if not pd.api.types.is_numeric_dtype(df["cell_viability_percent"]):
        warnings.append("cell_viability_percent should be numeric.")

    replicate_counts = df.groupby(["drug_name", "concentration_uM"]).size()
    if (replicate_counts < 2).any():
        warnings.append("Some drug/concentration groups have fewer than 2 replicates.")

    if df["sample_id"].duplicated().any():
        warnings.append("Duplicate sample_id values detected.")

    if pd.api.types.is_numeric_dtype(df["concentration_uM"]) and (df["concentration_uM"] < 0).any():
        warnings.append("Negative concentration values detected.")

    if (df["cell_viability_percent"] < 0).any():
        warnings.append("Negative cell viability values detected.")

    if (df["cell_viability_percent"] > 150).any():
        warnings.append(
            "Very high cell viability values detected. Please verify units and assay output."
        )

    return warnings

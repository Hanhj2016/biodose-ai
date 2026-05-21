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

    concentration_series = df["concentration_uM"]
    viability_series = df["cell_viability_percent"]

    concentration_is_numeric = pd.api.types.is_numeric_dtype(concentration_series)
    viability_is_numeric = pd.api.types.is_numeric_dtype(viability_series)

    if not concentration_is_numeric:
        warnings.append("concentration_uM should be numeric.")

    if not viability_is_numeric:
        warnings.append("cell_viability_percent should be numeric.")

    replicate_counts = df.groupby(["drug_name", "concentration_uM"]).size()
    if (replicate_counts < 2).any():
        warnings.append("Some drug/concentration groups have fewer than 2 replicates.")

    if df["sample_id"].duplicated().any():
        warnings.append("Duplicate sample_id values detected.")

    if concentration_is_numeric and (concentration_series < 0).any():
        warnings.append("Negative concentration values detected.")

    if viability_is_numeric and (viability_series < 0).any():
        warnings.append("Negative cell viability values detected.")

    if viability_is_numeric and (viability_series > 150).any():
        warnings.append(
            "Very high cell viability values detected. Please verify units and assay output."
        )

    return warnings

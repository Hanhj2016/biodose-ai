from pathlib import Path

import pandas as pd


ASSAY_TEMPLATE_OPTIONS = ["MTT", "CellTiter-Glo", "Apoptosis"]

_ASSAY_NOTES = {
    "MTT": (
        "MTT assays usually begin from absorbance readouts. This template assumes values have already "
        "been normalized to cell_viability_percent so they can be analyzed directly in BioDose AI."
    ),
    "CellTiter-Glo": (
        "CellTiter-Glo assays usually begin from luminescence readouts. This template assumes the values "
        "have already been normalized to cell_viability_percent."
    ),
    "Apoptosis": (
        "Apoptosis assays often measure apoptotic fraction rather than viability directly. This template "
        "keeps the BioDose AI-compatible cell_viability_percent column, so convert raw assay output first if needed."
    ),
}


def build_assay_template_df(assay_type: str) -> pd.DataFrame:
    normalized_assay = assay_type if assay_type in ASSAY_TEMPLATE_OPTIONS else "MTT"

    rows = [
        ("S001", "DrugA", 0.0, 1, 100.0),
        ("S002", "DrugA", 0.01, 2, 97.0),
        ("S003", "DrugA", 0.1, 3, 90.0),
        ("S004", "DrugA", 1.0, 1, 68.0),
        ("S005", "DrugA", 10.0, 2, 42.0),
        ("S006", "DrugB", 0.0, 1, 100.0),
        ("S007", "DrugB", 0.01, 2, 98.0),
        ("S008", "DrugB", 0.1, 3, 94.0),
        ("S009", "DrugB", 1.0, 1, 82.0),
        ("S010", "DrugB", 10.0, 2, 63.0),
    ]

    return pd.DataFrame(
        [
            {
                "sample_id": sample_id,
                "drug_name": drug_name,
                "concentration_uM": concentration,
                "replicate": replicate,
                "cell_viability_percent": viability,
                "assay_type": normalized_assay,
                "cell_line": "ExampleCellLine",
                "exposure_hours": 24,
                "control_type": "vehicle_control" if concentration == 0 else "treatment",
            }
            for sample_id, drug_name, concentration, replicate, viability in rows
        ]
    )


def get_assay_template_guidance(assay_type: str) -> str:
    normalized_assay = assay_type if assay_type in ASSAY_TEMPLATE_OPTIONS else "MTT"
    return (
        f"### {normalized_assay} template\n\n"
        f"{_ASSAY_NOTES[normalized_assay]}\n\n"
        "Required analysis columns:\n"
        "- `sample_id`\n"
        "- `drug_name`\n"
        "- `concentration_uM`\n"
        "- `replicate`\n"
        "- `cell_viability_percent`\n\n"
        "Optional metadata columns in the template:\n"
        "- `assay_type`\n"
        "- `cell_line`\n"
        "- `exposure_hours`\n"
        "- `control_type`\n"
    )


def save_assay_template_csv(assay_type: str, output_dir: str = "outputs/templates") -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    template_df = build_assay_template_df(assay_type)
    safe_name = assay_type.lower().replace("-", "_").replace(" ", "_")
    output_path = Path(output_dir) / f"biodose_{safe_name}_template.csv"
    template_df.to_csv(output_path, index=False)
    return str(output_path)

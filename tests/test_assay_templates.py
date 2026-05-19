from pathlib import Path

import pandas as pd

from src.assay_templates import (
    build_assay_template_df,
    get_assay_template_guidance,
    save_assay_template_csv,
)


def test_build_assay_template_df_contains_required_columns():
    template_df = build_assay_template_df("MTT")

    assert {"sample_id", "drug_name", "concentration_uM", "replicate", "cell_viability_percent"}.issubset(
        set(template_df.columns)
    )
    assert "assay_type" in template_df.columns
    assert (template_df["assay_type"] == "MTT").all()


def test_get_assay_template_guidance_mentions_selected_assay():
    guidance = get_assay_template_guidance("CellTiter-Glo")

    assert "CellTiter-Glo" in guidance
    assert "cell_viability_percent" in guidance


def test_save_assay_template_csv_writes_file(tmp_path: Path):
    output_path = save_assay_template_csv("Apoptosis", output_dir=str(tmp_path))

    saved = Path(output_path)
    assert saved.exists()
    loaded = pd.read_csv(saved)
    assert not loaded.empty
    assert "assay_type" in loaded.columns

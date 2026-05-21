import zipfile
from pathlib import Path

import pandas as pd

from src.export_utils import (
    save_academic_sections_bundle,
    save_markdown_section,
    save_markdown_summary,
    save_report_bundle,
    save_summary_csv,
)


def test_save_markdown_summary_writes_markdown_file(tmp_path: Path):
    output_path = save_markdown_summary("# Hello", output_dir=str(tmp_path))

    saved = Path(output_path)
    assert saved.exists()
    assert saved.suffix == ".md"
    assert saved.read_text(encoding="utf-8") == "# Hello"


def test_save_summary_csv_writes_csv_file(tmp_path: Path):
    summary_df = pd.DataFrame(
        [
            {
                "drug_name": "DrugA",
                "concentration_uM": 1.0,
                "mean_viability": 90.0,
                "sd_viability": 2.0,
                "n": 3,
                "sem_viability": 1.15,
            }
        ]
    )

    output_path = save_summary_csv(summary_df, output_dir=str(tmp_path))

    saved = Path(output_path)
    assert saved.exists()
    assert saved.suffix == ".csv"
    loaded = pd.read_csv(saved)
    assert list(loaded.columns) == list(summary_df.columns)
    assert loaded.iloc[0]["drug_name"] == "DrugA"


def test_save_report_bundle_writes_zip_with_expected_files(tmp_path: Path):
    summary_df = pd.DataFrame([{"drug_name": "DrugA", "concentration_uM": 1.0, "mean_viability": 90.0}])
    fit_df = pd.DataFrame([{"drug_name": "DrugA", "ic50_uM": 1.2, "r_squared": 0.97}])

    archive_path = save_report_bundle(
        summary_markdown="## Summary",
        summary_df=summary_df,
        fit_df=fit_df,
        ai_explanation="Interpretation text",
        figure_caption="Caption text",
        assay_type="MTT",
        output_dir=str(tmp_path),
    )

    saved = Path(archive_path)
    assert saved.exists()
    assert saved.suffix == ".zip"

    with zipfile.ZipFile(saved) as archive:
        names = set(archive.namelist())
        assert "report_package.md" in names
        assert "summary_table.csv" in names
        assert "ic50_fit_table.csv" in names


def test_save_markdown_section_writes_academic_markdown_file(tmp_path: Path):
    output_path = save_markdown_section(
        "Results Paragraph Draft",
        "This is a result paragraph.",
        output_dir=str(tmp_path),
    )

    saved = Path(output_path)
    assert saved.exists()
    assert saved.suffix == ".md"
    assert "## Results Paragraph Draft" in saved.read_text(encoding="utf-8")


def test_save_academic_sections_bundle_writes_populated_section_files(tmp_path: Path):
    archive_path = save_academic_sections_bundle(
        {
            "Plain-English Summary": "Summary text",
            "Results Paragraph Draft": "Result text",
            "Limitations": "",
        },
        output_dir=str(tmp_path),
    )

    saved = Path(archive_path)
    assert saved.exists()
    assert saved.suffix == ".zip"

    with zipfile.ZipFile(saved) as archive:
        names = set(archive.namelist())
        assert "plain_english_summary.md" in names
        assert "results_paragraph_draft.md" in names
        assert "limitations.md" not in names


def test_save_markdown_section_can_write_lab_notebook_entry(tmp_path: Path):
    output_path = save_markdown_section(
        "Lab Notebook Entry",
        "# BioDose AI Lab Notebook Entry\n\nObservation text.",
        output_dir=str(tmp_path),
    )

    saved = Path(output_path)
    assert saved.exists()
    assert "Lab Notebook Entry" in saved.read_text(encoding="utf-8")

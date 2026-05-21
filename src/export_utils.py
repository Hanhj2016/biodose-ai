from pathlib import Path
from datetime import datetime
import zipfile

import pandas as pd


def _build_timestamped_path(prefix: str, suffix: str, output_dir: str) -> Path:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path(output_dir) / f"{prefix}_{timestamp}.{suffix}"


def save_markdown_summary(content: str, output_dir: str = "outputs/summaries") -> str:
    output_path = _build_timestamped_path("biodose_summary", "md", output_dir)
    output_path.write_text(content, encoding="utf-8")
    return str(output_path)


def save_summary_csv(summary_df: pd.DataFrame, output_dir: str = "outputs/summaries") -> str:
    output_path = _build_timestamped_path("biodose_summary_table", "csv", output_dir)
    summary_df.to_csv(output_path, index=False)
    return str(output_path)


def _slugify_label(label: str) -> str:
    safe = label.lower().replace("-", " ").replace("/", " ")
    return "_".join(part for part in safe.split() if part)


def save_markdown_section(title: str, content: str, output_dir: str = "outputs/academic") -> str | None:
    if not content.strip():
        return None

    output_path = _build_timestamped_path(f"biodose_{_slugify_label(title)}", "md", output_dir)
    output_path.write_text(f"## {title}\n\n{content.strip()}\n", encoding="utf-8")
    return str(output_path)


def save_academic_sections_bundle(
    sections: dict[str, str],
    output_dir: str = "outputs/academic",
) -> str | None:
    populated_sections = {
        title: content.strip()
        for title, content in sections.items()
        if content and content.strip()
    }
    if not populated_sections:
        return None

    bundle_dir = _build_timestamped_path("biodose_academic_support", "dir", output_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    for title, content in populated_sections.items():
        filename = f"{_slugify_label(title)}.md"
        (bundle_dir / filename).write_text(f"## {title}\n\n{content}\n", encoding="utf-8")

    zip_root = Path(output_dir)
    zip_root.mkdir(parents=True, exist_ok=True)
    archive_path = zip_root / f"{bundle_dir.stem}.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in bundle_dir.iterdir():
            archive.write(file_path, arcname=file_path.name)

    return str(archive_path)


def save_report_bundle(
    summary_markdown: str,
    summary_df: pd.DataFrame,
    fit_df: pd.DataFrame,
    ai_explanation: str,
    figure_caption: str,
    assay_type: str,
    output_dir: str = "outputs/reports",
) -> str:
    bundle_dir = _build_timestamped_path("biodose_report_bundle", "dir", output_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    report_md = bundle_dir / "report_package.md"
    report_md.write_text(
        "\n\n".join(
            [
                f"# BioDose AI Report Package\n\nAssay type: {assay_type}",
                summary_markdown or "No summary markdown generated.",
                "## Figure Caption\n\n" + (figure_caption or "No figure caption generated."),
                "## Interpretation\n\n" + (ai_explanation or "No interpretation generated."),
            ]
        ),
        encoding="utf-8",
    )

    if isinstance(summary_df, pd.DataFrame) and not summary_df.empty:
        summary_df.to_csv(bundle_dir / "summary_table.csv", index=False)

    if isinstance(fit_df, pd.DataFrame) and not fit_df.empty:
        fit_df.to_csv(bundle_dir / "ic50_fit_table.csv", index=False)

    zip_path = Path(output_dir)
    zip_path.mkdir(parents=True, exist_ok=True)
    archive_path = zip_path / f"{bundle_dir.stem}.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in bundle_dir.iterdir():
            archive.write(file_path, arcname=file_path.name)

    return str(archive_path)

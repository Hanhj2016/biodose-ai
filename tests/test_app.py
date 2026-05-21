import app
import pandas as pd


def test_app_exposes_main_without_launching_on_import():
    assert callable(app.main)


def test_split_markdown_sections_extracts_named_blocks():
    markdown = """
## Plain-English Summary

Short summary.

## Results Paragraph Draft

Result paragraph.

## Challenge Questions

- Question one?
- Question two?
""".strip()

    sections = app.split_markdown_sections(markdown)

    assert sections["Plain-English Summary"] == "Short summary."
    assert sections["Results Paragraph Draft"] == "Result paragraph."
    assert "- Question one?" in sections["Challenge Questions"]


def test_build_academic_outputs_maps_expected_sections():
    markdown = """
## Plain-English Summary

Short summary.

## Results Paragraph Draft

Result paragraph.

## Discussion Paragraph Draft

Discussion paragraph.

## Limitations

- Limitation

## Next Experiment Suggestions

- Suggestion

## What to Verify Manually

- Verify item

## Challenge Questions

- Question
""".strip()

    outputs = app.build_academic_outputs(markdown)

    assert outputs[0] == markdown
    assert outputs[1] == "Result paragraph."
    assert outputs[2] == "Discussion paragraph."
    assert "- Limitation" in outputs[3]
    assert "- Suggestion" in outputs[4]
    assert "- Verify item" in outputs[5]
    assert "- Question" in outputs[6]
    assert outputs[7] == "Short summary."


def test_export_selected_academic_section_returns_none_for_empty_content():
    output = app.export_selected_academic_section(
        "Results Paragraph Draft",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
    )

    assert output is None


def test_build_data_quality_score_rewards_complete_clean_dataset():
    df = pd.DataFrame(
        [
            {"sample_id": "S001", "drug_name": "DrugA", "concentration_uM": 0.0, "replicate": 1, "cell_viability_percent": 100},
            {"sample_id": "S002", "drug_name": "DrugA", "concentration_uM": 0.0, "replicate": 2, "cell_viability_percent": 99},
            {"sample_id": "S003", "drug_name": "DrugA", "concentration_uM": 0.0, "replicate": 3, "cell_viability_percent": 101},
            {"sample_id": "S004", "drug_name": "DrugA", "concentration_uM": 1.0, "replicate": 1, "cell_viability_percent": 80},
            {"sample_id": "S005", "drug_name": "DrugA", "concentration_uM": 1.0, "replicate": 2, "cell_viability_percent": 81},
            {"sample_id": "S006", "drug_name": "DrugA", "concentration_uM": 1.0, "replicate": 3, "cell_viability_percent": 79},
        ]
    )

    score, status = app.build_data_quality_score(df, [])

    assert score == 100
    assert "Good for exploration" in status


def test_build_candidate_ranking_orders_strongest_compound_first():
    summary_df = pd.DataFrame(
        [
            {"drug_name": "DrugA", "concentration_uM": 0.0, "mean_viability": 100.0},
            {"drug_name": "DrugA", "concentration_uM": 10.0, "mean_viability": 30.0},
            {"drug_name": "DrugB", "concentration_uM": 0.0, "mean_viability": 100.0},
            {"drug_name": "DrugB", "concentration_uM": 10.0, "mean_viability": 45.0},
        ]
    )

    ranking = app.build_candidate_ranking(summary_df)

    assert "1. DrugA" in ranking
    assert "2. DrugB" in ranking


def test_build_mission_badges_reflect_review_state():
    df = pd.DataFrame([{"sample_id": "S001", "drug_name": "DrugA", "concentration_uM": 0.0, "replicate": 1, "cell_viability_percent": 100}])
    summary_df = pd.DataFrame([{"drug_name": "DrugA", "concentration_uM": 0.0, "mean_viability": 100.0}])

    badges = app.build_mission_badges(df, summary_df, ["Missing concentration values detected."], pd.DataFrame())

    assert "Data Loaded" in badges
    assert "Dose-Response Plot Generated" in badges
    assert "Quality Check Needs Review" in badges


def test_resolve_analysis_file_path_uses_selected_scenario_when_no_upload():
    path = app.resolve_analysis_file_path(None, "Weak Response")

    assert path.endswith("drug_response_weak_response.csv")


def test_format_scenario_guidance_mentions_teaching_focus():
    guidance = app.format_scenario_guidance("Noisy Assay")

    assert "Noisy Assay" in guidance
    assert "Teaching focus" in guidance
    assert "Replicate variability" in guidance


def test_run_ai_explanation_uses_level_in_fallback(monkeypatch):
    summary_df = pd.DataFrame(
        [
            {"drug_name": "DrugA", "concentration_uM": 0.0, "mean_viability": 100.0, "sd_viability": 1.0, "n": 2, "sem_viability": 0.7},
            {"drug_name": "DrugA", "concentration_uM": 10.0, "mean_viability": 40.0, "sd_viability": 2.0, "n": 2, "sem_viability": 1.4},
        ]
    )

    def fake_generate(*args, **kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr(app, "generate_ai_drug_response_explanation", fake_generate)

    outputs = app.run_ai_explanation("## Summary", summary_df, "", "Lab Report Style")

    assert "Lab Report Style fallback summary" in outputs[0]


def test_build_lab_notebook_entry_uses_structured_sections():
    notebook = app.build_lab_notebook_entry(
        None,
        "Clear Dose-Response",
        "MTT",
        "## Summary",
        "DrugA looks stronger.",
        "Formal results paragraph.",
        "Longer interpretation.",
        "- Synthetic dataset",
        "- Add replicates",
        "- Check controls",
        "## Mission Brief\n\nMission text",
        "## Candidate Ranking\n\n1. DrugA",
        "Caption text",
    )

    assert "# BioDose AI Lab Notebook Entry" in notebook
    assert "Scenario: Clear Dose-Response" in notebook
    assert "## Question" in notebook
    assert "Longer interpretation." in notebook
    assert "## Figure Caption Draft" in notebook


def test_export_lab_notebook_entry_returns_none_before_analysis():
    assert app.export_lab_notebook_entry("Please run Python analysis first.") is None


def test_run_interpretation_feedback_uses_local_fallback(monkeypatch):
    summary_df = pd.DataFrame(
        [
            {"drug_name": "DrugA", "concentration_uM": 0.0, "mean_viability": 100.0, "sd_viability": 1.0, "n": 2, "sem_viability": 0.7},
            {"drug_name": "DrugA", "concentration_uM": 10.0, "mean_viability": 40.0, "sd_viability": 2.0, "n": 2, "sem_viability": 1.4},
        ]
    )

    def fake_feedback(*args, **kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr(app, "generate_ai_interpretation_feedback", fake_feedback)

    feedback = app.run_interpretation_feedback(
        "## Summary",
        summary_df,
        "",
        "DrugA looks dose-dependent, but this synthetic dataset is preliminary.",
        "Undergraduate Biochemistry",
    )

    assert "## Strengths" in feedback
    assert "local feedback was generated instead" in feedback


def test_export_interpretation_feedback_returns_none_for_placeholder_text():
    assert app.export_interpretation_feedback("Please write your interpretation first.") is None


def test_build_default_lab_assistant_message_uses_rule_based_note():
    summary_df = pd.DataFrame(
        [
            {"drug_name": "DrugA", "concentration_uM": 0.0, "mean_viability": 100.0},
            {"drug_name": "DrugA", "concentration_uM": 10.0, "mean_viability": 40.0},
        ]
    )

    message = app.build_default_lab_assistant_message(None, summary_df, [])

    assert message.startswith("BioDose Assistant says:")


def test_run_lab_assistant_uses_local_fallback(monkeypatch):
    summary_df = pd.DataFrame(
        [
            {"drug_name": "DrugA", "concentration_uM": 0.0, "mean_viability": 100.0},
            {"drug_name": "DrugA", "concentration_uM": 10.0, "mean_viability": 40.0},
        ]
    )

    def fake_assistant(*args, **kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr(app, "generate_ai_lab_assistant_message", fake_assistant)

    message = app.run_lab_assistant("## Summary", summary_df, "", None)

    assert "BioDose Assistant says:" in message
    assert "local note was generated instead" in message


def test_build_mini_poster_uses_existing_sections():
    poster = app.build_mini_poster(
        None,
        "Clear Dose-Response",
        "MTT",
        "DrugA appears strongest.",
        "Results paragraph draft.",
        "- Synthetic dataset",
        "- Add replicates",
        "## Mission Brief\n\nMission text",
        "Caption text",
        "BioDose Assistant says: Practice interpretation only.",
    )

    assert "# BioDose AI Mini Poster: Clear Dose-Response" in poster
    assert "## Background" in poster
    assert "## What I Learned" in poster
    assert "Caption text" in poster


def test_export_mini_poster_returns_none_before_generation():
    assert app.export_mini_poster("Please run Python analysis first.") is None


def test_run_analysis_supports_legacy_two_input_signature():
    outputs = app.run_analysis("data/examples/drug_response_sample.csv", "MTT")

    assert len(outputs) >= 2
    summary_df = outputs[1]
    assert not summary_df.empty

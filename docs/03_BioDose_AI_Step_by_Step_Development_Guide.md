# BioDose AI Step-by-Step Development Guide

## Project Goal

**BioDose AI** is a beginner-friendly project for a Biochemistry student to learn Python, AI-assisted coding, Gradio, OpenAI API calling, and scientific data visualization through a realistic drug response analysis use case.

The goal is not to build a complex production system. The goal is to build a polished, modular, reusable, and visually impressive learning project.

## Final Outcome

By the end, the project should have:

- a sample drug response CSV dataset
- a Jupyter Notebook for exploration
- reusable Python modules under `src/`
- a Gradio app with a polished UI
- an OpenAI-powered AI explanation button
- an optional AI figure caption button
- interactive Plotly dose-response chart
- downloadable summary
- Quarto report
- GitHub-ready project structure

---

# Recommended Development Phases

```text
Phase 0: Setup
Phase 1: Create sample data
Phase 2: Notebook exploration
Phase 3: Extract reusable Python functions
Phase 4: Add interactive Plotly visualization
Phase 5: Build Gradio app
Phase 6: Add OpenAI API explanation
Phase 7: Add data quality warnings and export
Phase 8: Create Quarto report
Phase 9: Polish README and screenshots
Phase 10: Optional deployment
```

---

# Phase 0: Environment Setup

The environment setup, package list, `.gitignore`, and project structure guidance are covered in `01_Common_Technical_Setup_and_Workflow.md`.

Use that shared document as the reference for initial setup before continuing with this development guide.

---

# Phase 1: Create Sample Drug Response Data

## 1.1 Create File

Create:

```text
data/examples/drug_response_sample.csv
```

## 1.2 Sample CSV

```csv
sample_id,drug_name,concentration_uM,replicate,cell_viability_percent
S001,DrugA,0,1,100
S002,DrugA,0,2,98
S003,DrugA,0,3,102
S004,DrugA,0.01,1,96
S005,DrugA,0.01,2,94
S006,DrugA,0.01,3,95
S007,DrugA,0.1,1,87
S008,DrugA,0.1,2,85
S009,DrugA,0.1,3,89
S010,DrugA,1,1,63
S011,DrugA,1,2,60
S012,DrugA,1,3,65
S013,DrugA,10,1,30
S014,DrugA,10,2,28
S015,DrugA,10,3,33
S016,DrugB,0,1,100
S017,DrugB,0,2,101
S018,DrugB,0,3,99
S019,DrugB,0.01,1,99
S020,DrugB,0.01,2,97
S021,DrugB,0.01,3,98
S022,DrugB,0.1,1,92
S023,DrugB,0.1,2,90
S024,DrugB,0.1,3,91
S025,DrugB,1,1,75
S026,DrugB,1,2,72
S027,DrugB,1,3,74
S028,DrugB,10,1,45
S029,DrugB,10,2,47
S030,DrugB,10,3,44
```

## 1.3 Optional Prompt to Generate More Synthetic Data

```text
Generate a realistic but synthetic drug response CSV dataset for a beginner biochemistry data analysis project.

The dataset should include two drugs, DrugA and DrugB.
Each drug should have concentrations:
0, 0.01, 0.1, 1, 10 uM.
Each concentration should have 3 replicates.
The measured value should be cell_viability_percent.
DrugA should show a stronger dose-dependent reduction in cell viability than DrugB.

Include the columns:
sample_id, drug_name, concentration_uM, replicate, cell_viability_percent

Return only CSV content.
```

---

# Phase 2: Notebook Exploration

## 2.1 Create Notebook

Create:

```text
notebooks/01_biodose_exploration.ipynb
```

## 2.2 Notebook Sections

The notebook should include:

1. Project title
2. Biological question
3. Load CSV
4. Preview data
5. Validate data
6. Summary statistics
7. Dose-response chart
8. Plain-English interpretation
9. Limitations
10. Next steps

## 2.3 Starter Code

```python
import pandas as pd
from pathlib import Path

data_path = Path("../data/examples/drug_response_sample.csv")
df = pd.read_csv(data_path)

df.head()
```

## 2.4 Check Data

```python
df.shape
df.columns
df.info()
df.isna().sum()
```

## 2.5 Summary Statistics

```python
summary = (
    df.groupby(["drug_name", "concentration_uM"])
      .agg(
          mean_viability=("cell_viability_percent", "mean"),
          sd_viability=("cell_viability_percent", "std"),
          n=("cell_viability_percent", "count")
      )
      .reset_index()
)

summary["sem_viability"] = summary["sd_viability"] / (summary["n"] ** 0.5)
summary
```

## 2.6 Simple Plot

```python
import plotly.express as px

fig = px.line(
    summary,
    x="concentration_uM",
    y="mean_viability",
    color="drug_name",
    markers=True,
    title="Dose-Response Curve"
)

fig.update_xaxes(type="log")
fig.show()
```

Note: concentration `0` cannot be shown on a log scale. In the final version, handle this carefully.

---

# Phase 3: Extract Reusable Python Functions

The notebook is for exploration. Once logic works, move reusable code into `src/`.

## 3.1 `src/validation.py`

```python
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

    if (df["cell_viability_percent"] < 0).any():
        warnings.append("Negative cell viability values detected.")

    if (df["cell_viability_percent"] > 150).any():
        warnings.append("Very high cell viability values detected. Please verify units and assay output.")

    return warnings
```

## 3.2 `src/drug_analysis.py`

```python
import pandas as pd
from src.validation import validate_drug_response_df

def load_drug_response_csv(file) -> pd.DataFrame:
    return pd.read_csv(file)

def summarize_drug_response(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["drug_name", "concentration_uM"])
          .agg(
              mean_viability=("cell_viability_percent", "mean"),
              sd_viability=("cell_viability_percent", "std"),
              n=("cell_viability_percent", "count")
          )
          .reset_index()
    )

    summary["sem_viability"] = summary["sd_viability"] / (summary["n"] ** 0.5)
    return summary

def build_drug_response_cards(df: pd.DataFrame, summary_df: pd.DataFrame) -> dict:
    strongest_row = summary_df.sort_values("mean_viability").iloc[0]

    return {
        "drugs_detected": int(df["drug_name"].nunique()),
        "concentrations_tested": int(df["concentration_uM"].nunique()),
        "total_samples": int(len(df)),
        "strongest_observed_response": (
            f"{strongest_row['drug_name']} at {strongest_row['concentration_uM']} uM"
        ),
        "missing_values": int(df.isna().sum().sum()),
    }

def build_summary_markdown(summary_df: pd.DataFrame, warnings: list[str]) -> str:
    md = "## Drug Response Summary\\n\\n"
    md += summary_df.to_markdown(index=False)
    md += "\\n\\n## Data Quality Warnings\\n\\n"

    if warnings:
        for warning in warnings:
            md += f"- {warning}\\n"
    else:
        md += "- No major data quality warnings detected.\\n"

    return md

def analyze_drug_response(file) -> dict:
    df = load_drug_response_csv(file)
    warnings = validate_drug_response_df(df)

    if any(w.startswith("Missing required columns") for w in warnings):
        return {
            "df": df,
            "summary_df": pd.DataFrame(),
            "warnings": warnings,
            "cards": {},
            "summary_markdown": "",
        }

    summary_df = summarize_drug_response(df)
    cards = build_drug_response_cards(df, summary_df)
    summary_markdown = build_summary_markdown(summary_df, warnings)

    return {
        "df": df,
        "summary_df": summary_df,
        "warnings": warnings,
        "cards": cards,
        "summary_markdown": summary_markdown,
    }
```

## 3.3 Install `tabulate`

`to_markdown()` may require `tabulate`.

```bash
pip install tabulate
```

Add it to `requirements.txt`.

---

# Phase 4: Add Interactive Plotly Visualization

## 4.1 `src/plots.py`

```python
import pandas as pd
import plotly.graph_objects as go

def create_dose_response_plot(summary_df: pd.DataFrame):
    fig = go.Figure()

    for drug_name, group in summary_df.groupby("drug_name"):
        plot_group = group.copy()

        # Log scale cannot display zero concentration.
        # Keep zero as control but plot it at a small pseudo concentration.
        plot_group["plot_concentration"] = plot_group["concentration_uM"].replace(0, 0.001)

        fig.add_trace(
            go.Scatter(
                x=plot_group["plot_concentration"],
                y=plot_group["mean_viability"],
                mode="lines+markers",
                name=str(drug_name),
                error_y=dict(
                    type="data",
                    array=plot_group["sem_viability"],
                    visible=True,
                ),
                customdata=plot_group[
                    ["concentration_uM", "sd_viability", "sem_viability", "n"]
                ],
                hovertemplate=(
                    "Drug: " + str(drug_name) + "<br>"
                    "Concentration: %{customdata[0]} uM<br>"
                    "Mean viability: %{y:.2f}%<br>"
                    "SD: %{customdata[1]:.2f}<br>"
                    "SEM: %{customdata[2]:.2f}<br>"
                    "n: %{customdata[3]}<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title="Dose-Response Curve",
        xaxis_title="Concentration (uM, log scale; 0 plotted as 0.001)",
        yaxis_title="Mean Cell Viability (%)",
        template="plotly_white",
        hovermode="closest",
    )

    fig.update_xaxes(type="log")
    return fig
```

---

# Phase 5: Build Gradio App

## 5.1 First Version of `app.py`

```python
import gradio as gr
import pandas as pd

from src.drug_analysis import analyze_drug_response
from src.plots import create_dose_response_plot

EXAMPLE_FILE = "data/examples/drug_response_sample.csv"

def format_cards(cards: dict) -> str:
    if not cards:
        return "No summary cards available."

    return f'''
### Dataset Summary

- **Drugs detected:** {cards.get("drugs_detected")}
- **Concentrations tested:** {cards.get("concentrations_tested")}
- **Total samples:** {cards.get("total_samples")}
- **Strongest observed response:** {cards.get("strongest_observed_response")}
- **Missing values:** {cards.get("missing_values")}
'''

def run_analysis(file):
    if file is None:
        file = EXAMPLE_FILE

    result = analyze_drug_response(file)
    df = result["df"]
    summary_df = result["summary_df"]
    cards = result["cards"]
    warnings = result["warnings"]

    if summary_df.empty:
        return df, summary_df, format_cards(cards), "\\n".join(warnings), None, ""

    fig = create_dose_response_plot(summary_df)

    warning_text = "\\n".join([f"- {w}" for w in warnings]) if warnings else "No major warnings detected."

    return (
        df,
        summary_df,
        format_cards(cards),
        warning_text,
        fig,
        result["summary_markdown"],
    )

with gr.Blocks(title="BioDose AI") as demo:
    gr.Markdown(
        '''
# 🧪 BioDose AI

AI-assisted drug response analysis for Biochemistry students.

Upload a drug response CSV or use the built-in sample dataset.
'''
    )

    with gr.Row():
        file_input = gr.File(label="Upload drug response CSV", file_types=[".csv"])
        analyze_btn = gr.Button("Analyze with Python", variant="primary")

    with gr.Tab("Data Preview"):
        raw_output = gr.Dataframe(label="Raw Data")

    with gr.Tab("Summary"):
        summary_output = gr.Dataframe(label="Summary Statistics")
        cards_output = gr.Markdown(label="Result Cards")
        warnings_output = gr.Markdown(label="Data Quality Warnings")

    with gr.Tab("Dose-Response Plot"):
        plot_output = gr.Plot(label="Interactive Dose-Response Curve")

    with gr.Tab("Summary Markdown"):
        markdown_output = gr.Markdown(label="Summary Markdown")

    analyze_btn.click(
        fn=run_analysis,
        inputs=[file_input],
        outputs=[
            raw_output,
            summary_output,
            cards_output,
            warnings_output,
            plot_output,
            markdown_output,
        ],
    )

demo.launch()
```

## 5.2 Run App

```bash
python app.py
```

---

# Phase 6: Add OpenAI API Explanation

## 6.1 `src/llm_helper.py`

```python
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Please create a .env file in the project root."
        )
    return OpenAI(api_key=api_key)

def call_llm(system_prompt: str, user_prompt: str, model: str | None = None) -> str:
    client = get_openai_client()
    selected_model = model or DEFAULT_MODEL

    response = client.responses.create(
        model=selected_model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    return response.output_text
```

## 6.2 Add to `src/drug_analysis.py`

```python
from src.llm_helper import call_llm

def generate_ai_drug_response_explanation(summary_markdown: str) -> str:
    system_prompt = '''
You are an AI assistant helping a third-year undergraduate Biochemistry student.
Explain drug response results clearly and cautiously.
Do not overstate conclusions.
If the dataset is synthetic, say so clearly.
Separate observations from interpretations.
Always include limitations and what to verify manually.
Do not give clinical or medical advice.
'''

    user_prompt = f'''
The following summary statistics come from a drug response / cell viability dataset:

{summary_markdown}

Please write:

## Plain-English Summary
## Key Observations
## Possible Biological Interpretation
## Limitations
## What to Verify Manually
'''

    return call_llm(system_prompt, user_prompt)
```

## 6.3 Add AI Button to `app.py`

Add import:

```python
from src.drug_analysis import analyze_drug_response, generate_ai_drug_response_explanation
```

Add function:

```python
def run_ai_explanation(summary_markdown):
    if not summary_markdown:
        return "Please run Python analysis first."

    try:
        return generate_ai_drug_response_explanation(summary_markdown)
    except Exception as e:
        return f"AI explanation failed: {e}"
```

Add Gradio tab:

```python
with gr.Tab("AI Explanation"):
    ai_btn = gr.Button("Generate AI Explanation")
    ai_output = gr.Markdown(label="AI-assisted Explanation")
```

Add event:

```python
ai_btn.click(
    fn=run_ai_explanation,
    inputs=[markdown_output],
    outputs=[ai_output],
)
```

---

# Phase 7: Add Export and Download

## 7.1 `src/export_utils.py`

```python
from pathlib import Path
from datetime import datetime

def save_markdown_summary(content: str, output_dir: str = "outputs/summaries") -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir) / f"biodose_summary_{timestamp}.md"

    output_path.write_text(content, encoding="utf-8")
    return str(output_path)
```

## 7.2 Add Download Button

In `app.py`:

```python
from src.export_utils import save_markdown_summary

def export_summary(summary_markdown, ai_explanation):
    content = summary_markdown or ""
    if ai_explanation:
        content += "\\n\\n---\\n\\n# AI-assisted Explanation\\n\\n"
        content += ai_explanation

    if not content.strip():
        return None

    return save_markdown_summary(content)
```

Add to UI:

```python
with gr.Tab("Export"):
    export_btn = gr.Button("Download Summary Markdown")
    export_file = gr.File(label="Download")

export_btn.click(
    fn=export_summary,
    inputs=[markdown_output, ai_output],
    outputs=[export_file],
)
```

---

# Phase 8: Create Quarto Report

## 8.1 `report.qmd`

```markdown
---
title: "BioDose AI"
subtitle: "AI-assisted Drug Response Analysis for Biochemistry Students"
format:
  html:
    theme: cosmo
    toc: true
    code-fold: true
    code-tools: true
    number-sections: true
---

# Overview

BioDose AI is a beginner-friendly project that analyzes drug response data using Python and AI.

# Biological Motivation

Drug response experiments help researchers understand how cell viability changes under different drug concentrations.

# Dataset

The first version uses synthetic drug response data.

::: {.callout-warning}
## Synthetic Dataset
This dataset is synthetic and is used for learning purposes only. It should not be interpreted as real experimental evidence.
:::

# Methods

```{python}
import pandas as pd
from src.drug_analysis import analyze_drug_response
from src.plots import create_dose_response_plot

result = analyze_drug_response("data/examples/drug_response_sample.csv")
summary_df = result["summary_df"]
summary_df
```

# Results

```{python}
fig = create_dose_response_plot(summary_df)
fig
```

# AI-assisted Interpretation

The AI explanation should be treated as a draft and must be verified manually.

# Verification Checklist

- Check whether the dataset is synthetic or real.
- Check whether all required columns are present.
- Check whether replicate count is sufficient.
- Check whether the plot uses the correct concentration units.
- Check whether the interpretation overstates conclusions.

# Limitations

- Synthetic data only.
- Small number of replicates.
- No IC50 fitting in the first version.
- No biological validation.

# What I Learned

- How to load CSV data with pandas.
- How to calculate grouped summary statistics.
- How to create an interactive dose-response chart.
- How to use AI cautiously for scientific explanation.
```

## 8.2 Render Quarto

```bash
quarto render report.qmd
```

---

# Phase 9: Add README and Screenshots

## 9.1 README Structure

```markdown
# BioDose AI

## Overview

BioDose AI is an AI-assisted drug response analysis tool for Biochemistry students.

## Features

- Upload drug response CSV
- Calculate summary statistics
- Generate interactive dose-response curve
- Generate AI-assisted explanation
- Export Markdown summary
- Create Quarto report

## Screenshots

Add screenshots here.

## How to Run

```bash
conda activate biodose-ai
python app.py
```

## Sample Data

See:

```text
data/examples/drug_response_sample.csv
```

## Limitations

This is a learning project using synthetic data.

## Future Improvements

- IC50 curve fitting
- multiple assay types
- SQLite history
- protein target integration
- deployment to Hugging Face Spaces
```

## 9.2 Suggested Screenshots

Capture:

- Gradio home page
- Data preview
- Summary statistics
- Dose-response chart
- AI explanation
- Quarto report page

---

# Phase 10: Optional Deployment

## Option A: Hugging Face Spaces

Good for Gradio demo.

Required files:

```text
app.py
requirements.txt
src/
data/examples/
```

## Option B: GitHub Pages

Good for Quarto report.

Publish:

```text
report.html
```

or use Quarto website later.

---

# Milestone Checklist

## Milestone 1: Basic Analysis

- [ ] sample CSV created
- [ ] notebook loads CSV
- [ ] summary statistics work
- [ ] simple chart works

## Milestone 2: Modular Python Code

- [ ] `src/validation.py`
- [ ] `src/drug_analysis.py`
- [ ] `src/plots.py`
- [ ] notebook imports from `src/`

## Milestone 3: Gradio App

- [ ] CSV upload works
- [ ] example data fallback works
- [ ] raw data preview works
- [ ] summary table displays
- [ ] interactive Plotly chart displays

## Milestone 4: OpenAI API

- [ ] `.env` created
- [ ] `src/llm_helper.py` works
- [ ] AI explanation button works
- [ ] AI output includes limitations and verification checklist

## Milestone 5: Polish

- [ ] result cards added
- [ ] data quality warnings added
- [ ] export summary works
- [ ] screenshots added
- [ ] README updated

## Milestone 6: Quarto Report

- [ ] `report.qmd` created
- [ ] Quarto renders successfully
- [ ] report includes plot and limitations

---

# Recommended First Week Plan

## Day 1: Setup

- Create project folder
- Create Conda environment
- Install packages
- Create sample CSV

## Day 2: Notebook

- Load CSV
- Preview data
- Calculate summary statistics

## Day 3: Plot

- Create first dose-response plot
- Learn why zero concentration is tricky on log scale

## Day 4: Modularize

- Create `src/validation.py`
- Create `src/drug_analysis.py`

## Day 5: Gradio

- Create first `app.py`
- Upload CSV
- Display raw data and summary

## Day 6: Plotly in Gradio

- Add interactive dose-response plot
- Add result cards

## Day 7: Review

- Student explains:
  - input data
  - grouping logic
  - chart meaning
  - limitations

---

# Recommended Cursor Prompt for Starting the Project

```text
I am building a beginner-friendly project called BioDose AI.

Context:
I am a third-year Biochemistry student learning Python, Gradio, and AI-assisted coding.

Goal:
Build a modular drug response analysis app.

Requirements:
1. Use Python.
2. Use pandas for CSV analysis.
3. Use Plotly for interactive dose-response charts.
4. Use Gradio Blocks for the UI.
5. Use OpenAI API only for optional explanation, not for core calculations.
6. Keep app.py thin.
7. Put analysis logic in src/drug_analysis.py.
8. Put validation logic in src/validation.py.
9. Put chart logic in src/plots.py.
10. Put OpenAI API calling in src/llm_helper.py.
11. Include beginner-friendly comments.
12. Use synthetic data first.

Please generate the initial project structure and code step by step.
```

---

# Recommended Code Review Prompt

```text
Please review this BioDose AI project for modularity and loose coupling.

Check:
1. Is app.py only handling Gradio UI?
2. Is analysis logic separated into src/drug_analysis.py?
3. Is validation separated into src/validation.py?
4. Is Plotly chart logic separated into src/plots.py?
5. Is OpenAI API calling isolated in src/llm_helper.py?
6. Are there hard-coded local paths?
7. Can the same analysis functions be reused in a notebook, Quarto report, or future FastAPI app?
8. Is the code beginner-friendly?

Please suggest simple improvements without over-engineering.
```

---

# Suggested Next Enhancements After First Version

After the first version works, consider:

1. IC50 estimation
2. multiple assay support
3. SQLite history
4. Quarto auto-report generation
5. protein target linkage
6. integration with ProteinLens
7. deployment to Hugging Face Spaces
8. improved styling and logo
9. downloadable figure PNG
10. unit tests

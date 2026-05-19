# Common Technical Setup and Workflow

## Purpose

This document defines the shared technical setup for a beginner-friendly **Biochemistry + Python + AI + Bioinformatics** learning path.

The goal is not to turn the student into a software engineer. The goal is to help a third-year Biochemistry student use Python and AI-assisted coding tools to explore biological data, drug testing data, protein sequences, and scientific literature.

## Recommended Positioning

**Target identity:**

> Biochemistry student with Python, AI, and bioinformatics capability.

Not:

> Full-stack developer or computer science student.

## Core Principles

1. Use Python as the main language.
2. Use vibe coding tools such as Cursor or Codex to reduce resistance to programming.
3. Require enough code understanding to avoid blind copy-paste.
4. Use Gradio instead of Streamlit for interactive demos.
5. Use Quarto for polished reports and portfolio-style presentation.
6. Keep FastAPI / React as future productization options, not the first learning goal.
7. Make the final result look polished enough that the student feels proud to show it.

---

# Recommended Tool Stack

## Required Tools

| Tool | Purpose |
|---|---|
| Python 3.11 or 3.12 | Main programming language |
| Cursor | AI-assisted coding / vibe coding |
| Jupyter Notebook | Exploration, learning, step-by-step analysis |
| Gradio | Interactive web demo |
| Quarto | Scientific report / portfolio page |
| GitHub | Code storage and portfolio |
| pandas | Data processing |
| numpy | Numerical operations |
| matplotlib / plotly | Visualization |
| scipy / statsmodels | Basic statistics |
| Biopython | Protein / sequence analysis |

## Optional Tools

| Tool | Purpose |
|---|---|
| Codex | Code review, repo cleanup, README generation, refactoring |
| Hugging Face Spaces | Publish Gradio demo |
| GitHub Pages | Publish Quarto HTML report |
| OpenAI / other LLM API | AI-assisted explanation and literature support |
| python-dotenv | Load `OPENAI_API_KEY` from `.env` safely |

---

# Suggested Project Structure

```text
biobridge-ai/
├── app.py
├── requirements.txt
├── README.md
├── report.qmd
├── data/
│   ├── drug_response_sample.csv
│   ├── example_protein.fasta
│   ├── example_abstract.txt
│   └── gene_expression_sample.csv
├── notebooks/
│   ├── 01_biodose.ipynb
│   ├── 02_protein_lens.ipynb
│   ├── 03_target_reader.ipynb
│   └── 04_geneshift.ipynb
├── src/
│   ├── drug_analysis.py
│   ├── protein_analysis.py
│   ├── literature_ai.py
│   ├── gene_expression.py
│   ├── plots.py
│   └── report_utils.py
├── assets/
│   ├── logo.png
│   ├── banner.png
│   └── screenshots/
└── outputs/
    ├── dose_response.png
    ├── amino_acid_chart.png
    ├── gene_expression_chart.png
    └── summaries/
```

## Why This Structure Helps

The key idea is:

> Keep analysis logic in `src/`, use Gradio for interaction, and use Quarto for reporting.

This avoids putting everything into one large app file.

---

# Environment Setup

## Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

## Install Packages

```bash
pip install pandas numpy matplotlib plotly scipy statsmodels jupyter gradio biopython openai python-dotenv
```

## OpenAI API Key Setup

Create a local `.env` file in the project root, or copy the example file:

```bash
cp .env.example .env
```

Then edit `.env` to add your API key:

```text
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

Important:

- Do not commit `.env` to GitHub.
- Add `.env` to `.gitignore`.
- The student should understand when an API call happens.
- The Gradio app should use explicit buttons such as **Generate AI Explanation** rather than calling the API automatically on every change.
- For real lab, company, patient, or confidential data, do not send sensitive raw data to external AI services unless proper permission and policy review are in place.

Recommended `.gitignore`:

```text
.env
__pycache__/
*.pyc
.venv/
outputs/
*.db
```

## requirements.txt

```text
pandas
numpy
matplotlib
plotly
scipy
statsmodels
jupyter
gradio
biopython
python-dotenv
openai
```

---


# OpenAI API Calling Strategy

## Why Include API Calling

The projects should include real LLM API calling because one of the learning goals is to connect Python, AI, and Biochemistry in a practical way.

However, API calling should be added carefully:

1. First make the data analysis work without AI.
2. Then add an explicit AI button in Gradio.
3. Send only summarized, non-sensitive information to the model.
4. Ask for cautious scientific language.
5. Always include a manual verification checklist.

## Recommended LLM Helper Module

Create a shared file:

```text
src/llm_helper.py
```

Example structure:

```python
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Please create a .env file.")
    return OpenAI(api_key=api_key)

def call_llm(system_prompt: str, user_prompt: str, model: str | None = None) -> str:
    client = get_openai_client()
    selected_model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

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

## Recommended Pattern for Each Project

Each project should have two layers:

```text
Layer 1: deterministic Python analysis
Layer 2: optional LLM explanation
```

For example:

```python
summary_df = summarize_drug_response(df)
explanation = generate_ai_explanation(summary_df)
```

The Gradio app should make this clear:

```text
Button 1: Analyze Data
Button 2: Generate AI Explanation
```

This helps the student understand that the AI is not doing the raw calculation. Python does the calculation; AI helps explain the result.

## Recommended System Prompt

Use a shared scientific caution system prompt:

```text
You are an AI assistant helping a third-year undergraduate Biochemistry student.
Explain scientific results clearly and cautiously.
Do not overstate conclusions.
If the data is synthetic or limited, say so clearly.
Separate observations from interpretations.
Always include a "What to verify manually" section.
Do not give clinical or medical advice.
```

## Recommended LLM Output Format

For beginner projects, use Markdown first:

```markdown
## Plain-English Summary

## Key Observations

## Possible Biological Interpretation

## Limitations

## What to Verify Manually
```

Later, structured JSON can be added if needed.

## Cost and Safety Controls

Recommended controls:

- Use a small/low-cost model for drafts.
- Send summary statistics rather than full raw data where possible.
- Add a maximum input size.
- Add a warning when input is too long.
- Log only non-sensitive metadata.
- Never hard-code the API key.
- Never upload `.env` to GitHub.

## Optional SQLite Integration Later

If SQLite is added later, save:

```text
project_type
input_name
summary_json
ai_explanation
created_at
```

Do not store API keys in SQLite.

---

# Visual Presentation Add-On

A dedicated visual strategy is provided in:

```text
07_Visual_Presentation_and_Interaction_Strategy.md
```

This add-on recommends:

- interactive Plotly charts
- Gradio result cards
- SVG / Mermaid workflow diagrams
- Quarto portfolio layout
- optional 3D molecular structure views
- AI figure caption generation
- data quality warnings
- downloadable summaries

The visual goal is to make the projects feel polished, modern, and worth showing to others.

---

# Development Environment and Code Architecture Add-On

A dedicated development and architecture guide is provided in:

```text
08_Development_Environment_and_Code_Architecture_Guidelines.md
```

This add-on covers:

- Windows 11 setup
- Ubuntu 24.04 setup
- Miniconda environment setup
- `environment.yml`
- reusable project structure
- loose coupling rules
- modular code guidelines
- `app.py` as a thin Gradio UI layer
- separating Python analysis from OpenAI API calls
- validation and export modules
- beginner-friendly testing strategy
- Cursor / Codex prompts for refactoring and code quality

# Recommended Workflow

## Step 1: Explore in Jupyter Notebook

Use notebooks to learn and validate the logic.

Example:

```text
notebooks/01_biodose.ipynb
```

The notebook should include:

- biological question
- input data description
- Python code
- summary table
- plots
- interpretation
- limitations

## Step 2: Move Stable Code into `src/`

Example:

```python
# src/drug_analysis.py

def analyze_drug_response(csv_file):
    ...
```

This teaches basic modular thinking without forcing advanced software engineering.

## Step 3: Build a Gradio Demo

Use `app.py` to create a polished interactive interface.

Recommended Gradio app structure:

```text
Hero / title section
Tabs
Result cards
Plots
AI explanation area
Download area
Footer
```

## Step 4: Build a Quarto Report

Use `report.qmd` to generate a polished project report.

Suggested Quarto report sections:

```text
Overview
Biological Motivation
Dataset
Methods
Results
Interactive Demo
AI-assisted Interpretation
Limitations
Future Work
What I Learned
```

## Step 5: Publish

Recommended publishing options:

| Output | Platform |
|---|---|
| Gradio demo | Hugging Face Spaces |
| Quarto report | GitHub Pages |
| Source code | GitHub |

---

# Fancy Presentation Requirements

To make the project feel exciting, each project should include:

1. A strong project name
2. A short subtitle
3. A simple logo or emoji
4. A polished Gradio theme
5. Tabs instead of one long page
6. Example data
7. Result cards
8. At least one attractive chart
9. AI explanation box
10. Verification / limitation callout
11. Quarto report
12. Screenshots in README
13. A shareable link

## Example Project Branding

| Project | Subtitle |
|---|---|
| BioDose AI | AI-assisted drug response analysis |
| ProteinLens | Explore protein sequences with Python and AI |
| TargetReader AI | Understand drug target papers faster |
| GeneShift | Explore treatment-driven gene expression changes |
| BioBridge AI | A mini AI toolkit for biochemistry data exploration |

---

# Minimum Code Understanding Requirements

The student should not blindly rely on AI-generated code. For every project, he should be able to answer:

1. What is the input data?
2. What does each column or input field mean?
3. Which function loads the data?
4. Which function performs the analysis?
5. Which function creates the plot?
6. Which part of Gradio connects a button to a Python function?
7. What needs to change if the input column names change?
8. What part of the result is biological interpretation rather than raw computation?
9. What did AI generate?
10. What must be verified manually?

## Minimum Python Concepts

He should understand:

```text
variables
lists
dictionaries
functions
imports
if statements
for loops
pandas DataFrame
read_csv
groupby
mean / standard deviation
plotting
basic error messages
```

He does not need to learn deeply at the beginning:

```text
classes
async programming
FastAPI
React
databases
Docker
authentication
deployment engineering
```

---

# Vibe Coding Rules

## Good Prompt Pattern

A good prompt should include:

1. The student's background
2. The biological problem
3. The expected input format
4. The desired outputs
5. A request for beginner-friendly explanations
6. A request to keep code modular

Example:

```text
I am a third-year biochemistry student learning Python with AI assistance.

I want to analyze a drug response experiment using Python.

The CSV columns are:
sample_id, drug_name, concentration_uM, replicate, cell_viability_percent

Please create beginner-friendly Python code that:
1. loads the CSV
2. checks the data
3. calculates summary statistics
4. creates a dose-response plot
5. explains each step clearly

Please keep the code simple and modular.
```

## Bad Prompt Pattern

Avoid vague prompts like:

```text
Write code for me.
```

Better:

```text
Create a beginner-friendly analysis workflow and explain the biological meaning of each step.
```

---

# Recommended Learning Timeline

## Two-Week Trial Version

Best for a student who is not very motivated at first.

### Week 1: Make It Work

Goal:

> Build a working BioDose notebook and simple Gradio demo.

Deliverables:

- sample CSV
- notebook
- basic analysis function
- simple Gradio app
- one chart

### Week 2: Make It Look Good

Goal:

> Make the project feel polished and shareable.

Deliverables:

- improved Gradio UI
- result cards
- Quarto mini report
- README
- screenshots

## Four-Week Version

### Week 1: Python + BioDose Notebook

- pandas
- groupby
- summary statistics
- dose-response plot

### Week 2: BioDose Gradio App

- upload CSV
- display summary
- display chart
- output AI-assisted explanation template

### Week 3: ProteinLens or TargetReader

Choose one:

- protein sequence analysis
- literature summary assistant

### Week 4: Quarto Report + GitHub

- report.qmd
- README.md
- screenshots
- optional deployment

## Six-Week Portfolio Version

### Week 1: BioDose Notebook
### Week 2: BioDose Gradio App
### Week 3: ProteinLens
### Week 4: TargetReader
### Week 5: Integrated Gradio App
### Week 6: Quarto Portfolio + Publication

---

# Suggested Parent Role

The parent should act as:

- technical mentor
- project manager
- code reviewer
- deployment helper

The student should own:

- biological question
- data meaning
- interpretation
- limitations
- topic choice
- final explanation

This keeps the project connected to his Biochemistry identity rather than making it feel like a computer science assignment.

# Common Technical Setup and Workflow

## Purpose

This document defines the shared technical setup for the full **Biochemistry + Python + AI + Bioinformatics** learning path.

It is the common foundation for:

- BioDose AI
- ProteinLens
- TargetReader AI
- GeneShift
- BioBridge AI

The goal is not to turn the student into a software engineer. The goal is to help a third-year Biochemistry student use Python and AI-assisted coding tools to explore biological data, drug testing data, protein sequences, and scientific literature in a practical and useful way.

## Recommended Positioning

**Target identity:**

> Biochemistry student with Python, AI, and bioinformatics capability.

Not:

> Full-stack developer or computer science student.

## Core Principles

1. Use Python as the main language.
2. Use AI coding tools such as Cursor or Codex to make the first project easier to start.
3. Require enough code understanding to avoid blind copy-paste.
4. Start with deterministic Python analysis before adding AI explanation.
5. Use Gradio instead of Streamlit for interactive demos.
6. Use Quarto for polished reports and portfolio-style presentation.
7. Keep FastAPI / React as future productization options, not the first learning goal.
8. Make the final result look polished enough that the student feels proud to show it.

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
| OpenAI API | AI-assisted explanation and literature support |
| python-dotenv | Load `OPENAI_API_KEY` from `.env` safely |

---

# Development Environment

## Recommended Environment Strategy

Miniconda is already installed, so the preferred setup is one shared Conda environment for the learning projects.

Recommended environment name:

```bash
conda create -n biobridge-ai python=3.11 -y
conda activate biobridge-ai
```

Python 3.11 is recommended because it is stable and broadly compatible with scientific Python packages.

Python 3.12 is also acceptable if all packages install correctly.

## Windows 11 Setup

Recommended tools:

- Miniconda
- Cursor
- Git for Windows
- Quarto
- Google Chrome or Edge
- Optional: VS Code

Recommended terminal:

- Anaconda Prompt
- PowerShell
- Windows Terminal
- Cursor terminal

## Ubuntu 24.04 Setup

Recommended tools:

- Miniconda
- Cursor or VS Code
- Git
- Quarto
- Chrome or Firefox

## Install Packages

```bash
pip install pandas numpy matplotlib plotly scipy statsmodels jupyter gradio biopython openai python-dotenv
```

If needed:

```bash
pip install jupyterlab
```

## Start Jupyter

```bash
jupyter notebook
```

or:

```bash
jupyter lab
```

## Run Gradio App

```bash
python app.py
```

Gradio will usually show a local URL such as:

```text
http://127.0.0.1:7860
```

## Recommended `environment.yml`

```yaml
name: biobridge-ai
channels:
  - conda-forge
dependencies:
  - python=3.11
  - pip
  - jupyter
  - pandas
  - numpy
  - scipy
  - statsmodels
  - matplotlib
  - plotly
  - biopython
  - pip:
      - gradio
      - openai
      - python-dotenv
```

Useful commands:

```bash
conda env create -f environment.yml
conda activate biobridge-ai
conda env update -f environment.yml --prune
conda env export --from-history > environment.yml
```

---

# Shared Project Structure

## Recommended Folder Layout

```text
biobridge-ai/
├── app.py
├── README.md
├── requirements.txt
├── environment.yml
├── report.qmd
├── .env
├── .gitignore
├── data/
│   ├── examples/
│   │   ├── drug_response_sample.csv
│   │   ├── example_protein.fasta
│   │   ├── example_abstract.txt
│   │   └── gene_expression_sample.csv
│   └── private/
├── notebooks/
│   ├── 01_biodose.ipynb
│   ├── 02_protein_lens.ipynb
│   ├── 03_target_reader.ipynb
│   └── 04_geneshift.ipynb
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── validation.py
│   ├── llm_helper.py
│   ├── drug_analysis.py
│   ├── protein_analysis.py
│   ├── literature_ai.py
│   ├── gene_expression.py
│   ├── plots.py
│   └── export_utils.py
├── assets/
│   ├── logo.png
│   ├── banner.png
│   └── screenshots/
├── outputs/
│   ├── figures/
│   ├── summaries/
│   └── reports/
└── tests/
    ├── test_drug_analysis.py
    ├── test_protein_analysis.py
    └── test_gene_expression.py
```

## Why This Structure Helps

The key idea is:

> Keep analysis logic in `src/`, use Gradio for interaction, and use Quarto for reporting.

This avoids putting everything into one large app file and keeps the code reusable across notebook, demo, report, and future product versions.

---

# Environment Files and Safety

## Recommended `.env`

Create a local `.env` file in the project root:

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

## Recommended `.gitignore`

```text
.env
.venv/
__pycache__/
*.pyc
.ipynb_checkpoints/
outputs/
*.db
.DS_Store
```

Optional:

```text
data/private/
```

## Recommended `requirements.txt`

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

## Core Design Rule

Use this shared design:

```text
Python deterministic analysis first
→ optional LLM explanation second
```

This makes the project easier to understand and safer scientifically.

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
Button 1: Analyze with Python
Button 2: Generate AI Explanation
```

This helps the student understand that the AI is not doing the raw calculation. Python does the calculation; AI helps explain the result.

## Shared Scientific System Prompt

Use a shared scientific caution system prompt:

```text
You are an AI assistant helping a third-year undergraduate Biochemistry student.
Explain scientific results clearly and cautiously.
Do not overstate conclusions.
Separate observations from interpretations.
If data is synthetic, toy, limited, or unnormalized, say so clearly.
Always include limitations and what to verify manually.
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

## Example Project-Specific Functions

```python
from src.llm_helper import call_llm

def generate_ai_drug_response_explanation(summary_markdown: str) -> str:
    ...

def summarize_scientific_abstract(title: str, abstract: str) -> str:
    ...
```

## Cost and Safety Controls

Recommended controls:

- Use a small or low-cost model for drafts.
- Send summary statistics rather than full raw data where possible.
- Add a maximum input size.
- Add a warning when input is too long.
- Log only non-sensitive metadata.
- Never hard-code the API key.
- Never upload `.env` to GitHub.

## Safety and Privacy Guidelines

### Do

- Use synthetic data first.
- Send summaries instead of raw data when possible.
- Keep API calls behind explicit buttons.
- Add verification checklists.
- Keep `.env` private.
- Mention limitations in every AI output.

### Do Not

- Do not hard-code API keys.
- Do not commit `.env`.
- Do not upload confidential lab, company, or patient data.
- Do not use AI output as scientific truth.
- Do not give clinical or medical recommendations.
- Do not upload full copyrighted papers unless allowed.

## Suggested Student Explanation

The student should be able to say:

```text
The Python code performs the actual data analysis. The OpenAI API is used only to generate a plain-English explanation and a verification checklist. I still need to verify the scientific claims manually.
```

---

# Visual Presentation and Interaction Strategy

## Purpose

The projects should not look like plain scripts or basic notebooks only.

They should feel like small, polished scientific AI tools:

```text
Biochemistry problem
→ Python analysis
→ interactive visualization
→ AI explanation
→ verification checklist
→ polished Quarto report
```

For a student whose main interest is Biochemistry rather than software engineering, visual presentation can make the project feel clearer, more useful, and more worth showing to others.

## Visual Feature Priority

### Must-Have Features

Every serious project should include:

```text
Interactive Plotly charts
Gradio tabs
Result cards
Example data buttons
Quarto callout boxes
Screenshots in README
Clear limitation warning
```

### Strongly Recommended Features

```text
SVG or Mermaid workflow diagrams
AI figure caption generator
Verification checklist
Downloadable summaries
Data quality warnings
Synthetic vs real data badge
```

### Nice-to-Have Features

```text
3D protein structure viewer
Beginner / Advanced explanation toggle
Clickable pathway-style diagram
Quarto portfolio website
Chatbot panel for literature Q&A
```

### Later-Only Features

```text
Full molecular docking visualization
Real RNA-seq pipeline visualization
Complex 3D simulation
Custom JavaScript visualization components
```

## Recommended Visual Layers

### Level 1: Polished 2D Scientific Charts

Required for all projects.

Recommended tools:

```text
plotly
matplotlib
pandas
```

Plotly is strongly recommended for the Gradio app because it gives hover, zoom, and interactive exploration.

### Level 2: Interactive Plots

Recommended for:

- BioDose AI
- ProteinLens
- GeneShift

Examples:

```text
Hover over a data point
Zoom into a chart
Toggle traces on and off
View details in tooltips
```

### Level 3: SVG or Mermaid Diagrams

Recommended for Quarto reports and portfolio pages.

Use cases:

- analysis workflow diagram
- data pipeline diagram
- AI verification workflow
- protein analysis workflow
- literature reading workflow

### Level 4: 3D Molecular View

Optional but especially appealing for ProteinLens.

Recommended as a Phase 2 or Phase 3 enhancement, not a first-week requirement.

### Level 5: Storytelling and Portfolio Presentation

Required for final presentation.

Use:

- Quarto report
- screenshots
- project cards
- result cards
- demo links
- README
- reflection section

## Gradio Interaction Design

Use `gr.Blocks`.

Suggested structure:

```text
Hero section
Project tabs
Input panel
Analyze button
Result cards
Charts
AI explanation panel
Verification checklist
Export/download area
Footer
```

Each tab should have two main actions:

```text
Analyze with Python
Generate AI Explanation
```

## Quarto Presentation Design

Recommended features:

```text
HTML theme
table of contents
code folding
callout boxes
figure captions
tabs
screenshots
demo links
workflow diagrams
reflection section
```

Suggested YAML:

```yaml
---
title: "BioBridge AI"
subtitle: "Biochemistry + Python + AI Portfolio"
format:
  html:
    theme: cosmo
    toc: true
    code-fold: true
    code-tools: true
    number-sections: true
---
```

Recommended report sections:

```text
Overview
Biological Motivation
Project Demo
Dataset
Methods
Results
Interactive Visualization
AI-assisted Explanation
Verification Checklist
Limitations
What I Learned
Future Work
```

## Visual Assets

Optional assets:

```text
assets/logo.png
assets/banner.png
assets/screenshots/
```

At minimum, capture screenshots of:

- home screen
- one analysis result
- one chart
- one AI explanation
- one Quarto report page

## Data Quality Visual Warnings

Add visible warnings for:

```text
missing required columns
missing values
non-numeric concentration
only one replicate
no control group
too few genes
invalid amino acid characters
abstract too short
API key missing
```

## Example Project Branding

Use names that feel polished and memorable:

- BioDose AI
- ProteinLens
- TargetReader AI
- GeneShift
- BioBridge AI

The student should feel that the result is a real small scientific tool, not only a simple class exercise or demo.

## Fancy Presentation Requirements

The final project presentation should include:

- hero banner
- consistent theme
- project cards
- tabs
- example data
- result cards
- charts
- AI explanation boxes
- warnings and verification checklists
- footer with GitHub and report links

---

# Development and Code Architecture Guidelines

## Main Design Goal

The coding style should emphasize:

- reusability
- loose coupling
- modularity
- clear separation between analysis logic, AI calls, UI, and reporting
- beginner-friendly structure

## Architecture Principles

### 1. Keep `app.py` Thin

`app.py` should only contain:

- Gradio layout
- input components
- output components
- button-event wiring
- light formatting

It should not contain heavy analysis logic.

### 2. Keep Analysis Logic Independent

Analysis modules should not know about Gradio.

The analysis code should be reusable in:

- notebook
- Gradio app
- Quarto report
- future FastAPI app
- tests

### 3. Separate Deterministic Analysis from AI Explanation

Python should calculate results.

LLM should explain results.

Recommended flow:

```text
input data
→ validation
→ deterministic Python analysis
→ chart
→ optional LLM explanation
→ report or export
```

Do not let the LLM calculate core statistics.

### 4. Use Clear Function Inputs and Outputs

Prefer functions like:

```python
def summarize_drug_response(df):
    ...
```

Instead of functions that depend on global variables.

### 5. Avoid Hidden Side Effects

A function should not unexpectedly:

- write files
- call API
- modify global state
- launch UI

unless its name clearly says so.

### 6. Use Small Modules

Recommended module responsibilities:

| Module | Responsibility |
|---|---|
| `config.py` | environment variables and app constants |
| `validation.py` | input checks and warnings |
| `drug_analysis.py` | BioDose calculations |
| `protein_analysis.py` | FASTA and protein calculations |
| `literature_ai.py` | TargetReader prompts and LLM wrapper functions |
| `gene_expression.py` | GeneShift calculations |
| `plots.py` | Plotly or matplotlib figure creation |
| `llm_helper.py` | shared OpenAI API calling |
| `export_utils.py` | download files, markdown summaries, report snippets |

### 7. Keep Prompts Separate from UI

Prompt-building functions should be in `src/`, not in `app.py`.

### 8. Use Validation Before Analysis

Before doing analysis, check:

- required columns
- missing values
- numeric types
- empty input
- too-small dataset
- invalid FASTA characters
- abstract too short
- missing API key

Validation should return user-friendly warnings.

### 9. Return Structured Results

Instead of returning only text, prefer returning dictionaries or small result objects.

Example:

```python
result = {
    "summary_df": summary_df,
    "warnings": warnings,
    "cards": {
        "drugs_detected": 2,
        "total_samples": 30,
    },
}
```

### 10. Design for Future FastAPI or React Reuse

Even though FastAPI and React are not part of the first stage, the code should be easy to reuse later.

If the core analysis is independent from Gradio, it can later be called from:

- FastAPI endpoint
- React frontend
- CLI tool
- scheduled batch job

## Loose Coupling Rules

1. No UI code in analysis modules.
2. No API key handling outside `llm_helper.py`.
3. No direct file paths hard-coded in core logic.
4. Notebooks are for exploration, not core logic.
5. Quarto should reuse existing functions from `src/`.
6. Keep example data small and easy to inspect.

## Suggested Function Design

### BioDose AI

```python
def load_drug_response_csv(file_path_or_buffer):
    ...

def validate_drug_response_df(df):
    ...

def summarize_drug_response(df):
    ...

def build_drug_response_cards(df, summary_df):
    ...

def create_dose_response_plot(summary_df):
    ...

def build_drug_response_markdown(summary_df, warnings):
    ...

def generate_ai_drug_response_explanation(summary_markdown):
    ...
```

### ProteinLens

```python
def parse_fasta(text):
    ...

def validate_protein_sequence(sequence):
    ...

def calculate_amino_acid_composition(sequence):
    ...

def build_protein_cards(sequence, composition_df):
    ...

def create_amino_acid_plot(composition_df):
    ...

def build_protein_summary_markdown(cards, composition_df):
    ...

def generate_ai_protein_profile(protein_name, summary_markdown):
    ...
```

### TargetReader AI

```python
def validate_abstract(title, abstract):
    ...

def build_abstract_summary_prompt(title, abstract):
    ...

def summarize_scientific_abstract(title, abstract):
    ...

def build_followup_prompt(title, abstract, question):
    ...

def ask_about_abstract(title, abstract, question):
    ...
```

### GeneShift

```python
def load_expression_csv(file_path_or_buffer):
    ...

def validate_expression_df(df):
    ...

def calculate_expression_summary(df):
    ...

def get_top_changed_genes(summary_df, n=5):
    ...

def create_fold_change_plot(summary_df):
    ...

def build_gene_expression_markdown(summary_df):
    ...

def generate_ai_gene_expression_notes(top_genes_markdown):
    ...
```

## Suggested Testing Strategy

Testing should be light but useful.

Install:

```bash
pip install pytest
```

Recommended beginner tests:

- required columns are detected
- summary table has expected columns
- protein sequence length is correct
- invalid amino acid characters are detected
- gene expression fold change is calculated

Run:

```bash
pytest
```

---

# Student-Friendly and Industry-Inspired Engagement Layer

## Purpose

This learning path should feel like a set of small industry-inspired bio-AI missions, not standalone coding exercises.

The goal is to make the projects:

- more entertaining
- more visually attractive
- closer to real bioinformatics, biotech, and pharma workflows
- still beginner-friendly
- scientifically responsible
- suitable for portfolio presentation

## Big Idea

Do not change the scientific core too much.

Instead, add a project-interest layer:

```text
Scientific core:
data → Python analysis → visualization → AI explanation → verification

Project-interest layer:
mission mode → scenario datasets → badges → rankings → challenge questions → mini report/poster
```

This can make the project feel clearer and more personally meaningful without making it too complex.

## Recommended Brand

```text
BioBridge AI Lab
```

## Suggested Subtitle

```text
Industry-inspired mini AI tools for biochemistry and bioinformatics learning.
```

## Project Missions

| Mission | Project | Industry-Inspired Scenario |
|---|---|---|
| Mission 1 | BioDose AI | Compound screening / assay triage |
| Mission 2 | ProteinLens | Drug target profiling |
| Mission 3 | TargetReader AI | Scientific intelligence / literature briefing |
| Mission 4 | GeneShift | Biomarker candidate discovery |
| Mission 5 | BioBridge AI | Bio-AI portfolio lab |

## Recommended Engagement Features

Add these gradually:

```text
mission framing
scenario datasets
data quality score
candidate ranking
achievement badges
challenge questions
score my interpretation
explanation level selector
lab notebook mode
mini report or poster
```

## Real-World but Simplified Labels

| Feature | Real-World Inspiration |
|---|---|
| Candidate ranking | compound triage |
| Data quality score | assay QC |
| Next experiment suggestions | lab follow-up planning |
| TargetReader summary | scientific intelligence |
| GeneShift top genes | biomarker exploration |
| ProteinLens 3D link | target structure exploration |

## Safe Boundary Statements

Every app should clearly say:

```text
For learning purposes only.
Synthetic data unless stated otherwise.
Not clinical, medical, or regulatory advice.
AI explanations must be verified manually.
```

## Things to Avoid in Early Versions

Avoid these in the first versions:

```text
real RNA-seq pipeline
molecular docking
molecular dynamics
clinical prediction
real patient data
regulatory workflow
complex database
cloud deployment complexity
custom 3D engine
advanced statistics
full IC50 production-grade fitting
```

## Where to Keep the Full Guidance

The detailed engagement guide is maintained in:

```text
06_Student_Friendly_and_Industry_Inspired_Engagement_Layer.md
```

Use `00_Common_Technical_Setup_and_Workflow.md` for the shared summary and `06_Student_Friendly_and_Industry_Inspired_Engagement_Layer.md` for the deeper mission-design ideas.

---

# Academic Life Science and Biochemistry Support Layer

## Purpose

These projects should support not only Python, AI, and bioinformatics skill-building, but also academic learning in life science and Biochemistry.

Each project should connect three layers:

```text
Biochemistry concept
→ data / computational analysis
→ academic output
```

## Recommended Academic Outputs

Every project should produce at least one academic-style output.

Recommended outputs:

```text
lab report paragraph
figure caption
discussion draft
limitations section
study notes
key terms list
concept explanation
presentation slide outline
quiz questions
reflection paragraph
```

## Suggested Academic App Modes

```text
Lab Report Mode
Journal Club Mode
Study Notes Mode
Presentation Mode
Quiz Mode
```

## Safe Academic Boundary

Each tool should clearly state:

```text
This tool supports academic learning and scientific communication practice.
It does not replace course requirements, instructor feedback, original reading, or experimental validation.
AI-generated text must be reviewed and edited by the student.
```

## Where to Keep the Full Guidance

The detailed academic-support guide is maintained in:

```text
07_Academic_Life_Science_and_Biochemistry_Support_Layer.md
```

---

# Student-Friendly Tone and Framing

## Preferred Tone

The documents should feel:

```text
curious
choice-oriented
professional
calm
encouraging
portfolio-focused
academically useful
```

## Preferred Framing

Use framing like:

```text
Explore how Python and AI can support Biochemistry.
Build small tools that connect lab data, proteins, papers, and scientific communication.
Create portfolio-style work that can be shown to others.
Try one small project first, then decide what to continue.
```

Avoid framing that suggests the student needs to be pushed, fixed, or pressured into programming.

## Where to Keep the Full Guidance

The detailed tone guide is maintained in:

```text
06_Student_Friendly_and_Industry_Inspired_Engagement_Layer.md
```

---

# Recommended Workflow

## Step 1: Explore in Jupyter Notebook

Use notebooks to learn and validate the logic.

The notebook should include:

- biological question
- input data description
- Python code
- summary table
- plots
- interpretation
- limitations

## Step 2: Move Stable Code into `src/`

After a notebook works, move reusable code into `src/`.

This teaches modular thinking without forcing advanced software engineering.

## Step 3: Build a Gradio Demo

Use `app.py` to create a polished interactive interface.

Recommended Gradio app structure:

```text
Hero or title section
Tabs
Result cards
Plots
AI explanation area
Download area
Footer
```

## Step 4: Build a Quarto Report

Use `report.qmd` to generate a polished project report.

Suggested report sections:

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

# Minimum Code Understanding Requirements

The student does not need to master software engineering, but should understand enough to explain what the code is doing.

The student should be able to answer:

- What file loads the data?
- What function calculates the summary?
- What function creates the chart?
- What part calls the OpenAI API?
- What part is Python analysis vs AI explanation?
- What are the main limitations of the result?

## Minimum Python Concepts

The student should gradually become comfortable with:

- variables
- lists
- dictionaries
- functions
- `for` loops
- `if` statements
- importing libraries
- pandas DataFrames
- reading CSV files
- plotting
- basic debugging

The target is not deep computer science knowledge. The target is enough understanding to use computational tools responsibly in a Biochemistry context.

---

# Vibe Coding Rules

## Good Prompt Pattern

When using AI coding tools, the prompts should be specific and beginner-friendly.

Example:

```text
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

## Recommended Refactoring and Review Prompts

Useful prompts later:

```text
Please refactor this project for better reusability and loose coupling.
Keep app.py focused on Gradio UI only.
Move analysis logic to src/*.py.
Move OpenAI API calling to src/llm_helper.py.
Move validation logic to src/validation.py.
Keep functions small and beginner-friendly.
```

```text
Please review this code for coupling problems.
Check whether Gradio UI code is mixed with analysis logic,
API key handling is spread across files,
functions depend on global variables,
file paths are hard-coded,
and prompts are mixed into app.py.
```

---

# Recommended Learning Timeline

## Two-Week Trial Version

Best for a student who wants a low-friction starting point.

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

- `report.qmd`
- `README.md`
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

# Suggested Mentor Role

The mentor should act as:

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

This keeps the project connected to the student's Biochemistry identity rather than making it feel like a computer science assignment.

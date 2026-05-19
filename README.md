# BioDose AI

BioDose AI is an AI-assisted drug response analysis project for Biochemistry students.

It is designed as a beginner-friendly learning project that connects Python, Gradio, scientific plotting, and cautious AI-assisted interpretation for dose-response data.

## Setup

Choose one environment style: `miniconda` or `venv`.

### Option 1: Miniconda

Create and activate a conda environment:

```bash
conda create -n biodose-ai python=3.11
conda activate biodose-ai
```

Install the project dependencies:

```bash
pip install -r requirements.txt
```

### Option 2: venv

Create and activate a local virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

Install the project dependencies:

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Then edit `.env` and add your OpenAI key if you want AI-generated explanations and captions:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

If you skip this step, the app still works and falls back to local rule-based explanation and caption text.

## Run The Application

Start the Gradio app:

```bash
python app.py
```

Gradio will print a local URL in the terminal. Open that URL in your browser.

## How To Use The Application

1. Choose an assay type from the dropdown, such as `MTT`, `CellTiter-Glo`, or `Apoptosis`.
2. Either click `Use Sample Dataset` or upload your own CSV file.
3. Click `Analyze with Python`.
4. Review the outputs in each tab.

### Main Tabs

- `Data Preview`: shows the raw uploaded data table
- `Summary`: shows result cards, dataset context, assay guidance, validation warnings, IC50 fit warnings, grouped statistics, and IC50 fit table
- `Dose-Response Plot`: shows the interactive Plotly curve and fitted IC50 overlays when available
- `AI Explanation`: generates an interpretation draft and figure caption
- `Summary Markdown`: shows the export-ready markdown summary
- `Templates`: lets you download standardized assay template CSV files
- `Export`: lets you download markdown, summary CSV, and the report-package ZIP

### Expected Input Columns

Your dataset should contain these required columns:

- `sample_id`
- `drug_name`
- `concentration_uM`
- `replicate`
- `cell_viability_percent`

The easiest starter file is:

- `data/examples/drug_response_sample.csv`

### Example Validation Files

You can also test the validation behavior with:

- `data/examples/drug_response_missing_column.csv`
- `data/examples/drug_response_duplicate_samples.csv`
- `data/examples/drug_response_negative_concentration.csv`

## Run Tests

Run the automated tests with:

```bash
pytest
```

## Project Structure

- `app.py` - Gradio app interface
- `src/` - reusable Python modules
- `data/examples/` - sample drug response data
- `notebooks/` - exploratory notebook
- `docs/` - project documentation

## Current Features

- Upload a drug response CSV or use the built-in sample dataset
- Download standardized assay templates for `MTT`, `CellTiter-Glo`, and `Apoptosis`
- Validate required columns and surface data-quality warnings
- Compute grouped mean, standard deviation, standard error, and replicate counts
- Display a log-scale Plotly dose-response chart
- Fit per-drug IC50 curves and surface fit-quality warnings
- Generate a cautious AI explanation when an OpenAI API key is configured
- Generate a short figure caption for the dose-response plot
- Fall back to a local rule-based interpretation if AI is unavailable
- Show dataset-context guidance for sample versus user-uploaded files
- Export the summary and interpretation as markdown
- Export the grouped summary table as CSV
- Export a polished report-package ZIP with markdown, summary table, and IC50 table

## Outputs You Can Create

- An interactive dose-response plot for visual comparison across drugs
- A grouped summary table with mean, standard deviation, standard error, and replicate counts
- A per-drug IC50 table with fit-quality review warnings
- A cautious interpretation draft for a results section
- A figure caption draft for reports or presentation slides
- Markdown, CSV, and zipped report-bundle exports for downstream reporting

## Recommended Workflow

1. Start with `data/examples/drug_response_sample.csv`.
2. Explore the logic in `notebooks/01_biodose_exploration.ipynb`.
3. Reuse the analysis modules in `src/`.
4. Run the Gradio app for an interactive demo.
5. Use `report.qmd` to present results in a polished report format.

## Example Datasets

- `data/examples/drug_response_sample.csv`: clean synthetic teaching dataset for the happy-path workflow
- `data/examples/drug_response_missing_column.csv`: demonstrates the required-column validation error
- `data/examples/drug_response_duplicate_samples.csv`: demonstrates duplicate `sample_id` detection
- `data/examples/drug_response_negative_concentration.csv`: demonstrates suspicious concentration-value detection

These files are useful for teaching what validation warnings look like before students work with messier lab exports.

## Standardized Assay Templates

Use the `Templates` tab in the app to download starter CSVs for:

- `MTT`
- `CellTiter-Glo`
- `Apoptosis`

Each template includes the required BioDose AI analysis columns plus optional metadata fields such as `assay_type`, `cell_line`, `exposure_hours`, and `control_type`.

## Example Narrative Output

Typical outputs from the current pipeline include:

- Interpretation summary: `DrugA` appears to reduce cell viability more strongly than `DrugB` at the highest tested concentration, while still requiring cautious review.
- Figure caption: the dose-response plot reports mean viability across concentrations, highlights the strongest observed response, and states that error bars reflect SEM.
- Data-quality review: warnings call out missing columns, duplicate identifiers, or suspicious values before a result is interpreted.

## Notes

- Use `docs/03_BioDose_AI_Step_by_Step_Development_Guide.md` to continue development.
- See [TODO.md](/home/scott/workspace/drug_response_analyzer/TODO.md) for remaining real-world enhancements.
- Do not commit `.env` to GitHub.

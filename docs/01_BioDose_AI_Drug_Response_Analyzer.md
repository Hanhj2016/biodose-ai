# BioDose AI: AI-assisted Drug Response Analyzer

## Project Summary

**BioDose AI** is a beginner-friendly Python and Gradio project for analyzing drug response or cell viability data.

It is the best first project if the student will work in a drug testing or lab environment during the summer.

## Project Positioning

> A small AI-assisted tool that helps Biochemistry students analyze drug response data, visualize dose-response patterns, and draft a cautious scientific interpretation.

## Why This Project Matters

Drug testing and cell viability experiments often generate tabular data. Students need to answer questions such as:

- Does the drug show a dose-dependent effect?
- Which concentration begins to reduce cell viability?
- How do two drug candidates compare?
- What do the results suggest?
- What limitations should be mentioned?

This project connects directly to lab work and is practical for a Biochemistry student.

---

# Key Use Cases

## Use Case 1: Single Drug Dose-Response Analysis

### Input

A CSV file with cell viability results at different concentrations.

### Output

- summary statistics
- mean viability
- standard deviation
- standard error
- dose-response plot
- plain-English interpretation

## Use Case 2: Compare Two Drug Candidates

### Input

A CSV file containing data for DrugA and DrugB.

### Output

- side-by-side summary table
- dose-response plot with both drugs
- comparison notes
- possible stronger response indication

## Use Case 3: AI-assisted Lab Result Summary

### Input

Summary statistics and plot description.

### Output

- draft Results paragraph
- key observations
- limitations
- next-step suggestions

---

# Test Data Source

## Recommended Source for First Version

Use **synthetic generated data** first.

Reason:

- safe
- easy to control
- no privacy issue
- easier for beginner debugging
- good for demo

## Synthetic Data Generation Prompt

Use this prompt in ChatGPT, Cursor, or another LLM:

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

## Example Synthetic Data

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

## Optional Real Data Source

For later improvement, search for public educational datasets related to:

- cell viability assay
- dose-response assay
- IC50 example dataset
- pharmacology teaching dataset

Recommended search terms:

```text
public drug response cell viability csv dataset
dose response cell viability example dataset
IC50 example data csv
```

For the first version, synthetic data is strongly preferred.

---

# Required Analysis

The student should implement:

1. Load CSV with pandas.
2. Check data shape and column names.
3. Validate required columns.
4. Group by `drug_name` and `concentration_uM`.
5. Calculate:
   - mean
   - standard deviation
   - standard error
   - number of replicates
6. Create a dose-response plot.
7. Compare DrugA and DrugB visually.
8. Generate a cautious result interpretation.
9. List limitations.

---

# Suggested Python Functions

```python
def load_drug_response_data(csv_file):
    pass

def summarize_drug_response(df):
    pass

def create_dose_response_plot(summary_df):
    pass

def generate_interpretation(summary_df):
    pass
```

---

# Gradio Demo Requirements

## App Name

**BioDose AI**

## Subtitle

**AI-assisted drug response analysis for Biochemistry students**

## Interface Layout

Use `gr.Blocks`, not only `gr.Interface`.

Recommended tabs:

1. Upload Data
2. Summary Statistics
3. Dose-Response Plot
4. AI Explanation
5. Export

## Fancy UI Elements

Include:

- hero title with emoji, such as `🧪 BioDose AI`
- example data button
- result cards:
  - number of drugs
  - number of concentrations
  - total samples
  - strongest observed response
- interactive Plotly chart
- AI explanation card
- verification warning box
- download summary button

## Example Result Cards

```text
Drugs detected: 2
Concentrations tested: 5
Total samples: 30
Strongest response: DrugA at 10 uM
```

## Example AI Explanation Template

```text
In this synthetic dataset, DrugA appears to reduce cell viability more strongly than DrugB at higher concentrations. The response appears dose-dependent because the average cell viability decreases as concentration increases. However, this is only a toy dataset. Real conclusions require proper controls, sufficient biological replicates, assay validation, and statistical testing.
```

---

# Quarto Report Requirements

## Report Title

**BioDose AI: Drug Response Analysis Report**

## Suggested Sections

1. Overview
2. Biological Motivation
3. Dataset Description
4. Methods
5. Results
6. Dose-Response Visualization
7. AI-assisted Interpretation
8. Manual Verification Checklist
9. Limitations
10. Future Improvements
11. What I Learned

## Fancy Quarto Features

Use:

```yaml
format:
  html:
    theme: cosmo
    toc: true
    code-fold: true
    code-tools: true
    number-sections: true
```

Add callouts:

```markdown
::: {.callout-tip}
## Key Observation
DrugA shows a stronger reduction in cell viability at high concentration in the synthetic dataset.
:::

::: {.callout-warning}
## Verification Required
This dataset is synthetic. Real experimental conclusions require biological validation.
:::
```

---

# Recommended README Content

The README should include:

- project engagement
- screenshot of Gradio app
- screenshot of Quarto report
- sample input file
- how to run locally
- what the tool does
- what the tool does not do
- limitations
- future work

---

# Student Learning Goals

By completing this project, the student should learn:

- how to read a CSV file with pandas
- how to group data
- how to calculate basic statistics
- how to create a scientific plot
- how to use Gradio for an interactive demo
- how to write a scientific report with Quarto
- how to use AI carefully for interpretation
- how to explain limitations

---

# Vibe Coding Prompt

```text
I am a third-year Biochemistry student learning Python with AI assistance.

I want to build a project called BioDose AI. It analyzes synthetic drug response data.

The input CSV has these columns:
sample_id, drug_name, concentration_uM, replicate, cell_viability_percent

Please create beginner-friendly Python code with these files:
src/drug_analysis.py
src/plots.py
app.py

The app should use Gradio Blocks and include:
1. CSV upload
2. example data support
3. summary statistics
4. dose-response plot
5. AI-style interpretation template
6. verification warning

Please keep the code modular and explain each function in simple language.
```

---

# Success Criteria

Minimum success:

- Notebook works.
- Gradio app accepts CSV.
- Summary table is correct.
- Plot is generated.
- Interpretation is cautious.

Good success:

- App looks polished.
- Quarto report is generated.
- README has screenshots.
- Project can be shown to a friend or mentor.

Excellent success:

- App deployed on Hugging Face Spaces.
- Quarto report published on GitHub Pages.
- The student can explain the biological meaning and limitations.

---

# Visual and Interaction Enhancements

## Required Visuals

BioDose AI should include:

- interactive Plotly dose-response curve
- result cards
- dataset preview
- data quality warnings
- AI figure caption generator
- downloadable summary

## Recommended Result Cards

```text
Drugs detected
Concentrations tested
Total samples
Replicates per condition
Strongest observed response
Missing values
```

## Recommended Interactive Chart

```text
x-axis: concentration_uM
y-axis: mean cell viability percent
trace: drug_name
error bars: SEM or SD
hover: concentration, mean, SD, SEM, n
```

## Data Quality Warnings

Show warnings for:

```text
missing required columns
non-numeric concentration values
missing cell viability values
only one replicate
unexpected negative viability
viability greater than expected range
```

## Figure Caption AI Button

Add an optional button:

```text
Generate Figure Caption
```

The output should be a cautious scientific figure caption suitable for a lab report or Quarto report.

## Quarto Visual Additions

Include:

- workflow diagram: CSV → Python analysis → Plotly chart → AI explanation → verification
- dose-response screenshot
- callout warning about synthetic data


---

# Industry-Inspired Engagement Add-On

## Recommended Framing

Reframe BioDose AI as:

```text
BioDose AI: Compound Screening Challenge
```

## Mission

```text
Help a biotech lab decide which compound deserves follow-up testing.
```

## Suggested Engaging Features

Add these gradually:

```text
Scenario selector
Data quality score
Candidate ranking
Interactive Plotly chart
AI explanation level selector
Figure caption generator
Challenge questions
Lab notebook entry generator
Mini Quarto report/poster
Score my interpretation
```

## Suggested Scenario Datasets

```text
Scenario 1: Clear dose-response
Scenario 2: Weak response
Scenario 3: Noisy assay
Scenario 4: Missing replicate
Scenario 5: Possible outlier
Scenario 6: Two compounds with similar effect
Scenario 7: Strong effect but poor data quality
```

## Candidate Ranking

Example output:

```text
#1 DrugA — strongest viability reduction at high concentration
#2 DrugB — moderate reduction
```

Caution:

```text
Educational ranking based on synthetic assay data. Not a real efficacy or safety conclusion.
```

## Data Quality Score

Example output:

```text
Data Quality Score: 82 / 100
Status: Good for exploration, not enough for final conclusion
```

Possible factors:

```text
required columns
missing values
replicate count
control group
number of concentrations
outlier check
```

## Challenge Questions

Example:

```text
1. Which drug appears to reduce cell viability more at 10 uM?
2. Does the curve look dose-dependent?
3. Is the evidence strong or weak?
4. What additional experiment would you run next?
```

## Industry-Inspired but Simplified

Real-world inspiration:

```text
compound screening
assay QC
compound triage
follow-up experiment planning
scientific communication
```

Avoid early complexity:

```text
clinical claims
real drug efficacy conclusions
molecular docking
regulatory workflow
complex IC50 production modeling
```


---

# Academic Biochemistry Support Add-On

BioDose AI should support academic Biochemistry learning, not only bioinformatics skill-building.

## Academic Concepts

BioDose AI should help the student understand:

```text
dose-response relationship
cell viability assay
control vs treatment
biological replicates
standard deviation
standard error
error bars
experimental limitations
cautious scientific interpretation
```

## Academic Output Buttons

Recommended Gradio buttons:

```text
Generate Lab Report Paragraph
Generate Figure Caption
Generate Study Questions
Generate Next Experiment Suggestions
```

## Academic Challenge Questions

```text
1. What is the independent variable?
2. What is the dependent variable?
3. Why are replicates important?
4. What do the error bars represent?
5. Why should we avoid saying the drug is effective based only on this dataset?
6. What additional control would improve the experiment?
```

## Recommended Academic Output

The app should be able to generate:

```text
Results paragraph
Figure caption
Limitations
Next experiment suggestions
Study questions
```

This makes BioDose useful for both computational learning and academic Biochemistry practice.

"""Staged rubric generator V3 - Self-Documenting System.

Core insight: Force agents to create verifiable artifacts in specific shapes.
Then verification becomes trivial.

V3 improvements:
- Stage 1: SHAPE ENFORCEMENT (smoke test - must produce verifiable format)
- Stage 2: CORRECTNESS VERIFICATION (bounds checks, unit tests, consistency)
- Stage 3: QUALITY ASSESSMENT (holistic judgment)
"""

from curation.gdpeval.src.staged_rubric_schema import (
    StagedRubric,
    GDPEvalStagedRubric,
)
from openai import AsyncOpenAI
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


STAGED_RUBRIC_SYSTEM_PROMPT_V3 = """You are an expert at designing SELF-DOCUMENTING evaluation systems.

## CRITICAL: File-Based Resource System

**ALL resources are files** - No inline content, everything is stored on disk:
- Text outputs: `.md` files (markdown)
- Data outputs: `.xlsx` or `.csv` files
- Documents: `.pdf` or `.docx` files
- Images: `.png`, `.jpg` files
- Audio: `.wav`, `.mp3` files

**Code Rule Function Signature** (MUST USE THIS):
```python
def evaluate(workflow, context):
    \"\"\"
    Args:
        workflow: Workflow object
        context: ValidationContext with .files accessor
    
    Returns:
        float (score) or tuple[float, str] (score, feedback)
    \"\"\"
```

**Accessing Files in Code Rules**:
```python
# Get primary output (first output of last task)
output = context.get_primary_output()
if not output:
    return 0.0

# Check file type using Resource properties
if not output.is_spreadsheet:  # Also: .is_document, .is_text_format, .is_image
    return 0.0

# Read files using context.files helpers
df = context.files.read_excel(output.id, sheet_name='Analysis')  # Excel
text = context.files.read_pdf_text(output.id)  # PDF
text = context.files.read_docx_text(output.id)  # DOCX
text = context.files.read_text(output.id)  # Markdown/JSON

# Or get file path directly for custom processing
file_path = context.files.get_path(output.id)
df = pd.read_excel(file_path, sheet_name='Analysis')
```

**LLM Judge Rules**: GPT-4 Vision automatically receives multimodal context (PDFs as images, Excel as table images, etc.)

---

## The Philosophy: Self-Documenting Systems

**Core Insight**: Don't try to figure out if work is correct. Force the agent to PROVE it's correct by mandating verifiable artifacts.

**The 3-Stage Architecture**:

1. **Stage 1 (GATE): Shape Enforcement** - "Your output MUST be in THIS EXACT SHAPE"
   - This is the smoke test - if output isn't in verifiable format, we can't evaluate it
   - Defines the EXACT structure that makes verification trivial
   - If this fails → entire category = 0 (no point in checking quality of unverifiabl output)

2. **Stage 2 (VERIFICATION): Correctness Checks** - "Now that I can read it, is it correct?"
   - Code rules: Bounds checks, unit tests, structural validation
   - LLM rules: Consistency checks, cross-references, reasonableness
   - Both are allowed and encouraged when shape enables them!
   - **TARGET: 3-4 rules per stage for comprehensive verification**
   - **WEIGHTING RULE: Code rules should be worth ~5x LESS than LLM rules on average**
     * Example: If total stage points = 25, aim for ~4-5 points from code rules, ~20-21 points from LLM rules
     * This reflects that LLM judges handle more complex, nuanced evaluation while code does precise checks

3. **Stage 3 (QUALITY): Holistic Assessment** - "Is it good work overall?"
   - LLM judges professional presentation, strategic value, appropriateness
   - **TARGET: 3-4 rules per stage for thorough quality assessment**

---

## Stage 1: Shape Enforcement (THE CRITICAL GATE)

**Purpose**: Define EXACT output structure that enables trivial verification.

**Philosophy**: 
- The agent does 100% of the hard work (structuring output correctly)
- We do 0% of the hard work (just check structure exists)
- Without the right shape → verification is impossible → score = 0

**🚨 CRITICAL: STAGE 1 = LLM JUDGES ONLY 🚨**

**WHY LLM JUDGES FOR STAGE 1:**
- ✅ LLMs can SEE the actual rendered Excel/PDF content (via GPT-4 Vision)
- ✅ LLMs are FLEXIBLE with naming ("Sample" vs "Selected Sample" vs "Audit Sample")
- ✅ LLMs NEVER crash - they always return a score
- ✅ LLMs can check complex structure (sections, layout, presence of tables)
- ❌ Code rules are BRITTLE - require exact matches, crash easily
- ❌ Code rules can't see formatting/layout - only raw data

**RULE: NEVER use code rules in Stage 1. ONLY LLM judges.**

### For Analytical Tasks (Financial, Calculations, Data Analysis)

**Pattern**: LLM Mandates Specific Verifiable Structure (NO CODE!)

**Example - Financial NPV Analysis**:
```
Stage 1 LLM Judge: "Structured Output Format Requirement"
Weight: 1.0
Description: "Output must be Excel file with these EXACT structural requirements"

Judge Prompt:
"Check if output is an Excel file with the following structure:

**Sheet 1: 'NPV Analysis'**
Must contain these sections (section names in bold in column A):

1. **'Input Assumptions'** section (rows 1-10):
   - Table with columns: [Parameter Name | Value | Source/Justification]
   - Must include rows for: Discount Rate, Project Duration, Initial Investment
   - Example:
     | Discount Rate | 10% | Industry standard for this risk level |

2. **'Cash Flow Projections'** section (rows 12-20):
   - Table with columns: [Year | Revenue | Costs | Net Cash Flow]
   - Must have one row per year for project duration
   - Example:
     | Year | Revenue | Costs | Net Cash Flow |
     | 0    | $0      | $1000000 | -$1000000 |
     | 1    | $500000 | $200000  | $300000   |

3. **'NPV Calculation'** section (rows 22-30):
   - Must show step-by-step calculation log
   - Table with columns: [Year | Net Cash Flow | Discount Factor | Present Value]
   - Final row: NPV total

4. **'Sensitivity Analysis'** section (rows 32-40, OPTIONAL):
   - Table showing NPV at different discount rates

**Sheet 2: 'Supplier Comparison'**
   - Table comparing NPV for each supplier
   - Columns: [Supplier Name | NPV | Ranking]

**Scoring**:
- 1.0: All required sheets and sections present with correct structure
- 0.7: Missing optional section (Sensitivity Analysis) only
- 0.5: Missing one required section
- 0.0: Missing multiple sections OR wrong format (not Excel, wrong sheets)

**DO NOT** verify if calculations are correct. Only check if the STRUCTURE exists to make verification possible."
```

**Example - Tax Return Analysis**:
```
Stage 1 LLM Judge: "Structured Calculation Log Requirement"

Judge Prompt:
"Output must be Excel with:

**Sheet: 'Tax Calculations'**

1. **'Tax Liability by Country'** section:
   - Table columns: [Country | Gross Revenue | Tax Rate | Tax Withheld | Net Revenue]
   - Must have one row per country
   - All values must be visible (not hidden formulas)

2. **'Calculation Methodology'** section:
   - Text explaining:
     * Where tax rates came from
     * How withholding was calculated
     * Any assumptions made
   - Must be at least 3 sentences

3. **'Exchange Rate Log'** section:
   - Table: [Currency | USD Exchange Rate | Date | Source]
   - One row per foreign currency

4. **'Final Summary'** section:
   - Total USD revenue before tax
   - Total tax withheld
   - Net USD revenue

**Scoring**:
- 1.0: All sections present and properly structured
- 0.6: Missing 1 supporting section (Exchange Rate Log)
- 0.0: Missing core sections or not Excel format

Only check STRUCTURE, not correctness of calculations."
```

### For Document Tasks (Reports, Proposals, Guides)

**Pattern**: LLM checks format AND structural completeness (NO CODE in Stage 1!)

**Example - Professional Report**:
```
Stage 1 LLM Judge: "Document Format and Structure Requirements"
Weight: 1.0
Judge Prompt:
"Check if document is valid Word/PDF with required structure:

**Format Requirements**:
- Must be PDF or DOCX file (not plain text, not Excel)
- At least 2 pages minimum
- Professionally formatted with clear sections

**Required Sections** (check headers are visible):
1. 'Executive Summary' or 'Overview' (must be on first page)
2. 'Background' or 'Context'
3. 'Analysis' or 'Findings' (with at least 3 subsections)
4. 'Recommendations' or 'Conclusion'
5. 'Appendix' or 'Supporting Data' (tables/charts)

**Scoring** (be flexible with exact section names):
- 1.0: Valid format + all 5 sections present with clear headers
- 0.7: Valid format + 4/5 sections present
- 0.4: Valid format + 3/5 sections present
- 0.2: Valid format but only 1-2 sections
- 0.0: Wrong format (not PDF/DOCX) OR less than 2 pages

Just check PRESENCE and FORMAT, not quality of content."
```

### Key Principles for Stage 1

**CRITICAL DISTINCTION**:
- **Stage 1 LLM Judge**: Tells the agent what structure to produce (specific sheet/section names)
- **Stage 1 Code Rule** (if used): Does BASIC format validation only (file type, minimum structure)
- **Stage 2 Code Rules**: Use FLEXIBLE matching to verify the structure Stage 1 mandated

✅ **DO in Stage 1**:
- **ALWAYS use LLM judges** - they can see rendered content and are flexible
- **Use LLM judges to mandate** exact sheet/section names, table structures
- Define the contract: "You MUST include sheet 'Analysis' with sections X, Y, Z"
- Be EXTREMELY specific in LLM prompt about what agent should produce
- Be FLEXIBLE in matching: "Sheet 'Sample' OR similar name like 'Selected Sample'"
- Score based on structure completeness, not correctness
- Include examples of what good structure looks like

❌ **DON'T in Stage 1**:
- ❌ **NEVER write code rules in Stage 1** - they're brittle and crash easily!
- ❌ Check exact column names with code - LLMs handle this better
- ❌ Check if calculations are correct (Stage 2's job)
- ❌ Assess quality of content (Stage 3's job)  
- ❌ Be vague ("well-organized", "clear structure")

**Example Pattern (CORRECT)**:
```
Stage 1 LLM Judge: "Output must have Excel sheet 'NPV Analysis' with sections:
  - 'Input Assumptions' (table with columns Parameter, Value, Source)
  - 'Calculations' (step-by-step calculation log)
  - 'Results' (final metrics)"

Stage 2 Code Rule: 
  df = pd.read_excel(candidate_output, sheet_name=0)
  text = ' '.join(df.iloc[:, 0].astype(str)).lower()
  
  # Fuzzy match for sections Stage 1 mandated
  has_assumptions = 'assumption' in text or 'input' in text
  has_calculations = 'calculation' in text or 'method' in text
  has_results = 'result' in text or 'summary' in text
  
  return (has_assumptions + has_calculations + has_results) / 3.0
```

**Anti-Pattern (WRONG)**:
```
Stage 1 Code Rule:
  required_columns = ['Parameter Name', 'Value', 'Source']  # ❌ BRITTLE!
  if all(col in df.columns for col in required_columns):
    return 1.0
```

---

## Stage 2: Correctness Verification (MIXED CODE + LLM)

**Purpose**: Now that output is in verifiable shape, check if it's correct.

**Key Insight**: Because Stage 1 forced a specific shape, Stage 2 rules know exactly where to look!

### When to Use CODE Rules

Code rules are GREAT for Stage 2 when you can write deterministic checks:

#### 1. **Bounds Checks** (financial example)
```python
{
  "type": "code",
  "name": "NPV Within Plausible Bounds",
  "description": "Check if calculated NPV is within reasonable economic bounds",
  "weight": 0.3,
  "code": """


def evaluate(workflow, context) -> float:
    import pandas as pd

    try:
        # We KNOW there's a sheet 'NPV Analysis' (Stage 1 enforced it!)
        df = pd.read_excel(candidate_output, sheet_name="NPV Analysis")

        # Find NPV in the known structure
        # Look for 'NPV' in first column
        npv_row = df[
            df.iloc[:, 0].astype(str).str.contains("NPV", case=False, na=False)
        ]

        if npv_row.empty:
            return 0.0

        # Extract NPV value (should be in second column)
        npv_value = npv_row.iloc[0, 1]

        # Convert to float (handle currency symbols)
        if isinstance(npv_value, str):
            npv_value = float(npv_value.replace("$", "").replace(",", ""))

        # Plausibility bounds for business NPV
        # Typically -$10M to +$1B for normal projects
        if -10_000_000 <= npv_value <= 1_000_000_000:
            return 1.0
        else:
            return 0.0  # Implausibly large/small

    except Exception as e:
        # Print error for debugging (will be captured in evaluation feedback)
        print(f"ERROR: {type(e).__name__}: {e}")
        return 0.0


"""
}
```

#### 2. **Unit Tests** (variance example)
```python
{
  "type": "code",
  "name": "Variance Reasonableness Check",
  "description": "Variance should be within reasonable range relative to mean",
  "weight": 0.3,
  "code": """


def evaluate(workflow, context) -> float:
    import pandas as pd

    try:
        df = pd.read_excel(candidate_output, sheet_name="Analysis")

        # Extract variance and mean from known structure
        # Stage 1 enforced these sections exist!
        results_section = df[
            df.iloc[:, 0].astype(str).str.contains("Results", case=False, na=False)
        ]

        # Find variance and mean rows
        variance = None
        mean = None

        for idx in results_section.index:
            metric_name = str(df.iloc[idx, 0]).lower()
            metric_value = df.iloc[idx, 1]

            if "variance" in metric_name:
                variance = float(str(metric_value).replace("$", "").replace(",", ""))
            elif "mean" in metric_name or "average" in metric_name:
                mean = float(str(metric_value).replace("$", "").replace(",", ""))

        if variance is None or mean is None or mean == 0:
            return 0.5  # Missing data, partial credit

        # Calculate coefficient of variation
        std_dev = variance**0.5
        cv = std_dev / abs(mean)

        # Reasonable bounds for financial data
        if cv < 0.05:
            return 1.0  # Very stable, excellent
        elif cv < 0.2:
            return 0.9  # Good
        elif cv < 0.5:
            return 0.7  # Acceptable
        elif cv < 1.0:
            return 0.4  # High but plausible
        else:
            return 0.0  # Implausibly high variance

    except Exception as e:
        # Print error for debugging (will be captured in evaluation feedback)
        print(f"ERROR: {type(e).__name__}: {e}")
        return 0.0


"""
}
```

#### 3. **Structural Validation** (completeness checks)
```python
{
  "type": "code",
  "name": "All Required Calculations Present",
  "description": "Verify all required calculation steps are documented",
  "weight": 0.2,
  "code": """


def evaluate(workflow, context) -> float:
    import pandas as pd

    try:
        df = pd.read_excel(candidate_output, sheet_name="NPV Analysis")

        # Stage 1 enforced 'Cash Flow Projections' section exists
        # Check if it has entries for all years

        # Find Input Assumptions section to get project duration
        assumptions = df[
            df.iloc[:, 0]
            .astype(str)
            .str.contains("Input Assumptions", case=False, na=False)
        ]

        # Look for duration (fuzzy match)
        duration_row = df[
            df.iloc[:, 0]
            .astype(str)
            .str.lower()
            .str.contains("duration|years|period", na=False)
        ]

        if duration_row.empty:
            return 0.5  # Can't verify

        duration = int(duration_row.iloc[0, 1])

        # Find Cash Flow section
        cf_section = df[
            df.iloc[:, 0].astype(str).str.contains("Cash Flow", case=False, na=False)
        ]
        cf_start = cf_section.index[0] + 2  # Skip header

        # Count rows with year data
        year_rows = 0
        for i in range(cf_start, min(cf_start + 20, len(df))):
            if pd.notna(df.iloc[i, 0]) and str(df.iloc[i, 0]).isdigit():
                year_rows += 1

        # Check if we have duration + 1 years (including year 0)
        expected_rows = duration + 1

        if year_rows >= expected_rows:
            return 1.0
        elif year_rows >= expected_rows - 1:
            return 0.7  # Close enough
        else:
            return 0.0

    except Exception as e:
        # Print error for debugging (will be captured in evaluation feedback)
        print(f"ERROR: {type(e).__name__}: {e}")
        return 0.0


"""
}
```

#### 4. **Consistency Checks** (cross-field validation)
```python
{
  "type": "code",
  "name": "Cash Flow Consistency",
  "description": "Net cash flow should equal revenue minus costs",
  "weight": 0.2,
  "code": """


def evaluate(workflow, context) -> float:
    import pandas as pd

    try:
        df = pd.read_excel(candidate_output, sheet_name="NPV Analysis")

        # Find Cash Flow Projections table
        cf_section = df[
            df.iloc[:, 0].astype(str).str.contains("Cash Flow", case=False, na=False)
        ]
        cf_start = cf_section.index[0] + 2  # Skip section header and column headers

        errors = 0
        total_rows = 0

        # Check each row: Net CF = Revenue - Costs
        for i in range(cf_start, min(cf_start + 20, len(df))):
            if pd.notna(df.iloc[i, 0]) and str(df.iloc[i, 0]).isdigit():
                total_rows += 1

                # Columns: Year | Revenue | Costs | Net Cash Flow
                revenue = float(str(df.iloc[i, 1]).replace("$", "").replace(",", ""))
                costs = float(str(df.iloc[i, 2]).replace("$", "").replace(",", ""))
                net_cf = float(str(df.iloc[i, 3]).replace("$", "").replace(",", ""))

                expected_net_cf = revenue - costs

                # Allow 1% tolerance for rounding
                if abs(net_cf - expected_net_cf) > abs(expected_net_cf * 0.01):
                    errors += 1

        if total_rows == 0:
            return 0.0

        accuracy = 1.0 - (errors / total_rows)
        return accuracy

    except Exception as e:
        # Print error for debugging (will be captured in evaluation feedback)
        print(f"ERROR: {type(e).__name__}: {e}")
        return 0.0


"""
}
```

### When to Use LLM Rules

LLM rules are GREAT for Stage 2 when you need human judgment:

#### 1. **Cross-Referencing**
```
{
  "type": "llm_judge",
  "name": "Assumptions Match Calculations",
  "description": "Check if input assumptions are consistently used in calculations",
  "weight": 0.3,
  "judge_prompt": "Review the document structure:

1. Check the 'Input Assumptions' section - note the Discount Rate value
2. Check the 'NPV Calculation' section - verify the Discount Factor column uses this rate
3. Check for consistency across all years

**Cross-check**:
- If discount rate is 10%, Year 1 discount factor should be 1/1.10 = 0.909
- If discount rate is 15%, Year 1 discount factor should be 1/1.15 = 0.870

**DO NOT recalculate everything**. Just verify:
- Is the stated discount rate used consistently?
- Are any obvious inconsistencies present?

**Scoring**:
- 1.0: Assumptions and calculations are consistent
- 0.7: Minor inconsistencies (off by rounding)
- 0.3: Major inconsistencies
- 0.0: Completely inconsistent or can't determine"
}
```

#### 2. **Contextual Reasonableness**
```
{
  "type": "llm_judge",
  "name": "Input Parameters Are Domain-Appropriate",
  "description": "Assess if chosen parameter values are reasonable for the domain",
  "weight": 0.3,
  "judge_prompt": "Review the 'Input Assumptions' section. For each parameter, assess reasonableness:

**Discount Rate**:
- Consumer products: 8-12% typical
- Tech startups: 15-25% typical
- Government/utilities: 3-7% typical

**Project Duration**:
- Should match project type (1-3 years for software, 5-20 years for infrastructure)

**Initial Investment**:
- Should be appropriate magnitude for project type

**Revenue/Cost Projections**:
- Should follow realistic patterns (growth, seasonality, etc.)

Given the task context ({sector}, {occupation}), are the parameter choices reasonable?

**Score 0.0-1.0** based on appropriateness."
}
```

#### 3. **Methodology Assessment**
```
{
  "type": "llm_judge",
  "name": "NPV Methodology Is Sound",
  "description": "Evaluate if the NPV calculation approach is appropriate",
  "weight": 0.2,
  "judge_prompt": "Review the 'NPV Calculation' section:

1. Is the NPV formula correct conceptually?
   - Should discount each year's cash flow
   - Should sum all present values
   - Should subtract initial investment

2. Is the approach suitable for this comparison?
   - Comparing suppliers → NPV is appropriate
   - Comparing projects → NPV is appropriate
   - For risk analysis → sensitivity analysis helpful (but optional)

3. Are there any methodological red flags?
   - Wrong discount factor direction (multiplying vs dividing)
   - Missing initial investment
   - Not accounting for time value

**Score 0.0-1.0** based on methodology soundness."
}
```

### Mix Code and LLM Based on Task

**Good Stage 2 Pattern for Financial Tasks**:
```
Stage 2: "Calculation Verification" (30 points total)
TARGET: 3-4 rules minimum for comprehensive verification
WEIGHTING: Code rules ~5x less valuable than LLM rules (aim for ~15-20% code, ~80-85% LLM)

Code Rules (~5 points total = 17% - aim for 2-3 precise checks):
  - Bounds check on final NPV (weight 2.0 points)
  - Variance reasonableness check (weight 1.5 points)  
  - Data completeness check (weight 1.0 points)
  - Unit consistency validation (weight 0.5 points)

LLM Rules (~25 points total = 83% - aim for 3-4 nuanced assessments):
  - Assumptions match calculations (weight 8.0 points)
  - Input parameters domain-appropriate (weight 7.0 points)
  - Methodology is sound (weight 6.0 points)
  - Results are plausible given inputs (weight 4.0 points)
```

**Good Stage 2 Pattern for Document Tasks**:
```
Stage 2: "Content Completeness" (20 points total)
TARGET: 3-4 rules minimum for comprehensive verification
WEIGHTING: Code rules ~5x less valuable than LLM rules (aim for ~15-20% code, ~80-85% LLM)

LLM Rules (~17 points total = 85% - aim for 3-4 content assessments):
  - All required topics covered (weight 6.0 points)
  - Sufficient detail per section (weight 5.0 points)
  - Logical flow between sections (weight 4.0 points)
  - Accurate use of technical terminology (weight 2.0 points)

Code Rules (~3 points total = 15% - aim for 1-2 structural checks):
  - Word count minimums per section (weight 2.0 points)
  - Required tables/charts present (weight 1.0 points)
```

### Critical: Stage 2 Code Rules MUST Be Practical

**Because Stage 1 enforced shape, Stage 2 code can be simple**:

✅ **GOOD** (knows where to look):
```python
# We know NPV is in Sheet 'NPV Analysis', section 'Results'
df = pd.read_excel(candidate_output, sheet_name='NPV Analysis')
results = df[df.iloc[:, 0].str.contains('Results', na=False)]
npv = results[results.iloc[:, 0].str.contains('NPV', na=False)].iloc[0, 1]
```

❌ **BAD** (doesn't leverage Stage 1 shape):
```python
# Searching entire workbook for NPV... why? Stage 1 told us exactly where it is!
for sheet in workbook.sheets:
    for row in sheet.rows:
        for cell in row:
            if 'NPV' in str(cell.value):
                # ...
```

**Key Principles**:
- Stage 2 code rules TRUST that Stage 1 enforced the shape
- If shape isn't there, Stage 1 would have failed already (zero_category)
- So Stage 2 can be simple and focused

---

## Stage 3: Overall Quality Assessment

**Purpose**: Holistic judgment on professional quality and appropriateness.

**Key**: This is ALWAYS LLM-based. Focus on qualitative aspects that matter for real-world use.

### For Analytical Tasks

```
{
  "type": "llm_judge",
  "name": "Professional Presentation Quality",
  "description": "Assess overall presentation, clarity, and professionalism",
  "weight": 0.4,
  "judge_prompt": "Evaluate the overall quality of the analysis:

**Presentation**:
- Is the Excel file well-formatted (aligned columns, clear headers, appropriate number formatting)?
- Are sections clearly separated and easy to navigate?
- Is color/formatting used appropriately (not excessive)?

**Clarity**:
- Are section headers clear and descriptive?
- Is the methodology explanation understandable to non-experts?
- Are results presented in a digestible format?

**Professionalism**:
- Would this be acceptable to present to a client or senior management?
- Is attention to detail evident?
- Are there typos or sloppy errors?

**Score 0.0-1.0** based on overall professional quality."
},
{
  "type": "llm_judge",
  "name": "Strategic Insight and Value",
  "description": "Assess if analysis provides actionable strategic value",
  "weight": 0.4,
  "judge_prompt": "Evaluate the strategic value:

**Actionability**:
- Does the analysis lead to a clear recommendation?
- Is there a summary that highlights the key finding (e.g., 'Supplier A has highest NPV')?

**Insight**:
- Does sensitivity analysis (if present) highlight key risks?
- Are important caveats or assumptions called out?

**Business Value**:
- Would this analysis help a decision-maker?
- Are results contextualized appropriately?

**Score 0.0-1.0** based on strategic value."
},
{
  "type": "llm_judge",
  "name": "Completeness and Thoroughness",
  "description": "Assess if analysis is complete and thorough",
  "weight": 0.2,
  "judge_prompt": "Evaluate thoroughness:

- Are all requested analyses included?
- Are edge cases or special scenarios addressed?
- Is documentation complete (sources, assumptions, limitations)?

**Score 0.0-1.0** based on completeness."
}
```

### For Document Tasks

```
{
  "type": "llm_judge",
  "name": "Writing Quality and Clarity",
  "description": "Assess writing quality, grammar, and clarity",
  "weight": 0.4,
  "judge_prompt": "Evaluate writing quality:

**Clarity**:
- Is the writing clear and concise?
- Are complex ideas explained simply?
- Is jargon used appropriately?

**Grammar and Style**:
- Are there grammar, spelling, or punctuation errors?
- Is sentence structure varied and engaging?
- Is the tone appropriate for the audience?

**Structure**:
- Do paragraphs have clear topic sentences?
- Are transitions smooth between sections?

**Score 0.0-1.0** based on writing quality."
},
{
  "type": "llm_judge",
  "name": "Professional Formatting and Presentation",
  "description": "Assess document formatting and visual presentation",
  "weight": 0.3,
  "judge_prompt": "Evaluate formatting:

**Layout**:
- Is the document visually appealing and easy to read?
- Are headings, fonts, and spacing used consistently?
- Are tables/charts well-formatted and integrated?

**Professionalism**:
- Would this be acceptable to share externally?
- Is attention to detail evident?

**Score 0.0-1.0** based on presentation quality."
},
{
  "type": "llm_judge",
  "name": "Audience Appropriateness",
  "description": "Assess if content is appropriate for intended audience",
  "weight": 0.3,
  "judge_prompt": "Evaluate audience appropriateness:

Given this is for {sector} / {occupation}:

- Is the level of detail appropriate?
- Is technical complexity appropriate?
- Are the right topics emphasized?
- Would the intended audience find this useful?

**Score 0.0-1.0** based on appropriateness."
}
```

---

## Putting It All Together: Complete Patterns

### Pattern A: Analytical Tasks (Financial, Data Analysis, Calculations)

**When to use**: Any task involving calculations, multi-step analysis, or data processing.

**Structure**:
```
Category: "[Task Name] Quality" (40-50 points)
Rationale: "Uses self-documenting 3-stage pattern: (1) Gate enforces structured output shape enabling verification, (2) Mixed code/LLM verify correctness via bounds checks and consistency validation, (3) LLM assesses professional quality and strategic value."

Stage 1 (GATE): Shape Enforcement (10 pts, is_required=true, on_failure_action="zero_category")
  - LLM Judge (weight 1.0): Mandates specific Excel structure with sections X, Y, Z
  
Stage 2 (VERIFICATION): Correctness Checks (25 pts, is_required=false)
  TARGET: 3-4 rules minimum for comprehensive verification
  WEIGHTING: Code ~5x less than LLM (aim for ~4 pts code, ~21 pts LLM)
  
  Code Rules (~4 points total - aim for 2-3 precise checks):
    - Bounds check on key metric (2.0 pts)
    - Data consistency validation (1.5 pts)
    - Structural completeness (0.5 pts)
  
  LLM Rules (~21 points total - aim for 3-4 nuanced assessments):
    - Cross-check consistency (7.0 pts)
    - Parameter reasonableness (7.0 pts)
    - Methodology appropriateness (7.0 pts)

Stage 3 (QUALITY): Professional Assessment (15 pts, is_required=false)
  TARGET: 3-4 rules minimum for thorough quality assessment
  
  - LLM Judge (weight 0.30): Professional presentation quality
  - LLM Judge (weight 0.30): Strategic insight and value
  - LLM Judge (weight 0.25): Completeness and thoroughness
  - LLM Judge (weight 0.15): Clarity and accessibility
```

### Pattern B: Document Tasks (Reports, Proposals, Guides)

**When to use**: Any task producing Word/PDF documents without heavy calculations.

**Structure**:
```
Category: "[Document Type] Quality" (40-50 points)
Rationale: "Uses 3-stage pattern for documents: (1) Gate validates format and required sections, (2) Verification checks content completeness, (3) Quality assesses writing and professionalism."

Stage 1 (GATE): Format and Structure (10 pts, is_required=true, on_failure_action="zero_category")
  - LLM Judge (weight 1.0): Required sections present and format validated

Stage 2 (VERIFICATION): Content Completeness (15 pts, is_required=false)
  TARGET: 3-4 rules minimum for comprehensive verification
  WEIGHTING: Code ~5x less than LLM (aim for ~2-3 pts code, ~12-13 pts LLM)
  
  LLM Rules (~13 points total - aim for 3-4 content assessments):
    - All topics covered (5.0 pts)
    - Sufficient detail per section (4.0 pts)
    - Logical flow between sections (2.5 pts)
    - Technical accuracy (1.5 pts)
  
  Code Rules (~2 points total - aim for 1 structural check):
    - Word count minimums (2.0 pts)

Stage 3 (QUALITY): Professional Quality (20 pts, is_required=false)
  TARGET: 3-4 rules minimum for thorough quality assessment
  
  - LLM Judge (weight 0.30): Writing quality and clarity
  - LLM Judge (weight 0.25): Professional formatting
  - LLM Judge (weight 0.25): Audience appropriateness
  - LLM Judge (weight 0.20): Visual presentation and readability
```

### Pattern C: Mixed Tasks (Documents with Embedded Analysis)

**When to use**: Reports containing calculations, presentations with data, proposals with financial models.

**Structure**:
```
Category: "[Mixed Task] Quality" (45-50 points)
Rationale: "Hybrid pattern combining document and analytical verification: (1) Gate requires both document structure AND embedded data sections, (2) Verification checks narrative completeness and data correctness separately, (3) Quality assesses integration and overall value."

Stage 1 (GATE): Format and Data Structure (10 pts, is_required=true, on_failure_action="zero_category")
  - LLM Judge (weight 1.0): Required narrative sections, data tables, and overall format validated

Stage 2 (VERIFICATION): Content and Data Quality (20 pts, is_required=false)
  TARGET: 3-4 rules minimum for comprehensive verification
  WEIGHTING: Code ~5x less than LLM (aim for ~3-4 pts code, ~16-17 pts LLM)
  
  LLM Rules (~17 points total - aim for 3-4 nuanced assessments):
    - Narrative covers all topics (7.0 pts)
    - Data and narrative are consistent (6.0 pts)
    - Technical accuracy (4.0 pts)
  
  Code Rules (~3 points total - aim for 2 precise checks):
    - Quantitative results within bounds (2.0 pts)
    - Calculation consistency (1.0 pts)

Stage 3 (QUALITY): Integration and Polish (15 pts, is_required=false)
  TARGET: 3-4 rules minimum for thorough quality assessment
  
  - LLM Judge (weight 0.30): Narrative and data well-integrated
  - LLM Judge (weight 0.25): Professional presentation
  - LLM Judge (weight 0.25): Strategic coherence
  - LLM Judge (weight 0.20): Visual clarity and impact
```

---

## Critical Implementation Requirements

### For Code Rules

**NEW FILE-BASED API**: All resources are files with direct path access.

**Function Signature**:
```python
def evaluate(workflow: Workflow, context: ValidationContext) -> float | tuple[float, str]:
    '''
    Evaluate using ValidationContext with direct file access.
    
    Args:
        workflow: Current workflow being evaluated
        context: ValidationContext with .files accessor
        
    Returns:
        score (float) or (score, feedback) tuple
    '''
```

**Accessing Files**:
```python
# Get primary output (first output of last task)
output = context.get_primary_output()
if not output or not output.is_spreadsheet:
    return 0.0

# Read Excel file directly
df = context.files.read_excel(output.id, sheet_name='NPV Analysis')

# Or get file path for custom processing
file_path = context.files.get_path(output.id)
df = pd.read_excel(file_path, sheet_name='NPV Analysis')

# For PDFs
text = context.files.read_pdf_text(output.id)

# For DOCX
text = context.files.read_docx_text(output.id)

# For plain text/markdown
text = context.files.read_text(output.id)
```

**ALWAYS**:
1. **Use `context.get_primary_output()` to get the main output Resource**
2. **Check file type with Resource properties** - `.is_spreadsheet`, `.is_document`, `.is_text_format`
3. **Use `context.files.*` helpers** for common formats (Excel, PDF, DOCX, CSV)
4. **Use try/except** - files might be malformed, always return 0.0 on error
5. **Leverage Stage 1 shape** - you KNOW where things are, so code is simple
6. **Be flexible** - use `.str.contains()` not exact matches, handle various formats
7. **Handle data types** - cast to string before checking, remove `$` and `,` from numbers
8. **Partial credit** - when appropriate, give scores between 0.0 and 1.0

**NEVER**:
1. ❌ Use old signature `def evaluate(task_input: str, candidate_output: str)` - THIS IS BROKEN!
2. ❌ Use exact column names/letters: `df['Column A']` or `required_cols = ['Exact Name']`
3. ❌ Call magic methods: `output.extract_tabs()` - always use file path
4. ❌ Fail silently - always wrap in try/except and return 0.0 on errors
5. ❌ Overcomplicate - Stage 1 enforced shape, so Stage 2 can be direct

### For LLM Rules

**ALWAYS**:
1. **Be specific** about what to check
2. **Provide scoring guidance** (1.0 if X, 0.7 if Y, 0.0 if Z)
3. **Reference specific sections** that Stage 1 enforced
4. **Distinguish** verification (Stage 2) from quality (Stage 3)
5. **Provide context** from the task (sector, occupation, task description)

**NEVER**:
1. ❌ Ask LLM to recalculate complex math
2. ❌ Be vague: "check if output is good"
3. ❌ Forget scoring guidance - always include scale and examples
4. ❌ Ask LLM to do code's job (counting, exact matching, parsing)

---

## Your Task

Generate a `StagedRubric` for the given professional task.

**You will receive**:
- Task ID, Sector, Occupation
- Task Description (the prompt given to workers)
- Reference Materials (files/context available)

**Your output**:
1. **Analyze the task type**:
   - Is it analytical (calculations, data processing)? → Pattern A
   - Is it a document (report, guide, proposal)? → Pattern B
   - Is it mixed (document + data)? → Pattern C

2. **Design Stage 1 (GATE)**:
   - **🚨 MANDATORY: Stage 1 = LLM JUDGES ONLY - NEVER use code rules in Stage 1! 🚨**
   - LLM judges can SEE rendered content (Excel tables, PDF layout) via GPT-4 Vision
   - LLM judges mandate structure: "Output must have Excel sheet 'Analysis' with sections X, Y, Z"
   - Be EXTREMELY specific in LLM prompt: exact sheet names, section names, table structures
   - Make it a checklist the agent can follow with examples
   - Be FLEXIBLE in scoring: "Sheet name 'Sample' OR 'Selected Sample' OR 'Audit Sample'"
   - **Code rules belong in Stage 2, NOT Stage 1** (for bounds checks, calculations verification)
   - Set `is_required=True`, `on_failure_action="zero_category"`
   - **CRITICAL: min_score_to_pass MUST be ≤ max_points!**
   - For `min_score_to_pass`, use an absolute score value (e.g., if max_points=8, use 4-6 for ~50-75%)
   - **NEVER set min_score_to_pass higher than max_points (e.g., if max_points=10, min_score_to_pass must be ≤ 10)**

3. **Design Stage 2 (VERIFICATION)**:
   - **TARGET: Include 3-4 rules minimum per Stage 2 for comprehensive verification**
   - **CRITICAL WEIGHTING: Code rules should be worth ~5x LESS than LLM rules**
     * If stage has 25 points total: ~4-5 points from code rules, ~20-21 points from LLM rules
     * This creates ~15-20% code weight, ~80-85% LLM weight
     * Code rules = precision checks (bounds, counts, structure)
     * LLM rules = nuanced assessments (consistency, reasonableness, methodology)
   - For analytical tasks: aim for 2-3 code rules (~4 pts) + 3-4 LLM rules (~21 pts)
   - For document tasks: aim for 1-2 code rules (~2-3 pts) + 3-4 LLM rules (~12-17 pts)
   - All rules should leverage the shape Stage 1 enforced
   - Each rule should be focused on a specific aspect to ensure comprehensive coverage

4. **Design Stage 3 (QUALITY)**:
   - **TARGET: Include 3-4 rules minimum per Stage 3 for thorough quality assessment**
   - All LLM judges
   - Focus on professional presentation, strategic value, appropriateness, and clarity
   - Break down quality into distinct dimensions (e.g., presentation, strategic value, completeness, clarity)
   - This is the "would I present this to a client?" stage
   - Each rule should assess a different quality dimension

5. **Write executable code rules**:
   - Real Python code that opens files and processes them
   - Simple and direct (leverage Stage 1 shape!)
   - Robust (try/except, handle edge cases)
   - Flexible (fuzzy matching, type casting)

6. **Write clear LLM prompts**:
   - Specific about what to check
   - Include scoring guidance
   - Reference the enforced structure
   - Include task context (sector, occupation)

Generate the staged rubric now!
"""


async def generate_staged_rubric_v3(
    task_id: str,
    sector: str,
    occupation: str,
    prompt: str,
    reference_file_urls: list[str],
    model: str = "gpt-5",
    temperature: float = 1.0,
    seed: int | None = None,
) -> GDPEvalStagedRubric:
    """Generate a staged rubric V3 with self-documenting system approach."""

    # Format reference files summary
    if reference_file_urls is not None and len(reference_file_urls) > 0:
        ref_summary = (
            f"{len(reference_file_urls)} reference files available:\n"
            + "\n".join([f"- {url}" for url in reference_file_urls])
        )
    else:
        ref_summary = "No reference files provided."

    user_prompt = f"""Generate a STAGED evaluation rubric for this professional task:

**Sector**: {sector}
**Occupation**: {occupation}

**Task Description**:
{prompt}

**Available Reference Materials**:
{ref_summary}

**Analysis Required**:

1. **Task Type** - Which pattern fits?
   - Analytical (calculations, data analysis, financial models) → Pattern A
   - Document (reports, proposals, guides) → Pattern B
   - Mixed (documents with embedded data/analysis) → Pattern C

2. **Output Format** - What will the agent produce?
   - Excel/CSV → Can parse with pandas, write code rules for bounds checks
   - Word/PDF → Can extract text, use LLM for content checks
   - Code/scripts → Can analyze syntax, check structure

3. **Stage 1: Shape Enforcement**
   - Define the EXACT structure that makes verification trivial
   - Be extremely specific (sheet names, section names, table columns)
   - This is a GATE - if shape is wrong, entire category = 0

4. **Stage 2: Correctness Verification**
   - **IMPORTANT: Include 3-4 rules minimum for comprehensive verification**
   - What can I check with code? (bounds, unit tests, consistency)
   - What needs LLM judgment? (cross-references, reasonableness, methodology)
   - Mix appropriately based on task type
   - Break down verification into distinct, focused checks

5. **Stage 3: Quality Assessment**
   - **IMPORTANT: Include 3-4 rules minimum for thorough quality assessment**
   - Professional presentation quality
   - Strategic value and insight
   - Audience appropriateness
   - Clarity and accessibility
   - Break down quality into distinct dimensions

**CRITICAL REMINDERS**:

1. **Use new API for ALL code rules**: `def evaluate(workflow, context)` - Access files via `context.get_primary_output()` and `context.files.*`
2. **Check Resource types**: Use `.is_spreadsheet`, `.is_document`, `.is_text_format` properties
3. **Stage 1 = LLM JUDGES ONLY** - NEVER use code in Stage 1! LLMs see rendered content, are flexible, don't crash
4. **Stage 1 must have at least 1 LLM judge** - It checks format, structure, and presence of required elements
5. **Stage 2 code rules = ENCOURAGED** - Use correct API, flexible matching, try/except, bounds checks
6. **Leverage the shape** - Stage 2 can be simple because Stage 1 enforced structure via LLM
7. **Be practical** - flexible matching (substring, .lower()), handle edge cases (try/except)
8. **LLM judges get multimodal context** - PDFs/Excel automatically rendered as images for GPT-4 Vision
9. **OLD API = FORBIDDEN**: NEVER use `def evaluate(task_input: str, candidate_output: str)` - this is broken!
10. **NO .extract_* METHODS**: These don't exist. Use pandas: `pd.ExcelFile(file_path).sheet_names`

Generate the staged rubric following the V3 self-documenting system approach!"""

    try:
        completion = await client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": STAGED_RUBRIC_SYSTEM_PROMPT_V3},
                {"role": "user", "content": user_prompt},
            ],
            response_format=StagedRubric,
            temperature=temperature,
            seed=seed,
        )

        staged_rubric = completion.choices[0].message.parsed

        if staged_rubric is None:
            raise ValueError("Failed to parse staged rubric from response")

        # Validate
        staged_rubric.validate_stages()

        # Wrap with task_id
        result = GDPEvalStagedRubric(task_id=task_id, rubric=staged_rubric)

        logger.info(
            f"[V3] Generated staged rubric for {task_id}: "
            f"{staged_rubric.category_name} with {len(staged_rubric.stages)} stages, "
            f"max score: {staged_rubric.max_total_score}"
        )

        return result

    except Exception as e:
        logger.error(f"Error generating V3 staged rubric for {task_id}: {e}")
        raise

"""Test all code-based evaluation rules from the generated rubric."""

import asyncio
import json
import sys
import tempfile
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from manager_agent_gym.core.evaluation.engine.code_rule_executor import CodeRuleExecutor
from manager_agent_gym.schemas.domain.resource import Resource


async def test_rubric_code_rules():
    """Test all code rules from the rubric generation."""
    
    # Load the pre-execution JSON
    pre_exec_path = Path("simulation_outputs/run_20251023_113758/workflow_outputs/pre_execution_20251023_113758.json")
    
    if not pre_exec_path.exists():
        print(f"❌ Could not find pre-execution JSON at {pre_exec_path}")
        return False
    
    with open(pre_exec_path) as f:
        pre_exec_data = json.load(f)
    
    # Extract the generated rubric rules
    rubric = pre_exec_data[0]["generated_rubrics"][0]
    code_rules = [r for r in rubric["rules"] if r["type"] == "code"]
    
    print("=" * 80)
    print("Testing Generated Code Evaluation Rules")
    print("=" * 80)
    print(f"\nFound {len(code_rules)} code-based rules to test:")
    for i, rule in enumerate(code_rules, 1):
        print(f"  {i}. {rule['name']} (weight: {rule['weight']})")
    
    # Create mock resources similar to what the workers generated
    # Based on the output from the previous run
    temp_dir = Path(tempfile.mkdtemp(prefix="rubric_test_"))
    
    try:
        # Create mock Excel file (Analysis + Summary sheets)
        excel_path = temp_dir / "churn_predictions.xlsx"
        import pandas as pd
        import numpy as np
        
        # Analysis sheet
        analysis_df = pd.DataFrame({
            'customer_id': [f'C{i:04d}' for i in range(1, 11)],
            'risk_level': ['High', 'High', 'High', 'Medium', 'Medium', 'Medium', 'Low', 'Low', 'Low', 'Low'],
            'risk_score': [85, 78, 72, 55, 48, 42, 28, 22, 15, 8],
            'churn_probability': [0.85, 0.78, 0.72, 0.55, 0.48, 0.42, 0.28, 0.22, 0.15, 0.08],
            'top_factors': [
                'Low tenure; High tickets; Low usage',
                'Low usage; High tickets',
                'Low tenure; Low spend',
                'Moderate risk profile',
                'Low spend',
                'Moderate risk profile',
                'Moderate risk profile',
                'Moderate risk profile',
                'Moderate risk profile',
                'Moderate risk profile',
            ],
            'tenure_months': [3, 6, 5, 12, 18, 15, 24, 30, 36, 48],
            'monthly_spend': [25, 35, 30, 60, 55, 65, 80, 90, 95, 100],
            'support_tickets_30d': [8, 6, 5, 3, 2, 1, 1, 0, 0, 0],
            'usage_score': [25, 30, 35, 60, 65, 70, 80, 85, 90, 95],
        })
        
        # Summary sheet with KPIs
        summary_data = {
            'KPI': [
                'PR-AUC',
                'ROC-AUC',
                'Brier',
                'ECE',
                'High-Risk Precision',
                'High-Risk Recall',
                'High-Risk F1',
                'Recall@10%',
                'Recall@20%',
                '',
                'Risk Distribution',
                'Band',
                'High',
                'Medium',
                'Low',
            ],
            'Value': [
                0.41,
                0.79,
                0.16,
                0.03,
                0.52,
                0.60,
                0.56,
                0.45,
                0.68,
                '',
                '',
                'Count',
                3,
                3,
                4,
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        
        # Write Excel file
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            analysis_df.to_excel(writer, sheet_name='Analysis', index=False)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Create mock Markdown file
        md_path = temp_dir / "churn_methodology.md"
        md_content = """# Customer Churn Risk Analysis

## Methodology

Our risk scoring system uses weighted factors to predict churn:
- **Tenure**: 35% weight - customers with short tenure are higher risk
- **Spend**: 25% weight - low monthly spend indicates risk  
- **Support tickets**: 25% weight - high ticket volume correlates with churn
- **Usage**: 15% weight - declining usage is a strong signal

Risk score ranges from 0-100, with thresholds:
- Low risk: 0-34
- Medium risk: 35-64
- High risk: 65-100

## Risk Distribution

The model classified 30% of customers as High risk, 30% as Medium, and 40% as Low.

## Key Findings

High-risk customers show patterns of low tenure, high support tickets, and declining usage.
The model achieved strong calibration with Brier score of 0.16 and ECE of 0.03.

## Metrics

- PR-AUC: 0.41 (target ≥0.35) ✓
- ROC-AUC: 0.79 (target ≥0.75) ✓
- High-risk precision: 0.52, recall: 0.60
- Recall@top-10%: 0.45, recall@top-20%: 0.68

## Recommendations

1. Priority outreach to High-risk segment (30% of base)
2. Proactive retention offers for customers showing usage decline
3. Enhanced support for high-ticket customers

## Deliverables

- churn_predictions.xlsx with Analysis and Summary sheets
- This methodology report
"""
        md_path.write_text(md_content)
        
        # Create Resource objects
        resources = [
            Resource(
                name="Churn Predictions Workbook",
                description="Excel workbook with predictions and summary",
                file_path=str(excel_path),
                mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                size_bytes=excel_path.stat().st_size,
            ),
            Resource(
                name="Churn Methodology Report",
                description="Markdown report explaining methodology",
                file_path=str(md_path),
                mime_type="text/markdown",
                size_bytes=md_path.stat().st_size,
            ),
        ]
        
        print(f"\n📄 Created {len(resources)} mock resources:")
        for r in resources:
            print(f"   - {r.name} ({r.mime_type})")
        
        # Test each code rule
        executor = CodeRuleExecutor()
        results = []
        
        print("\n" + "=" * 80)
        print("Running Code Evaluation Rules")
        print("=" * 80)
        
        for i, rule in enumerate(code_rules, 1):
            print(f"\n[{i}/{len(code_rules)}] {rule['name']}")
            print(f"    Weight: {rule['weight']}")
            print(f"    Description: {rule['description'][:100]}...")
            
            try:
                score, feedback = await executor.execute(rule['code'], resources)
                
                status = "✅ PASS" if score > 0 else "⚠️  ZERO"
                print(f"    Result: {status}")
                print(f"    Score: {score:.3f}")
                if feedback:
                    print(f"    Feedback: {feedback[:200]}")
                
                results.append({
                    'rule': rule['name'],
                    'weight': rule['weight'],
                    'score': score,
                    'feedback': feedback,
                    'passed': score > 0,
                    'error': None
                })
                
            except Exception as e:
                print(f"    Result: ❌ ERROR")
                print(f"    Error: {str(e)[:200]}")
                results.append({
                    'rule': rule['name'],
                    'weight': rule['weight'],
                    'score': 0.0,
                    'feedback': None,
                    'passed': False,
                    'error': str(e)
                })
        
        # Summary
        print("\n" + "=" * 80)
        print("Test Summary")
        print("=" * 80)
        
        passed = [r for r in results if r['passed']]
        failed = [r for r in results if not r['passed']]
        errors = [r for r in results if r['error']]
        
        print(f"\n✅ Passed: {len(passed)}/{len(results)}")
        print(f"❌ Failed: {len(failed)}/{len(results)}")
        print(f"🔥 Errors: {len(errors)}/{len(results)}")
        
        if passed:
            print("\n✅ Passing Rules:")
            for r in passed:
                print(f"   - {r['rule']} (score: {r['score']:.3f}, weight: {r['weight']})")
        
        if failed:
            print("\n❌ Failed Rules:")
            for r in failed:
                if r['error']:
                    print(f"   - {r['rule']} (ERROR: {r['error'][:100]}...)")
                else:
                    print(f"   - {r['rule']} (score: {r['score']:.3f})")
        
        # Weighted total
        weighted_score = sum(r['score'] * r['weight'] for r in results)
        total_weight = sum(r['weight'] for r in results)
        
        print(f"\n📊 Weighted Score: {weighted_score:.3f} / {total_weight:.3f} ({weighted_score/total_weight*100:.1f}%)")
        
        return all(r['passed'] or r['score'] > 0 for r in results)
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


async def main():
    success = await test_rubric_code_rules()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


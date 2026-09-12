#!/usr/bin/env python3
"""
Calculate agreement between LLM judge and human reviewer.

This script compares the evaluations from both reviewers and produces
agreement metrics including Cohen's Kappa, percentage agreement, and
detailed dimension-level analysis.
"""

import json
import os
import sys
import argparse
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

LLM_JUDGE_RESULTS = "data/evaluation/llm_judge_results.jsonl"
HUMAN_REVIEW_RESULTS = "data/evaluation/human_review_results.jsonl"
OUTPUT_JSON = "data/evaluation/llm_human_agreement.json"
OUTPUT_REPORT = "data/evaluation/llm_human_agreement_report.md"


def load_jsonl(path):
    """Load results from a JSONL file."""
    if not os.path.exists(path):
        return []
    results = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            results.append(json.loads(line))
    return results


def calculate_cohens_kappa(observations1, observations2):
    """
    Calculate Cohen's Kappa for two sets of categorical observations.

    Args:
        observations1: List of category labels from reviewer 1
        observations2: List of category labels from reviewer 2

    Returns:
        Kappa score (float between -1 and 1)
    """
    if len(observations1) != len(observations2):
        raise ValueError("Observation lists must be same length")

    n = len(observations1)
    if n == 0:
        return 0.0

    # Count agreements
    agreements = sum(1 for o1, o2 in zip(observations1, observations2) if o1 == o2)
    po = agreements / n  # Observed agreement

    # Calculate expected agreement (pe)
    counter1 = Counter(observations1)
    counter2 = Counter(observations2)

    total_items = sum(counter1.values())

    pe = 0.0
    for category in set(observations1) | set(observations2):
        p1 = counter1.get(category, 0) / total_items
        p2 = counter2.get(category, 0) / total_items
        pe += p1 * p2

    # Handle edge case where pe = 1
    if pe == 1:
        return 1.0 if po == 1 else 0.0

    kappa = (po - pe) / (1 - pe)
    return kappa


def calculate_agreement_metrics(llm_results, human_results):
    """Calculate agreement metrics between LLM judge and human."""
    # Index by example_id
    llm_by_id = {r['example_id']: r for r in llm_results if 'error' not in r}
    human_by_id = {r['example_id']: r for r in human_results if r.get('decision') != 'SKIPPED'}

    # Find common examples
    common_ids = set(llm_by_id.keys()) & set(human_by_id.keys())

    if not common_ids:
        return {
            'error': 'No common examples between LLM and human results',
            'llm_count': len(llm_by_id),
            'human_count': len(human_by_id)
        }

    # Extract decisions and scores
    llm_decisions = [llm_by_id[id]['decision'] for id in common_ids]
    human_decisions = [human_by_id[id]['decision'] for id in common_ids]

    # Calculate decision agreement
    decision_agreements = sum(1 for ld, hd in zip(llm_decisions, human_decisions) if ld == hd)
    decision_agreement_rate = decision_agreements / len(common_ids) if common_ids else 0

    # Calculate Cohen's Kappa for decisions
    kappa = calculate_cohens_kappa(llm_decisions, human_decisions)

    # Dimension-level analysis
    dimensions = ['factual_accuracy', 'policy_alignment', 'empathy_tone', 'completeness', 'coherence']
    dimension_agreements = {}
    dimension_diffs = {}

    for dim in dimensions:
        llm_scores = [llm_by_id[id].get(dim, 0) for id in common_ids]
        human_scores = [human_by_id[id].get(dim, 0) for id in common_ids]

        # Agreement (exact match)
        agreements = sum(1 for ls, hs in zip(llm_scores, human_scores) if ls == hs)
        dim_agreement = agreements / len(common_ids) if common_ids else 0
        dimension_agreements[dim] = round(dim_agreement, 3)

        # Average absolute difference
        diffs = [abs(ls - hs) for ls, hs in zip(llm_scores, human_scores)]
        avg_diff = sum(diffs) / len(diffs) if diffs else 0
        dimension_diffs[dim] = round(avg_diff, 2)

    # Average score correlation
    llm_avg_scores = [llm_by_id[id].get('overall_score', 0) for id in common_ids]
    human_avg_scores = [human_by_id[id].get('average_score', 0) for id in common_ids]

    # Calculate correlation (simple Pearson-like correlation)
    n = len(llm_avg_scores)
    if n > 0:
        mean_llm = sum(llm_avg_scores) / n
        mean_human = sum(human_avg_scores) / n

        numerator = sum((llm_avg_scores[i] - mean_llm) * (human_avg_scores[i] - mean_human) for i in range(n))
        denom_llm = sum((x - mean_llm) ** 2 for x in llm_avg_scores) ** 0.5
        denom_human = sum((x - mean_human) ** 2 for x in human_avg_scores) ** 0.5

        if denom_llm > 0 and denom_human > 0:
            correlation = numerator / (denom_llm * denom_human)
        else:
            correlation = 0.0
    else:
        correlation = 0.0

    # Confusion matrix for decisions
    confusion = {
        'llm_accept_human_accept': 0,
        'llm_accept_human_revise': 0,
        'llm_revise_human_accept': 0,
        'llm_revise_human_revise': 0
    }

    for id in common_ids:
        ld = llm_by_id[id]['decision']
        hd = human_by_id[id]['decision']
        key = f'llm_{ld.lower()}_human_{hd.lower()}'
        if key in confusion:
            confusion[key] += 1

    return {
        'common_examples': len(common_ids),
        'llm_count': len(llm_by_id),
        'human_count': len(human_by_id),
        'decision_agreement_rate': round(decision_agreement_rate, 3),
        'cohens_kappa': round(kappa, 3),
        'dimension_agreements': dimension_agreements,
        'dimension_avg_diff': dimension_diffs,
        'score_correlation': round(correlation, 3),
        'confusion_matrix': confusion,
        'llm_decisions': dict(Counter(llm_decisions)),
        'human_decisions': dict(Counter(human_decisions))
    }


def generate_report(metrics, output_path):
    """Generate a markdown report from agreement metrics."""
    report = """# LLM-as-Judge vs Human Agreement Report

## Executive Summary

| Metric | Value |
|--------|-------|
| Common Examples Evaluated | {common} |
| Decision Agreement Rate | {agree_rate:.1%} |
| Cohen's Kappa | {kappa:.3f} |
| Score Correlation | {corr:.3f} |

**Interpretation of Cohen's Kappa:**
- κ < 0: No agreement
- 0 ≤ κ < 0.20: Slight agreement
- 0.20 ≤ κ < 0.40: Fair agreement
- 0.40 ≤ κ < 0.60: Moderate agreement
- 0.60 ≤ κ < 0.80: Substantial agreement
- 0.80 ≤ κ ≤ 1.00: Almost perfect agreement

---

## 1. Decision Agreement Analysis

### Decision Distribution

| Reviewer | ACCEPT | REVISE |
|----------|--------|--------|
| LLM Judge | {llm_accept} | {llm_revise} |
| Human | {human_accept} | {human_revise} |

### Confusion Matrix

|  | Human ACCEPT | Human REVISE |
|--|--------------|--------------|
| **LLM ACCEPT** | {llm_accept_human_accept} | {llm_accept_human_revise} |
| **LLM REVISE** | {llm_revise_human_accept} | {llm_revise_human_revise} |

---

## 2. Dimension-Level Analysis

### Agreement Rate by Dimension

| Dimension | Agreement Rate | Avg Score Difference |
|-----------|---------------|---------------------|
| Factual Accuracy | {fact_agree:.1%} | {fact_diff:.2f} |
| Policy Alignment | {policy_agree:.1%} | {policy_diff:.2f} |
| Empathy & Tone | {empathy_agree:.1%} | {empathy_diff:.2f} |
| Completeness | {complete_agree:.1%} | {complete_diff:.2f} |
| Coherence | {coherence_agree:.1%} | {coherence_diff:.2f} |

### Interpretation

- **Highest Agreement**: {highest_dim} ({highest_agree:.1%})
- **Lowest Agreement**: {lowest_dim} ({lowest_agree:.1%})
- **Most Consistent Scores**: {most_consistent_dim} (diff={most_consistent_diff:.2f})
- **Least Consistent Scores**: {least_consistent_dim} (diff={least_consistent_diff:.2f})

---

## 3. Agreement Strength Interpretation

Based on Cohen's Kappa of **{kappa:.3f}**, the agreement between the LLM judge
and human reviewer is: **{strength}**.

This suggests that the LLM judge **{interpretation}**.

---

## 4. Recommendations

{recommendations}

---

## 5. Files

- LLM Judge Results: `data/evaluation/llm_judge_results.jsonl`
- Human Review Results: `data/evaluation/human_review_results.jsonl`
- Agreement Metrics: `data/evaluation/llm_human_agreement.json`

---

*Report generated: {timestamp}*
*Note: Results based on {common} examples with both LLM and human evaluations.*
""".format(
        common=metrics.get('common_examples', 0),
        agree_rate=metrics.get('decision_agreement_rate', 0),
        kappa=metrics.get('cohens_kappa', 0),
        corr=metrics.get('score_correlation', 0),
        llm_accept=metrics.get('llm_decisions', {}).get('ACCEPT', 0),
        llm_revise=metrics.get('llm_decisions', {}).get('REVISE', 0),
        human_accept=metrics.get('human_decisions', {}).get('ACCEPT', 0),
        human_revise=metrics.get('human_decisions', {}).get('REVISE', 0),
        llm_accept_human_accept=metrics.get('confusion_matrix', {}).get('llm_accept_human_accept', 0),
        llm_accept_human_revise=metrics.get('confusion_matrix', {}).get('llm_accept_human_revise', 0),
        llm_revise_human_accept=metrics.get('confusion_matrix', {}).get('llm_revise_human_accept', 0),
        llm_revise_human_revise=metrics.get('confusion_matrix', {}).get('llm_revise_human_revise', 0),
        fact_agree=metrics.get('dimension_agreements', {}).get('factual_accuracy', 0),
        fact_diff=metrics.get('dimension_avg_diff', {}).get('factual_accuracy', 0),
        policy_agree=metrics.get('dimension_agreements', {}).get('policy_alignment', 0),
        policy_diff=metrics.get('dimension_avg_diff', {}).get('policy_alignment', 0),
        empathy_agree=metrics.get('dimension_agreements', {}).get('empathy_tone', 0),
        empathy_diff=metrics.get('dimension_avg_diff', {}).get('empathy_tone', 0),
        complete_agree=metrics.get('dimension_agreements', {}).get('completeness', 0),
        complete_diff=metrics.get('dimension_avg_diff', {}).get('completeness', 0),
        coherence_agree=metrics.get('dimension_agreements', {}).get('coherence', 0),
        coherence_diff=metrics.get('dimension_avg_diff', {}).get('coherence', 0),
        highest_dim=max(metrics.get('dimension_agreements', {}).items(), key=lambda x: x[1])[0] if metrics.get('dimension_agreements') else 'N/A',
        highest_agree=max(metrics.get('dimension_agreements', {}).values()) if metrics.get('dimension_agreements') else 0,
        lowest_dim=min(metrics.get('dimension_agreements', {}).items(), key=lambda x: x[1])[0] if metrics.get('dimension_agreements') else 'N/A',
        lowest_agree=min(metrics.get('dimension_agreements', {}).values()) if metrics.get('dimension_agreements') else 0,
        most_consistent_dim=min(metrics.get('dimension_avg_diff', {}).items(), key=lambda x: x[1])[0] if metrics.get('dimension_avg_diff') else 'N/A',
        most_consistent_diff=min(metrics.get('dimension_avg_diff', {}).values()) if metrics.get('dimension_avg_diff') else 0,
        least_consistent_dim=max(metrics.get('dimension_avg_diff', {}).items(), key=lambda x: x[1])[0] if metrics.get('dimension_avg_diff') else 'N/A',
        least_consistent_diff=max(metrics.get('dimension_avg_diff', {}).values()) if metrics.get('dimension_avg_diff') else 0,
        strength=get_kappa_strength(metrics.get('cohens_kappa', 0)),
        interpretation=get_kappa_interpretation(metrics.get('cohens_kappa', 0)),
        recommendations=get_recommendations(metrics),
        timestamp=__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    return report


def get_kappa_strength(kappa):
    """Get strength label for kappa value."""
    if kappa < 0:
        return "No agreement"
    elif kappa < 0.20:
        return "Slight agreement"
    elif kappa < 0.40:
        return "Fair agreement"
    elif kappa < 0.60:
        return "Moderate agreement"
    elif kappa < 0.80:
        return "Substantial agreement"
    else:
        return "Almost perfect agreement"


def get_kappa_interpretation(kappa):
    """Get interpretation text for kappa value."""
    if kappa < 0:
        return "performs worse than random chance"
    elif kappa < 0.40:
        return "agrees with humans at a below-expected rate"
    elif kappa < 0.60:
        return "provides moderately reliable evaluations"
    elif kappa < 0.80:
        return "provides substantially reliable evaluations"
    else:
        return "provides highly reliable evaluations that closely match human judgment"


def get_recommendations(metrics):
    """Generate recommendations based on metrics."""
    recommendations = []

    kappa = metrics.get('cohens_kappa', 0)
    if kappa < 0.40:
        recommendations.append("1. **Improve LLM judge prompt**: The current rubric may need refinement to align better with human expectations.")
        recommendations.append("2. **Add dimension-specific guidance**: Provide more examples of what constitutes high/low scores for each dimension.")

    if kappa < 0.60:
        recommendations.append("3. **Consider ensemble approach**: Combine LLM judge with rule-based checks for critical dimensions like policy alignment.")

    dim_agreements = metrics.get('dimension_agreements', {})
    lowest_dim = min(dim_agreements.items(), key=lambda x: x[1])[0] if dim_agreements else None
    if lowest_dim and dim_agreements.get(lowest_dim, 0) < 0.5:
        recommendations.append(f"4. **Focus on {lowest_dim}**: This dimension shows the weakest agreement and may need rubric clarification.")

    if not recommendations:
        recommendations.append("1. **Continue monitoring**: Current agreement levels are acceptable. Continue periodic validation.")

    return "\n".join(recommendations)


def main():
    parser = argparse.ArgumentParser(description='Calculate LLM-human agreement metrics')
    parser.add_argument('--llm', default=LLM_JUDGE_RESULTS, help='LLM judge results JSONL')
    parser.add_argument('--human', default=HUMAN_REVIEW_RESULTS, help='Human review results JSONL')
    parser.add_argument('--output-json', default=OUTPUT_JSON, help='Output JSON file')
    parser.add_argument('--output-report', default=OUTPUT_REPORT, help='Output markdown report')
    args = parser.parse_args()

    print("Loading results...")
    llm_results = load_jsonl(args.llm)
    human_results = load_jsonl(args.human)

    print(f"LLM results: {len(llm_results)} examples")
    print(f"Human results: {len(human_results)} examples")

    print("\nCalculating agreement metrics...")
    metrics = calculate_agreement_metrics(llm_results, human_results)

    if 'error' in metrics:
        print(f"\nError: {metrics['error']}")
        print(f"LLM count: {metrics.get('llm_count', 0)}")
        print(f"Human count: {metrics.get('human_count', 0)}")
        return

    # Save JSON metrics
    with open(args.output_json, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    print(f"\nMetrics saved to: {args.output_json}")

    # Generate and save report
    report = generate_report(metrics, args.output_report)
    print(f"Report saved to: {args.output_report}")

    # Print summary
    print("\n" + "=" * 60)
    print("AGREEMENT SUMMARY")
    print("=" * 60)
    print(f"Common examples: {metrics['common_examples']}")
    print(f"Decision agreement: {metrics['decision_agreement_rate']:.1%}")
    print(f"Cohen's Kappa: {metrics['cohens_kappa']:.3f} ({get_kappa_strength(metrics['cohens_kappa'])})")
    print(f"Score correlation: {metrics['score_correlation']:.3f}")


if __name__ == '__main__':
    main()
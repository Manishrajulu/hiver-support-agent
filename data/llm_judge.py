#!/usr/bin/env python3
"""
LLM-as-Judge Evaluation for Reply Quality

This module implements rubric-based reply quality evaluation using Groq LLM.
It also supports human-vs-LLM agreement measurement.

Usage:
    python llm_judge.py                    # Evaluate all AUTO_HANDLE replies
    python llm_judge.py --sample 30        # Sample 30 for human review
    python llm_judge.py --human-review     # Run human review subset
"""

import json
import os
import sys
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables from project root .env file
_dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(_dotenv_path)

# =============================================================================
# Rubric Definition
# =============================================================================

RUBRIC = """
## Reply Quality Rubric (0-5 scale per dimension)

### 1. Factual Accuracy (0-5)
- 5: All facts from evidence, no invented details
- 4: Minor omission, mostly accurate
- 3: Some inaccurate details or significant omissions
- 2: Many inaccuracies or fabricated facts
- 1: Mostly fabricated
- 0: Completely wrong or harmful

### 2. Policy Alignment (0-5)
- 5: Perfectly aligned with Amazon policies in evidence
- 4: Minor deviation, no significant policy violation
- 3: Some policy misalignment
- 2: Clear policy violation
- 1: Significant policy violation
- 0: Completely inappropriate response

### 3. Empathy & Tone (0-5)
- 5: Warm, empathetic, professional throughout
- 4: Generally empathetic with minor issues
- 3: Neutral or inconsistent tone
- 2: Lacks empathy or unprofessional
- 1: Cold, dismissive, or inappropriate tone
- 0: Hostile or offensive

### 4. Completeness (0-5)
- 5: Fully addresses customer issue
- 4: Addresses most issues, minor gaps
- 3: Partial response, significant gaps
- 2: Addresses few aspects
- 1: Misses most of the issue
- 0: Completely irrelevant response

### 5. Coherence (0-5)
- 5: Clear, logical flow, well-structured
- 4: Generally clear with minor issues
- 3: Some confusion or unclear parts
- 2: Frequently confusing
- 1: Mostly incoherent
- 0: No logical structure

## Overall Score
Average of 5 dimensions, rounded to nearest integer:
- 5: Excellent
- 4: Good
- 3: Adequate
- 2: Poor
- 1: Very Poor
- 0: Unacceptable

## Decision Categories
- ACCEPT: Overall score >= 3
- REVISE: Overall score < 3
"""

JUDGE_PROMPT = """You are an expert Amazon customer service quality evaluator.
Evaluate the following generated reply against the customer's issue and evidence.

## Customer Issue
{customer_text}

## Detected Intent
{intent}

## Evidence (from knowledge base)
{evidence_text}

## Generated Reply to Evaluate
{reply}

## Your Task
Evaluate the reply using the rubric below and return your evaluation.

{rubric}

## Output Format
Return a JSON object with:
{{
  "factual_accuracy": <score 0-5>,
  "policy_alignment": <score 0-5>,
  "empathy_tone": <score 0-5>,
  "completeness": <score 0-5>,
  "coherence": <score 0-5>,
  "overall_score": <average of 5 dimensions>,
  "decision": "ACCEPT|REVISE",
  "reasoning": "<brief explanation of scores>"
}}
"""


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class EvaluationResult:
    """Result of LLM-as-judge evaluation."""
    conversation_id: str
    intent: str
    reply: str
    factual_accuracy: int
    policy_alignment: int
    empathy_tone: int
    completeness: int
    coherence: int
    overall_score: float
    decision: str
    reasoning: str
    judge_model: str


# =============================================================================
# Evaluation Function
# =============================================================================

def load_api_key():
    """Load Groq API key from environment variable."""
    return os.getenv("GROQ_API_KEY")


def format_evidence(evidences):
    """Format evidence list for prompt."""
    if not evidences:
        return "No evidence retrieved."
    result = ""
    for i, e in enumerate(evidences[:5], 1):
        result += f"\n[{i}] Intent: {e.get('intent', 'N/A')}, Similarity: {e.get('similarity_score', 0):.2f}\n"
        result += f"    Customer: {e.get('customer_text', '')[:200]}\n"
    return result


def evaluate_reply(customer_text, intent, reply, evidence, groq_client, model="qwen/qwen3.8-27b"):
    """
    Evaluate a single reply using LLM-as-judge.

    Args:
        customer_text: Original customer message
        intent: Detected intent
        reply: Generated reply to evaluate
        evidence: List of evidence dicts
        groq_client: Groq client instance
        model: Model to use for evaluation

    Returns:
        EvaluationResult
    """
    if not groq_client:
        raise ValueError("Groq client not available")

    evidence_text = format_evidence(evidence)

    prompt = JUDGE_PROMPT.format(
        customer_text=customer_text,
        intent=intent,
        evidence_text=evidence_text,
        reply=reply,
        rubric=RUBRIC
    )

    response = groq_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert Amazon customer service quality evaluator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=1000
    )

    content = response.choices[0].message.content

    # Parse JSON from response
    try:
        # Try to extract JSON
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            result = json.loads(json_str)
        else:
            raise ValueError("No JSON found in response")

        return EvaluationResult(
            conversation_id="",
            intent=intent,
            reply=reply,
            factual_accuracy=result['factual_accuracy'],
            policy_alignment=result['policy_alignment'],
            empathy_tone=result['empathy_tone'],
            completeness=result['completeness'],
            coherence=result['coherence'],
            overall_score=result['overall_score'],
            decision=result['decision'],
            reasoning=result['reasoning'],
            judge_model=model
        )
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Failed to parse LLM response: {e}\n{content[:500]}")


def run_llm_judge(input_path, output_path, sample_size=None):
    """
    Run LLM-as-judge on pipeline outputs.

    Args:
        input_path: Path to JSONL with pipeline predictions
        output_path: Path to save evaluation results
        sample_size: If set, randomly sample this many examples
    """
    if not GROQ_AVAILABLE:
        print("ERROR: Groq library not available")
        return

    api_key = load_api_key()
    if not api_key:
        print("ERROR: Groq API key not found")
        return

    client = Groq(api_key=api_key)

    # Load predictions
    with open(input_path, 'r', encoding='utf-8') as f:
        predictions = [json.loads(line) for line in f]

    # Filter to AUTO_HANDLE with replies
    auto_handle = [p for p in predictions if p.get('decision') == 'AUTO_HANDLE' and p.get('draft_reply')]

    if sample_size:
        import random
        auto_handle = random.sample(auto_handle, min(sample_size, len(auto_handle)))

    print(f"Evaluating {len(auto_handle)} AUTO_HANDLE replies...")

    results = []
    for i, pred in enumerate(auto_handle):
        print(f"[{i+1}/{len(auto_handle)}] Evaluating {pred.get('conversation_id', 'unknown')}...")

        try:
            result = evaluate_reply(
                customer_text=pred.get('message', ''),
                intent=pred.get('intent', ''),
                reply=pred.get('draft_reply', ''),
                evidence=pred.get('evidence', []),
                groq_client=client
            )
            result.conversation_id = pred.get('conversation_id', '')
            results.append(result)
            print(f"  Score: {result.overall_score:.2f} ({result.decision})")
        except Exception as e:
            print(f"  ERROR: {e}")

    # Save results
    output = []
    for r in results:
        output.append({
            'conversation_id': r.conversation_id,
            'intent': r.intent,
            'factual_accuracy': r.factual_accuracy,
            'policy_alignment': r.policy_alignment,
            'empathy_tone': r.empathy_tone,
            'completeness': r.completeness,
            'coherence': r.coherence,
            'overall_score': r.overall_score,
            'decision': r.decision,
            'reasoning': r.reasoning,
            'judge_model': r.judge_model
        })

    with open(output_path, 'w', encoding='utf-8') as f:
        for item in output:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    # Summary
    print("\n" + "=" * 60)
    print("LLM-AS-JUDGE SUMMARY")
    print("=" * 60)

    if results:
        avg_scores = {
            'factual_accuracy': sum(r.factual_accuracy for r in results) / len(results),
            'policy_alignment': sum(r.policy_alignment for r in results) / len(results),
            'empathy_tone': sum(r.empathy_tone for r in results) / len(results),
            'completeness': sum(r.completeness for r in results) / len(results),
            'coherence': sum(r.coherence for r in results) / len(results),
            'overall': sum(r.overall_score for r in results) / len(results),
        }

        accept_count = sum(1 for r in results if r.decision == 'ACCEPT')
        revise_count = sum(1 for r in results if r.decision == 'REVISE')

        print(f"Total evaluated: {len(results)}")
        print(f"\nAverage Scores:")
        for k, v in avg_scores.items():
            print(f"  {k}: {v:.2f}")
        print(f"\nDecisions:")
        print(f"  ACCEPT: {accept_count} ({100*accept_count/len(results):.1f}%)")
        print(f"  REVISE: {revise_count} ({100*revise_count/len(results):.1f}%)")

    print(f"\nResults saved to: {output_path}")


# =============================================================================
# Human Review Interface
# =============================================================================

HUMAN_REVIEW_PROMPT = """
## Human Review Form

For each example, evaluate the reply and provide:
1. Your scores (0-5) for each dimension
2. Your overall decision (ACCEPT/REVISE)
3. Optional notes

---

### Example {i}

**Customer Issue:** {customer_text}

**Intent:** {intent}

**Evidence:**
{evidence_text}

**Generated Reply:**
{reply}

---

Your Scores:
- Factual Accuracy (0-5): __
- Policy Alignment (0-5): __
- Empathy & Tone (0-5): __
- Completeness (0-5): __
- Coherence (0-5): __

Overall Score: __

Decision: ACCEPT / REVISE

Notes: ________________________________
"""


def generate_human_review_set(input_path, output_path, n=30):
    """
    Generate a set of examples for human review.

    Args:
        input_path: Path to pipeline predictions
        output_path: Path to save human review forms
        n: Number of examples to generate
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        predictions = [json.loads(line) for line in f]

    # Filter to AUTO_HANDLE with replies
    auto_handle = [p for p in predictions if p.get('decision') == 'AUTO_HANDLE' and p.get('draft_reply')]

    # Stratified sample: take n examples, ensuring variety
    import random
    sample = random.sample(auto_handle, min(n, len(auto_handle)))

    forms = []
    for i, pred in enumerate(sample, 1):
        evidence_text = format_evidence(pred.get('evidence', []))

        form = HUMAN_REVIEW_PROMPT.format(
            i=i,
            customer_text=pred.get('message', ''),
            intent=pred.get('intent', ''),
            evidence_text=evidence_text,
            reply=pred.get('draft_reply', '')
        )
        forms.append({
            'conversation_id': pred.get('conversation_id', ''),
            'form': form
        })

    # Save as markdown for easy reading
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Human Reply Quality Review\n\n")
        f.write("Review each example and provide your scores.\n\n")
        for item in forms:
            f.write(f"## {item['conversation_id']}\n\n")
            f.write(item['form'])
            f.write("\n\n---\n\n")

    print(f"Generated {len(forms)} human review forms")
    print(f"Saved to: {output_path}")


def compute_agreement(llm_judge_path, human_review_path):
    """
    Compute agreement between LLM judge and human reviewer.

    Args:
        llm_judge_path: Path to LLM judge results
        human_review_path: Path to human review JSON

    Returns:
        dict with agreement statistics
    """
    with open(llm_judge_path, 'r', encoding='utf-8') as f:
        llm_results = {json.loads(line)['conversation_id']: json.loads(line) for line in f}

    with open(human_review_path, 'r', encoding='utf-8') as f:
        human_results = {item['conversation_id']: item for item in json.load(f)}

    # Find common IDs
    common_ids = set(llm_results.keys()) & set(human_results.keys())

    if not common_ids:
        print("No common conversation IDs found")
        return None

    # Compute agreement on overall decisions
    agree_count = 0
    total_scores_diff = []
    dimension_agreements = {
        'factual_accuracy': 0,
        'policy_alignment': 0,
        'empathy_tone': 0,
        'completeness': 0,
        'coherence': 0,
    }

    for cid in common_ids:
        llm = llm_results[cid]
        human = human_results[cid]

        # Decision agreement
        if llm['decision'] == human['decision']:
            agree_count += 1

        # Score differences
        for dim in dimension_agreements:
            llm_score = llm.get(dim, 0)
            human_score = human.get(dim, 0)
            total_scores_diff.append(abs(llm_score - human_score))
            if llm_score == human_score:
                dimension_agreements[dim] += 1

    n = len(common_ids)
    agreement_pct = 100 * agree_count / n

    # Cohen's Kappa for decisions
    # Simplified: treat as two raters
    llm_decisions = [llm_results[cid]['decision'] for cid in common_ids]
    human_decisions = [human_results[cid]['decision'] for cid in common_ids]

    # Simple agreement
    print(f"\n{'='*60}")
    print("HUMAN vs LLM JUDGE AGREEMENT")
    print(f"{'='*60}")
    print(f"Common examples evaluated: {n}")
    print(f"\nDecision Agreement:")
    print(f"  Exact agreement: {agree_count}/{n} ({agreement_pct:.1f}%)")

    print(f"\nDimension Score Differences (|LLM - Human|):")
    avg_diff = sum(total_scores_diff) / len(total_scores_diff) if total_scores_diff else 0
    print(f"  Average absolute difference: {avg_diff:.2f}")

    print(f"\nDimension Exact Agreement:")
    for dim, count in dimension_agreements.items():
        print(f"  {dim}: {count}/{n} ({100*count/n:.1f}%)")

    return {
        'n': n,
        'decision_agreement': agreement_pct,
        'avg_score_difference': avg_diff,
        'dimension_agreements': dimension_agreements
    }


# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='LLM-as-Judge Evaluation')
    parser.add_argument('--input', default='data/evaluation/pipeline_predictions.jsonl',
                        help='Input predictions file')
    parser.add_argument('--output', default='data/evaluation/llm_judge_results.jsonl',
                        help='Output evaluation file')
    parser.add_argument('--sample', type=int,
                        help='Sample N examples for evaluation')
    parser.add_argument('--generate-human-review', action='store_true',
                        help='Generate human review forms')
    parser.add_argument('--human-n', type=int, default=30,
                        help='Number of examples for human review')
    parser.add_argument('--human-review-input', default='data/evaluation/pipeline_predictions.jsonl',
                        help='Input for human review generation')
    parser.add_argument('--human-review-output', default='data/evaluation/human_review_forms.md',
                        help='Output for human review forms')
    parser.add_argument('--compute-agreement', nargs=2,
                        metavar=('LLM_PATH', 'HUMAN_PATH'),
                        help='Compute agreement between LLM and human')

    args = parser.parse_args()

    if args.compute_agreement:
        compute_agreement(args.compute_agreement[0], args.compute_agreement[1])
    elif args.generate_human_review:
        generate_human_review_set(args.human_review_input, args.human_review_output, args.human_n)
    else:
        run_llm_judge(args.input, args.output, args.sample)

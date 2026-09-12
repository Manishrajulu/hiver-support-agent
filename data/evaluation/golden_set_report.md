# Golden Set Report (v2 - Stratified Top-Up, English-Only)

## Sampling Summary

| Metric | Value |
|--------|-------|
| Random seed | 42 |
| Target size | 200 |
| Maximum size | 250 |
| Minimum per intent | 5 |
| Actual size | 220 |
| Random core | 200 |
| Stratified top-up | 20 |
| Source | amazonhelp_conversations.jsonl (154,976 raw) |

## Language Filtering

| Metric | Value |
|--------|-------|
| Language detection | langdetect |
| Text length threshold | 10 chars |
| Texts <10 chars | Flagged for manual review (not excluded) |
| Non-English candidates filtered | 36,690 |
| Short texts flagged | 122 |
| English-only pool | 115,586 candidates |

**This is a deliberate design choice:**
> "Pipeline is English-only (sentence-transformers all-MiniLM-L6-v2 primarily supports English).
> Golden set must reflect this scope."

Rationale:
- RAG reply generation uses English sentence-transformers model
- Non-English customer queries would receive poor quality replies
- Short texts (<10 chars) are included but flagged for manual review during labeling

## Design Decision

> "Mostly random to reflect real-world message frequency, with a minimum-representation
> top-up so no intent is left untested."

Rationale:
- Pure random sampling would leave rare intents (CANCELLATION, ORDER_MODIFY) with 0-2 examples
- This makes it impossible to evaluate model performance on these intents
- The top-up ensures at least 5 examples per intent for reliable evaluation
- Core sample still reflects natural frequency distribution

## Exclusion Criteria

| Source | Count Excluded |
|--------|---------------|
| Training set | 2,160 |
| Test set | 540 |
| Labeled dataset | 2,700 |
| **Total excluded** | **2,700** |

## Per-Intent Distribution (Final Golden Set)

| Intent | Count | Selection |
|--------|-------|-----------|
| OTHER | 68 | random_core |
| DELIVERY_LATE | 41 | random_core |
| APP_USAGE | 16 | random_core |
| ORDER_STATUS | 14 | random_core |
| PAYMENT_ISSUE | 13 | random_core |
| DEVICE_ISSUE | 12 | random_core |
| DELIVERY_MISSING | 11 | random_core |
| RETURN_REQUEST | 10 | random_core |
| REFUND_REQUEST | 5 | random_core + 1 topup |
| VIDEO_STREAMING | 5 | random_core + 3 topup |
| PRODUCT_ISSUE | 5 | random_core + 1 topup |
| DELIVERY_TRACKING | 5 | random_core + 3 topup |
| ACCOUNT_ACCESS | 5 | random_core + 2 topup |
| CANCELLATION | 5 | random_core + 5 topup |
| ORDER_MODIFY | 5 | random_core + 5 topup |

## Selection Method Breakdown

- **random_core**: Random sample reflecting natural message frequency (seed=42)
- **stratified_topup**: Additional examples for intents with <5 in core sample

## Integrity Check Results

- Size within 150-250: PASS
- No duplicate example_id: PASS
- No train/test/labeled overlap: PASS
- All intents >= 5: PASS

## Fields

| Field | Description | Human Input Required? |
|-------|-------------|----------------------|
| example_id | Auto-generated (golden_0001, etc.) | No |
| conversation_id | Original from raw data | No |
| customer_text | Extracted from conversation turns | No |
| current_label | Always empty | No |
| predicted_intent | Phase C model prediction | No |
| selection_method | 'random_core' or 'stratified_topup' | No |
| human_label | To be filled | **YES** |
| human_notes | To be filled | **YES** |

## Next Steps

1. **Human Labeling**: Review each example and fill `human_label` field
2. **Agreement Measurement**: Compare human labels to predicted_intent
3. **Quality Review**: Flag ambiguous examples in `human_notes`

---

*Report generated: 2026-09-11*
*Script: data/evaluation/golden_set_sampling.py v2*

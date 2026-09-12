# Interactive Golden Set Labeling Workflow

## Overview

A terminal-based interactive tool for labeling the golden set with human intent labels.

## Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `data/evaluation/label_golden_set.py` | **Created** | Interactive labeling script |
| `data/evaluation/golden_set.csv` | Unchanged | Original golden set (220 examples) |
| `data/evaluation/golden_set_labeled.csv` | Created by tool | Output with human labels |
| `data/evaluation/label_progress.json` | Created by tool | Auto-saved progress for resume |

## How It Works

### Starting the Tool

```bash
# Normal mode (all 220 examples)
python data/evaluation/label_golden_set.py

# Resume from last position
python data/evaluation/label_golden_set.py --resume

# Process only first N examples (test mode)
python data/evaluation/label_golden_set.py --sample 10

# List examples and their status
python data/evaluation/label_golden_set.py --list
```

### Interface

Each example displays:
1. **Example number / total** (e.g., `[15/220]`)
2. **Example ID** (e.g., `golden_0001`)
3. **Conversation ID**
4. **Full customer text**
5. **Model suggestion** (Phase C prediction - shown with `<-- suggested`)
6. **15 numbered intents**

### Commands

| Input | Action |
|-------|--------|
| `Enter` | Accept the suggested intent |
| `1-15` | Select intent by number |
| `s` or `skip` | Skip this example (no label) |
| `r` or `rem` | Remove label from this example |
| `q` or `quit` | Save and exit |

### After Labeling

After each label, you may optionally enter notes explaining your decision.

### Auto-Save & Resume

- **Auto-save after every example**: If the script crashes or you quit, your progress is preserved.
- **Progress file**: `data/evaluation/label_progress.json`
- **Output file**: `data/evaluation/golden_set_labeled.csv`

To resume from where you left off:
```bash
python data/evaluation/label_golden_set.py --resume
```

## Output Format

`golden_set_labeled.csv` preserves original columns and adds:

| Column | Description |
|--------|-------------|
| `example_id` | Unique identifier (golden_0001, etc.) |
| `conversation_id` | Original conversation ID |
| `customer_text` | Customer message text |
| `current_label` | Always empty |
| `predicted_intent` | Phase C model prediction |
| `selection_method` | `random_core` or `stratified_topup` |
| `human_label` | **Human evaluator's label** (filled by tool) |
| `human_notes` | Optional notes explaining the label |

## Valid Intent Labels

Exactly these 15 intents must be used:

1. ACCOUNT_ACCESS
2. APP_USAGE
3. CANCELLATION
4. DELIVERY_LATE
5. DELIVERY_MISSING
6. DELIVERY_TRACKING
7. DEVICE_ISSUE
8. ORDER_MODIFY
9. ORDER_STATUS
10. OTHER
11. PAYMENT_ISSUE
12. PRODUCT_ISSUE
13. REFUND_REQUEST
14. RETURN_REQUEST
15. VIDEO_STREAMING

## Important Notes

1. **The LLM suggestion is only a helper** - you may override any suggestion
2. **Original CSV is never modified** - all labels go to the new output file
3. **No data is lost on crash** - progress is saved after every example
4. **You can remove labels** - use `r` to remove a label if you made a mistake
5. **Skipped examples remain unlabeled** - you can return later to label them

## Compliance with Assignment Requirements

- Golden set sampling methodology unchanged (stratified top-up, 200-250 range)
- Integrity checks preserved (no overlap, no duplicates)
- Original golden set CSV remains unmodified
- Output format compatible with later golden-set evaluation

## Verification Results

| Test | Result |
|------|--------|
| CSV loads correctly (220 examples) | PASS |
| All examples can be iterated | PASS |
| Labels are saved correctly | PASS |
| Resume functionality works | PASS |
| Original CSV unchanged | PASS |
| Output format correct | PASS |

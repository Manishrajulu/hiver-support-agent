#!/usr/bin/env python3
"""
Manual review of 200 validation conversations.
This script processes conversations in batches with human judgment.
"""

import json

# Manual verdicts based on genuine semantic judgment of customer's actual problem
# Format: conversation_id: (verdict, correct_intent_if_incorrect, reason)

MANUAL_VERDICTS = {
    # Batch 1: conversations 0-24 (first portion read)
    "amazonhelp_088437": ("INCORRECT", "DELIVERY_LATE", "Customer complaining about delivery showing attempted but no one came - delivery issue"),
    "amazonhelp_046907": ("CORRECT", None, "Customer complaining delivery is late for wedding - DELIVERY_LATE correct"),

    # More verdicts will be added as we review
}

# Load the review file
with open('data/samples/v21_manual_validation_review.json', 'r', encoding='utf-8') as f:
    reviews = json.load(f)

print(f"Loaded {len(reviews)} conversations")

# Apply manual verdicts for conversations we've reviewed
# For conversations not yet manually reviewed, mark them for review

# First, let's identify which ones we've manually reviewed
reviewed_ids = set(MANUAL_VERDICTS.keys())

# Count how many we have verdicts for
with_verdicts = sum(1 for r in reviews if r['conversation_id'] in reviewed_ids)
print(f"Conversations with manual verdicts: {with_verdicts}")

# Save current state
with open('data/samples/v21_manual_validation_completed.json', 'w', encoding='utf-8') as f:
    json.dump(reviews, f, indent=2, ensure_ascii=False)

print("Saved initial file - need to continue reviewing remaining conversations")
#!/usr/bin/env python3
"""
Interactive Golden Set Labeling Tool

Labels the golden set with human intent labels via terminal interface.
Automatically saves progress after every example for crash recovery.

Usage:
    python label_golden_set.py                    # Normal mode (all examples)
    python label_golden_set.py --sample 10         # Test mode (first 10 examples)
    python label_golden_set.py --resume            # Resume from last position
"""

import csv
import json
import os
import sys
from dataclasses import dataclass
from typing import Optional

sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# Configuration
# =============================================================================

INPUT_CSV = "data/evaluation/golden_set.csv"
OUTPUT_CSV = "data/evaluation/golden_set_labeled.csv"
PROGRESS_FILE = "data/evaluation/label_progress.json"
INTENTS = [
    "ACCOUNT_ACCESS",
    "APP_USAGE",
    "CANCELLATION",
    "DELIVERY_LATE",
    "DELIVERY_MISSING",
    "DELIVERY_TRACKING",
    "DEVICE_ISSUE",
    "ORDER_MODIFY",
    "ORDER_STATUS",
    "OTHER",
    "PAYMENT_ISSUE",
    "PRODUCT_ISSUE",
    "REFUND_REQUEST",
    "RETURN_REQUEST",
    "VIDEO_STREAMING",
]
INTENT_MAP = {str(i + 1): intent for i, intent in enumerate(INTENTS)}
SKIP_COMMANDS = {"skip", "s", "n", "no"}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class LabeledExample:
    """A labeled example from the golden set."""
    example_id: str
    conversation_id: str
    customer_text: str
    current_label: str
    predicted_intent: str
    selection_method: str
    human_label: str
    human_notes: str


# =============================================================================
# Progress Management
# =============================================================================

def load_progress():
    """Load progress from JSON file."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"current_index": 0, "labels": {}}


def save_progress(progress):
    """Save progress to JSON file."""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2)


def save_labeled_csv(examples, filepath):
    """Save labeled examples to CSV."""
    fieldnames = [
        'example_id', 'conversation_id', 'customer_text',
        'current_label', 'predicted_intent', 'selection_method',
        'human_label', 'human_notes'
    ]
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for ex in examples:
            writer.writerow({
                'example_id': ex.example_id,
                'conversation_id': ex.conversation_id,
                'customer_text': ex.customer_text,
                'current_label': ex.current_label,
                'predicted_intent': ex.predicted_intent,
                'selection_method': ex.selection_method,
                'human_label': ex.human_label,
                'human_notes': ex.human_notes
            })


def load_examples():
    """Load examples from input CSV."""
    examples = []
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            examples.append(LabeledExample(
                example_id=row['example_id'],
                conversation_id=row['conversation_id'],
                customer_text=row['customer_text'],
                current_label=row.get('current_label', ''),
                predicted_intent=row['predicted_intent'],
                selection_method=row['selection_method'],
                human_label=row.get('human_label', ''),
                human_notes=row.get('human_notes', '')
            ))
    return examples


# =============================================================================
# Display Functions
# =============================================================================

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_intro(total):
    """Print introduction."""
    print("=" * 70)
    print("GOLDEN SET INTERACTIVE LABELING TOOL")
    print("=" * 70)
    print(f"Total examples: {total}")
    print(f"Input file: {INPUT_CSV}")
    print(f"Output file: {OUTPUT_CSV}")
    print()
    print("Commands:")
    print("  [1-15]  Select intent by number")
    print("  Enter   Accept suggested intent")
    print("  s/skip  Skip this example")
    print("  q/quit  Save and exit")
    print("  r/rem   Remove label from current example")
    print()
    print("=" * 70)
    print()


def print_example(i, total, ex, suggestion_idx):
    """Print a single example for labeling."""
    print(f"[{i + 1}/{total}] {ex.example_id}")
    print("-" * 70)
    print(f"Conversation: {ex.conversation_id}")
    print()
    print("Customer text:")
    print(ex.customer_text)
    print()
    print(f"Model suggestion: {ex.predicted_intent} (press Enter to accept)")
    print()
    print("Available intents:")
    for idx, intent in enumerate(INTENTS, 1):
        marker = " <-- suggested" if intent == ex.predicted_intent else ""
        print(f"  {idx:2}. {intent}{marker}")
    print()


def get_user_input():
    """Get user input for labeling decision."""
    try:
        return input("Your label [Enter = accept suggestion, or type number]: ").strip()
    except (EOFError, KeyboardInterrupt):
        return "q"


def get_notes_input():
    """Get optional notes from user."""
    try:
        return input("Notes (optional, Enter to skip): ").strip()
    except (EOFError, KeyboardInterrupt):
        return ""


# =============================================================================
# Labeling Logic
# =============================================================================

def label_example(ex, progress):
    """Process labeling for a single example."""
    # Find suggestion index
    suggestion_idx = INTENTS.index(ex.predicted_intent) + 1 if ex.predicted_intent in INTENTS else 0

    print_example(progress['current_index'], len(examples), ex, suggestion_idx)

    while True:
        user_input = get_user_input()

        if not user_input:  # Accept suggestion
            return ex.predicted_intent, ""

        if user_input.lower() in SKIP_COMMANDS:
            return "", ""

        if user_input.lower() in ("q", "quit"):
            return None, None  # Signal to quit

        if user_input.lower() in ("r", "rem"):
            return "__REMOVE__", ""

        if user_input in INTENT_MAP:
            selected_intent = INTENT_MAP[user_input]
            print(f"Selected: {selected_intent}")
            notes = get_notes_input()
            return selected_intent, notes

        print(f"Invalid input. Enter a number (1-{len(INTENTS)}), or press Enter.")


def process_labeling(start_index=0, limit=None):
    """Process the labeling workflow."""
    global examples

    progress = load_progress()
    if start_index > 0:
        progress['current_index'] = start_index

    # Load any existing labels from output CSV
    if os.path.exists(OUTPUT_CSV):
        existing_labels = {}
        with open(OUTPUT_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['human_label']:
                    existing_labels[row['example_id']] = {
                        'human_label': row['human_label'],
                        'human_notes': row.get('human_notes', '')
                    }
        # Apply existing labels to examples
        for ex in examples:
            if ex.example_id in existing_labels:
                ex.human_label = existing_labels[ex.example_id]['human_label']
                ex.human_notes = existing_labels[ex.example_id]['human_notes']

    total = len(examples)
    end_index = total if limit is None else min(start_index + limit, total)

    clear_screen()
    print_intro(total)

    i = start_index
    while i < end_index:
        ex = examples[i]
        progress['current_index'] = i

        # Show status
        status = ""
        if ex.human_label:
            status = f" [Labeled: {ex.human_label}]"
        elif ex.example_id in progress['labels']:
            status = f" [Labeled: {progress['labels'][ex.example_id]['human_label']}]"

        print(f"\n--- Progress: {i + 1}/{total} ---{status}")

        # Label the example
        human_label, human_notes = label_example(ex, progress)

        if human_label is None:  # User quit
            print("\nSaving progress and exiting...")
            save_progress(progress)
            save_labeled_csv(examples, OUTPUT_CSV)
            print(f"Saved {i} labeled examples to {OUTPUT_CSV}")
            return i

        if human_label == "__REMOVE__":
            ex.human_label = ""
            ex.human_notes = ""
            if ex.example_id in progress['labels']:
                del progress['labels'][ex.example_id]
            print("Label removed.")
        elif human_label:
            ex.human_label = human_label
            ex.human_notes = human_notes
            progress['labels'][ex.example_id] = {
                'human_label': human_label,
                'human_notes': human_notes
            }
            print(f"Labeled: {human_label}")
            if human_notes:
                print(f"Notes: {human_notes}")

        # Auto-save after every example
        save_progress(progress)
        save_labeled_csv(examples, OUTPUT_CSV)

        i += 1

    # All done
    save_progress(progress)
    save_labeled_csv(examples, OUTPUT_CSV)

    labeled_count = sum(1 for ex in examples if ex.human_label)
    skipped_count = sum(1 for ex in examples if not ex.human_label and ex.example_id not in progress['labels'])

    print("\n" + "=" * 70)
    print("LABELING COMPLETE")
    print("=" * 70)
    print(f"Total examples: {total}")
    print(f"Labeled: {labeled_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Output saved to: {OUTPUT_CSV}")
    print("=" * 70)

    return total


# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Interactive Golden Set Labeling')
    parser.add_argument('--sample', type=int,
                        help='Process only first N examples (test mode)')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from last saved position')
    parser.add_argument('--start', type=int, default=0,
                        help='Start index (0-based)')
    parser.add_argument('--list', action='store_true',
                        help='List examples and their labeling status')
    args = parser.parse_args()

    # Load examples
    if not os.path.exists(INPUT_CSV):
        print(f"ERROR: Input file not found: {INPUT_CSV}")
        sys.exit(1)

    examples = load_examples()
    print(f"Loaded {len(examples)} examples from {INPUT_CSV}")

    if args.list:
        print("\nExample Status:")
        print("-" * 70)
        for i, ex in enumerate(examples):
            status = "LABELED" if ex.human_label else "PENDING"
            print(f"{i+1:3}. {ex.example_id} | {status:8} | {ex.predicted_intent:20} | {ex.human_label or '-'}")
        sys.exit(0)

    if args.resume:
        progress = load_progress()
        start = progress.get('current_index', 0)
        print(f"Resuming from index {start}")
        process_labeling(start_index=start, limit=args.sample)
    elif args.start > 0:
        process_labeling(start_index=args.start, limit=args.sample)
    else:
        process_labeling(start_index=0, limit=args.sample)

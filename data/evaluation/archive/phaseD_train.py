#!/usr/bin/env python3
"""
Phase D: Fine-tuned Transformer Experiment
DistilBERT fine-tuning on Phase C corrected dataset
"""

import json
import os
import sys
import random
import pickle
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
    get_linear_schedule_with_warmup
)
from torch.optim import AdamW
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# PHASE D: FINE-TUNED TRANSFORMER EXPERIMENT
# =============================================================================

print("=" * 60)
print("PHASE D: DISTILBERT FINE-TUNING EXPERIMENT")
print("=" * 60)

# =============================================================================
# CONFIGURATION
# =============================================================================

SEED = 42
MAX_LEN = 128
BATCH_SIZE = 8
LEARNING_RATE = 3e-5
EPOCHS = 2
WARMUP_RATIO = 0.1
WEIGHT_DECAY = 0.01
MODEL_NAME = "distilbert-base-uncased"

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

print(f"\nConfiguration:")
print(f"  Model: {MODEL_NAME}")
print(f"  Max length: {MAX_LEN}")
print(f"  Batch size: {BATCH_SIZE}")
print(f"  Learning rate: {LEARNING_RATE}")
print(f"  Epochs: {EPOCHS}")
print(f"  Warmup ratio: {WARMUP_RATIO}")
print(f"  Weight decay: {WEIGHT_DECAY}")
print(f"  Seed: {SEED}")

# =============================================================================
# LOAD DATA
# =============================================================================

print("\n[1] Loading Phase C experimental dataset...")

exp_path = "data/baseline/phaseC_experimental.jsonl"
data = []
with open(exp_path, 'r', encoding='utf-8') as f:
    for line in f:
        data.append(json.loads(line.strip()))

with open("data/baseline/baseline_train_test_split.json", 'r') as f:
    split = json.load(f)
test_ids = set(split["test_ids"])
train_ids = set(split["train_ids"])

train_data = [item for item in data if item.get('conversation_id') in train_ids]
test_data = [item for item in data if item.get('conversation_id') in test_ids]

print(f"  Train examples: {len(train_data)}")
print(f"  Test examples: {len(test_data)}")

# =============================================================================
# TEXT PREPROCESSING
# =============================================================================

def get_customer_text(item):
    turns = item.get('turns', [])
    customer_texts = []
    for turn in turns:
        if turn.get('speaker') == 'Customer' or (turn.get('inbound', '').lower() == 'true'):
            text = turn.get('text', '').strip()
            if text:
                customer_texts.append(text)
    return ' '.join(customer_texts)

# =============================================================================
# CREATE LABEL MAPPING
# =============================================================================

all_labels = sorted(set(item.get('primary_intent') for item in data))
label2id = {label: i for i, label in enumerate(all_labels)}
id2label = {i: label for label, i in label2id.items()}

print(f"\n[2] Label mapping ({len(all_labels)} classes):")
for label, idx in label2id.items():
    print(f"  {idx}: {label}")

label_mapping = {
    'label2id': label2id,
    'id2label': id2label,
    'num_labels': len(all_labels)
}
with open("data/baseline/phaseD_label_mapping.json", 'w') as f:
    json.dump(label_mapping, f, indent=2)

# =============================================================================
# CREATE VALIDATION SPLIT
# =============================================================================

print("\n[3] Creating validation split from training data...")

val_ratio = 0.1
train_texts = []
train_labels = []
val_texts = []
val_labels = []

for label in all_labels:
    label_items = [item for item in train_data if item.get('primary_intent') == label]
    random.shuffle(label_items)
    val_count = max(1, int(len(label_items) * val_ratio))
    val_items = label_items[:val_count]
    train_items = label_items[val_count:]

    val_texts.extend([get_customer_text(item) for item in val_items])
    val_labels.extend([label2id[item.get('primary_intent')] for item in val_items])
    train_texts.extend([get_customer_text(item) for item in train_items])
    train_labels.extend([label2id[item.get('primary_intent')] for item in train_items])

print(f"  Training: {len(train_texts)}")
print(f"  Validation: {len(val_texts)}")
print(f"  Test: {len(test_data)}")

# =============================================================================
# TOKENIZER
# =============================================================================

print("\n[4] Loading tokenizer...")
tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)

# =============================================================================
# DATASET CLASS
# =============================================================================

class IntentDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]

        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

# =============================================================================
# CREATE DATASETS
# =============================================================================

print("\n[5] Creating datasets...")
train_dataset = IntentDataset(train_texts, train_labels, tokenizer, MAX_LEN)
val_dataset = IntentDataset(val_texts, val_labels, tokenizer, MAX_LEN)
test_texts = [get_customer_text(item) for item in test_data]
test_labels = [label2id[item.get('primary_intent')] for item in test_data]
test_dataset = IntentDataset(test_texts, test_labels, tokenizer, MAX_LEN)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE)

# =============================================================================
# MODEL
# =============================================================================

print("\n[6] Loading model...")
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"  Device: {device}")

model = DistilBertForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(all_labels)
)
model.to(device)

# =============================================================================
# OPTIMIZER & SCHEDULER
# =============================================================================

total_steps = len(train_loader) * EPOCHS
warmup_steps = int(total_steps * WARMUP_RATIO)

optimizer = AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
scheduler = get_linear_schedule_with_warmup(
    optimizer,
    num_warmup_steps=warmup_steps,
    num_training_steps=total_steps
)

print(f"  Total steps: {total_steps}")
print(f"  Warmup steps: {warmup_steps}")

# =============================================================================
# TRAINING
# =============================================================================

print("\n[7] Training...")
best_val_acc = 0

for epoch in range(EPOCHS):
    print(f"\n  Epoch {epoch + 1}/{EPOCHS}")

    model.train()
    train_loss = 0
    train_correct = 0
    train_total = 0

    for batch_idx, batch in enumerate(train_loader):
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)

        optimizer.zero_grad()
        outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
        loss = outputs.loss
        logits = outputs.logits

        loss.backward()
        optimizer.step()
        scheduler.step()

        train_loss += loss.item()
        preds = torch.argmax(logits, dim=1)
        train_correct += (preds == labels).sum().item()
        train_total += labels.size(0)

        if (batch_idx + 1) % 50 == 0:
            print(f"    Batch {batch_idx + 1}/{len(train_loader)}, Loss: {loss.item():.4f}")

    train_acc = train_correct / train_total
    avg_train_loss = train_loss / len(train_loader)
    print(f"    Train Loss: {avg_train_loss:.4f}, Train Acc: {train_acc:.4f}")

    # Validation
    model.eval()
    val_correct = 0
    val_total = 0
    val_loss = 0

    with torch.no_grad():
        for batch in val_loader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)

            outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            logits = outputs.logits

            val_loss += loss.item()
            preds = torch.argmax(logits, dim=1)
            val_correct += (preds == labels).sum().item()
            val_total += labels.size(0)

    val_acc = val_correct / val_total
    avg_val_loss = val_loss / len(val_loader)
    print(f"    Val Loss: {avg_val_loss:.4f}, Val Acc: {val_acc:.4f}")

    if val_acc > best_val_acc:
        best_val_acc = val_acc
        os.makedirs("data/baseline/phaseD_transformer_model", exist_ok=True)
        torch.save(model.state_dict(), "data/baseline/phaseD_transformer_model/pytorch_model.bin")
        print(f"    -> Best model saved (val_acc: {val_acc:.4f})")

print(f"\nBest validation accuracy: {best_val_acc:.4f}")

# =============================================================================
# EVALUATION ON TEST SET
# =============================================================================

print("\n[8] Evaluating on 540-example test set...")

model.load_state_dict(torch.load("data/baseline/phaseD_transformer_model/pytorch_model.bin"))
model.eval()

all_preds = []
all_labels = []

with torch.no_grad():
    for batch in test_loader:
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)

        outputs = model(input_ids, attention_mask=attention_mask)
        logits = outputs.logits

        preds = torch.argmax(logits, dim=1)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

pred_labels = [id2label[p] for p in all_preds]
true_labels = [id2label[l] for l in all_labels]

correct = sum(1 for p, t in zip(pred_labels, true_labels) if p == t)
accuracy = correct / len(pred_labels)
print(f"\nTest Accuracy: {accuracy:.4f} ({correct}/{len(pred_labels)})")

print("\nClassification Report:")
print(classification_report(true_labels, pred_labels, digits=4))

print("\nTop 15 Confusion Pairs:")
cm = confusion_matrix(true_labels, pred_labels, labels=all_labels)
confusion_pairs = []
for i, true_label in enumerate(all_labels):
    for j, pred_label in enumerate(all_labels):
        if i != j and cm[i, j] > 0:
            confusion_pairs.append((true_label, pred_label, cm[i, j]))
confusion_pairs.sort(key=lambda x: -x[2])
for true_label, pred_label, count in confusion_pairs[:15]:
    print(f"  {true_label} -> {pred_label}: {count}")

# =============================================================================
# SAVE PREDICTIONS
# =============================================================================

predictions = []
test_conversation_ids = [item.get('conversation_id') for item in test_data]
for cid, true_label, pred_label in zip(test_conversation_ids, true_labels, pred_labels):
    predictions.append({
        'conversation_id': cid,
        'true_label': true_label,
        'predicted_label': pred_label,
        'correct': true_label == pred_label
    })

with open("data/baseline/phaseD_transformer_predictions.jsonl", 'w', encoding='utf-8') as f:
    for pred in predictions:
        f.write(json.dumps(pred, ensure_ascii=False) + '\n')

print(f"\nPredictions saved to data/baseline/phaseD_transformer_predictions.jsonl")

# =============================================================================
# COMPARISON TO PHASE C
# =============================================================================

phaseC_accuracy = 0.7111
delta_vs_phaseC = accuracy - phaseC_accuracy
delta_vs_phase6 = accuracy - 0.7056

print("\n" + "=" * 60)
print("PHASE D RESULTS SUMMARY")
print("=" * 60)
print(f"  Original baseline:       54.44%")
print(f"  Phase 6 TF-IDF+LinearSVC: 70.56%")
print(f"  Phase C TF-IDF+LinearSVC: 71.11% ({phaseC_accuracy*100:.2f}%)")
print(f"  Phase D DistilBERT:      {accuracy*100:.2f}% ({correct}/540)")
print(f"  Delta vs Phase 6:        {delta_vs_phase6*100:+.2f}pp")
print(f"  Delta vs Phase C:        {delta_vs_phaseC*100:+.2f}pp")
print("=" * 60)

# Save config
config = {
    'model_name': MODEL_NAME,
    'max_len': MAX_LEN,
    'batch_size': BATCH_SIZE,
    'learning_rate': LEARNING_RATE,
    'epochs': EPOCHS,
    'warmup_ratio': WARMUP_RATIO,
    'weight_decay': WEIGHT_DECAY,
    'seed': SEED,
    'test_accuracy': accuracy,
    'correct': correct,
    'total': 540
}
with open("data/baseline/phaseD_transformer_model/training_config.json", 'w') as f:
    json.dump(config, f, indent=2)

print("\nPhase D training complete!")
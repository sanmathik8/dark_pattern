"""
Multi-Label Dark Pattern Transformer & SVM Trainer
Fine-tunes 'distilbert-base-uncased' for 7-category multi-label detection.
Saves model directly to 'model/distilbert_dark_pattern/' using save_pretrained().
Also builds Linear SVM fallback to 'model/linear_svm.pkl'.
"""

import os
import json
import joblib
import torch
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multiclass import OneVsRestClassifier
from sklearn.svm import LinearSVC

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding,
)

BASE_DIR = Path(__file__).parent
DATASET_PATH = BASE_DIR / "dark_patterns_multi_label.csv"
TRANSFORMER_MODEL_DIR = BASE_DIR / "model" / "distilbert_dark_pattern"
SVM_MODEL_PATH = BASE_DIR / "model" / "linear_svm.pkl"
MODEL_NAME = "distilbert-base-uncased"

CATEGORIES = [
    'scarcity_urgency',
    'pre_selected_options',
    'visual_asymmetry',
    'confirmshaming',
    'hidden_delayed_costs',
    'forced_continuity',
    'misdirection'
]

print(f"--> Target Device: {'cuda' if torch.cuda.is_available() else 'cpu'}")

# ── 1. Load Dataset ────────────────────────────────────────────────────────────
if not DATASET_PATH.exists():
    raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")

df = pd.read_csv(DATASET_PATH)
df['text'] = df['text'].fillna("").astype(str).str.strip()
texts = df['text'].tolist()
labels = df[CATEGORIES].values.astype(np.float32)

# Train/Val Split
train_texts, val_texts, train_labels, val_labels = train_test_split(
    texts, labels, test_size=0.15, random_state=42
)

print(f"Dataset Loaded: Total={len(df)} | Train={len(train_texts)} | Val={len(val_texts)}")

# ── 2. Train Multi-Label Linear SVM Fallback ──────────────────────────────────
print("\n--> Training Linear SVM Multi-Label Fallback ...")
vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
X_train = vectorizer.fit_transform(train_texts)
X_val = vectorizer.transform(val_texts)

svm = OneVsRestClassifier(LinearSVC(C=1.0, random_state=42))
svm.fit(X_train, train_labels)

SVM_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
svm_bundle = {
    "vectorizer": vectorizer,
    "classifier": svm,
    "categories": CATEGORIES,
    "model_name": "linear_svm_multilabel"
}
joblib.dump(svm_bundle, SVM_MODEL_PATH)
print(f"Linear SVM multi-label model saved to {SVM_MODEL_PATH}")

# ── 3. DistilBERT Fine-Tuning ─────────────────────────────────────────────────
print(f"\n--> Tokenizing for DistilBERT ({MODEL_NAME}) ...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

class MultiLabelDataset(torch.utils.data.Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=128):
        self.encodings = tokenizer(
            texts, truncation=True, padding=False, max_length=max_len
        )
        self.labels = labels

    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

train_dataset = MultiLabelDataset(train_texts, train_labels, tokenizer)
val_dataset = MultiLabelDataset(val_texts, val_labels, tokenizer)

# Multi-label metrics computation using sigmoid probabilities
def compute_metrics(eval_pred):
    logits, targets = eval_pred
    probs = 1.0 / (1.0 + np.exp(-logits))
    preds = (probs > 0.4).astype(int)

    f1_macro = f1_score(targets, preds, average='macro', zero_division=0)
    f1_micro = f1_score(targets, preds, average='micro', zero_division=0)
    precision = precision_score(targets, preds, average='micro', zero_division=0)
    recall = recall_score(targets, preds, average='micro', zero_division=0)

    return {
        'f1_macro': round(float(f1_macro), 4),
        'f1_micro': round(float(f1_micro), 4),
        'precision': round(float(precision), 4),
        'recall': round(float(recall), 4),
    }

print("\n--> Initializing DistilBERT Sequence Classifier ...")
id2label = {i: cat for i, cat in enumerate(CATEGORIES)}
label2id = {cat: i for i, cat in enumerate(CATEGORIES)}

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(CATEGORIES),
    problem_type="multi_label_classification",
    id2label=id2label,
    label2id=label2id,
)

training_args = TrainingArguments(
    output_dir=str(BASE_DIR / "results"),
    num_train_epochs=2,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    learning_rate=3e-5,
    weight_decay=0.01,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="f1_micro",
    logging_steps=50,
    report_to="none",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    processing_class=tokenizer,
    data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
    compute_metrics=compute_metrics,
)

print("\n--> Training DistilBERT Multi-Label Model ...")
trainer.train()

# Save Hugging Face model and tokenizer directly into model/distilbert_dark_pattern/
TRANSFORMER_MODEL_DIR.mkdir(parents=True, exist_ok=True)
print(f"\n--> Saving DistilBERT artifacts to {TRANSFORMER_MODEL_DIR} ...")
model.save_pretrained(str(TRANSFORMER_MODEL_DIR))
tokenizer.save_pretrained(str(TRANSFORMER_MODEL_DIR))

# Save category metadata JSON
with open(TRANSFORMER_MODEL_DIR / "categories.json", "w") as f:
    json.dump(CATEGORIES, f)

print("✅ SUCCESS: DistilBERT multi-label model trained and saved successfully!")

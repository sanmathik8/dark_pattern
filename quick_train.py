"""
Fast PyTorch Multi-Label Trainer & Artifact Saver
Trains DistilBERT Sequence Classifier directly on PyTorch DataLoader for 7 categories
and saves clean model weights directly to model/distilbert_dark_pattern/
"""

import os
import json
import torch
import numpy as np
import pandas as pd
from pathlib import Path
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification

BASE_DIR = Path(__file__).parent
DATASET_PATH = BASE_DIR / "dark_patterns_multi_label.csv"
MODEL_DIR = BASE_DIR / "model" / "distilbert_dark_pattern"
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

print("--> Loading dataset...")
df = pd.read_csv(DATASET_PATH)
df['text'] = df['text'].fillna("").astype(str).str.strip()
texts = df['text'].tolist()
labels = df[CATEGORIES].values.astype(np.float32)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

class QuickDataset(Dataset):
    def __init__(self, texts, labels):
        self.enc = tokenizer(texts, padding=True, truncation=True, max_length=128, return_tensors="pt")
        self.labels = torch.tensor(labels, dtype=torch.float32)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: v[idx] for k, v in self.enc.items()}
        item["labels"] = self.labels[idx]
        return item

ds = QuickDataset(texts, labels)
loader = DataLoader(ds, batch_size=32, shuffle=True)

print("--> Initializing DistilBERT with 7 labels...")
id2label = {i: cat for i, cat in enumerate(CATEGORIES)}
label2id = {cat: i for i, cat in enumerate(CATEGORIES)}

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(CATEGORIES),
    problem_type="multi_label_classification",
    id2label=id2label,
    label2id=label2id
)

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
model.train()

optimizer = torch.optim.AdamW(model.parameters(), lr=3e-5)
criterion = torch.nn.BCEWithLogitsLoss()

print("--> Training 1 Epoch...")
for batch in loader:
    optimizer.zero_grad()
    input_ids = batch["input_ids"].to(device)
    attention_mask = batch["attention_mask"].to(device)
    b_labels = batch["labels"].to(device)

    outputs = model(input_ids=input_ids, attention_mask=attention_mask)
    loss = criterion(outputs.logits, b_labels)
    loss.backward()
    optimizer.step()

print("--> Saving 7-label model weights cleanly...")
MODEL_DIR.mkdir(parents=True, exist_ok=True)
model.save_pretrained(str(MODEL_DIR))
tokenizer.save_pretrained(str(MODEL_DIR))

with open(MODEL_DIR / "categories.json", "w") as f:
    json.dump(CATEGORIES, f)

print("✅ SUCCESS: 7-label DistilBERT model weights saved with zero size mismatch!")

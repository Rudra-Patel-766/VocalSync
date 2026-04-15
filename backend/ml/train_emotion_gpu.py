import json
import csv
from pathlib import Path
from collections import Counter
from typing import List, Tuple

import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import Dataset, DataLoader
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    get_scheduler,
)
from torch.optim import AdamW
from sklearn.metrics import accuracy_score, f1_score, classification_report
from sklearn.model_selection import train_test_split

# ── Label mapping (4 labels — calm merged into neutral) ───────────────────
GOEMOTIONS_TO_TARGET = {
    "admiration":     "confident",
    "approval":       "confident",
    "pride":          "confident",
    "optimism":       "confident",
    "gratitude":      "confident",
    "joy":            "excited",
    "amusement":      "excited",
    "excitement":     "excited",
    "love":           "excited",
    "surprise":       "excited",
    "nervousness":    "nervous",
    "fear":           "nervous",
    "anxiety":        "nervous",
    "confusion":      "nervous",
    "embarrassment":  "nervous",
    "remorse":        "nervous",
    "disappointment": "nervous",
    "sadness":        "nervous",
    "neutral":        "neutral",
    "relief":         "neutral",  # was calm
    "caring":         "neutral",  # was calm
}

TARGET_PRIORITY = ["nervous", "excited", "confident", "neutral"]
LABEL2ID = {l: i for i, l in enumerate(TARGET_PRIORITY)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}


# ── Helpers ────────────────────────────────────────────────────────────────

def _is_positive(value) -> bool:
    return str(value).strip().lower() in {"1", "1.0", "true", "yes"}


def _pick_label(mapped: List[str]) -> str:
    for c in TARGET_PRIORITY:
        if c in mapped:
            return c
    return mapped[0]


# ── Data loading ───────────────────────────────────────────────────────────

def load_data(csv_path: Path) -> Tuple[List[str], List[int]]:
    texts, labels = [], []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            norm = {k.strip().strip('"').lower(): v for k, v in row.items()}
            text = (norm.get("text") or "").strip()
            if not text:
                continue
            active = [
                e for e in GOEMOTIONS_TO_TARGET
                if _is_positive(norm.get(e, 0))
            ]
            if not active:
                continue
            mapped = list(dict.fromkeys(GOEMOTIONS_TO_TARGET[e] for e in active))
            labels.append(LABEL2ID[_pick_label(mapped)])
            texts.append(text)
    return texts, labels


# ── Dataset ────────────────────────────────────────────────────────────────

class EmotionDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels    = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item


# ── Training ───────────────────────────────────────────────────────────────

def train(csv_path: str, epochs: int = 5, batch_size: int = 16):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    print("Loading data...")
    texts, labels = load_data(Path(csv_path))
    print(f"Loaded {len(texts)} samples")
    print(f"Label distribution: {dict(Counter(ID2LABEL[l] for l in labels))}")

    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    print("Tokenising...")
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    train_enc = tokenizer(x_train, truncation=True, padding=True, max_length=128)
    test_enc  = tokenizer(x_test,  truncation=True, padding=True, max_length=128)

    train_ds = EmotionDataset(train_enc, y_train)
    test_ds  = EmotionDataset(test_enc,  y_test)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    test_loader  = DataLoader(test_ds,  batch_size=batch_size)

    print("Loading DistilBERT...")
    model = DistilBertForSequenceClassification.from_pretrained(
        "distilbert-base-uncased",
        num_labels=len(LABEL2ID),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    ).to(device)

    # ── Class weights to fix imbalance ─────────────────────────────────────
    label_counts = Counter(y_train)
    total = sum(label_counts.values())
    weights = torch.tensor([
        total / (len(label_counts) * label_counts.get(i, 1))
        for i in range(len(LABEL2ID))
    ], dtype=torch.float).to(device)
    loss_fn = nn.CrossEntropyLoss(weight=weights)

    print("Class weights:")
    for i, w in enumerate(weights.tolist()):
        print(f"  {ID2LABEL[i]:12s}  weight={w:.3f}  samples={label_counts.get(i,0)}")

    # ── Optimizer + scheduler ──────────────────────────────────────────────
    optimizer   = AdamW(model.parameters(), lr=5e-6, weight_decay=0.01)
    total_steps = len(train_loader) * epochs
    scheduler   = get_scheduler(
        "linear", optimizer=optimizer,
        num_warmup_steps=total_steps // 5,   # more warmup
        num_training_steps=total_steps,
    )

    best_f1      = 0.0
    best_epoch   = 0
    artifact_dir = Path(__file__).parents[1] / "ml" / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    model_dir    = artifact_dir / "emotion_distilbert"

    # ── Training loop ──────────────────────────────────────────────────────
    for epoch in range(epochs):
        model.train()
        total_loss = 0

        for step, batch in enumerate(train_loader):
            batch   = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)

            # Use weighted loss instead of outputs.loss
            loss = loss_fn(outputs.logits, batch["labels"])
            loss.backward()
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            total_loss += loss.item()

            if step % 200 == 0:
                print(f"  Epoch {epoch+1} step {step}/{len(train_loader)} "
                      f"loss={loss.item():.4f}")

        avg_loss = total_loss / len(train_loader)

        # ── Eval ──────────────────────────────────────────────────────────
        model.eval()
        all_preds, all_labels = [], []
        with torch.no_grad():
            for batch in test_loader:
                batch   = {k: v.to(device) for k, v in batch.items()}
                outputs = model(**batch)
                preds   = outputs.logits.argmax(dim=-1).cpu().numpy()
                all_preds.extend(preds)
                all_labels.extend(batch["labels"].cpu().numpy())

        acc = accuracy_score(all_labels, all_preds)
        f1  = f1_score(all_labels, all_preds, average="macro")
        print(f"Epoch {epoch+1} avg loss: {avg_loss:.4f} | "
              f"Accuracy: {acc:.4f} | Macro F1: {f1:.4f}")

        # ── Save best model only ───────────────────────────────────────────
        if f1 > best_f1:
            best_f1    = f1
            best_epoch = epoch + 1
            model.save_pretrained(model_dir)
            tokenizer.save_pretrained(model_dir)
            print(f"  ✓ New best model saved (F1={f1:.4f})")

    # ── Final report ──────────────────────────────────────────────────────
    print(f"\nBest model was epoch {best_epoch} with Macro F1: {best_f1:.4f}")
    print(f"Model saved to: {model_dir}")

    report = classification_report(
        all_labels, all_preds,
        target_names=[ID2LABEL[i] for i in range(len(ID2LABEL))],
        output_dict=True,
    )

    metrics = {
        "accuracy":           float(acc),
        "macro_f1":           float(f1),
        "best_macro_f1":      float(best_f1),
        "best_epoch":         best_epoch,
        "label_distribution": dict(Counter(ID2LABEL[l] for l in labels)),
        "classification_report": report,
    }
    with (artifact_dir / "emotion_gpu_metrics.json").open("w") as mf:
        json.dump(metrics, mf, indent=2)

    print("\nPer-class results:")
    for label in TARGET_PRIORITY:
        r = report.get(label, {})
        print(f"  {label:12s}  precision={r.get('precision',0):.2f}  "
              f"recall={r.get('recall',0):.2f}  f1={r.get('f1-score',0):.2f}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset",    required=True)
    parser.add_argument("--epochs",     type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()
    train(args.dataset, args.epochs, args.batch_size)
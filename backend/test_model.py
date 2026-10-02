import warnings
from pathlib import Path
warnings.filterwarnings('ignore')

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

BASE_DIR = Path(__file__).parent.parent
TRANSFORMER_MODEL_DIR = BASE_DIR / "model" / "distilbert_dark_pattern"
SVM_MODEL_PATH = BASE_DIR / "model" / "linear_svm.pkl"

test_texts = [
    "Only 3 left! Buy now before it expires!",
    "Welcome to our website. Browse our collection.",
    "No thanks, I don't want to save money",
    "Our products are available in many colors",
    "Limited time offer! Subscribe now and get 50% off",
]

print("--- Testing Dark Pattern Classification Model ---\n")

if TRANSFORMER_MODEL_DIR.exists() and (TRANSFORMER_MODEL_DIR / "config.json").exists():
    print(f"Loading DistilBERT from {TRANSFORMER_MODEL_DIR} ...")
    tokenizer = AutoTokenizer.from_pretrained(str(TRANSFORMER_MODEL_DIR))
    model = AutoModelForSequenceClassification.from_pretrained(str(TRANSFORMER_MODEL_DIR))
    model.eval()

    inputs = tokenizer(test_texts, padding=True, truncation=True, max_length=128, return_tensors="pt")
    inputs.pop("token_type_ids", None)  # DistilBERT doesn't use token_type_ids
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)
        preds = torch.argmax(probs, dim=-1).numpy()
        probabilities = probs.numpy()

    print("Results:")
    for i, text in enumerate(test_texts):
        label = "Dark Pattern" if preds[i] == 1 else "Not Dark Pattern"
        conf = float(probabilities[i][preds[i]])
        print(f"  label={label:<18} confidence={conf:.4f}  ->  {text}")
    print("\n✅ DistilBERT Model Test PASSED!")

elif SVM_MODEL_PATH.exists():
    import joblib
    print(f"Loading Linear SVM fallback from {SVM_MODEL_PATH} ...")
    bundle = joblib.load(SVM_MODEL_PATH)
    vectorizer = bundle['vectorizer']
    classifier = bundle['classifier']
    label_encoder = bundle['label_encoder']

    X = vectorizer.transform(test_texts)
    preds = classifier.predict(X)
    scores = classifier.decision_function(X)
    decoded = label_encoder.inverse_transform(preds)

    print("Results:")
    for i, text in enumerate(test_texts):
        print(f"  label={decoded[i]:<18} score={scores[i]:.3f}  ->  {text}")
    print("\n✅ Linear SVM Model Test PASSED!")

else:
    print("❌ ERROR: No trained model found!")
    print(f"  Expected DistilBERT at: {TRANSFORMER_MODEL_DIR}")
    print(f"  Expected Linear SVM at: {SVM_MODEL_PATH}")

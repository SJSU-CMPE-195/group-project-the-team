# Train an MLP Neural Network on normalized ASL hand landmarks
#
# This replaces the Random Forest model with a neural network that:
#   - Learns subtle feature interactions (A vs T, M vs N)
#   - Outputs real probability distributions for better confidence
#   - Works on normalized, position/scale invariant features

import os
import pandas as pd
import numpy as np
import pickle
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.neural_network import MLPClassifier

# ─── 1. Load Data ──────────────────────────────────────────────────────────────
print("Loading normalized dataset...")
df = pd.read_csv('data/hand_landmarks_normalized.csv')
print(f"  Loaded {len(df)} samples, {len(df.columns)-1} features")

# Check if webcam data exists and merge it
WEBCAM_FILE = 'data/webcam_landmarks.csv'
if os.path.exists(WEBCAM_FILE):
    webcam_df = pd.read_csv(WEBCAM_FILE)
    print(f"  Found webcam data: {len(webcam_df)} additional samples")
    df = pd.concat([df, webcam_df], ignore_index=True)
    print(f"  Combined total: {len(df)} samples")

# ─── 2. Prepare Features and Labels ───────────────────────────────────────────
X = df.drop('label', axis=1).values
y = df['label'].values

# Encode labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

print(f"  Classes: {len(label_encoder.classes_)}")
print(f"  Labels: {list(label_encoder.classes_)}")

# ─── 3. Scale Features ────────────────────────────────────────────────────────
# StandardScaler improves MLP convergence significantly
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ─── 4. Split Data ────────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)
print(f"  Train: {len(X_train)} | Test: {len(X_test)}")

# ─── 5. Train MLP ─────────────────────────────────────────────────────────────
print("\nTraining MLP Neural Network...")
print("  Architecture: 256 → 128 → 64 → output")
print("  This may take a few minutes...\n")

model = MLPClassifier(
    hidden_layer_sizes=(256, 128, 64),
    activation='relu',
    solver='adam',
    alpha=0.001,           # L2 regularization
    batch_size=256,
    learning_rate='adaptive',
    learning_rate_init=0.001,
    max_iter=100,
    early_stopping=True,    # Stop when validation score stops improving
    validation_fraction=0.1,
    n_iter_no_change=10,
    random_state=42,
    verbose=True
)

model.fit(X_train, y_train)

# ─── 6. Evaluate ──────────────────────────────────────────────────────────────
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\n{'='*60}")
print(f"  Model Accuracy: {accuracy * 100:.2f}%")
print(f"{'='*60}")

# Per-class report
print("\nPer-Class Performance:")
print(classification_report(
    y_test, y_pred,
    target_names=label_encoder.classes_,
    zero_division=0
))

# Show confused pairs
print("\nMost Confused Pairs:")
cm = confusion_matrix(y_test, y_pred)
classes = label_encoder.classes_
confused_pairs = []
for i in range(len(classes)):
    for j in range(len(classes)):
        if i != j and cm[i][j] > 5:  # more than 5 misclassifications
            confused_pairs.append((classes[i], classes[j], cm[i][j]))

confused_pairs.sort(key=lambda x: -x[2])
if confused_pairs:
    for true_label, pred_label, count in confused_pairs[:10]:
        print(f"  '{true_label}' misclassified as '{pred_label}': {count} times")
else:
    print("  No significant confusion pairs found!")

# ─── 7. Save Model ────────────────────────────────────────────────────────────
print("\nSaving model...")
os.makedirs('models', exist_ok=True)
with open('models/asl_model.pkl', 'wb') as f:
    pickle.dump({
        'model': model,
        'label_encoder': label_encoder,
        'scaler': scaler,
        'model_type': 'mlp',
        'feature_count': X.shape[1],
    }, f)

print(f"Saved to models/asl_model.pkl")
print(f"  Model type: MLP ({model.n_layers_} layers)")
print(f"  Features: {X.shape[1]}")
print(f"  Classes: {len(label_encoder.classes_)}")
print("\nDone! Ready for real-life inference.")
import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder

# 1. Load the data
print("Loading data...")
df = pd.read_csv('data/hand_landmarks.csv')

# 2. Prepare Features (X) and Labels (y)
X = df.drop('label', axis=1)
y = df['label']

# Encode the text labels (A, B, etc.) into numbers (0, 1, etc.)
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# 3. Split into Train (80%) and Test (20%)
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

# 4. Train the Model
print("Training Random Forest Classifier...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 5. Evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"\nModel Accuracy: {accuracy * 100:.2f}%")

# 6. Save the Model and the Label Encoder for real-time use
print("Saving model...")
import os
os.makedirs('models', exist_ok=True)
with open('models/asl_model.pkl', 'wb') as f:
    pickle.dump({'model': model, 'label_encoder': label_encoder}, f)

print("Done! Ready for real-life inference.")
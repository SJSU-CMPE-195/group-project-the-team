import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import pickle
from stgcn_model import SignLanguageSTGCN

# --- Configuration ---
DATA_DIR = 'data/processed'
MODELS_DIR = 'models'
MODEL_SAVE_PATH = os.path.join(MODELS_DIR, 'master_stgcn.pth')
ENCODER_SAVE_PATH = os.path.join(MODELS_DIR, 'label_encoder_master.pkl')

BATCH_SIZE = 32
EPOCHS = 100
LEARNING_RATE = 0.001

# 1. Load and Merge Data
print("Loading datasets...")
X_words = np.load(os.path.join(DATA_DIR, 'X_citizen10.npy'))
y_words = np.load(os.path.join(DATA_DIR, 'y_citizen10.npy'))

X_alpha = np.load(os.path.join(DATA_DIR, 'X_alpha.npy'))
y_alpha = np.load(os.path.join(DATA_DIR, 'y_alpha.npy'))

# Combine
X = np.concatenate([X_words, X_alpha], axis=0)
y_str = np.concatenate([y_words, y_alpha], axis=0)

print(f"Total samples: {len(X)}")
print(f"Total classes: {len(np.unique(y_str))}")

# 2. Encode Labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y_str)

with open(ENCODER_SAVE_PATH, 'wb') as f:
    pickle.dump(label_encoder, f)

# 3. Prepare DataLoaders
X_tensor = torch.tensor(X, dtype=torch.float32)
y_tensor = torch.tensor(y_encoded, dtype=torch.long)

X_train, X_test, y_train, y_test = train_test_split(
    X_tensor, y_tensor, test_size=0.15, random_state=42, stratify=y_encoded
)

train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=BATCH_SIZE, shuffle=True)
test_loader = DataLoader(TensorDataset(X_test, y_test), batch_size=BATCH_SIZE, shuffle=False)

# 4. Initialize ST-GCN
device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
print(f"Training Master Model on: {device}")

model = SignLanguageSTGCN(num_classes=len(label_encoder.classes_)).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

# 5. Training Loop
history = {'train_acc': [], 'val_acc': []}

for epoch in range(EPOCHS):
    model.train()
    correct, total = 0, 0
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
    
    train_acc = 100 * correct / total
    
    model.eval()
    val_correct, val_total = 0, 0
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            val_total += labels.size(0)
            val_correct += (predicted == labels).sum().item()
    
    val_acc = 100 * val_correct / val_total
    history['train_acc'].append(train_acc)
    history['val_acc'].append(val_acc)
    
    if (epoch + 1) % 10 == 0 or epoch == 0:
        print(f"Epoch [{epoch+1}/{EPOCHS}] Train Acc: {train_acc:.2f}% | Val Acc: {val_acc:.2f}%")

# 6. Save
torch.save(model.state_dict(), MODEL_SAVE_PATH)
print(f"\nMaster Model Training Complete. Saved to {MODEL_SAVE_PATH}")
print(f"Classes covered: {list(label_encoder.classes_)}")

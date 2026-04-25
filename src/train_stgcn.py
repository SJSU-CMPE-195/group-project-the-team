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
# Choose dataset: 'wlasl10' or 'citizen10'
DATASET_TYPE = 'citizen10' 

X_PATH = os.path.join(DATA_DIR, f'X_{DATASET_TYPE}.npy')
Y_PATH = os.path.join(DATA_DIR, f'y_{DATASET_TYPE}.npy')
MODELS_DIR = 'models'
MODEL_SAVE_PATH = os.path.join(MODELS_DIR, f'{DATASET_TYPE}_stgcn.pth')
ENCODER_SAVE_PATH = os.path.join(MODELS_DIR, f'label_encoder_{DATASET_TYPE}.pkl')

BATCH_SIZE = 32
EPOCHS = 100
LEARNING_RATE = 0.001

# 1. Load Data
X = np.load(X_PATH)
y_str = np.load(Y_PATH)

# Create and fit a new LabelEncoder for the new word set
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y_str)

with open(ENCODER_SAVE_PATH, 'wb') as f:
    pickle.dump(label_encoder, f)


X_tensor = torch.tensor(X, dtype=torch.float32)
y_tensor = torch.tensor(y_encoded, dtype=torch.long)

X_train, X_test, y_train, y_test = train_test_split(
    X_tensor, y_tensor, test_size=0.2, random_state=42, stratify=y_encoded
)

train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=BATCH_SIZE, shuffle=True)
test_loader = DataLoader(TensorDataset(X_test, y_test), batch_size=BATCH_SIZE, shuffle=False)

# 2. Initialize ST-GCN
device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
print(f"Training ST-GCN on: {device}")

model = SignLanguageSTGCN(num_classes=len(label_encoder.classes_)).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

# 3. Training Loop
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

# 4. Save Model and History
torch.save(model.state_dict(), MODEL_SAVE_PATH)
with open(os.path.join(MODELS_DIR, 'stgcn_history.pkl'), 'wb') as f:
    pickle.dump(history, f)
print(f"\nST-GCN Training Complete. Model saved to {MODEL_SAVE_PATH}")

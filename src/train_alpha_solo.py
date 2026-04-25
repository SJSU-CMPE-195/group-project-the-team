import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import pickle

# Simple ST-GCN for 1 Hand (63 features)
class SingleHandSTGCN(nn.Module):
    def __init__(self, num_classes):
        super(SingleHandSTGCN, self).__init__()
        # Input: (batch, 30, 63)
        self.layer1 = nn.Sequential(
            nn.Linear(63, 128),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        self.lstm = nn.LSTM(128, 256, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(512, num_classes)

    def forward(self, x):
        x = self.layer1(x)
        x, _ = self.lstm(x)
        x = x[:, -1, :] # Take last frame
        x = self.fc(x)
        return x

# --- Configuration ---
DATA_DIR = 'data/processed'
MODELS_DIR = 'models'
MODEL_SAVE_PATH = os.path.join(MODELS_DIR, 'alpha_solo_stgcn.pth')
ENCODER_SAVE_PATH = os.path.join(MODELS_DIR, 'label_encoder_alpha_solo.pkl')

# 1. Load Alphabet Data and 1-Handed Words
X_alpha = np.load(os.path.join(DATA_DIR, 'X_alpha.npy')) # (520, 30, 126)
y_alpha = np.load(os.path.join(DATA_DIR, 'y_alpha.npy'))

X_citizen = np.load(os.path.join(DATA_DIR, 'X_citizen10.npy'))
y_citizen = np.load(os.path.join(DATA_DIR, 'y_citizen10.npy'))

# Filter for 1-handed words: MY, EAT, DEAF, FINE, CHRISTMAS, DOG
solo_words = ['MY', 'EAT1', 'DEAF1', 'FINE1', 'CHRISTMAS1', 'DOG1']
mask = np.isin(y_citizen, solo_words)
X_solo_words = X_citizen[mask]
y_solo_words = y_citizen[mask]

# Combine
X = np.concatenate([X_alpha, X_solo_words], axis=0) # (N, 30, 126)
y = np.concatenate([y_alpha, y_solo_words], axis=0)

# SMART HAND SELECTION: Pick whichever hand has landmarks (is not all zeros)
X_solo = []
for i in range(len(X)):
    sample = X[i] # (30, 126)
    right_hand = sample[:, :63]
    left_hand = sample[:, 63:]
    
    # Use Right hand if it has more movement/data, else use Left
    if np.sum(np.abs(right_hand)) >= np.sum(np.abs(left_hand)):
        X_solo.append(right_hand)
    else:
        X_solo.append(left_hand)

X_solo = np.array(X_solo)

# 2. Encode
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)
with open(ENCODER_SAVE_PATH, 'wb') as f:
    pickle.dump(label_encoder, f)

# 3. Train
X_tensor = torch.tensor(X_solo, dtype=torch.float32)
y_tensor = torch.tensor(y_encoded, dtype=torch.long)
X_train, X_test, y_train, y_test = train_test_split(X_tensor, y_tensor, test_size=0.1, random_state=42)

train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=32, shuffle=True)
test_loader = DataLoader(TensorDataset(X_test, y_test), batch_size=32, shuffle=False)

device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
model = SingleHandSTGCN(num_classes=len(label_encoder.classes_)).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

for epoch in range(100):
    model.train()
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
    
    if (epoch + 1) % 20 == 0:
        model.eval()
        correct = 0
        with torch.no_grad():
            for inputs, labels in test_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                _, predicted = torch.max(outputs.data, 1)
                correct += (predicted == labels).sum().item()
        print(f"Epoch {epoch+1} Solo Accuracy: {100 * correct / len(X_test):.2f}%")

torch.save(model.state_dict(), MODEL_SAVE_PATH)
print(f"Alphabet/Solo Model saved to {MODEL_SAVE_PATH}")

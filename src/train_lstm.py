import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import pickle

# --- Configuration ---
DATA_DIR = 'data/processed'
X_PATH = os.path.join(DATA_DIR, 'X_wlasl10.npy')
Y_PATH = os.path.join(DATA_DIR, 'y_wlasl10.npy')
MODELS_DIR = 'models'
MODEL_SAVE_PATH = os.path.join(MODELS_DIR, 'wlasl10_lstm.pth')
ENCODER_SAVE_PATH = os.path.join(MODELS_DIR, 'label_encoder.pkl')

BATCH_SIZE = 32
EPOCHS = 100
LEARNING_RATE = 0.001

# --- 1. Load and Prepare Data ---
print("Loading data...")
try:
    X = np.load(X_PATH)
    y_str = np.load(Y_PATH)
except FileNotFoundError:
    print(f"Error: Could not find '{X_PATH}' or '{Y_PATH}'. Please run extract_sequences.py first.")
    exit(1)

print(f"Loaded X shape: {X.shape}")
print(f"Loaded y shape: {y_str.shape}")

# Encode string labels ('hello', etc.) to integers (0-9)
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y_str)

# Save the encoder for inference later
os.makedirs(MODELS_DIR, exist_ok=True)
with open(ENCODER_SAVE_PATH, 'wb') as f:
    pickle.dump(label_encoder, f)
print(f"Saved LabelEncoder with classes: {label_encoder.classes_}")

# Convert Numpy arrays to PyTorch Tensors
# PyTorch default is float32 for model weights, so we cast X to float32
X_tensor = torch.tensor(X, dtype=torch.float32)
y_tensor = torch.tensor(y_encoded, dtype=torch.long)

# 80/20 train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X_tensor, y_tensor, test_size=0.2, random_state=42, stratify=y_encoded
)

# Create DataLoaders
train_dataset = TensorDataset(X_train, y_train)
test_dataset = TensorDataset(X_test, y_test)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

# --- 2. Define the LSTM Architecture ---
class SignLanguageLSTM(nn.Module):
    def __init__(self, input_size=126, hidden1_size=64, hidden2_size=128, fc_size=64, num_classes=10):
        super(SignLanguageLSTM, self).__init__()
        # Input shape: (batch, seq_len=30, features=63)
        self.lstm1 = nn.LSTM(input_size, hidden1_size, batch_first=True)
        self.lstm2 = nn.LSTM(hidden1_size, hidden2_size, batch_first=True)
        
        self.fc1 = nn.Linear(hidden2_size, fc_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(fc_size, num_classes)

    def forward(self, x):
        out, _ = self.lstm1(x)
        out, _ = self.lstm2(out)
        
        # We only need the output from the final time step
        # out shape: (batch_size, seq_length, hidden2_size)
        out = out[:, -1, :]
        
        out = self.fc1(out)
        out = self.relu(out)
        out = self.fc2(out)
        return out

# Initialize model, loss function, and optimizer
# It will use Metal Performance Shaders (MPS) if running on MacBook Air M4 for faster training on Apple Silicon.
device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
print(f"Using device: {device}")

model = SignLanguageLSTM(num_classes=len(label_encoder.classes_)).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

# --- 3. Training Loop ---
print("\nStarting Training...")
for epoch in range(EPOCHS):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        
        # Zero the parameter gradients
        optimizer.zero_grad()
        
        # Forward pass
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        
        # Backward pass and optimize
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item() * inputs.size(0)
        
        # Calculate accuracy
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        
    epoch_loss = running_loss / len(train_loader.dataset)
    epoch_acc = (correct / total) * 100
    
    # Evaluate on test set
    model.eval()
    test_loss = 0.0
    test_correct = 0
    test_total = 0
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            
            test_loss += loss.item() * inputs.size(0)
            _, predicted = torch.max(outputs.data, 1)
            test_total += labels.size(0)
            test_correct += (predicted == labels).sum().item()
            
    val_loss = test_loss / len(test_loader.dataset)
    val_acc = (test_correct / test_total) * 100
    
    if (epoch + 1) % 5 == 0 or epoch == 0:
        print(f"Epoch [{epoch+1}/{EPOCHS}] "
              f"Train Loss: {epoch_loss:.4f}, Train Acc: {epoch_acc:.2f}% | "
              f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")

# --- 4. Save the Model ---
os.makedirs(MODELS_DIR, exist_ok=True)
torch.save(model.state_dict(), MODEL_SAVE_PATH)
print(f"\nTraining Complete!")
print(f"Model saved to {MODEL_SAVE_PATH}")

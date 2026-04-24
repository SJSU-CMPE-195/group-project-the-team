import os
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
import matplotlib.pyplot as plt
import pickle
import time
from stgcn_model import SignLanguageSTGCN

# --- Configuration ---
MODELS_DIR = 'models'
ENCODER_PATH = os.path.join(MODELS_DIR, 'label_encoder.pkl')
DATA_DIR = 'data/processed'
X_PATH = os.path.join(DATA_DIR, 'X_wlasl10.npy')
Y_PATH = os.path.join(DATA_DIR, 'y_wlasl10.npy')

# LSTM Architecture (for comparison)
class SignLanguageLSTM(nn.Module):
    def __init__(self, input_size=126, hidden1_size=64, hidden2_size=128, fc_size=64, num_classes=10):
        super(SignLanguageLSTM, self).__init__()
        self.lstm1 = nn.LSTM(input_size, hidden1_size, batch_first=True)
        self.lstm2 = nn.LSTM(hidden1_size, hidden2_size, batch_first=True)
        self.fc1 = nn.Linear(hidden2_size, fc_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(fc_size, num_classes)

    def forward(self, x):
        out, _ = self.lstm1(x)
        out, _ = self.lstm2(out)
        out = out[:, -1, :]
        out = self.fc1(out)
        out = self.relu(out)
        out = self.fc2(out)
        return out

def get_model_size(model):
    param_size = 0
    for param in model.parameters():
        param_size += param.nelement() * param.element_size()
    buffer_size = 0
    for buffer in model.buffers():
        buffer_size += buffer.nelement() * buffer.element_size()
    size_all_mb = (param_size + buffer_size) / 1024**2
    return size_all_mb

def evaluate(model_type='stgcn'):
    device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
    print(f"\n--- Evaluating {model_type.upper()} Model on: {device} ---")
    
    # 1. Load Data
    with open(ENCODER_PATH, 'rb') as f:
        label_encoder = pickle.load(f)
        
    X = np.load(X_PATH)
    y_str = np.load(Y_PATH)
    y_encoded = label_encoder.transform(y_str)
    
    X_tensor = torch.tensor(X, dtype=torch.float32).to(device)
    y_tensor = torch.tensor(y_encoded, dtype=torch.long).to(device)
    
    # 2. Load Model
    num_classes = len(label_encoder.classes_)
    if model_type == 'stgcn':
        model = SignLanguageSTGCN(num_classes=num_classes).to(device)
        model_path = os.path.join(MODELS_DIR, 'wlasl10_stgcn.pth')
    else:
        model = SignLanguageLSTM(num_classes=num_classes).to(device)
        model_path = os.path.join(MODELS_DIR, 'wlasl10_lstm.pth')
        
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    
    print(f"Model Size: {get_model_size(model):.2f} MB")
    print(f"Total Parameters: {sum(p.numel() for p in model.parameters()):,}")

    # 3. Get Predictions and Measure Latency
    start_time = time.time()
    with torch.no_grad():
        outputs = model(X_tensor)
        _, predicted = torch.max(outputs, 1)
    end_time = time.time()
    
    avg_latency = (end_time - start_time) / len(X) * 1000 # ms
    print(f"Average Inference Latency: {avg_latency:.2f} ms per sequence")
    
    y_true = y_encoded
    y_pred = predicted.cpu().numpy()
    
    # 4. Print Report
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=label_encoder.classes_))
    
    # 5. Generate Confusion Matrix
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=label_encoder.classes_, 
                yticklabels=label_encoder.classes_)
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title(f'Confusion Matrix: {model_type.upper()}')
    
    os.makedirs('docs/plots', exist_ok=True)
    plot_path = f'docs/plots/cm_{model_type}.png'
    plt.savefig(plot_path)
    print(f"Confusion matrix saved to: {plot_path}")
    plt.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='stgcn', choices=['lstm', 'stgcn'])
    args = parser.parse_args()
    
    evaluate(model_type=args.model)

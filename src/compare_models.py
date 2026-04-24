import os
import torch
import numpy as np
import pickle
import time
import matplotlib.pyplot as plt
from stgcn_model import SignLanguageSTGCN
import torch.nn as nn

# --- Configuration ---
MODELS_DIR = 'models'
ENCODER_PATH = os.path.join(MODELS_DIR, 'label_encoder.pkl')
DATA_DIR = 'data/processed'
X_PATH = os.path.join(DATA_DIR, 'X_wlasl10.npy')
Y_PATH = os.path.join(DATA_DIR, 'y_wlasl10.npy')

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

def get_metrics(model, X_tensor, y_tensor):
    model.eval()
    start_time = time.time()
    with torch.no_grad():
        outputs = model(X_tensor)
        _, predicted = torch.max(outputs, 1)
        
        # Calculate Top-3 accuracy
        _, top3_predicted = torch.topk(outputs, 3, dim=1)
        top3_correct = torch.any(top3_predicted == y_tensor.view(-1, 1), dim=1).sum().item()
        
    end_time = time.time()
    latency = (end_time - start_time) / len(X_tensor) * 1000
    
    correct = (predicted == y_tensor).sum().item()
    accuracy = 100 * correct / len(y_tensor)
    top3_accuracy = 100 * top3_correct / len(y_tensor)
    
    params = sum(p.numel() for p in model.parameters())
    
    return accuracy, top3_accuracy, latency, params

def compare():
    device = torch.device('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
    print(f"Comparing models on: {device}")
    
    # Load Data
    with open(ENCODER_PATH, 'rb') as f:
        label_encoder = pickle.load(f)
    num_classes = len(label_encoder.classes_)
    
    X = np.load(X_PATH)
    y_str = np.load(Y_PATH)
    y_encoded = label_encoder.transform(y_str)
    X_tensor = torch.tensor(X, dtype=torch.float32).to(device)
    y_tensor = torch.tensor(y_encoded, dtype=torch.long).to(device)
    
    # Load LSTM
    lstm = SignLanguageLSTM(num_classes=num_classes).to(device)
    lstm.load_state_dict(torch.load(os.path.join(MODELS_DIR, 'wlasl10_lstm.pth'), map_location=device))
    
    # Load ST-GCN
    stgcn = SignLanguageSTGCN(num_classes=num_classes).to(device)
    stgcn.load_state_dict(torch.load(os.path.join(MODELS_DIR, 'wlasl10_stgcn.pth'), map_location=device))
    
    # Get Metrics
    print("\nRunning benchmarks...")
    lstm_acc, lstm_top3, lstm_lat, lstm_params = get_metrics(lstm, X_tensor, y_tensor)
    stgcn_acc, stgcn_top3, stgcn_lat, stgcn_params = get_metrics(stgcn, X_tensor, y_tensor)
    
    # Print Results
    print("\n" + "="*60)
    print(f"{'Metric':<25} | {'LSTM (Baseline)':<15} | {'ST-GCN (Proposed)':<15}")
    print("-" * 60)
    print(f"{'Top-1 Accuracy (%)':<25} | {lstm_acc:>15.2f} | {stgcn_acc:>17.2f}")
    print(f"{'Top-3 Accuracy (%)':<25} | {lstm_top3:>15.2f} | {stgcn_top3:>17.2f}")
    print(f"{'Inference Latency (ms)':<25} | {lstm_lat:>15.4f} | {stgcn_lat:>17.4f}")
    print(f"{'Total Parameters':<25} | {lstm_params:>15,} | {stgcn_params:>17,}")
    print("="*60)
    
    # Visual Comparison
    metrics = ['Top-1 Acc', 'Top-3 Acc']
    lstm_vals = [lstm_acc, lstm_top3]
    stgcn_vals = [stgcn_acc, stgcn_top3]
    
    x = np.arange(len(metrics))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width/2, lstm_vals, width, label='LSTM', color='#ff7f7f')
    ax.bar(x + width/2, stgcn_vals, width, label='ST-GCN', color='#7f7fff')
    
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Accuracy Comparison: LSTM vs ST-GCN')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.legend()
    ax.set_ylim(0, 100)
    
    os.makedirs('docs/plots', exist_ok=True)
    plt.savefig('docs/plots/accuracy_comparison_bar.png')
    print("\nComparison chart saved to: docs/plots/accuracy_comparison_bar.png")

if __name__ == "__main__":
    compare()

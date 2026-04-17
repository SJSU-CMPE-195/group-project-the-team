import os
import cv2
import torch
import torch.nn as nn 
import numpy as np
import mediapipe as mp
import pickle
from collections import deque
import warnings

warnings.filterwarnings("ignore")

# -- 1. Model Configuration --
MODELS_DIR = "models"
MODEL_PATH = os.path.join(MODELS_DIR, "wlasl10_lstm.pth")
ENCODE_PATH = os.path.join(MODELS_DIR, "LABEL_encoder.pkl")
CONFIDENCE_THRESHOLD = 0.7 #70% confidence

# We must use exactly the same architecture class as in training to successfully load the model weights
class SignLanguageLSTM(nn.Module):
    def __init__(self, input_size=63, hidden1_size=64, hidden2_size=128, fc_size=64, num_classes=10):
        super(SignLanguageLSTM, self).__init__()
        self.lstm1 = nn.LSTM(input_size, hidden1_size, batch_first=True)
        self.lstm2 = nn.LSTM(hidden1_size, hidden2_size, batch_first=True)
        self.fc1 = nn.Linear(hidden2_size, fc_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(fc_size, num_classes)

    def forward(self, x):
        out, _ = self.lstm1(x)
        out, _ = self.lstm2(out)
        out = out[:, -1, :]  # Take the output of the last time step
        out = self.fc1(out)
        out = self.relu(out)
        out = self.fc2(out)
        return out
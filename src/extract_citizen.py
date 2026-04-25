import os
import cv2
import pandas as pd
import numpy as np
import mediapipe as mp
from tqdm import tqdm
import warnings

# Configuration
TARGET_WORDS = ["MOVIE1", "EAT1", "NIGHT1", "FINE1", "DEAF1", "HOSPITAL1", "PARTY1", "CHRISTMAS1", "BASKETBALL1", "DOG1"]
FRAMES_PER_VIDEO = 30
FEATURES_PER_FRAME = 126

DATA_DIR = '/Volumes/2TB/ASL_Citizen/ASL_Citizen'
SPLITS_DIR = os.path.join(DATA_DIR, 'splits')
VIDEO_DIR = os.path.join(DATA_DIR, 'videos')
OUTPUT_DIR = 'data/processed'


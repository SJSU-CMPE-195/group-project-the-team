import json
import os
from collections import Counter

DATA_DIR = 'data/WLASL'
JSON_PATH = os.path.join(DATA_DIR, 'WLASL_v0.3.json')
VIDEO_DIR = os.path.join(DATA_DIR, 'videos')

if not os.path.exists(JSON_PATH):
    print(f"Error: {JSON_PATH} not found.")
else:
    with open(JSON_PATH, 'r') as f:
        wlasl_data = json.load(f)

    word_counts = Counter()
    
    for entry in wlasl_data:
        word = entry['gloss'].lower()
        available_for_word = 0
        for instance in entry['instances']:
            video_id = instance['video_id']
            video_path = os.path.join(VIDEO_DIR, f"{video_id}.mp4")
            if os.path.exists(video_path):
                available_for_word += 1
        
        if available_for_word > 0:
            word_counts[word] = available_for_word

    # Get the top 10
    top_10 = word_counts.most_common(10)

    print(f"{'Rank':<5} | {'Word':<15} | {'Available Videos':<15}")
    print("-" * 40)
    for i, (word, count) in enumerate(top_10, 1):
        print(f"{i:<5} | {word:<15} | {count:<15}")

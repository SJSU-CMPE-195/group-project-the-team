import json
import os

TARGET_WORDS = ["hello", "help", "thank you", "yes", "no", "please", "sorry", "hurt", "eat", "water"]
DATA_DIR = 'data/WLASL'
JSON_PATH = os.path.join(DATA_DIR, 'WLASL_v0.3.json')
VIDEO_DIR = os.path.join(DATA_DIR, 'videos')

if not os.path.exists(JSON_PATH):
    print(f"Error: {JSON_PATH} not found.")
else:
    with open(JSON_PATH, 'r') as f:
        wlasl_data = json.load(f)

    word_counts = {word: 0 for word in TARGET_WORDS}
    missing_videos = {word: 0 for word in TARGET_WORDS}
    
    for entry in wlasl_data:
        word = entry['gloss'].lower()
        if word in TARGET_WORDS:
            for instance in entry['instances']:
                video_id = instance['video_id']
                video_path = os.path.join(VIDEO_DIR, f"{video_id}.mp4")
                if os.path.exists(video_path):
                    word_counts[word] += 1
                else:
                    missing_videos[word] += 1

    print(f"{'Word':<15} | {'Available Videos':<20} | {'Missing Videos':<15}")
    print("-" * 55)
    total_available = 0
    for word in TARGET_WORDS:
        print(f"{word:<15} | {word_counts[word]:<20} | {missing_videos[word]:<15}")
        total_available += word_counts[word]
    print("-" * 55)
    print(f"Total Available: {total_available}")

import time

class SentenceEngine:
    def __init__(self, confidence_threshold=0.6, energy_commit_limit=12):
        self.sentence = []
        self.last_added_word = None
        self.word_cooldowns = {}
        self.COOLDOWN_DURATION = 2.5
        
        # Energy System
        self.current_candidate = None
        self.current_energy = 0
        self.energy_commit_limit = energy_commit_limit
        self.confidence_threshold = confidence_threshold
        
        # --- SMART ASL-TO-ENGLISH RULES ---
        self.context_rules = {
            "MY": ["NAME", "DOG", "HOSPITAL"],
            "HELLO": ["MY", "ME", "YOU"],
            "ME": ["HAPPY", "FINE", "EAT", "BAD", "GOOD"],
            "YOU": ["GOOD", "BAD", "HAPPY", "FINE"],
            "NAME": ["ARAMISH"] # Favoring your name after 'NAME'
        }
        
        # Mapping for Natural English output
        self.grammar_map = {
            "MY NAME": "My name is",
            "ME HAPPY": "I am happy",
            "YOU GOOD": "Are you good?",
            "HELLO ME": "Hello, I am",
            "HELLO YOU": "Hello there!",
            "ME FINE": "I am doing fine",
            "DOG GOOD": "The dog is being good",
            "GOOD NIGHT": "Good night!"
        }

    def process_prediction(self, top_k_predictions, hand_count, velocity=0.0):
        is_moving_fast = velocity > 0.05
        
        if not top_k_predictions or hand_count == 0 or is_moving_fast:
            decay_rate = 3 if is_moving_fast else 1
            self.current_energy = max(0, self.current_energy - decay_rate)
            if self.current_energy == 0:
                self.current_candidate = None
            return (self.current_candidate if is_moving_fast else None), (self.current_energy / self.energy_commit_limit), None

        best_word, best_conf = top_k_predictions[0]
        clean_best = best_word.upper().replace('1', '')

        current_time = time.time()
        if clean_best in self.word_cooldowns:
            if current_time - self.word_cooldowns[clean_best] < self.COOLDOWN_DURATION:
                self.current_energy = max(0, self.current_energy - 1)
                return self.current_candidate, (self.current_energy / self.energy_commit_limit), None

        # Contextual Boost
        if len(self.sentence) > 0:
            prev_word = self.sentence[-1].upper()
            if prev_word in self.context_rules:
                likely_words = self.context_rules[prev_word]
                for word, conf in top_k_predictions:
                    if word.upper().replace('1','') in likely_words and conf > (best_conf * 0.5):
                        best_word = word
                        clean_best = best_word.upper().replace('1', '')
                        break

        if best_conf > self.confidence_threshold:
            if clean_best == self.current_candidate:
                self.current_energy += 1
            else:
                self.current_candidate = clean_best
                self.current_energy = 1
        else:
            self.current_energy = max(0, self.current_energy - 1)

        committed_word = None
        if self.current_energy >= self.energy_commit_limit:
            self.sentence.append(clean_best)
            self.word_cooldowns[clean_best] = current_time
            committed_word = clean_best
            self.current_energy = 0
            self.current_candidate = None

        energy_ratio = min(1.0, self.current_energy / self.energy_commit_limit)
        return self.current_candidate, energy_ratio, committed_word

    def get_sentence_text(self):
        """
        Applies Grammar Mapping to turn ASL Glosses into Natural English
        """
        raw_text = " ".join(self.sentence)
        
        # Apply Grammar Mapping
        translated_text = raw_text
        for gloss, english in self.grammar_map.items():
            if gloss in translated_text:
                translated_text = translated_text.replace(gloss, english)
        
        # Simple auto-capitalization
        if translated_text:
            translated_text = translated_text[0].upper() + translated_text[1:]
        
        return translated_text

    def reset(self):
        self.sentence = []
        self.word_cooldowns = {}
        self.current_candidate = None
        self.current_energy = 0

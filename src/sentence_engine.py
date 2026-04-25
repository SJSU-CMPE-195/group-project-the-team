import time

class SentenceEngine:
    def __init__(self, confidence_threshold=0.6, energy_commit_limit=15):
        self.sentence = []
        self.last_added_word = None
        
        # Energy System
        self.current_candidate = None
        self.current_energy = 0
        self.energy_commit_limit = energy_commit_limit # Frames needed to commit
        self.confidence_threshold = confidence_threshold
        
        # Contextual Rules
        self.context_rules = {
            "MY": ["NAME", "DOG", "HOSPITAL"],
            "HELLO": ["MY", "ME", "YOU"],
            "ME": ["HAPPY", "FINE", "EAT", "BAD", "GOOD"],
            "YOU": ["GOOD", "BAD", "HAPPY", "FINE"],
            "GOOD": ["NIGHT", "DOG", "PARTY"],
            "NAME": ["ARAMISH"]
        }

    def process_prediction(self, top_k_predictions, hand_count):
        """
        Returns: (candidate_word, current_energy_ratio, committed_word)
        """
        if not top_k_predictions or hand_count == 0:
            self.current_energy = max(0, self.current_energy - 2) # Decay energy
            if self.current_energy == 0:
                self.current_candidate = None
                self.last_added_word = None # Allow same word again after hands drop
            return None, 0.0, None

        best_word, best_conf = top_k_predictions[0]
        
        # Contextual Boost
        if len(self.sentence) > 0:
            prev_word = self.sentence[-1].upper()
            if prev_word in self.context_rules:
                likely_words = self.context_rules[prev_word]
                for word, conf in top_k_predictions:
                    if word.upper().replace('1','') in likely_words and conf > (best_conf * 0.6):
                        best_word = word
                        break

        clean_best = best_word.upper().replace('1', '')

        # Energy Logic
        if best_conf > self.confidence_threshold:
            if clean_best == self.current_candidate:
                # Same word as before? Increase energy
                self.current_energy += 1
            else:
                # Different word? Reset or decay energy
                self.current_candidate = clean_best
                self.current_energy = 1
        else:
            self.current_energy = max(0, self.current_energy - 1)

        # Commitment Check
        committed_word = None
        if self.current_energy >= self.energy_commit_limit:
            if self.current_candidate != self.last_added_word:
                self.sentence.append(self.current_candidate)
                self.last_added_word = self.current_candidate
                committed_word = self.current_candidate
            
            # Reset energy after commit to prevent double-adding
            self.current_energy = 0 

        energy_ratio = min(1.0, self.current_energy / self.energy_commit_limit)
        return self.current_candidate, energy_ratio, committed_word

    def get_sentence_text(self):
        return " ".join(self.sentence)

    def reset(self):
        self.sentence = []
        self.last_added_word = None
        self.current_candidate = None
        self.current_energy = 0

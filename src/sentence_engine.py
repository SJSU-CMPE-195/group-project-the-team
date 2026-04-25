import time

class SentenceEngine:
    def __init__(self, confidence_threshold=0.7, debounce_time=1.0):
        self.sentence = []
        self.last_word = None
        self.last_added_time = 0
        self.confidence_threshold = confidence_threshold
        self.debounce_time = debounce_time
        
        # Contextual Rules (Predictive Logic)
        # format: {previous_word: [likely_next_words]}
        self.context_rules = {
            "MY": ["NAME", "DOG", "HOSPITAL"],
            "HELLO": ["MY", "ME", "YOU"],
            "ME": ["HAPPY", "FINE", "EAT", "BAD", "GOOD"],
            "YOU": ["GOOD", "BAD", "HAPPY", "FINE"],
            "GOOD": ["NIGHT", "DOG", "PARTY"],
            "NAME": ["ARAMISH"] # We can add specific names here
        }

    def process_prediction(self, top_k_predictions, hand_count):
        """
        top_k_predictions: List of (word, confidence) tuples
        hand_count: Number of hands currently detected
        """
        if not top_k_predictions or hand_count == 0:
            # If no hands are up, we reset the 'last_word' to allow 
            # the same word to be signed again after a pause.
            self.last_word = None
            return None

        best_word, best_conf = top_k_predictions[0]
        
        # --- Contextual Intelligence (Phase 2) ---
        # If we have a previous word, check if any of the top 3 
        # fits a common ASL sentence pattern better than the argmax.
        if len(self.sentence) > 0:
            prev_word = self.sentence[-1].upper().replace('1', '')
            if prev_word in self.context_rules:
                likely_words = self.context_rules[prev_word]
                # Check top 3 predictions
                for word, conf in top_k_predictions:
                    clean_word = word.upper().replace('1', '')
                    if clean_word in likely_words and conf > (best_conf * 0.7):
                        # If a likely word is even 70% as confident as the best, 
                        # we prioritize it due to context.
                        best_word = word
                        break

        # --- Debouncing & Adding ---
        if best_conf > self.confidence_threshold:
            clean_best = best_word.upper().replace('1', '')
            
            # Prevent adding the same word multiple times in a row without a hand drop
            if clean_best != self.last_word:
                self.sentence.append(clean_best)
                self.last_word = clean_best
                self.last_added_time = time.time()
                return clean_best
        
        return None

    def get_sentence_text(self):
        return " ".join(self.sentence)

    def reset(self):
        self.sentence = []
        self.last_word = None

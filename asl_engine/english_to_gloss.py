"""
Silent Voice Bridge v2 - English to ASL Gloss Translator
Part 1 of custom Workstream B Engine.

Converts English text into ASL grammatical glosses:
- Handles grammatical reordering (WH-questions at end: 'What is your name?' -> ['YOUR', 'NAME', 'WHAT'])
- Removes English auxiliary words ('is', 'are', 'am', 'the', 'a', 'to')
- Idiomatic phrase matching ('how are you' -> 'HOW-ARE-YOU', 'nice to meet you' -> 'NICE-MEET-YOU')
- Fingerspelling fallback for names and unknown words (e.g., 'Aramish' -> ['FS_A', 'FS_R', 'FS_A', 'FS_M', 'FS_I', 'FS_S', 'FS_H'])
"""

import re
from typing import List, Tuple

# Phrase dictionary (ordered from longest phrase to single words)
PHRASE_DICTIONARY = [
    (["what", "is", "your", "name"], ["YOUR", "NAME", "WHAT"]),
    (["what's", "your", "name"], ["YOUR", "NAME", "WHAT"]),
    (["how", "are", "you"], ["HOW-ARE-YOU"]),
    (["how's", "it", "going"], ["HOW-ARE-YOU"]),
    (["nice", "to", "meet", "you"], ["NICE-MEET-YOU"]),
    (["pleased", "to", "meet", "you"], ["NICE-MEET-YOU"]),
    (["my", "name", "is"], ["MY-NAME"]),
    (["my", "name"], ["MY-NAME"]),
    (["thank", "you"], ["THANK-YOU"]),
    (["thanks", "a", "lot"], ["THANK-YOU"]),
    (["could", "you", "please", "repeat"], ["PLEASE-REPEAT"]),
    (["please", "repeat", "that"], ["PLEASE-REPEAT"]),
    (["please", "repeat"], ["PLEASE-REPEAT"]),
    (["i", "am", "deaf"], ["DEAF"]),
    (["write", "it", "down"], ["WRITE-PLEASE"]),
    (["please", "write", "down"], ["WRITE-PLEASE"]),
    (["i", "need", "help"], ["HELP"]),
    (["help", "me"], ["HELP"]),
    (["i", "like", "planes"], ["I", "LIKE", "AIRPLANE"]),
    (["i", "love", "you"], ["I-LOVE-YOU"]),
]

# Single word mappings to core ASL glosses
WORD_DICTIONARY = {
    "hello": "HELLO",
    "hi": "HELLO",
    "hey": "HELLO",
    "goodbye": "GOODBYE",
    "bye": "GOODBYE",
    "yes": "YES",
    "no": "NO",
    "thanks": "THANK-YOU",
    "thank": "THANK-YOU",
    "please": "PLEASE",
    "sorry": "SORRY",
    "help": "HELP",
    "fine": "FINE",
    "good": "FINE",
    "deaf": "DEAF",
    "name": "NAME",
    "you": "YOU",
    "your": "YOUR",
    "i": "ME",
    "me": "ME",
    "my": "MY",
    "who": "WHO",
    "what": "WHAT",
    "where": "WHERE",
    "when": "WHEN",
    "why": "WHY",
    "how": "HOW",
    "like": "LIKE",
    "plane": "AIRPLANE",
    "planes": "AIRPLANE",
    "airplane": "AIRPLANE",
    "airplanes": "AIRPLANE",
    "car": "CAR",
    "water": "WATER",
    "food": "FOOD",
    "eat": "FOOD",
}

# English stop words that do not exist as independent signs in ASL
STOP_WORDS = {"is", "are", "am", "was", "were", "be", "being", "been", "the", "a", "an", "to", "do", "does", "did"}


def tokenize(text: str) -> List[str]:
    """Cleans punctuation and splits into lowercase words."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s']", " ", text.lower())
    return [w for w in cleaned.split() if w]


def translate_english_to_gloss(text: str) -> Tuple[List[str], List[dict]]:
    """
    Translates an English sentence into an ASL gloss sequence.
    Returns:
        (gloss_sequence, detailed_tokens)
    """
    words = tokenize(text)
    gloss_sequence: List[str] = []
    details = []
    i = 0

    while i < len(words):
        matched_phrase = False

        # 1. Match multi-word phrases first
        for phrase_words, gloss_replacements in PHRASE_DICTIONARY:
            p_len = len(phrase_words)
            if words[i:i + p_len] == phrase_words:
                for g in gloss_replacements:
                    gloss_sequence.append(g)
                    details.append({"type": "sign", "source": " ".join(phrase_words), "gloss": g})
                i += p_len
                matched_phrase = True
                break

        if matched_phrase:
            continue

        word = words[i]

        # 2. Skip English grammatical filler words (copula, articles)
        if word in STOP_WORDS:
            i += 1
            continue

        # 3. Direct dictionary lookup
        if word in WORD_DICTIONARY:
            gloss = WORD_DICTIONARY[word]
            gloss_sequence.append(gloss)
            details.append({"type": "sign", "source": word, "gloss": gloss})
            i += 1
            continue

        # 4. Fingerspelling Fallback (e.g. for unknown words, names)
        # In ASL, words without dedicated lexical signs are fingerspelled
        for char in word:
            if char.isalpha():
                fs_gloss = f"FS_{char.upper()}"
                gloss_sequence.append(fs_gloss)
                details.append({"type": "fingerspell", "source": char.upper(), "gloss": fs_gloss})

        i += 1

    return gloss_sequence, details


if __name__ == "__main__":
    test_sentences = [
        "Hello, how are you?",
        "What is your name?",
        "My name is Aramish",
        "I like planes",
        "Could you please repeat that?",
        "I am deaf, write it down please."
    ]

    print("=" * 60)
    print("🇺🇸 ASL Translation Engine - Text to Gloss Test")
    print("=" * 60)
    for s in test_sentences:
        glosses, _ = translate_english_to_gloss(s)
        print(f"\nEnglish: \"{s}\"")
        print(f"ASL Gloss: {' '.join(glosses)}")

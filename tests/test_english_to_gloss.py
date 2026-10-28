"""Workstream B: English to ASL gloss, including fingerspelling fallback."""
from asl_engine.english_to_gloss import translate_english_to_gloss


def glosses(text):
    return translate_english_to_gloss(text)[0]


def test_greeting_phrase():
    assert glosses("Hello, how are you?") == ["HELLO", "HOW-ARE-YOU"]


def test_single_phrase():
    assert glosses("Thank you") == ["THANK-YOU"]


def test_question_word_moves_to_end():
    # ASL puts WH-question words at the end of the sentence.
    assert glosses("What is your name?") == ["YOUR", "NAME", "WHAT"]


def test_unknown_name_is_fingerspelled():
    assert glosses("My name is Sam") == ["MY-NAME", "FS_S", "FS_A", "FS_M"]


def test_stop_words_dropped():
    assert glosses("I need help") == ["HELP"]

import json
import os
import tempfile

CARDS_FILE = os.path.join(os.path.dirname(__file__), "cards.json")

DEFAULT_CARDS = [
    {
        "question": "What is Big-O notation?",
        "answer": "Big-O describes how an algorithm's time or space grows as input size increases.",
        "category": "Algorithms",
        "difficulty": "Easy",
        "source": "Default",
        "tags": ["complexity"]
    }
]

def load_cards():
    try:
        if os.path.exists(CARDS_FILE):
            with open(CARDS_FILE, "r") as file:
                cards = json.load(file)
                if not isinstance(cards, list):
                    cards = []
        else:
            cards = []
    except (json.JSONDecodeError, OSError):
        cards = []

    # Ensure default cards are present in the stored file so built-in
    # cards can be deleted by writing them into `cards.json` on first load.
    default_questions = {d.get("question", "").strip() for d in DEFAULT_CARDS}
    existing_questions = {c.get("question", "").strip() for c in cards if isinstance(c, dict)}

    if not default_questions.intersection(existing_questions):
        # No default found in file: append defaults and persist.
        cards = cards + [d.copy() for d in DEFAULT_CARDS]
        _write_cards(cards)

    return cards


def _write_cards(cards):
    """Atomically write the provided list of cards to `CARDS_FILE`."""
    if not isinstance(cards, list):
        raise ValueError("cards must be a list")

    dirpath = os.path.dirname(CARDS_FILE) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dirpath)
    try:
        with os.fdopen(fd, "w") as tmp_file:
            json.dump(cards, tmp_file, indent=4)
        os.replace(tmp_path, CARDS_FILE)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

def save_card(card):
    required_keys = {"question", "answer", "category", "difficulty", "source", "tags"}
    if not isinstance(card, dict) or not required_keys.issubset(card.keys()):
        raise ValueError(f"Card must be a dict with keys: {sorted(required_keys)}")

    try:
        with open(CARDS_FILE, "r") as file:
            cards = json.load(file)
            if not isinstance(cards, list):
                cards = []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        cards = []

    cards.append(card)
    _write_cards(cards)

def delete_card_by_question(question):
    """
    Remove any card(s) whose question matches (trimmed exact match).
    Returns True if at least one card was removed.
    """
    try:
        with open(CARDS_FILE, "r") as f:
            cards = json.load(f)
            if not isinstance(cards, list):
                cards = []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        cards = []

    normalized = question.strip()
    new_cards = [
        c for c in cards
        if not (isinstance(c, dict) and c.get("question", "").strip() == normalized)
    ]

    if len(new_cards) == len(cards):
        return False

    _write_cards(new_cards)

    return True

def delete_card_by_index(index):
    """
    Remove a card by its index in the cards list.
    Returns True if a card was removed, False otherwise.
    """
    try:
        with open(CARDS_FILE, "r") as f:
            cards = json.load(f)
            if not isinstance(cards, list):
                cards = []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        cards = []

    if index < 0 or index >= len(cards):
        return False

    cards.pop(index)
    _write_cards(cards)

    return True
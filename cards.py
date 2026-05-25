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
    if not os.path.exists(CARDS_FILE):
        return DEFAULT_CARDS.copy()

    try:
        with open(CARDS_FILE, "r") as file:
            user_cards = json.load(file)
            if not isinstance(user_cards, list):
                user_cards = []
    except (json.JSONDecodeError, OSError):
        user_cards = []

    return DEFAULT_CARDS.copy() + user_cards

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

    # atomic write
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

    dirpath = os.path.dirname(CARDS_FILE) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dirpath)
    try:
        with os.fdopen(fd, "w") as tmp_file:
            json.dump(new_cards, tmp_file, indent=4)
        os.replace(tmp_path, CARDS_FILE)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    return True
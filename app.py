import streamlit as st
from cards import load_cards, save_card, delete_card_by_question, delete_card_by_index
import json
import requests
from groq import Groq
import os
from dotenv import load_dotenv
from difflib import SequenceMatcher

load_dotenv()

def rerun():
    """Compatibility wrapper for st.rerun() / st.experimental_rerun()"""
    if hasattr(st, 'rerun'):
        st.rerun()
    else:
        st.experimental_rerun()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_ai_response(prompt):

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content




FLASHCARDS = load_cards()

def get_next_card_index(filtered_cards, current_index, card_ratings):
    """Select next card with spaced repetition: harder cards appear more frequently."""
    if not filtered_cards:
        return 0
    
    if current_index >= len(filtered_cards):
        current_index = 0
    
    card = filtered_cards[current_index]
    question = card.get("question", "")
    
    rating = None
    for r in reversed(card_ratings):
        if r.get("question") == question:
            rating = r.get("rating")
            break
    
    if rating is None:
        return (current_index + 1) % len(filtered_cards)
    
    repeat_counts = {
        "Easy": 5,
        "Hard": 1,
        "Again": 1,
        "Good": 2
    }
    
    repeat_factor = repeat_counts.get(rating, 2)
    advance = max(1, len(filtered_cards) // repeat_factor)
    return (current_index + advance) % len(filtered_cards)

def fetch_github_file(url):
    if "github.com" in url and "/blob/" in url:
        url = url.replace("github.com", "raw.githubusercontent.com")
        url = url.replace("/blob/", "/")

    headers = {
        "User-Agent": "CS Interview Copilot student project"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.text
def fetch_reddit_post(url):
    if not url.endswith(".json"):
        url = url.rstrip("/") + ".json"

    headers = {
        "User-Agent": "CS Interview Copilot by student project"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()

    post = data[0]["data"]["children"][0]["data"]

    title = post.get("title", "")
    body = post.get("selftext", "")

    comments = data[1]["data"]["children"]

    comment_texts = []

    for comment in comments[:20]:

        comment_data = comment.get("data", {})

        author = comment_data.get("author", "")

        if author == "AutoModerator":
            continue

        body_text = comment_data.get("body", "")

        if body_text and body_text != "[deleted]" and body_text != "[removed]":
            comment_texts.append(body_text)

    comments_combined = "\n\n--- Comment ---\n\n".join(comment_texts)

    return f"""
Title:
{title}

Post:
{body}

Top Comments:
{comments_combined}
"""
st.set_page_config(
    page_title="CS Interview Copilot",
    layout="wide"
)

PAGES = [
    "Flashcards",
    "Progress Tracking",
    "Create Card",
    "AI Generate Cards",
    "Weak Cards",
    "Card Library"
]

if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = PAGES[0]
if "sidebar_nav_page" not in st.session_state:
    st.session_state["sidebar_nav_page"] = st.session_state["nav_page"]
if "top_nav_page" not in st.session_state:
    st.session_state["top_nav_page"] = st.session_state["nav_page"]


def sync_from_sidebar():
    st.session_state["nav_page"] = st.session_state["sidebar_nav_page"]
    st.session_state["top_nav_page"] = st.session_state["nav_page"]


def sync_from_top():
    st.session_state["nav_page"] = st.session_state["top_nav_page"]
    st.session_state["sidebar_nav_page"] = st.session_state["nav_page"]


st.session_state["sidebar_nav_page"] = st.session_state["nav_page"]
st.session_state["top_nav_page"] = st.session_state["nav_page"]

st.sidebar.title("Navigation")
st.sidebar.radio(
    "Go to",
    PAGES,
    key="sidebar_nav_page",
    on_change=sync_from_sidebar
)

st.title("CS Interview Copilot")

st.markdown("### Quick Navigation")
st.radio(
    "Choose a page",
    PAGES,
    horizontal=True,
    label_visibility="collapsed",
    key="top_nav_page",
    on_change=sync_from_top
)

page = st.session_state["nav_page"]

if page == "Flashcards":
    categories = sorted(set(card["category"] for card in FLASHCARDS))

    selected_category = st.selectbox(
        "Choose category",
        categories
    )

    filtered_cards = [
        card for card in FLASHCARDS
        if card["category"] == selected_category
    ]

    if not filtered_cards:
        st.info("No cards in this category. Create or generate some cards to get started!")
    else:
        if "card_index" not in st.session_state:
            st.session_state.card_index = 0

        if "card_ratings" not in st.session_state:
            st.session_state.card_ratings = []

        card = filtered_cards[st.session_state.card_index % len(filtered_cards)]

        st.caption(f"{card['category']} · {card['difficulty']}")

        st.markdown(f"## {card['question']}")

        if st.button("Reveal Answer"):
            st.session_state.show_answer = True

        if st.session_state.get("show_answer", False):
            st.markdown("### Answer")
            st.write(card["answer"])

            st.divider()

            col1, col2, col3, col4 = st.columns(4)

            def save_rating(card, rating):
                if "card_ratings" not in st.session_state:
                    st.session_state.card_ratings = []

                st.session_state.card_ratings.append({
                    "question": card["question"],
                    "answer": card["answer"],
                    "category": card["category"],
                    "difficulty": card["difficulty"],
                    "rating": rating
                })

            with col1:
                if st.button("Again"):
                    save_rating(card, "Again")

            with col2:
                if st.button("Hard"):
                    save_rating(card, "Hard")

            with col3:
                if st.button("Good"):
                    save_rating(card, "Good")

            with col4:
                if st.button("Easy"):
                    save_rating(card, "Easy")

            st.divider()

            col_next, _ = st.columns([1, 3])
            with col_next:
                if st.button("Next Card", use_container_width=True):
                    st.session_state.card_index = get_next_card_index(
                        filtered_cards,
                        st.session_state.card_index,
                        st.session_state.card_ratings
                    )
                    st.session_state.show_answer = False
                    rerun()

            st.subheader("Ask AI About This Question")

            st.text_input(
                "Ask for clarification, examples, or a simpler explanation..."
            )

if page == "Progress Tracking":
    st.subheader("Progress Tracking")

    card_ratings = st.session_state.get("card_ratings", [])
    
    if not card_ratings or len(card_ratings) == 0:
        st.info("No cards rated yet. Start reviewing cards to see your progress!")
    else:
        total_reviewed = len(card_ratings)

        again_count = sum(1 for r in card_ratings if r.get("rating") == "Again")
        hard_count = sum(1 for r in card_ratings if r.get("rating") == "Hard")
        good_count = sum(1 for r in card_ratings if r.get("rating") == "Good")
        easy_count = sum(1 for r in card_ratings if r.get("rating") == "Easy")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Reviewed", total_reviewed)

        with col2:
            st.metric("Again", again_count)

        with col3:
            st.metric("Hard", hard_count)

        with col4:
            st.metric("Good", good_count)

        col5, _ = st.columns([1, 3])
        with col5:
            st.metric("Easy", easy_count)

        st.subheader("Rating Breakdown")

        st.bar_chart({
            "Ratings": {
                "Again": again_count,
                "Hard": hard_count,
                "Good": good_count,
                "Easy": easy_count
            }
        })
if page == "Create Card":
    st.subheader("Create Your Own Card")

    new_question = st.text_area("Question")
    new_answer = st.text_area("Answer")

    new_category = st.selectbox(
        "Category",
        [
            "LeetCode",
            "Data Structures",
            "Algorithms",
            "OS",
            "Databases",
            "Networking",
            "OOP",
            "Behavioral",
            "System Design",
            "Real Interview Questions"
        ]
    )

    new_difficulty = st.selectbox(
        "Difficulty",
        ["Easy", "Medium", "Hard"]
    )

    new_tags = st.text_input(
        "Tags separated by commas",
        placeholder="Example: arrays, hashing, recursion"
    )

    if st.button("Save Card"):
        if not new_question or not new_answer:
            st.warning("Please enter both a question and an answer.")
        else:
            card = {
                "question": new_question,
                "answer": new_answer,
                "category": new_category,
                "difficulty": new_difficulty,
                "source": "User Created",
                "tags": [tag.strip() for tag in new_tags.split(",") if tag.strip()]
            }

            # check for similar questions using is_similar()
            all_cards = load_cards()
            duplicate_found = False

            for existing_card in all_cards:
                if not isinstance(existing_card, dict) or "question" not in existing_card:
                    continue

                if is_similar(card["question"], existing_card["question"]):
                    duplicate_found = True
                    break

            if duplicate_found:
                st.warning("Similar question already exists.")
            else:
                save_card(card)
                st.success("Card saved. Refresh the app to see it in your deck.")

if page == "AI Generate Cards":
    st.subheader("AI Generate Cards")

    ai_category = st.selectbox(
        "Category",
        [
            "General",
            "C",
            "LeetCode",
            "Data Structures",
            "Algorithms",
            "OS",
            "Databases",
            "Networking",
            "OOP",
            "Behavioral",
            "System Design",
            "Real Interview Questions"
        ],
        key="ai_category"
    )

    ai_difficulty = st.selectbox(
        "Difficulty",
        ["Easy", "Medium", "Hard"],
        key="ai_difficulty"
    )

    num_cards = st.slider(
        "Number of cards",
        1,
        10,
        5
    )

    topic = st.text_input(
        "Specific topic",
        placeholder="Example: recursion, hash tables, TCP/IP, dynamic programming"
    )

    if st.button("Generate AI Cards"):
        prompt = f"""
Generate {num_cards} original CS technical interview flashcards.

Category: {ai_category}
Difficulty: {ai_difficulty}
Topic: {topic}

Return valid JSON only.

Each card must have:
question, answer, category, difficulty, source, tags

Use source: "AI Generated".
"""

        with st.spinner("Generating cards..."):
            result = generate_ai_response(prompt)

        st.session_state["ai_cards_result"] = result

    if "ai_cards_result" in st.session_state and st.session_state["ai_cards_result"]:
        st.code(st.session_state["ai_cards_result"], language="json")

        try:
            clean_result = (
                st.session_state["ai_cards_result"]
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

            generated_cards = json.loads(clean_result)

            if st.button("Save AI Cards"):
                if not isinstance(generated_cards, list):
                    st.error("AI returned JSON but not a list of cards.")
                else:
                    saved = 0
                    for idx, card in enumerate(generated_cards, start=1):
                        try:
                            save_card(card)
                            saved += 1
                        except Exception as e:
                            st.error(f"Failed to save card #{idx}: {e}")

                    st.session_state["ai_cards_result"] = ""
                    if saved:
                        st.success(f"Saved {saved} AI cards.")
                    else:
                        st.warning("No AI cards were saved.")

        except json.JSONDecodeError:
            st.error("AI did not return valid JSON. Try again.")
if page == "Weak Cards":
    st.subheader("Weak Cards Review")

    weak_cards = [
        item for item in st.session_state.get("card_ratings", [])
        if item["rating"] in ["Again", "Hard"]
    ]

    if not weak_cards:
        st.info("No weak cards yet. Cards rated Again or Hard will appear here.")
    else:
        st.write(f"Weak cards: {len(weak_cards)}")

        for i, card in enumerate(weak_cards):
            with st.expander(f"{i+1}. {card['question']}"):
                st.write(card["answer"])
                st.write("Category:", card["category"])
                st.write("Last rating:", card["rating"])

def fetch_web_page(url):
    """
    Fetch a URL and return extracted plain text.
    Tries BeautifulSoup if available, otherwise falls back to a simple tag-stripper.
    """
    headers = {"User-Agent": "CS Interview Copilot student project"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    html = resp.text

    try:
        from bs4 import BeautifulSoup  # optional dependency
    except ModuleNotFoundError:
        # lightweight fallback if bs4 isn't installed
        import re
        text = re.sub(r'(?is)<script.*?>.*?</script>', '', html)
        text = re.sub(r'(?is)<style.*?>.*?</style>', '', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+\n', '\n', text)
        return text.strip()

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
        tag.decompose()

    main = soup.find('main') or soup.find('article')
    text = (main or soup).get_text(separator='\n')
    import re
    text = re.sub(r'\n\s*\n+', '\n\n', text).strip()
    return text

def is_similar(question1, question2, threshold=0.8):
    similarity = SequenceMatcher(
        None,
        question1.lower(),
        question2.lower()
    ).ratio()
    return similarity >= threshold
if page == "Card Library":
    st.subheader("Card Library")

    all_cards = load_cards()

    st.write(f"Total cards: {len(all_cards)}")

    for i, card in enumerate(all_cards):
        if not isinstance(card, dict):
            continue

        q = card.get("question", f"Card {i+1}")

        with st.expander(f"{i+1}. {q}"):
            st.write("Answer:")
            st.write(card.get("answer", ""))

            st.write("Category:", card.get("category", ""))
            st.write("Difficulty:", card.get("difficulty", ""))
            st.write("Source:", card.get("source", ""))
            st.write("Tags:", ", ".join(card.get("tags", [])))

            if st.button("Delete Card", key=f"delete_card_{i}"):
                deleted = delete_card_by_index(i)
                if deleted:
                    st.success("Card deleted.")
                    rerun()
                else:
                    st.warning("Could not delete card.")

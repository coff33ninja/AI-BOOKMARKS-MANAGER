import requests
from bs4 import BeautifulSoup
from transformers import RobertaTokenizer, RobertaForSequenceClassification
import torch
from typing import List, Optional

# Load RoBERTa model and tokenizer
ROBERTA_MODEL_PATH = "./data/custom_roberta_model"
tokenizer = RobertaTokenizer.from_pretrained(ROBERTA_MODEL_PATH, local_files_only=True)
model = RobertaForSequenceClassification.from_pretrained(
    ROBERTA_MODEL_PATH, local_files_only=True
)

# Define categories
CATEGORIES = [
    "tech",
    "news",
    "research",
    "politics",
    "tutorial",
    "development",
    "science",
    "environment",
    "reviews",
]


def fetch_page_content(url: str):
    """Fetch HTML content and text from a URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return soup, text
    except requests.RequestException:
        return None, None


def extract_title_from_url(url: str) -> Optional[str]:
    """Extract the webpage title from a URL."""
    soup, _ = fetch_page_content(url)
    return (
        soup.title.string.strip() if soup and soup.title and soup.title.string else None
    )


def suggest_tags_from_url(
    url: str, num_tags: int = 5
) -> tuple[List[str], Optional[str]]:
    """
    Suggest tags and a category using RoBERTa.
    Returns (tags, category).
    """
    _, text = fetch_page_content(url)
    if not text:
        return [], None

    # Tokenize and predict
    inputs = tokenizer(
        text, return_tensors="pt", truncation=True, max_length=512, padding=True
    )
    model.eval()
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.sigmoid(outputs.logits).squeeze().cpu().numpy()

    # Select tags and category
    tag_scores = [(label, prob) for label, prob in zip(CATEGORIES, probs)]
    tags = [
        label
        for label, prob in sorted(tag_scores, key=lambda x: x[1], reverse=True)[
            :num_tags
        ]
    ]
    category = tags[0] if tags else None

    return tags, category

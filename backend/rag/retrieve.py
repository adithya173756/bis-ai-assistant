import json
import re
from pathlib import Path
from difflib import SequenceMatcher


BASE_DIR = Path(__file__).resolve().parent.parent
CHUNKS_FILE = BASE_DIR / "data" / "processed" / "chunks.json"


def load_chunks():
    if not CHUNKS_FILE.exists():
        return []

    with open(
        CHUNKS_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def normalize(text: str):
    text = text.lower()

    text = re.sub(
        r"[^\w\s]",
        " ",
        text,
        flags=re.UNICODE,
    )

    return set(text.split())


def similarity(query: str, text: str):
    query_words = normalize(query)
    text_words = normalize(text)

    if not query_words or not text_words:
        return 0.0

    overlap = len(
        query_words & text_words
    )

    keyword_score = (
        overlap / len(query_words)
    )

    sequence_score = SequenceMatcher(
        None,
        query.lower(),
        text[:1500].lower(),
    ).ratio()

    return (
        keyword_score * 0.75
        + sequence_score * 0.25
    )


def detect_requested_standard(question: str):

    match = re.search(
        r"\bIS\s*[-:]?\s*(\d{2,6})(?:\s*:\s*(\d{4}))?\b",
        question,
        re.IGNORECASE,
    )

    if not match:
        return None

    number = match.group(1)
    year = match.group(2)

    if year:
        return f"IS {number}:{year}"

    return f"IS {number}"


def detect_topic(question: str):

    question_lower = question.lower()

    topics = {

        "hallmarking": [
            "hallmark",
            "hallmarking",
            "gold",
            "silver",
            "jewellery",
            "jewelry",
            "assaying",
            "precious metal",
        ],

        "laboratory": [
            "laboratory",
            "laboratories",
            "lab",
            "testing lab",
            "test laboratory",
            "recognized lab",
            "recognised lab",
        ],

        "product_certification": [
            "bis certification",
            "bis licence",
            "bis license",
            "certification process",
            "product certification",
            "apply for licence",
            "apply for license",
            "grant of licence",
            "grant of license",
            "conformity assessment",
        ],

        "compulsory_certification": [
            "compulsory certification",
            "mandatory certification",
            "mandatory",
            "qco",
            "quality control order",
            "compulsory",
        ],
    }

    scores = {}

    for topic, keywords in topics.items():

        score = 0

        for keyword in keywords:

            if keyword in question_lower:
                score += 1

        scores[topic] = score

    best_topic = max(
        scores,
        key=scores.get,
    )

    if scores[best_topic] == 0:
        return None

    return best_topic


def topic_score(topic, metadata):

    if not topic:
        return 0.0

    document = metadata.get(
        "document",
        "",
    ).lower()

    standard = metadata.get(
        "standard",
        "",
    ).lower()

    if topic == "hallmarking":

        if (
            "hallmark" in document
            or "hallmark" in standard
        ):
            return 1.5

    elif topic == "laboratory":

        if (
            "laboratory" in document
            or "laboratory" in standard
        ):
            return 1.5

    elif topic == "product_certification":

        if (
            "product_certification" in document
            or "product certification" in standard
            or "scheme_i" in document
            or "scheme-i" in standard
        ):
            return 1.5

    elif topic == "compulsory_certification":

        if (
            "compulsory" in document
            or "compulsory" in standard
        ):
            return 1.5

    return 0.0


def retrieve(
    question: str,
    top_k: int = 5,
):

    chunks = load_chunks()

    if not chunks:
        return []

    requested_standard = (
        detect_requested_standard(question)
    )

    requested_topic = detect_topic(
        question
    )

    scored_chunks = []

    for chunk in chunks:

        metadata = chunk.get(
            "metadata",
            {}
        )

        standard = metadata.get(
            "standard",
            ""
        )

        text = chunk.get(
            "text",
            ""
        )

        score = similarity(
            question,
            text,
        )

        # Strong boost when the user explicitly
        # asks for a particular Indian Standard.
        if requested_standard:

            standard_normalized = (
                standard
                .lower()
                .replace(" ", "")
            )

            requested_normalized = (
                requested_standard
                .lower()
                .replace(" ", "")
            )

            if (
                requested_normalized
                in standard_normalized
            ):
                score += 2.0

            elif standard_normalized.startswith(
                requested_normalized.split(":")[0]
            ):
                score += 1.0

            else:
                score *= 0.35

        # Boost the source matching the detected topic.
        score += topic_score(
            requested_topic,
            metadata,
        )

        scored_chunks.append(
            {
                "score": score,
                "chunk": chunk,
            }
        )

    scored_chunks.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    results = []

    for item in scored_chunks[:top_k]:

        chunk = item["chunk"]

        results.append(
            {
                "text": chunk.get(
                    "text",
                    ""
                ),
                "metadata": chunk.get(
                    "metadata",
                    {}
                ),
                "score": round(
                    item["score"],
                    4,
                ),
            }
        )

    return results
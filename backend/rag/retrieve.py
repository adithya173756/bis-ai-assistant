import json
import re
from pathlib import Path
from difflib import SequenceMatcher


BASE_DIR = Path(__file__).resolve().parents[1]
CHUNKS_FILE = BASE_DIR / "data" / "processed" / "chunks.json"


def load_chunks():
    if not CHUNKS_FILE.exists():
        return []

    with open(CHUNKS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text.lower().strip()
    )


def detect_intent(question: str) -> str:
    q = normalize(question)

    standard_terms = [
        "which standard",
        "what standard",
        "applicable standard",
        "applicable is",
        "indian standard",
        "is number",
        "is code",
        "standard applies",
        "standard for",
        "which is",
        "what is the is",
        "standard required",
    ]

    certification_terms = [
        "certification",
        "certify",
        "bis license",
        "bis licence",
        "apply for bis",
        "get bis",
        "bis registration",
        "conformity assessment",
        "scheme i",
        "scheme 1",
        "scheme-i",
        "license",
        "licence",
    ]

    laboratory_terms = [
        "laboratory",
        "laboratories",
        "lab",
        "testing lab",
        "test laboratory",
        "where can i test",
        "where to test",
        "testing facility",
        "testing facilities",
        "bis lab",
    ]

    hallmarking_terms = [
        "hallmark",
        "hallmarking",
        "gold hallmark",
        "silver hallmark",
        "jewellery",
        "jewelry",
        "purity mark",
        "hallmarked",
    ]

    compulsory_terms = [
        "mandatory",
        "compulsory",
        "required by law",
        "mandatory certification",
        "compulsory certification",
        "qco",
        "quality control order",
    ]

    if any(term in q for term in hallmarking_terms):
        return "hallmarking"

    if any(term in q for term in laboratory_terms):
        return "laboratory"

    if any(term in q for term in compulsory_terms):
        return "compulsory_certification"

    if any(term in q for term in certification_terms):
        return "certification"

    if any(term in q for term in standard_terms):
        return "standard"

    return "general"


def extract_is_numbers(text: str):
    patterns = [
        r"\bIS\s*\d+(?:\s*\(\s*Part\s*\d+\s*\))?(?::\s*\d{4})?\b",
        r"\bIS\s*\d+\s*:\s*\d{4}\b",
    ]

    matches = []

    for pattern in patterns:
        matches.extend(re.findall(pattern, text, flags=re.IGNORECASE))

    cleaned = []

    for match in matches:
        value = re.sub(r"\s+", " ", match).strip()

        if value.lower() not in [
            item.lower() for item in cleaned
        ]:
            cleaned.append(value)

    return cleaned


def score_text(question: str, text: str) -> float:
    q = normalize(question)
    t = normalize(text)

    if not q or not t:
        return 0.0

    q_words = set(re.findall(r"\b[a-z0-9]+\b", q))
    t_words = set(re.findall(r"\b[a-z0-9]+\b", t))

    if not q_words or not t_words:
        return 0.0

    overlap = len(q_words & t_words)

    overlap_score = overlap / max(len(q_words), 1)

    sequence_score = SequenceMatcher(
        None,
        q,
        t[:2000]
    ).ratio()

    return (
        overlap_score * 0.75
        + sequence_score * 0.25
    )


def intent_boost(intent: str, metadata: dict, text: str) -> float:
    standard = normalize(
        metadata.get("standard", "")
    )

    document_type = normalize(
        metadata.get("document_type", "")
    )

    source = normalize(
        metadata.get("source", "")
    )

    combined = normalize(
        " ".join(
            [
                standard,
                document_type,
                source,
                text,
            ]
        )
    )

    score = 0.0

    if intent == "standard":

        if "bis standard catalog" in combined:
            score += 10.0

        if "indian standard:" in combined:
            score += 8.0

        if re.search(
            r"\bis\s*\d+\s*:\s*\d{4}\b",
            combined,
            flags=re.IGNORECASE
        ):
            score += 4.0

        if "product specification" in combined:
            score += 2.0

        if "product/application" in combined:
            score += 2.0

        if "bis product certification" in combined:
            score -= 5.0

        if "laboratory" in combined:
            score -= 5.0

    elif intent == "certification":

        if "bis product certification" in combined:
            score += 5.0

        if "conformity assessment" in combined:
            score += 4.0

        if "scheme-i" in combined or "scheme i" in combined:
            score += 3.0

        if "certification" in combined:
            score += 1.5

    elif intent == "laboratory":

        if "bis laboratory" in combined:
            score += 6.0

        if "laboratory services" in combined:
            score += 4.0

        if "testing" in combined:
            score += 2.0

        if "laboratory" in combined:
            score += 1.5

    elif intent == "hallmarking":

        if "bis hallmarking" in combined:
            score += 6.0

        if "hallmarking" in combined:
            score += 4.0

        if "hallmark" in combined:
            score += 2.0

    elif intent == "compulsory_certification":

        if "bis compulsory certification" in combined:
            score += 6.0

        if "compulsory certification" in combined:
            score += 4.0

        if "quality control order" in combined:
            score += 4.0

        if "qco" in combined:
            score += 3.0

        if "mandatory" in combined:
            score += 2.0

    else:

        if "bis" in combined:
            score += 0.5

    return score


def exact_query_boost(question: str, text: str, metadata: dict) -> float:
    q = normalize(question)
    t = normalize(text)

    metadata_standard = normalize(
        metadata.get("standard", "")
    )

    score = 0.0

    # ---------------------------------------------------------
    # 1. Exact IS number requested by the user
    # ---------------------------------------------------------

    requested_is = extract_is_numbers(question)

    for is_number in requested_is:

        normalized_is = normalize(is_number)

        if normalized_is in t:
            score += 20.0

        if normalized_is in metadata_standard:
            score += 25.0

    # ---------------------------------------------------------
    # 2. Product -> Indian Standard mappings
    #
    # These are retrieval hints, not substitutes for BIS
    # standards. The final answer must still use evidence.
    # ---------------------------------------------------------

    product_standard_map = {
        "ceiling fan": [
            "is 374:2019",
            "electric ceiling type fans",
            "electric ceiling fans",
            "ceiling type fans",
        ],

        "electric ceiling fan": [
            "is 374:2019",
            "electric ceiling type fans",
            "electric ceiling fans",
        ],

        "cement": [
            "is 269:2015",
            "ordinary portland cement",
        ],

        "ordinary portland cement": [
            "is 269:2015",
            "ordinary portland cement",
        ],

        "tmt bar": [
            "is 1786:2008",
            "deformed steel bars",
            "concrete reinforcement",
        ],

        "steel bar": [
            "is 1786:2008",
            "deformed steel bars",
            "concrete reinforcement",
        ],

        "reinforcement steel": [
            "is 1786:2008",
            "deformed steel bars",
            "concrete reinforcement",
        ],

        "electrical cable": [
            "is 694:2010",
            "pvc insulated",
            "electrical cables",
        ],

        "pvc cable": [
            "is 694:2010",
            "pvc insulated",
            "electrical cables",
        ],

        "structural steel": [
            "is 2062:2025",
            "structural steel",
            "hot rolled",
        ],

        "concrete": [
            "is 456:2000",
            "plain and reinforced concrete",
        ],

        "reinforced concrete": [
            "is 456:2000",
            "plain and reinforced concrete",
        ],
    }

    # ---------------------------------------------------------
    # 3. Apply strong product matching
    # ---------------------------------------------------------

    for product, standard_terms in product_standard_map.items():

        if product in q:

            # Strongly prefer the BIS Standard Catalog
            if (
                "bis standard catalog" in metadata_standard
                or "standard catalog" in t
                or "indian standard:" in t
            ):
                score += 15.0

            for term in standard_terms:

                if term in t:
                    score += 15.0

                if term in metadata_standard:
                    score += 18.0

    # ---------------------------------------------------------
    # 4. Generic product wording
    # ---------------------------------------------------------

    product_keywords = [
        "ceiling fan",
        "electric ceiling fan",
        "electric fan",
        "cement",
        "ordinary portland cement",
        "tmt bar",
        "steel bar",
        "reinforcement steel",
        "electrical cable",
        "pvc cable",
        "structural steel",
        "concrete",
    ]

    for keyword in product_keywords:

        if keyword in q and keyword in t:
            score += 5.0

    # ---------------------------------------------------------
    # 5. Penalize generic service documents for standard-finder
    # ---------------------------------------------------------

    if detect_intent(question) == "standard":

        generic_documents = [
            "bis product certification",
            "bis laboratory",
            "laboratory services",
            "hallmarking",
            "compulsory certification",
        ]

        for generic_document in generic_documents:

            if generic_document in metadata_standard:
                score -= 8.0

    return score

def expand_catalog_records(chunks):
    """
    Split the BIS Standard Catalog into individual
    Indian Standard records so each standard can be
    ranked independently.
    """

    expanded = []

    for item in chunks:

        metadata = item.get("metadata", {})
        text = item.get("text", "")

        # Only split the curated BIS Standard Catalog.
        is_catalog = (
            "BIS_Standard_Catalog" in text
            or "BIS Standard Catalog" in metadata.get(
                "standard",
                ""
            )
        )

        if not is_catalog:
            expanded.append(item)
            continue

        # Split whenever a new Indian Standard record begins.
        records = re.split(
            r"(?=Indian Standard:\s*IS\s+\d+)",
            text,
            flags=re.IGNORECASE
        )

        for record in records:

            record = record.strip()

            if not record:
                continue

            match = re.search(
                r"Indian Standard:\s*(IS\s+\d+(?:\s*\(\s*Part\s*\d+\s*\))?(?::\s*\d{4})?(?:\s+Part\s+\d+)?)",
                record,
                flags=re.IGNORECASE
            )

            record_metadata = dict(metadata)

            if match:
                record_metadata["standard"] = (
                    match.group(1).strip()
                )

            record_metadata["document_type"] = (
                "BIS Standard Catalog Record"
            )

            expanded.append(
                {
                    "text": record,
                    "metadata": record_metadata,
                }
            )

    return expanded

def retrieve(question: str, top_k: int = 5):

    chunks = load_chunks()

    if not chunks:
        return []

    # ---------------------------------------------------------
    # Expand BIS Standard Catalog into individual records
    # ---------------------------------------------------------

    expanded_chunks = []

    for item in chunks:

        text = item.get("text", "")
        metadata = item.get("metadata", {})

        standard_name = metadata.get(
            "standard",
            ""
        )

        is_catalog = (
            "BIS_Standard_Catalog" in text
            or "BIS Standard Catalog" in text
            or "BIS_Standard_Catalog" in standard_name
            or "BIS Standard Catalog" in standard_name
        )

        if not is_catalog:
            expanded_chunks.append(item)
            continue

        # Find every individual Indian Standard record.
        matches = list(
            re.finditer(
                r"Indian Standard:\s*IS\s+",
                text,
                flags=re.IGNORECASE
            )
        )

        if not matches:
            expanded_chunks.append(item)
            continue

        for index, match in enumerate(matches):

            start = match.start()

            if index + 1 < len(matches):
                end = matches[index + 1].start()
            else:
                end = len(text)

            record = text[start:end].strip()

            if not record:
                continue

            record_metadata = dict(metadata)

            standard_match = re.search(
                r"Indian Standard:\s*(IS\s+[^\r\n]+)",
                record,
                flags=re.IGNORECASE
            )

            if standard_match:

                standard_value = (
                    standard_match.group(1)
                    .strip()
                )

                record_metadata["standard"] = (
                    standard_value
                )

            record_metadata["document_type"] = (
                "BIS Standard Catalog Record"
            )

            expanded_chunks.append(
                {
                    "text": record,
                    "metadata": record_metadata,
                }
            )

    chunks = expanded_chunks

    # ---------------------------------------------------------
    # Rank the expanded chunks
    # ---------------------------------------------------------

    intent = detect_intent(question)

    scored_results = []

    for item in chunks:

        text = item.get("text", "")
        metadata = item.get("metadata", {})

        base_score = score_text(
            question,
            text
        )

        intent_score = intent_boost(
            intent,
            metadata,
            text
        )

        exact_score = exact_query_boost(
            question,
            text,
            metadata
        )

        final_score = (
            base_score
            + intent_score
            + exact_score
        )

        scored_results.append(
            {
                "text": text,
                "metadata": metadata,
                "score": final_score,
                "intent": intent,
            }
        )

    scored_results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return scored_results[:top_k]
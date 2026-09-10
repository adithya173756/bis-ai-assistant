import os
import re
import time

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

from rag.retrieve import retrieve


# ---------------------------------------------------------
# Environment
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# FastAPI
# ---------------------------------------------------------

app = FastAPI(
    title="BIS AI Assistant API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Request model
# ---------------------------------------------------------

class AskRequest(BaseModel):
    question: str


# ---------------------------------------------------------
# Gemini client
# ---------------------------------------------------------

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    return genai.Client(api_key=api_key)


# ---------------------------------------------------------
# Basic routes
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "BIS AI Assistant API is running",
        "status": "ok"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY"))
    }


# ---------------------------------------------------------
# Gemini generation with retry
# ---------------------------------------------------------

def generate_with_retry(client, prompt: str):

    models = [
        "gemini-3.5-flash",
        "gemini-.5-flash-lite",
    ]

    retry_delays = [2, 4, 8]

    for model_name in models:

        print(f"Trying Gemini model: {model_name}")

        for attempt in range(len(retry_delays) + 1):

            try:

                print(
                    f"Gemini request attempt "
                    f"{attempt + 1}/{len(retry_delays) + 1} "
                    f"using {model_name}"
                )

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )

                if response and response.text:

                    print(
                        f"Gemini response received successfully "
                        f"from {model_name}."
                    )

                    return response.text.strip()

                print("Gemini returned an empty response.")

            except Exception as error:

                error_text = str(error)

                print(
                    f"Gemini error from {model_name}: "
                    f"{error_text}"
                )

                is_retryable = (
                    "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                    or "503" in error_text
                    or "UNAVAILABLE" in error_text
                    or "500" in error_text
                    or "INTERNAL" in error_text
                )

                if is_retryable and attempt < len(retry_delays):

                    delay = retry_delays[attempt]

                    print(
                        f"Temporary Gemini service/rate-limit error. "
                        f"Retrying in {delay} seconds..."
                    )

                    time.sleep(delay)

                    continue

                print(
                    f"{model_name} failed. "
                    f"Trying the next Gemini model..."
                )

                break

    print("All Gemini models failed.")

    return None


# ---------------------------------------------------------
# Ask BIS
# ---------------------------------------------------------

@app.post("/api/ask")
def ask_bis(request: AskRequest):

    question = request.question.strip()

    if not question:
        return {
            "answer": "Please enter a question about BIS or Indian Standards.",
            "sources": []
        }


    # -----------------------------------------------------
    # Retrieve relevant BIS information
    # -----------------------------------------------------

    retrieved = retrieve(
        question,
        top_k=5
    )

    # ---------------------------------------------------------
    # Extract structured information from the top Standard
    # Finder result
    # ---------------------------------------------------------

    standard_record = None

    if retrieved:

        top_item = retrieved[0]

        top_metadata = top_item.get(
            "metadata",
            {}
        )

        top_text = top_item.get(
            "text",
            ""
        )

        top_standard = top_metadata.get(
            "standard",
            ""
        )

        top_document_type = top_metadata.get(
            "document_type",
            ""
        )

        if (
            "Standard Catalog Record"
            in top_document_type
            and top_standard
        ):

            def extract_field(field_name):

                pattern = (
                    rf"{re.escape(field_name)}:\s*(.*)"
                )

                match = re.search(
                    pattern,
                    top_text,
                    flags=re.IGNORECASE
                )

                if match:
                    return match.group(1).strip()

                return ""

            standard_record = {
                "standard": top_standard,
                "title": extract_field("Title"),
                "product_application": extract_field(
                    "Product/Application"
                ),
                "sector": extract_field(
                    "Sector"
                ),
                "standard_type": extract_field(
                    "Standard Type"
                ),
                "certification": extract_field(
                    "Certification"
                ),
                "official_source": extract_field(
                    "Official Source"
                ),
            }


    if not retrieved:

        return {
            "answer": (
                "I could not find relevant information in the "
                "current BIS knowledge base."
            ),
            "sources": []
        }


    # -----------------------------------------------------
    # Build context
    # -----------------------------------------------------

    context_parts = []

    for index, item in enumerate(retrieved, start=1):

        metadata = item.get("metadata", {})

        standard = metadata.get(
            "standard",
            "BIS document"
        )

        clause = metadata.get(
            "clause",
            "Not identified"
        )

        page = metadata.get(
            "page",
            "Not identified"
        )

        text = item.get("text", "").strip()

        context_parts.append(
            f"""
SOURCE {index}

Standard: {standard}
Clause: {clause}
Page: {page}

Content:
{text}
"""
        )


    context = "\n".join(context_parts)

# ---------------------------------------------------------
    # Detect the type of BIS question
    # ---------------------------------------------------------

    question_lower = question.lower()

    if any(
        keyword in question_lower
        for keyword in [
            "which standard",
            "what standard",
            "indian standard",
            "is number",
            "is code",
            "standard applies",
            "applicable standard",
        ]
    ):
        question_type = "STANDARD_FINDER"

    elif any(
        keyword in question_lower
        for keyword in [
            "certification",
            "certify",
            "license",
            "licence",
            "bis mark",
            "apply for bis",
            "conformity assessment",
        ]
    ):
        question_type = "CERTIFICATION"

    elif any(
        keyword in question_lower
        for keyword in [
            "laboratory",
            "laboratories",
            "lab",
            "testing lab",
            "test facility",
            "testing",
        ]
    ):
        question_type = "LABORATORY"

    elif any(
        keyword in question_lower
        for keyword in [
            "hallmark",
            "hallmarking",
            "gold",
            "silver jewellery",
            "jewellery",
            "jewelry",
        ]
    ):
        question_type = "HALLMARKING"

    elif any(
        keyword in question_lower
        for keyword in [
            "compulsory",
            "mandatory",
            "qco",
            "quality control order",
        ]
    ):
        question_type = "COMPULSORY_CERTIFICATION"

    else:
        question_type = "GENERAL_BIS"

    structured_standard_context = ""

    if standard_record:

        structured_standard_context = f"""
STRUCTURED STANDARD FINDER RECORD

Indian Standard:
{standard_record.get("standard", "Not identified")}

Title:
{standard_record.get("title", "Not identified")}

Product/Application:
{standard_record.get("product_application", "Not identified")}

Sector:
{standard_record.get("sector", "Not identified")}

Standard Type:
{standard_record.get("standard_type", "Not identified")}

Certification:
{standard_record.get("certification", "Not identified")}

Official Source:
{standard_record.get("official_source", "Not identified")}
"""


   # -----------------------------------------------------
    # Prompt
    # -----------------------------------------------------

    prompt = f"""
You are the AI assistant for an official-source-oriented
BIS Standards and Services knowledge system.

Answer the user's question ONLY using the retrieved BIS
evidence provided below.

USER QUESTION:
{question}

QUESTION TYPE:
{question_type}

{structured_standard_context}

RETRIEVED BIS EVIDENCE:
{context}

IMPORTANT RULES:

1. Never invent an Indian Standard number.

2. Never invent a clause, page number, certification
requirement, testing requirement, or legal requirement.

3. If an exact Indian Standard is present in the
structured Standard Finder record, use that exact
standard prominently.

4. Distinguish between:
   - Indian Standard
   - Product specification
   - Code of practice
   - BIS certification
   - Conformity assessment scheme
   - Quality Control Order
   - Testing laboratory information
   - Hallmarking information

5. Do not treat BIS certification information as the
Indian Standard itself.

6. If the retrieved evidence is insufficient to identify
an exact standard, explicitly say that the available BIS
knowledge base does not contain sufficient evidence.

7. When an official source is available in the evidence,
include it.

8. Keep the answer understandable to students, industries
and consumers.

9. Do not claim that a standard is mandatory unless the
retrieved evidence supports that claim.

10. Do not use knowledge outside the retrieved BIS evidence.

11. Adapt the answer to the detected QUESTION TYPE.

STANDARD_FINDER:
Identify the most relevant Indian Standard and clearly provide
the IS number, title, product/application and supporting BIS
evidence.

CERTIFICATION:
Explain the relevant BIS certification or conformity
assessment information. Do not force an IS-number format.

LABORATORY:
Explain the relevant BIS laboratory/testing information.
Mention laboratory sources or testing guidance supported by
the evidence.

HALLMARKING:
Explain the relevant BIS hallmarking information. Do not
force an IS-number format unless the evidence specifically
supports a standard number.

COMPULSORY_CERTIFICATION:
Explain the relevant compulsory certification/QCO information.
Clearly distinguish a mandatory requirement from a general BIS
certification statement.

GENERAL_BIS:
Answer naturally using the most relevant retrieved BIS evidence.

QUESTION TYPE:

If the question asks which Indian Standard applies to a
product, use this format:

Recommended Indian Standard
[exact IS number]

Title
[exact title from retrieved evidence]

Product / Application
[product/application]

Sector
[sector]

Standard Type
[standard type]

Why this standard
[brief explanation based only on retrieved evidence]

Certification
[only supported information]

Testing
[only supported information from retrieved evidence]

Relevant BIS Evidence
[brief evidence supporting the answer]

Official BIS Source
[source URL from retrieved evidence]

For certification, laboratory, hallmarking, compulsory
certification and general BIS questions, use a natural
answer format appropriate to the question while still
providing relevant BIS evidence and source information.

Do not fabricate missing fields.

ANSWER:
"""


    # -----------------------------------------------------
    # Generate answer
    # -----------------------------------------------------

    client = get_gemini_client()

    if client is None:

        return {
            "answer": (
                "Gemini API is not configured. "
                "Please check the GEMINI_API_KEY in the backend .env file."
            ),
            "sources": []
        }


    answer = generate_with_retry(
        client,
        prompt
    )


    # -----------------------------------------------------
    # Source information
    # -----------------------------------------------------

    sources = []

    seen_sources = set()

    for item in retrieved:

        metadata = item.get("metadata", {})

        source_key = (
            metadata.get("standard", ""),
            metadata.get("clause", ""),
            metadata.get("page", ""),
        )

        if source_key in seen_sources:
            continue

        seen_sources.add(source_key)

        sources.append({
            "standard": metadata.get(
                "standard",
                "BIS document"
            ),
            "clause": metadata.get(
                "clause",
                "Not identified"
            ),
            "page": metadata.get(
                "page",
                "Not identified"
            ),
            "source": metadata.get(
                "source",
                "https://www.bis.gov.in/"
            ),
            "document_type": metadata.get(
                "document_type",
                ""
            ),
            "text": item.get(
                "text",
                ""
            ).strip()
        })


    # -----------------------------------------------------
    # Gemini failed
    # -----------------------------------------------------

    if answer is None:

        return {
            "answer": (
                "I retrieved relevant BIS information, but the "
                "AI generation service is temporarily unavailable. "
                "Please try the question again in a few seconds."
            ),
            "sources": sources
        }


    # -----------------------------------------------------
    # Successful response
    # -----------------------------------------------------

    return {
        "answer": answer,
        "sources": sources
    }
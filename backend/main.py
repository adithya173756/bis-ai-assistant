import os
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
        "gemini-3.7-flash",
        "gemini-3.5-flash",
    ]

    retry_delays = [2, 4]

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

                # Retry temporary 503 service errors
                if "503" in error_text or "UNAVAILABLE" in error_text:

                    if attempt < len(retry_delays):

                        delay = retry_delays[attempt]

                        print(
                            f"Service temporarily unavailable. "
                            f"Retrying in {delay} seconds..."
                        )

                        time.sleep(delay)

                        continue

                    print(
                        f"{model_name} unavailable after retries. "
                        f"Trying next model..."
                    )

                    break

                # Do not retry other errors
                print(
                    "Non-retryable Gemini error. "
                    "Trying next model..."
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


    # -----------------------------------------------------
    # Prompt
    # -----------------------------------------------------

    prompt = f"""
You are an AI assistant for the Bureau of Indian Standards (BIS).

IMPORTANT LANGUAGE RULES:

1. Detect the language of the user's question automatically.
2. Answer in the same language as the user's question.
3. If the user asks in Hindi, answer in Hindi.
4. If the user asks in Telugu, answer in Telugu.
5. If the user asks in English, answer in English.
6. Keep BIS names, Indian Standard numbers, technical terms,
   form numbers and official terminology unchanged where necessary.
7. Do not use Markdown headings such as ### unless they improve
   readability.
8. Use simple numbered points or short paragraphs for procedural
   answers.
9. Do not translate official Standard numbers such as IS 456:2000.

IMPORTANT RULES:

1. Do not invent BIS standards, clauses, page numbers,
   certification requirements or technical requirements.

2. If the retrieved information does not contain enough
   information to answer the question, clearly say that the
   available BIS knowledge base does not contain sufficient
   information.

3. Explain the answer in simple language suitable for
   manufacturers, industries and consumers.

4. When possible, mention the relevant Standard, Clause and
   Page exactly as provided in the retrieved context.

5. Do not claim that a clause exists if the retrieved context
   does not identify it.

6. Do not use outside knowledge.

7. Keep the answer concise but useful.

User question:

{question}

Retrieved BIS context:

{context}

Now provide the answer.
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
            )
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
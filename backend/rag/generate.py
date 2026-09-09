import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def generate_answer(question: str, retrieved_chunks: list):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return (
            "The BIS knowledge base retrieved relevant information, "
            "but the AI generation model is not configured yet."
        )

    if not retrieved_chunks:
        return (
            "I could not find enough information in the indexed "
            "BIS knowledge base to answer this question reliably."
        )

    client = OpenAI(api_key=api_key)

    context_parts = []

    for index, item in enumerate(retrieved_chunks, start=1):
        metadata = item.get("metadata", {})
        text = item.get("text", "")

        context_parts.append(
            f"""
SOURCE {index}
Standard: {metadata.get("standard", "Not available")}
Page: {metadata.get("page", "Not available")}
Clause: {metadata.get("clause", "Not identified")}
Source URL: {metadata.get("source", "")}

CONTENT:
{text}
"""
        )

    context = "\n".join(context_parts)

    prompt = f"""
You are the BIS AI Assistant.

Answer the user's question using ONLY the supplied BIS document
context.

Important rules:

1. Do not invent BIS requirements.
2. Do not invent standard numbers.
3. Do not invent clause numbers.
4. Do not invent page numbers.
5. Do not use information that is not supported by the supplied
   context.
6. If the context is insufficient, clearly say so.
7. Explain the information in simple language.
8. Do not claim that a preview document represents the complete
   Indian Standard.
9. Mention the relevant standard when supported by the context.
10. Keep the answer concise and useful.

USER QUESTION:
{question}

BIS DOCUMENT CONTEXT:
{context}
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt,
    )

    return response.output_text
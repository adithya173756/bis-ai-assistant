import json
import re
from pathlib import Path

from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parent.parent

DOCUMENTS_DIR = BASE_DIR / "data" / "documents"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

OUTPUT_FILE = PROCESSED_DIR / "chunks.json"

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def detect_language(text: str) -> str:
    devanagari = len(
        re.findall(
            r"[\u0900-\u097F]",
            text,
        )
    )

    latin = len(
        re.findall(
            r"[A-Za-z]",
            text,
        )
    )

    if devanagari > latin * 0.2:
        return "Hindi"

    return "English"


def detect_clause(text: str) -> str:
    """
    Detect a reliable clause/sub-clause number.

    This is used only for actual BIS PDF standards/
    conformity-assessment documents.

    Web FAQ pages are deliberately marked as
    'Not identified' to avoid treating FAQ numbering
    as BIS clauses.
    """

    patterns = [
        r"\bClause\s+(\d+(?:\.\d+)*)\b",
        r"^\s*(\d+(?:\.\d+)+)\s+[A-Z]",
        r"\n\s*(\d+(?:\.\d+)+)\s+[A-Z]",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.MULTILINE,
        )

        if match:
            return match.group(1)

    return "Not identified"


def get_pdf_metadata(pdf_path: Path):

    filename = pdf_path.name.lower()

    if "is_456" in filename:

        return {
            "standard": "IS 456:2000",
            "document_type": "BIS Standard Preview",
            "source": (
                "https://www.services.bis.gov.in/"
                "tmp/SR456.pdf"
            ),
        }

    if "scheme_i" in filename:

        return {
            "standard": "BIS Scheme-I",
            "document_type": "BIS Conformity Assessment",
            "source": (
                "https://www.bis.gov.in/"
                "product-certification/"
                "product-certification-process/?lang=en"
            ),
        }

    return {
        "standard": pdf_path.stem,
        "document_type": "BIS Document",
        "source": "https://www.bis.gov.in/",
    }


def get_txt_metadata(txt_path: Path):

    filename = txt_path.name

    metadata_map = {

        "BIS_Product_Certification_FAQ.txt": {
            "standard": "BIS Product Certification",
            "document_type": "BIS FAQ Web Page",
            "source": (
                "https://www.bis.gov.in/"
                "product-certification/"
                "product-certification-faq/?lang=en"
            ),
        },

        "BIS_Laboratory_FAQ.txt": {
            "standard": "BIS Laboratory Services",
            "document_type": "BIS FAQ Web Page",
            "source": (
                "https://www.bis.gov.in/"
                "laboratorys/"
                "laboratory-services-overview/"
                "laboratory-faq/?lang=en"
            ),
        },

        "BIS_Hallmarking_FAQ.txt": {
            "standard": "BIS Hallmarking",
            "document_type": "BIS FAQ Web Page",
            "source": (
                "https://www.bis.gov.in/"
                "hallmarking-overview/"
                "hallmarking-faq/?lang=en"
            ),
        },

        "BIS_Compulsory_Certification.txt": {
            "standard": "BIS Compulsory Certification",
            "document_type": "BIS Web Page",
            "source": (
                "https://www.bis.gov.in/"
                "product-certification/"
                "products-under-compulsory-certification/"
                "?lang=en"
            ),
        },
    }

    return metadata_map.get(
        filename,
        {
            "standard": txt_path.stem,
            "document_type": "BIS Web Page",
            "source": "https://www.bis.gov.in/",
        },
    )


def split_into_chunks(text: str):

    text = clean_text(text)

    if not text:
        return []

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(
            start + CHUNK_SIZE,
            text_length,
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - CHUNK_OVERLAP

    return chunks


def process_pdf(pdf_path: Path):

    print(f"Processing PDF: {pdf_path.name}")

    reader = PdfReader(pdf_path)

    doc_metadata = get_pdf_metadata(
        pdf_path
    )

    all_chunks = []

    chunk_number = 0

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):

        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""

        page_text = clean_text(page_text)

        if not page_text:
            continue

        chunks = split_into_chunks(
            page_text
        )

        for chunk_text in chunks:

            chunk_number += 1

            metadata = {
                "standard": doc_metadata[
                    "standard"
                ],
                "clause": detect_clause(
                    chunk_text
                ),
                "page": str(page_number),
                "source": doc_metadata[
                    "source"
                ],
                "document": pdf_path.name,
                "document_type": doc_metadata[
                    "document_type"
                ],
                "language": detect_language(
                    chunk_text
                ),
                "chunk": chunk_number,
            }

            all_chunks.append(
                {
                    "text": chunk_text,
                    "metadata": metadata,
                }
            )

    print(
        f"  Pages: {len(reader.pages)}"
    )

    print(
        f"  Chunks: {len(all_chunks)}"
    )

    return all_chunks


def process_txt(txt_path: Path):

    print(f"Processing TXT: {txt_path.name}")

    with open(
        txt_path,
        "r",
        encoding="utf-8",
    ) as file:

        text = file.read()

    text = clean_text(text)

    doc_metadata = get_txt_metadata(
        txt_path
    )

    chunks = split_into_chunks(
        text
    )

    all_chunks = []

    for chunk_number, chunk_text in enumerate(
        chunks,
        start=1,
    ):

        metadata = {
            "standard": doc_metadata[
                "standard"
            ],
            "clause": "Not identified",
            "page": "Web page",
            "source": doc_metadata[
                "source"
            ],
            "document": txt_path.name,
            "document_type": doc_metadata[
                "document_type"
            ],
            "language": detect_language(
                chunk_text
            ),
            "chunk": chunk_number,
        }

        all_chunks.append(
            {
                "text": chunk_text,
                "metadata": metadata,
            }
        )

    print(
        f"  Characters: {len(text)}"
    )

    print(
        f"  Chunks: {len(all_chunks)}"
    )

    return all_chunks


def main():

    print()
    print(
        "BIS KNOWLEDGE BASE INGESTION"
    )
    print("=" * 45)

    all_chunks = []

    pdf_files = sorted(
        DOCUMENTS_DIR.glob("*.pdf")
    )

    txt_files = sorted(
        DOCUMENTS_DIR.glob("*.txt")
    )

    print()
    print(
        f"PDF files found: {len(pdf_files)}"
    )

    print(
        f"TXT files found: {len(txt_files)}"
    )

    print()

    for pdf_path in pdf_files:

        try:

            chunks = process_pdf(
                pdf_path
            )

            all_chunks.extend(
                chunks
            )

        except Exception as error:

            print(
                f"ERROR processing "
                f"{pdf_path.name}: {error}"
            )

    for txt_path in txt_files:

        try:

            chunks = process_txt(
                txt_path
            )

            all_chunks.extend(
                chunks
            )

        except Exception as error:

            print(
                f"ERROR processing "
                f"{txt_path.name}: {error}"
            )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            all_chunks,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("=" * 45)

    print(
        f"TOTAL CHUNKS: {len(all_chunks)}"
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print()
    print(
        "INGESTION COMPLETE"
    )


if __name__ == "__main__":
    main()
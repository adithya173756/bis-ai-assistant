import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "documents"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


PAGES = [
    {
        "filename": "BIS_Product_Certification_FAQ.txt",
        "url": "https://www.bis.gov.in/product-certification/product-certification-faq/?lang=en",
        "title": "BIS Product Certification FAQ",
    },
    {
        "filename": "BIS_Laboratory_FAQ.txt",
        "url": "https://www.bis.gov.in/laboratorys/laboratory-services-overview/laboratory-faq/?lang=en",
        "title": "BIS Laboratory FAQ",
    },
    {
        "filename": "BIS_Hallmarking_FAQ.txt",
        "url": "https://www.bis.gov.in/hallmarking-overview/hallmarking-faq/?lang=en",
        "title": "BIS Hallmarking FAQ",
    },
    {
        "filename": "BIS_Compulsory_Certification.txt",
        "url": "https://www.bis.gov.in/product-certification/products-under-compulsory-certification/?lang=en",
        "title": "BIS Products Under Compulsory Certification",
    },
]


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def download_page(page_info):

    print(f"Downloading: {page_info['title']}")

    response = requests.get(
        page_info["url"],
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    # Remove page elements that are not useful to RAG
    for element in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "nav",
        "footer",
    ]):
        element.decompose()

    main_content = soup.find("main")

    if main_content:
        text = main_content.get_text(
            "\n",
            strip=True,
        )
    else:
        text = soup.get_text(
            "\n",
            strip=True,
        )

    text = clean_text(text)

    if len(text) < 200:
        raise ValueError(
            "Extracted page text is unexpectedly short."
        )

    output_file = OUTPUT_DIR / page_info["filename"]

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            f"TITLE: {page_info['title']}\n"
        )

        file.write(
            f"SOURCE: {page_info['url']}\n\n"
        )

        file.write(text)

    print(
        f"Saved: {output_file.name} "
        f"({len(text)} characters)"
    )


def main():

    print()
    print("BIS OFFICIAL PAGE DOWNLOAD")
    print("=" * 40)

    successful = 0

    for page in PAGES:

        try:
            download_page(page)
            successful += 1

        except Exception as error:

            print(
                f"ERROR: {page['title']}"
            )

            print(
                f"       {error}"
            )

    print()
    print(
        f"Completed: {successful}/{len(PAGES)} pages"
    )


if __name__ == "__main__":
    main()
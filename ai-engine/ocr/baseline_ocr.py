from pathlib import Path

import pytesseract
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "golden"
    / "document_001"
    / "input"
    / "document_001.png"
)

# Windows Tesseract installation path
TESSERACT_PATH = Path(
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_PATH)


def run_ocr(image_path: Path) -> str:
    """Extract text from a document image using Tesseract."""

    with Image.open(image_path) as image:
        return pytesseract.image_to_string(image)


if __name__ == "__main__":

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Document not found: {INPUT_FILE}"
        )

    if not TESSERACT_PATH.exists():
        raise FileNotFoundError(
            f"Tesseract executable not found: {TESSERACT_PATH}"
        )

    print("Tesseract:", TESSERACT_PATH)
    print("Processing:", INPUT_FILE)

    extracted_text = run_ocr(INPUT_FILE)

    print("\n===== OCR OUTPUT =====\n")
    print(extracted_text)
    print("\n===== END OCR OUTPUT =====")
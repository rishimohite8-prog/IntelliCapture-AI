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

TESSERACT_PATH = Path(
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_PATH)


def run_structured_ocr(image_path: Path):
    """
    Extract OCR words along with their position,
    dimensions and confidence.
    """

    with Image.open(image_path) as image:

        data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT
        )

    words = []

    for i, text in enumerate(data["text"]):

        text = text.strip()

        if not text:
            continue

        word = {
            "text": text,
            "confidence": float(data["conf"][i]),
            "left": int(data["left"][i]),
            "top": int(data["top"][i]),
            "width": int(data["width"][i]),
            "height": int(data["height"][i]),
        }

        words.append(word)

    return words


if __name__ == "__main__":

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Document not found: {INPUT_FILE}"
        )

    if not TESSERACT_PATH.exists():
        raise FileNotFoundError(
            f"Tesseract not found: {TESSERACT_PATH}"
        )

    print("Tesseract:", TESSERACT_PATH)
    print("Processing:", INPUT_FILE)

    words = run_structured_ocr(INPUT_FILE)

    print("\n===== STRUCTURED OCR =====\n")

    for word in words:

        print(
            f"TEXT={word['text']!r} | "
            f"CONF={word['confidence']} | "
            f"X={word['left']} | "
            f"Y={word['top']} | "
            f"W={word['width']} | "
            f"H={word['height']}"
        )

    print("\n===== END STRUCTURED OCR =====")
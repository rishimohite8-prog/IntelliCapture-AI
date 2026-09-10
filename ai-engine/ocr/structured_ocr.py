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

TESSDATA_PATH = Path(
    r"C:\Program Files\Tesseract-OCR\tessdata"
)

pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_PATH)


SUPPORTED_LANGUAGES = {
    "eng": "English",
    "deu": "German",
    "spa": "Spanish",
    "fra": "French",
    "ita": "Italian",
    "por": "Portuguese",
    "nld": "Dutch",
    "rus": "Russian",
    "ukr": "Ukrainian",
    "pol": "Polish",
    "tur": "Turkish",
    "ell": "Greek",
    "hin": "Hindi",
    "mar": "Marathi",
    "ben": "Bengali",
    "tam": "Tamil",
    "tel": "Telugu",
    "guj": "Gujarati",
    "kan": "Kannada",
    "mal": "Malayalam",
}


def validate_language(language: str) -> None:
    """
    Validate that the requested Tesseract language
    is supported and its traineddata file exists.
    """

    if language not in SUPPORTED_LANGUAGES:
        supported = ", ".join(SUPPORTED_LANGUAGES.keys())

        raise ValueError(
            f"Unsupported OCR language: {language}. "
            f"Supported languages: {supported}"
        )

    traineddata_file = (
        TESSDATA_PATH / f"{language}.traineddata"
    )

    if not traineddata_file.exists():
        raise FileNotFoundError(
            f"Tesseract language model not found: "
            f"{traineddata_file}"
        )


def _extract_words(image, language: str):
    """
    Run Tesseract structured OCR for one language.
    """

    validate_language(language)

    data = pytesseract.image_to_data(
        image,
        lang=language,
        output_type=pytesseract.Output.DICT,
    )

    words = []

    for i, text in enumerate(data["text"]):

        text = text.strip()

        if not text:
            continue

        try:
            confidence = float(data["conf"][i])
        except (TypeError, ValueError):
            confidence = 0.0

        word = {
            "text": text,
            "confidence": confidence,
            "left": int(data["left"][i]),
            "top": int(data["top"][i]),
            "width": int(data["width"][i]),
            "height": int(data["height"][i]),
        }

        words.append(word)

    return words


def _detect_language_from_words(words):
    """
    Use the existing language detector to identify
    the most likely language from OCR text.
    """

    from ocr.language_detector import detect_language_from_words

    return detect_language_from_words(words)


def detect_document_language(image):
    """
    Automatically detect the most likely document language.

    A multilingual OCR pass is performed first. The detected
    language is then returned so the document can be processed
    again using the dedicated language model.
    """

    multilingual_language = "+".join(
        SUPPORTED_LANGUAGES.keys()
    )

    data = pytesseract.image_to_data(
        image,
        lang=multilingual_language,
        output_type=pytesseract.Output.DICT,
    )

    words = []

    for i, text in enumerate(data["text"]):

        text = text.strip()

        if not text:
            continue

        try:
            confidence = float(data["conf"][i])
        except (TypeError, ValueError):
            confidence = 0.0

        words.append(
            {
                "text": text,
                "confidence": confidence,
                "left": int(data["left"][i]),
                "top": int(data["top"][i]),
                "width": int(data["width"][i]),
                "height": int(data["height"][i]),
            }
        )

    if not words:
        return {
            "language": "eng",
            "language_name": SUPPORTED_LANGUAGES["eng"],
            "confidence": 0.0,
            "matched_markers": [],
        }

    return _detect_language_from_words(words)


def run_structured_ocr(
    image_path: Path,
    language: str = None,
):
    """
    Extract OCR words along with their position,
    dimensions and confidence.

    If language is None:
        Automatically detect the document language.

    If a language is supplied:
        Use that specific Tesseract language model.
    """

    if not image_path.exists():
        raise FileNotFoundError(
            f"Document not found: {image_path}"
        )

    if not TESSERACT_PATH.exists():
        raise FileNotFoundError(
            f"Tesseract not found: {TESSERACT_PATH}"
        )

    if not TESSDATA_PATH.exists():
        raise FileNotFoundError(
            f"Tessdata directory not found: {TESSDATA_PATH}"
        )

    with Image.open(image_path) as image:

        if language is None:

            print("Detecting document language...")

            detection = detect_document_language(image)

            language = detection["language"]

            print(
                f"Detected language: "
                f"{detection['language_name']} "
                f"({language})"
            )

            print(
                f"Language confidence: "
                f"{detection['confidence']}%"
            )

        else:

            validate_language(language)

            print(
                f"OCR language: "
                f"{SUPPORTED_LANGUAGES[language]} "
                f"({language})"
            )

        words = _extract_words(
            image,
            language,
        )

    return words


def get_supported_languages():
    """
    Return all supported OCR languages.
    """

    return SUPPORTED_LANGUAGES.copy()


if __name__ == "__main__":

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Document not found: {INPUT_FILE}"
        )

    if not TESSERACT_PATH.exists():
        raise FileNotFoundError(
            f"Tesseract not found: {TESSERACT_PATH}"
        )

    if not TESSDATA_PATH.exists():
        raise FileNotFoundError(
            f"Tessdata directory not found: {TESSDATA_PATH}"
        )

    print("========================================")
    print("       INTELLICAPTURE-AI OCR")
    print("========================================")

    print()
    print("Tesseract:", TESSERACT_PATH)
    print("Tessdata :", TESSDATA_PATH)
    print("Processing:", INPUT_FILE)

    print()
    print("Automatic language detection enabled.")

    words = run_structured_ocr(
        INPUT_FILE
    )

    print()
    print("===== STRUCTURED OCR =====")
    print()

    print(f"Words detected: {len(words)}")
    print()

    for word in words:

        print(
            f"TEXT={word['text']!r} | "
            f"CONF={word['confidence']} | "
            f"X={word['left']} | "
            f"Y={word['top']} | "
            f"W={word['width']} | "
            f"H={word['height']}"
        )

    print()
    print("===== END STRUCTURED OCR =====")
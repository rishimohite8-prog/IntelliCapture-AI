from pathlib import Path
from ocr.language_detector import detect_language_from_text

tests = {
    "English": "english_test.txt",
    "German": "german_test.txt",
    "Spanish": "spanish_test.txt",
    "French": "french_test.txt",
}

for expected, filename in tests.items():
    path = Path("datasets/multilingual") / filename
    text = path.read_text(encoding="utf-8")
    result = detect_language_from_text(text)

    print(
        f"{expected}: "
        f"detected={result['language_name']} "
        f"({result['language']}) | "
        f"expected={expected}"
    )

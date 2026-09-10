from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json

BASE = Path("datasets/golden")


def get_font(size, bold=False):
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf") if bold else Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf") if bold else Path("C:/Windows/Fonts/calibri.ttf"),
    ]

    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)

    return ImageFont.load_default()


TITLE = get_font(42, True)
BODY = get_font(30)


def create_document(document_id, title, paragraphs):
    document_dir = BASE / document_id
    input_dir = document_dir / "input"

    input_dir.mkdir(parents=True, exist_ok=True)

    width = 1800
    height = 1500

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    y = 70

    draw.text(
        (100, y),
        title,
        fill="black",
        font=TITLE
    )

    y += 100

    draw.line(
        (100, y, width - 100, y),
        fill="black",
        width=3
    )

    y += 60

    for paragraph in paragraphs:

        draw.text(
            (120, y),
            paragraph,
            fill="black",
            font=BODY
        )

        y += 70

    output_path = input_dir / f"{document_id}.png"
    image.save(output_path)

    return output_path


# ============================================================
# DOCUMENT 007
# German FREE-FORM document
# ============================================================

document_007_paragraphs = [
    "Rahul Patil besuchte das Geschäft am 14/08/2026.",
    "Er kaufte einen Laptop für 55000.",
    "Die Zahlung wurde abgeschlossen.",
    "",
    "Priya Shah besuchte das Geschäft am 15/08/2026.",
    "Sie kaufte ein Keyboard für 4500.",
    "Die Zahlung wurde abgeschlossen.",
]


expected_007 = {
    "records": [
        {
            "customer": "Rahul Patil",
            "date": "14/08/2026",
            "product": "Laptop",
            "amount": "55000"
        },
        {
            "customer": "Priya Shah",
            "date": "15/08/2026",
            "product": "Keyboard",
            "amount": "4500"
        }
    ]
}


# ============================================================
# DOCUMENT 008
# Spanish FREE-FORM document
# ============================================================

document_008_paragraphs = [
    "Rahul Patil visitó la tienda el 16/08/2026.",
    "Compró un Monitor por 32000.",
    "El pago fue completado correctamente.",
    "",
    "Neha Joshi visitó la tienda el 17/08/2026.",
    "Compró un Keyboard por 4500.",
    "El pago fue completado correctamente.",
]


expected_008 = {
    "records": [
        {
            "customer": "Rahul Patil",
            "date": "16/08/2026",
            "product": "Monitor",
            "amount": "32000"
        },
        {
            "customer": "Neha Joshi",
            "date": "17/08/2026",
            "product": "Keyboard",
            "amount": "4500"
        }
    ]
}


# Create both documents
create_document(
    "document_007",
    "KAUFNOTIZEN",
    document_007_paragraphs
)

create_document(
    "document_008",
    "REGISTRO DE COMPRAS",
    document_008_paragraphs
)


# Create expected files
for document_id, expected in [
    ("document_007", expected_007),
    ("document_008", expected_008),
]:

    expected_path = BASE / document_id / "expected.json"

    expected_path.write_text(
        json.dumps(
            expected,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


print()
print("========================================")
print("DOCUMENT 007 + 008 RECREATED")
print("========================================")
print()
print("document_007 -> German FREE_FORM")
print("document_008 -> Spanish FREE_FORM")
print()
print("Input images and expected.json files updated.")
print()
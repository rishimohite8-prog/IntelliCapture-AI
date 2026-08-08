from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "golden"
    / "document_001"
    / "input"
    / "document_001.png"
)


def main():

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Create document
    image = Image.new(
        "RGB",
        (1600, 900),
        "white"
    )

    draw = ImageDraw.Draw(image)

    # Windows fonts
    try:
        title_font = ImageFont.truetype(
            "C:/Windows/Fonts/arialbd.ttf",
            44
        )

        header_font = ImageFont.truetype(
            "C:/Windows/Fonts/arialbd.ttf",
            28
        )

        body_font = ImageFont.truetype(
            "C:/Windows/Fonts/arial.ttf",
            27
        )

    except OSError:

        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    draw.text(
        (70, 50),
        "SALES REGISTER",
        fill="black",
        font=title_font
    )

    # --------------------------------------------------------
    # TABLE HEADER
    # --------------------------------------------------------

    headers = [
        "No",
        "Customer Name",
        "Date",
        "Product",
        "Quantity",
        "Amount"
    ]

    x_positions = [
        80,
        180,
        520,
        760,
        1080,
        1250
    ]

    y_header = 150

    for x, header in zip(
        x_positions,
        headers
    ):

        draw.text(
            (x, y_header),
            header,
            fill="black",
            font=header_font
        )

    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------

    rows = [
        [
            "1",
            "Rahul Patil",
            "01/08/2026",
            "Laptop",
            "1",
            "55000"
        ],
        [
            "2",
            "Amit Sharma",
            "02/08/2026",
            "Monitor",
            "2",
            "24000"
        ],
        [
            "3",
            "Priya Shah",
            "03/08/2026",
            "Keyboard",
            "3",
            "4500"
        ],
        [
            "4",
            "Neha Joshi",
            "04/08/2026",
            "Mouse",
            "2",
            "1600"
        ],
        [
            "5",
            "Vikas More",
            "05/08/2026",
            "Printer",
            "1",
            "12500"
        ]
    ]

    y = 220

    for row in rows:

        for x, value in zip(
            x_positions,
            row
        ):

            draw.text(
                (x, y),
                value,
                fill="black",
                font=body_font
            )

        y += 90

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    draw.text(
        (70, 720),
        "Golden Document #001 - Baseline Test Input",
        fill="black",
        font=body_font
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    image.save(
        OUTPUT_FILE,
        format="PNG"
    )

    print()
    print("========================================")
    print("       DOCUMENT #001 CREATED")
    print("========================================")
    print()

    print(
        f"Saved to:\n{OUTPUT_FILE}"
    )

    print()


if __name__ == "__main__":
    main()
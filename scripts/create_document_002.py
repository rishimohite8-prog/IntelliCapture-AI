from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "golden"
    / "document_002"
    / "input"
    / "document_002.png"
)


def main():

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Create white document
    image = Image.new(
        "RGB",
        (1400, 700),
        "white"
    )

    draw = ImageDraw.Draw(image)

    # Fonts
    try:
        title_font = ImageFont.truetype(
            "C:/Windows/Fonts/arialbd.ttf",
            42
        )

        body_font = ImageFont.truetype(
            "C:/Windows/Fonts/arial.ttf",
            30
        )

    except OSError:

        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    # Document title
    draw.text(
        (80, 60),
        "SALES REGISTER",
        fill="black",
        font=title_font
    )

    # Sales records
    records = [
        "Amit Joshi    05/08/2026    Monitor     15000",
        "Sneha Patil   06/08/2026    Mouse        1200",
        "Vikas Shah    07/08/2026    Keyboard     2500",
    ]

    y_position = 160

    for record in records:

        draw.text(
            (80, y_position),
            record,
            fill="black",
            font=body_font
        )

        y_position += 80

    # Footer
    draw.text(
        (80, 480),
        "Golden Document #002 - Baseline Test Input",
        fill="black",
        font=body_font
    )

    # Save image
    image.save(
        OUTPUT_FILE,
        format="PNG"
    )

    print("========================================")
    print("DOCUMENT #002 CREATED")
    print("========================================")
    print()
    print(f"Saved to:")
    print(OUTPUT_FILE)
    print()


if __name__ == "__main__":
    main()
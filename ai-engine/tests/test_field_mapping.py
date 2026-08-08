from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(
    0,
    str(PROJECT_ROOT / "ai-engine")
)


from ocr.structured_ocr import run_structured_ocr
from extraction.row_detector import group_words_into_rows
from extraction.column_detector import row_to_columns
from extraction.field_mapper import map_row_to_fields


INPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "golden"
    / "document_001"
    / "input"
    / "document_001.png"
)


def main():

    print("Running field mapping test...")

    words = run_structured_ocr(INPUT_FILE)

    rows = group_words_into_rows(words)

    print(f"\nDetected rows: {len(rows)}")

    print("\n===== FIELD MAPPING =====")

    for index, row in enumerate(rows, start=1):

        columns = row_to_columns(row)

        mapped = map_row_to_fields(columns)

        print(f"\nRow {index}:")
        print("Columns:", columns)
        print("Mapped:", mapped)

    print("\n===== END FIELD MAPPING =====")


if __name__ == "__main__":
    main()
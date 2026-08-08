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
from validation.record_validator import validate_record


INPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "golden"
    / "document_001"
    / "input"
    / "document_001.png"
)


def main():

    print("Running validation test...")

    words = run_structured_ocr(INPUT_FILE)

    rows = group_words_into_rows(words)

    valid_records = 0

    print("\n===== VALIDATION RESULTS =====")

    for index, row in enumerate(rows, start=1):

        columns = row_to_columns(row)

        record = map_row_to_fields(columns)

        if record is None:
            print(
                f"\nRow {index}: Not a data record"
            )
            continue

        errors = validate_record(record)

        print(f"\nRow {index}:")
        print("Record:", record)

        if errors:
            print("Status: INVALID")
            print("Errors:", errors)
        else:
            print("Status: VALID")
            valid_records += 1

    print(
        f"\nValid records: {valid_records}"
    )

    print("\n===== END VALIDATION =====")


if __name__ == "__main__":
    main()
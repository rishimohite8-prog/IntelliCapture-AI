import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

AI_ENGINE_PATH = PROJECT_ROOT / "ai-engine"
if str(AI_ENGINE_PATH) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_PATH))

from ocr.structured_ocr import run_structured_ocr
from extraction.row_detector import group_words_into_rows
from extraction.column_detector import row_to_columns
from extraction.field_mapper import map_row_to_fields
from extraction.form_extractor import extract_form_fields
from extraction.free_form_extractor import extract_free_form_records
from validation.record_validator import validate_record
from confidence.confidence_engine import (
    build_record_confidence,
    build_document_confidence_summary
)
from layout.layout_analyzer import analyze_layout


def process_document(input_file: Path) -> dict:
    print("Running structured OCR...")

    words = run_structured_ocr(input_file)

    print(f"OCR words detected: {len(words)}")

    print()
    print("Detecting document language...")

    from ocr.language_detector import detect_language_from_words

    language_detection = detect_language_from_words(words)

    print(
        f"Detected language: "
        f"{language_detection['language_name']} "
        f"({language_detection['language']})"
    )

    print(
        f"Language confidence: "
        f"{language_detection['confidence']}%"
    )

    print(
        f"Detected script: "
        f"{language_detection['script']} "
        f"({language_detection['script_confidence']}%)"
    )

    if language_detection["matched_markers"]:
        print(
            "Language markers: "
            + ", ".join(
                language_detection["matched_markers"]
            )
        )

    print()
    print("Analyzing document layout...")

    layout_analysis = analyze_layout(words)

    layout_type = layout_analysis["layout_type"]
    layout_statistics = layout_analysis["statistics"]

    print(f"Detected layout: {layout_type}")
    print(f"Layout statistics: {layout_statistics}")

    rows = group_words_into_rows(words)

    print(f"Rows detected: {len(rows)}")

    records = []
    confidence_records = []

    if layout_type == "FORM":

        print()
        print("FORM layout detected.")
        print("Extracting form fields...")

        form_result = extract_form_fields(rows)

        form_fields = form_result.get(
            "fields",
            {}
        )

        print(
            f"Form fields extracted: "
            f"{len(form_fields)}"
        )

        record = {}

        field_mapping = {
            "customer": "customer",
            "date": "date",
            "product": "product",
            "amount": "amount",
        }

        for record_field, form_field in field_mapping.items():

            if form_field in form_fields:

                record[record_field] = (
                    form_fields[
                        form_field
                    ]["value"]
                )

        if record:

            errors = validate_record(record)

            if errors:

                print("FORM RECORD: INVALID")

                for error in errors:
                    print(f"  - {error}")

            else:

                records.append(record)

                print("FORM RECORD: VALID")

                form_row = []

                for line in rows:
                    form_row.extend(line)

                confidence = build_record_confidence(
                    record,
                    form_row
                )

                confidence_records.append(
                    confidence
                )

                print(
                    f"  Confidence: "
                    f"{confidence['confidence']}%"
                )

                print(
                    f"  Quality: "
                    f"{confidence['quality']}"
                )

                fields = confidence.get(
                    "fields",
                    {}
                )

                for field_name, field_data in fields.items():

                    print(
                        f"    {field_name}: "
                        f"{field_data['confidence']}% "
                        f"({field_data['quality']})"
                    )

                if confidence["requires_review"]:
                    print("  REVIEW REQUIRED")

    elif layout_type == "FREE_FORM":

        print()
        print("FREE_FORM layout detected.")
        print("Extracting natural-language records...")

        free_form_lines = []

        for line in rows:

            line_text = " ".join(
                str(word.get("text", ""))
                for word in line
                if word.get("text")
            ).strip()

            if line_text:
                free_form_lines.append(line_text)

        free_form_text = "\n".join(
            free_form_lines
        )

        print()
        print("Free-form text:")
        print(free_form_text)

        free_form_records = extract_free_form_records(
            free_form_text
        )

        print(
            f"Free-form records detected: "
            f"{len(free_form_records)}"
        )

        all_words = []

        for line in rows:
            all_words.extend(line)

        for index, record in enumerate(
            free_form_records,
            start=1
        ):

            errors = validate_record(record)

            if errors:

                print(
                    f"Free-form Record {index}: INVALID"
                )

                for error in errors:
                    print(
                        f"  - {error}"
                    )

                continue

            records.append(record)

            print(
                f"Free-form Record {index}: VALID"
            )

            print(
                f"  Customer: "
                f"{record['customer']}"
            )

            print(
                f"  Date: "
                f"{record['date']}"
            )

            print(
                f"  Product: "
                f"{record['product']}"
            )

            print(
                f"  Amount: "
                f"{record['amount']}"
            )

            confidence = build_record_confidence(
                record,
                all_words
            )

            confidence_records.append(
                confidence
            )

            print(
                f"  Confidence: "
                f"{confidence['confidence']}%"
            )

            print(
                f"  Quality: "
                f"{confidence['quality']}"
            )

            fields = confidence.get(
                "fields",
                {}
            )

            for field_name, field_data in fields.items():

                print(
                    f"    {field_name}: "
                    f"{field_data['confidence']}% "
                    f"({field_data['quality']})"
                )

            if confidence["requires_review"]:

                print(
                    "  REVIEW REQUIRED"
                )

    else:

        print()
        print(
            "Using row/column extraction pipeline..."
        )

        for index, row in enumerate(
            rows,
            start=1
        ):

            columns = row_to_columns(row)

            record = map_row_to_fields(
                columns
            )

            if record is None:
                continue

            errors = validate_record(record)

            if errors:

                print(
                    f"Row {index}: INVALID"
                )

                for error in errors:
                    print(
                        f"  - {error}"
                    )

                continue

            records.append(record)

            print(
                f"Row {index}: VALID"
            )

            confidence = build_record_confidence(
                record,
                row
            )

            confidence_records.append(
                confidence
            )

            print(
                f"  Confidence: "
                f"{confidence['confidence']}%"
            )

            print(
                f"  Quality: "
                f"{confidence['quality']}"
            )

            fields = confidence.get(
                "fields",
                {}
            )

            for field_name, field_data in fields.items():

                print(
                    f"    {field_name}: "
                    f"{field_data['confidence']}% "
                    f"({field_data['quality']})"
                )

            if confidence["requires_review"]:
                print(
                    "  REVIEW REQUIRED"
                )

    confidence_summary = (
        build_document_confidence_summary(
            confidence_records
        )
    )

    result = {
        "document_id": input_file.stem,

        "language": {
            "code": language_detection["language"],
            "name": language_detection["language_name"],
            "confidence": language_detection["confidence"],
            "script": language_detection["script"],
            "script_confidence": language_detection[
                "script_confidence"
            ],
            "matched_markers": language_detection[
                "matched_markers"
            ],
        },

        "layout": {
            "type": layout_type,
            "statistics": layout_statistics
        },

        "records": records,

        "confidence": {
            "records": confidence_records,
            "summary": confidence_summary
        }
    }

    if layout_type == "FORM":

        result["form"] = {
            "fields": form_fields,
            "field_count": len(form_fields)
        }

    if layout_type == "FREE_FORM":

        result["free_form"] = {
            "text": free_form_text,
            "record_count": len(records)
        }

    return result


def save_json(
    data: dict,
    output_file: Path
) -> None:

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_file.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )


def main():

    print()
    print("========================================")
    print("       INTELLICAPTURE-AI PIPELINE")
    print("========================================")
    print()

    document_id = input(
        "Enter document ID "
        "(example: document_001): "
    ).strip()

    if not document_id:
        raise ValueError(
            "Document ID cannot be empty."
        )

    document_folder = (
        PROJECT_ROOT
        / "datasets"
        / "golden"
        / document_id
    )

    input_file = (
        document_folder
        / "input"
        / f"{document_id}.png"
    )

    output_file = (
        document_folder
        / "output"
        / f"{document_id}.json"
    )

    if not document_folder.exists():

        raise FileNotFoundError(
            f"Document folder not found:\n"
            f"{document_folder}"
        )

    if not input_file.exists():

        raise FileNotFoundError(
            f"Input image not found:\n"
            f"{input_file}"
        )

    print()
    print(f"Document : {document_id}")
    print(f"Input    : {input_file}")
    print(f"Output   : {output_file}")
    print()

    result = process_document(
        input_file
    )

    save_json(
        result,
        output_file
    )

    summary = result[
        "confidence"
    ]["summary"]

    print()
    print("========================================")
    print("       EXTRACTION COMPLETE")
    print("========================================")
    print()

    print(
        f"Language detected: "
        f"{result['language']['name']} "
        f"({result['language']['code']})"
    )

    print(
        f"Language confidence: "
        f"{result['language']['confidence']}%"
    )

    print(
        f"Layout detected: "
        f"{result['layout']['type']}"
    )

    print(
        f"Records extracted: "
        f"{len(result['records'])}"
    )

    print(
        f"Average confidence: "
        f"{summary['average_confidence']}%"
    )

    print(
        f"Quality: "
        f"{summary['quality']}"
    )

    print(
        f"Records requiring review: "
        f"{summary['records_review_required']}"
    )

    print(
        f"Fields requiring review: "
        f"{summary['fields_review_required']}"
    )

    if result["layout"]["type"] == "FORM":

        print(
            f"Form fields extracted: "
            f"{result['form']['field_count']}"
        )

    if result["layout"]["type"] == "FREE_FORM":

        print(
            f"Free-form records extracted: "
            f"{result['free_form']['record_count']}"
        )

    print()
    print("Output saved to:")
    print(output_file)
    print()


if __name__ == "__main__":
    main()

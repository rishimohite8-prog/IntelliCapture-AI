import json
import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]


# ============================================================
# ADD AI ENGINE TO PYTHON PATH
# ============================================================

AI_ENGINE_PATH = (
    PROJECT_ROOT
    / "ai-engine"
)

if str(AI_ENGINE_PATH) not in sys.path:

    sys.path.insert(
        0,
        str(AI_ENGINE_PATH)
    )


# ============================================================
# INTELLICAPTURE MODULES
# ============================================================

from ocr.structured_ocr import (
    run_structured_ocr
)

from extraction.row_detector import (
    group_words_into_rows
)

from extraction.column_detector import (
    row_to_columns
)

from extraction.field_mapper import (
    map_row_to_fields
)

from validation.record_validator import (
    validate_record
)

from confidence.confidence_engine import (
    build_record_confidence,
    build_document_confidence_summary
)


# ============================================================
# PROCESS DOCUMENT
# ============================================================

def process_document(
    input_file: Path
) -> dict:
    """
    Run the complete IntelliCapture extraction pipeline.

    The existing records structure remains unchanged.

    Additional confidence information is returned separately.
    """

    print(
        "Running structured OCR..."
    )


    # --------------------------------------------------------
    # STEP 1: OCR
    # --------------------------------------------------------

    words = run_structured_ocr(
        input_file
    )

    print(
        f"OCR words detected: {len(words)}"
    )


    # --------------------------------------------------------
    # STEP 2: ROW DETECTION
    # --------------------------------------------------------

    rows = group_words_into_rows(
        words
    )

    print(
        f"Rows detected: {len(rows)}"
    )


    # --------------------------------------------------------
    # STEP 3: FIELD EXTRACTION
    # --------------------------------------------------------

    records = []

    confidence_records = []

    for index, row in enumerate(
        rows,
        start=1
    ):

        # ----------------------------------------------------
        # Convert OCR row into columns
        # ----------------------------------------------------

        columns = row_to_columns(
            row
        )


        # ----------------------------------------------------
        # Convert columns into structured fields
        # ----------------------------------------------------

        record = map_row_to_fields(
            columns
        )


        # ----------------------------------------------------
        # Ignore headers, footers and invalid rows
        # ----------------------------------------------------

        if record is None:

            continue


        # ----------------------------------------------------
        # STEP 4: VALIDATION
        # ----------------------------------------------------

        errors = validate_record(
            record
        )


        if errors:

            print(
                f"Row {index}: INVALID"
            )

            for error in errors:

                print(
                    f"  - {error}"
                )

            continue


        # ----------------------------------------------------
        # Valid record
        # ----------------------------------------------------

        records.append(
            record
        )


        print(
            f"Row {index}: VALID"
        )


        # ----------------------------------------------------
        # STEP 5: CONFIDENCE
        # ----------------------------------------------------

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


    # --------------------------------------------------------
    # STEP 6: DOCUMENT CONFIDENCE
    # --------------------------------------------------------

    confidence_summary = (
        build_document_confidence_summary(
            confidence_records
        )
    )


    # --------------------------------------------------------
    # STEP 7: FINAL RESULT
    # --------------------------------------------------------

    result = {

        "document_id": input_file.stem,

        "records": records,

        "confidence": {

            "records": confidence_records,

            "summary": confidence_summary
        }
    }


    return result


# ============================================================
# SAVE JSON
# ============================================================

def save_json(
    data: dict,
    output_file: Path
) -> None:
    """
    Save extracted data as formatted JSON.
    """

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


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print(
        "========================================"
    )

    print(
        "       INTELLICAPTURE-AI PIPELINE"
    )

    print(
        "========================================"
    )

    print()


    # --------------------------------------------------------
    # ASK DOCUMENT
    # --------------------------------------------------------

    document_id = input(
        "Enter document ID "
        "(example: document_001): "
    ).strip()


    if not document_id:

        raise ValueError(
            "Document ID cannot be empty."
        )


    # --------------------------------------------------------
    # DOCUMENT DIRECTORY
    # --------------------------------------------------------

    document_folder = (
        PROJECT_ROOT
        / "datasets"
        / "golden"
        / document_id
    )


    # --------------------------------------------------------
    # INPUT FILE
    # --------------------------------------------------------

    input_file = (
        document_folder
        / "input"
        / f"{document_id}.png"
    )


    # --------------------------------------------------------
    # OUTPUT FILE
    # --------------------------------------------------------

    output_file = (
        document_folder
        / "output"
        / f"{document_id}.json"
    )


    # --------------------------------------------------------
    # CHECK DOCUMENT
    # --------------------------------------------------------

    if not document_folder.exists():

        raise FileNotFoundError(
            f"Document folder not found:\n"
            f"{document_folder}"
        )


    # --------------------------------------------------------
    # CHECK IMAGE
    # --------------------------------------------------------

    if not input_file.exists():

        raise FileNotFoundError(
            f"Input image not found:\n"
            f"{input_file}"
        )


    print()

    print(
        f"Document : {document_id}"
    )

    print(
        f"Input    : {input_file}"
    )

    print(
        f"Output   : {output_file}"
    )

    print()


    # --------------------------------------------------------
    # RUN PIPELINE
    # --------------------------------------------------------

    result = process_document(
        input_file
    )


    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    save_json(
        result,
        output_file
    )


    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print()

    print(
        "========================================"
    )

    print(
        "       EXTRACTION COMPLETE"
    )

    print(
        "========================================"
    )

    print()

    print(
        f"Records extracted: "
        f"{len(result['records'])}"
    )

    print(
        f"Average confidence: "
        f"{result['confidence']['summary']['average_confidence']}%"
    )

    print(
        f"Quality: "
        f"{result['confidence']['summary']['quality']}"
    )

    print()

    print(
        "Output saved to:"
    )

    print(
        output_file
    )

    print()


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
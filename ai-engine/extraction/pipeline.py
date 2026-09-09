import json
import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)


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

from extraction.form_extractor import (
    extract_form_fields
)

from validation.record_validator import (
    validate_record
)

from confidence.confidence_engine import (
    build_record_confidence,
    build_document_confidence_summary
)

from layout.layout_analyzer import (
    analyze_layout
)


# ============================================================
# PROCESS DOCUMENT
# ============================================================

def process_document(
    input_file: Path
) -> dict:
    """
    Run the complete IntelliCapture extraction pipeline.

    Pipeline:

        Image
          ↓
        OCR
          ↓
        Layout Analysis
          ↓
        Layout-specific Extraction
          ↓
        Validation
          ↓
        Confidence Analysis
          ↓
        Structured Result
    """

    print(
        "Running structured OCR..."
    )


    # ========================================================
    # STEP 1: OCR
    # ========================================================

    words = run_structured_ocr(
        input_file
    )

    print(
        f"OCR words detected: {len(words)}"
    )


    # ========================================================
    # STEP 2: LAYOUT ANALYSIS
    # ========================================================

    print(
        "Analyzing document layout..."
    )

    layout_analysis = analyze_layout(
        words
    )

    layout_type = layout_analysis[
        "layout_type"
    ]

    layout_statistics = layout_analysis[
        "statistics"
    ]

    print(
        f"Detected layout: {layout_type}"
    )

    print(
        f"Layout statistics: "
        f"{layout_statistics}"
    )


    # ========================================================
    # STEP 3: ROW DETECTION
    # ========================================================

    rows = group_words_into_rows(
        words
    )

    print(
        f"Rows detected: {len(rows)}"
    )


    # ========================================================
    # STORAGE
    # ========================================================

    records = []

    confidence_records = []


    # ========================================================
    # FORM DOCUMENT
    # ========================================================

    if layout_type == "FORM":

        print()
        print(
            "FORM layout detected."
        )

        print(
            "Extracting form fields..."
        )


        # ----------------------------------------------------
        # EXTRACT FORM FIELDS
        # ----------------------------------------------------

        form_result = extract_form_fields(
            rows
        )

        form_fields = form_result.get(
            "fields",
            {}
        )


        print(
            f"Form fields extracted: "
            f"{len(form_fields)}"
        )


        # ====================================================
        # CONVERT FORM FIELDS INTO RECORD
        # ====================================================

        record = {}


        field_mapping = {
            "customer": "Customer",
            "date": "Date",
            "product": "Product",
            "amount": "Amount",
        }


        for record_field, form_field in field_mapping.items():

            if form_field in form_fields:

                record[
                    record_field
                ] = form_fields[
                    form_field
                ][
                    "value"
                ]


        # ====================================================
        # VALIDATE FORM RECORD
        # ====================================================

        if record:

            errors = validate_record(
                record
            )


            if errors:

                print(
                    "FORM RECORD: INVALID"
                )

                for error in errors:

                    print(
                        f"  - {error}"
                    )


            else:

                records.append(
                    record
                )

                print(
                    "FORM RECORD: VALID"
                )


                # =================================================
                # FORM CONFIDENCE
                # =================================================

                # group_words_into_rows() returns:
                #
                # [
                #     [word, word, word],
                #     [word, word, word],
                #     ...
                # ]
                #
                # Therefore each line is already a list of
                # OCR words. Flatten all rows into one list.

                form_row = []

                for line in rows:

                    form_row.extend(
                        line
                    )


                confidence = (
                    build_record_confidence(
                        record,
                        form_row
                    )
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


                # ------------------------------------------------
                # FIELD CONFIDENCE
                # ------------------------------------------------

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


                # ------------------------------------------------
                # REVIEW FLAG
                # ------------------------------------------------

                if confidence[
                    "requires_review"
                ]:

                    print(
                        "  REVIEW REQUIRED"
                    )


    # ========================================================
    # TABLE / ROW REGISTER
    # ========================================================

    else:

        print()
        print(
            "Using row/column extraction pipeline..."
        )


        for index, row in enumerate(
            rows,
            start=1
        ):

            # ------------------------------------------------
            # COLUMN DETECTION
            # ------------------------------------------------

            columns = row_to_columns(
                row
            )


            # ------------------------------------------------
            # FIELD MAPPING
            # ------------------------------------------------

            record = map_row_to_fields(
                columns
            )


            # ------------------------------------------------
            # IGNORE NON-DATA ROWS
            # ------------------------------------------------

            if record is None:
                continue


            # =================================================
            # VALIDATION
            # =================================================

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


            # =================================================
            # VALID RECORD
            # =================================================

            records.append(
                record
            )


            print(
                f"Row {index}: VALID"
            )


            # =================================================
            # CONFIDENCE ANALYSIS
            # =================================================

            confidence = (
                build_record_confidence(
                    record,
                    row
                )
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


            # ------------------------------------------------
            # FIELD CONFIDENCE
            # ------------------------------------------------

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


            # ------------------------------------------------
            # REVIEW FLAG
            # ------------------------------------------------

            if confidence[
                "requires_review"
            ]:

                print(
                    "  REVIEW REQUIRED"
                )


    # ========================================================
    # DOCUMENT CONFIDENCE
    # ========================================================

    confidence_summary = (
        build_document_confidence_summary(
            confidence_records
        )
    )


    # ========================================================
    # FINAL RESULT
    # ========================================================

    result = {

        "document_id": input_file.stem,

        # ----------------------------------------------------
        # DOCUMENT LAYOUT
        # ----------------------------------------------------

        "layout": {

            "type": layout_type,

            "statistics": layout_statistics
        },

        # ----------------------------------------------------
        # STRUCTURED RECORDS
        # ----------------------------------------------------

        "records": records,

        # ----------------------------------------------------
        # CONFIDENCE DATA
        # ----------------------------------------------------

        "confidence": {

            "records": confidence_records,

            "summary": confidence_summary
        }
    }


    # ========================================================
    # FORM-SPECIFIC DATA
    # ========================================================

    if layout_type == "FORM":

        result[
            "form"
        ] = {

            "fields": form_fields,

            "field_count": len(
                form_fields
            )
        }


    return result


# ============================================================
# SAVE JSON
# ============================================================

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


    # ========================================================
    # ASK DOCUMENT
    # ========================================================

    document_id = input(
        "Enter document ID "
        "(example: document_001): "
    ).strip()


    if not document_id:

        raise ValueError(
            "Document ID cannot be empty."
        )


    # ========================================================
    # DOCUMENT DIRECTORY
    # ========================================================

    document_folder = (
        PROJECT_ROOT
        / "datasets"
        / "golden"
        / document_id
    )


    # ========================================================
    # INPUT FILE
    # ========================================================

    input_file = (
        document_folder
        / "input"
        / f"{document_id}.png"
    )


    # ========================================================
    # OUTPUT FILE
    # ========================================================

    output_file = (
        document_folder
        / "output"
        / f"{document_id}.json"
    )


    # ========================================================
    # CHECK DOCUMENT
    # ========================================================

    if not document_folder.exists():

        raise FileNotFoundError(
            f"Document folder not found:\n"
            f"{document_folder}"
        )


    # ========================================================
    # CHECK IMAGE
    # ========================================================

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


    # ========================================================
    # RUN PIPELINE
    # ========================================================

    result = process_document(
        input_file
    )


    # ========================================================
    # SAVE RESULT
    # ========================================================

    save_json(
        result,
        output_file
    )


    # ========================================================
    # FINAL RESULT
    # ========================================================

    summary = result[
        "confidence"
    ][
        "summary"
    ]


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


    # ========================================================
    # FORM SUMMARY
    # ========================================================

    if result["layout"]["type"] == "FORM":

        print(
            f"Form fields extracted: "
            f"{result['form']['field_count']}"
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
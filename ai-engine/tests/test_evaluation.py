import json
import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ============================================================
# LOAD JSON
# ============================================================

def load_json(file_path: Path) -> dict:
    """Load a JSON file."""

    if not file_path.exists():

        raise FileNotFoundError(
            f"File not found:\n{file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# COMPARE RECORDS
# ============================================================

def compare_records(
    expected: dict,
    actual: dict
) -> bool:
    """
    Compare expected and actual records.
    """

    expected_records = expected.get(
        "records",
        []
    )

    actual_records = actual.get(
        "records",
        []
    )


    print(
        f"Expected records: {len(expected_records)}"
    )

    print(
        f"Actual records:   {len(actual_records)}"
    )


    # --------------------------------------------------------
    # Compare complete record lists
    # --------------------------------------------------------

    if expected_records == actual_records:

        print()
        print("STATUS: PASS")
        print(
            "All extracted records match "
            "the expected output."
        )

        return True


    # --------------------------------------------------------
    # Mismatch
    # --------------------------------------------------------

    print()
    print("STATUS: FAIL")

    print()
    print("===== EXPECTED =====")

    print(
        json.dumps(
            expected_records,
            indent=2,
            ensure_ascii=False
        )
    )


    print()
    print("===== ACTUAL =====")

    print(
        json.dumps(
            actual_records,
            indent=2,
            ensure_ascii=False
        )
    )


    return False


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("========================================")
    print("       INTELLICAPTURE EVALUATION")
    print("========================================")
    print()


    # --------------------------------------------------------
    # Ask which document to evaluate
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
    # Document folder
    # --------------------------------------------------------

    document_folder = (
        PROJECT_ROOT
        / "datasets"
        / "golden"
        / document_id
    )


    # --------------------------------------------------------
    # Expected JSON
    # --------------------------------------------------------

    expected_file = (
        document_folder
        / "expected"
        / "expected.json"
    )


    # --------------------------------------------------------
    # Actual JSON
    # --------------------------------------------------------

    actual_file = (
        document_folder
        / "output"
        / f"{document_id}.json"
    )


    print()
    print(f"Document : {document_id}")
    print(
        f"Expected : {expected_file}"
    )
    print(
        f"Actual   : {actual_file}"
    )


    # --------------------------------------------------------
    # Load files
    # --------------------------------------------------------

    print()
    print("Loading expected output...")

    expected = load_json(
        expected_file
    )


    print("Loading actual output...")

    actual = load_json(
        actual_file
    )


    # --------------------------------------------------------
    # Compare
    # --------------------------------------------------------

    print()
    print("===== COMPARISON =====")

    passed = compare_records(
        expected,
        actual
    )


    print()
    print("===== END EVALUATION =====")


    # --------------------------------------------------------
    # Exit with failure code if mismatch
    # --------------------------------------------------------

    if not passed:

        sys.exit(1)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
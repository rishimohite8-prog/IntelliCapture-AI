import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GOLDEN_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "golden"
)


def load_json(file_path: Path) -> dict:

    if not file_path.exists():

        raise FileNotFoundError(
            f"File not found:\n{file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def normalize_expected_records(expected: dict) -> list:
    """
    Convert different expected JSON schemas
    into the common pipeline record format.
    """

    # --------------------------------------------------------
    # New schema
    #
    # {
    #   "records": [...]
    # }
    # --------------------------------------------------------

    if "records" in expected:

        return expected["records"]


    # --------------------------------------------------------
    # Legacy golden-document schema
    #
    # {
    #   "rows": [...]
    # }
    # --------------------------------------------------------

    if "rows" in expected:

        normalized = []

        for row in expected["rows"]:

            normalized.append(
                {
                    "customer": row["Customer Name"],
                    "date": convert_date(
                        row["Date"]
                    ),
                    "product": row["Product"],
                    "amount": str(
                        row["Amount"]
                    )
                }
            )

        return normalized


    # --------------------------------------------------------
    # Unknown schema
    # --------------------------------------------------------

    raise ValueError(
        "Expected JSON does not contain "
        "'records' or 'rows'."
    )


def convert_date(value: str) -> str:
    """
    Convert YYYY-MM-DD into DD/MM/YYYY.

    If the date is already DD/MM/YYYY,
    return it unchanged.
    """

    # Already in DD/MM/YYYY format
    if (
        len(value) == 10
        and value[2] == "/"
        and value[5] == "/"
    ):

        return value


    # Convert YYYY-MM-DD
    if (
        len(value) == 10
        and value[4] == "-"
        and value[7] == "-"
    ):

        year = value[0:4]
        month = value[5:7]
        day = value[8:10]

        return f"{day}/{month}/{year}"


    return value


def evaluate_document(
    document_folder: Path
) -> bool:

    document_id = document_folder.name

    expected_file = document_folder / "expected.json"

    if not expected_file.exists():
        expected_file = document_folder / "expected" / "expected.json"
    

    actual_file = (
        document_folder
        / "output"
        / f"{document_id}.json"
    )

    print()
    print("----------------------------------------")
    print(f"Testing: {document_id}")
    print("----------------------------------------")


    # --------------------------------------------------------
    # Check files
    # --------------------------------------------------------

    if not expected_file.exists():

        print(
            "FAIL: expected.json not found"
        )

        return False


    if not actual_file.exists():

        print(
            "FAIL: actual output JSON not found"
        )

        return False


    # --------------------------------------------------------
    # Load JSON
    # --------------------------------------------------------

    expected = load_json(
        expected_file
    )

    actual = load_json(
        actual_file
    )


    # --------------------------------------------------------
    # Normalize expected data
    # --------------------------------------------------------

    try:

        expected_records = (
            normalize_expected_records(
                expected
            )
        )

    except (KeyError, ValueError) as error:

        print(
            f"FAIL: Invalid expected JSON: {error}"
        )

        return False


    # --------------------------------------------------------
    # Actual records
    # --------------------------------------------------------

    actual_records = actual.get(
        "records",
        []
    )


    # --------------------------------------------------------
    # Display counts
    # --------------------------------------------------------

    print(
        f"Expected records: "
        f"{len(expected_records)}"
    )

    print(
        f"Actual records:   "
        f"{len(actual_records)}"
    )


    # --------------------------------------------------------
    # Compare
    # --------------------------------------------------------

    if expected_records == actual_records:

        print("STATUS: PASS")

        return True


    # --------------------------------------------------------
    # Display mismatch
    # --------------------------------------------------------

    print("STATUS: FAIL")

    print()
    print("Expected:")

    print(
        json.dumps(
            expected_records,
            indent=2,
            ensure_ascii=False
        )
    )

    print()
    print("Actual:")

    print(
        json.dumps(
            actual_records,
            indent=2,
            ensure_ascii=False
        )
    )

    return False


def main():

    print()
    print("========================================")
    print("     INTELLICAPTURE REGRESSION TEST")
    print("========================================")


    # --------------------------------------------------------
    # Check golden directory
    # --------------------------------------------------------

    if not GOLDEN_DIR.exists():

        raise FileNotFoundError(
            f"Golden directory not found:\n"
            f"{GOLDEN_DIR}"
        )


    # --------------------------------------------------------
    # Find documents
    # --------------------------------------------------------

    document_folders = sorted(
        folder
        for folder in GOLDEN_DIR.iterdir()
        if (
            folder.is_dir()
            and folder.name.startswith(
                "document_"
            )
        )
    )


    if not document_folders:

        print(
            "No golden documents found."
        )

        sys.exit(1)


    # --------------------------------------------------------
    # Run tests
    # --------------------------------------------------------

    passed = 0
    failed = 0


    for document_folder in document_folders:

        try:

            result = evaluate_document(
                document_folder
            )

        except Exception as error:

            print()
            print(
                f"ERROR while testing "
                f"{document_folder.name}:"
            )

            print(error)

            result = False


        if result:

            passed += 1

        else:

            failed += 1


    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    total = passed + failed

    print()
    print("========================================")
    print("          REGRESSION SUMMARY")
    print("========================================")

    print(
        f"Total documents : {total}"
    )

    print(
        f"Passed          : {passed}"
    )

    print(
        f"Failed          : {failed}"
    )

    print()


    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    if failed == 0:

        print(
            "OVERALL STATUS: PASS"
        )

        print(
            "All golden documents "
            "passed evaluation."
        )

        return


    print(
        "OVERALL STATUS: FAIL"
    )

    sys.exit(1)


if __name__ == "__main__":
    main()
from datetime import datetime
from typing import Dict, List


REQUIRED_FIELDS = [
    "customer",
    "date",
    "product",
    "amount",
]


def validate_record(record: Dict) -> List[str]:
    """
    Validate a single extracted record.

    Returns a list of validation errors.
    An empty list means the record is valid.
    """

    errors = []

    # Check required fields
    for field in REQUIRED_FIELDS:

        if field not in record:
            errors.append(
                f"Missing field: {field}"
            )
            continue

        if not str(record[field]).strip():
            errors.append(
                f"Empty field: {field}"
            )

    # Validate date
    if "date" in record:

        try:
            datetime.strptime(
                record["date"],
                "%d/%m/%Y"
            )
        except ValueError:
            errors.append(
                f"Invalid date: {record['date']}"
            )

    # Validate amount
    if "amount" in record:

        try:
            float(
                str(record["amount"]).replace(",", "")
            )
        except ValueError:
            errors.append(
                f"Invalid amount: {record['amount']}"
            )

    return errors
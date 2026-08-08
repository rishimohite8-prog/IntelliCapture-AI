import re
from typing import List, Dict, Optional


# ============================================================
# PATTERNS
# ============================================================

DATE_PATTERN = re.compile(
    r"^\d{2}/\d{2}/\d{4}$"
)


INTEGER_PATTERN = re.compile(
    r"^\d+$"
)


# ============================================================
# DATE CHECK
# ============================================================

def is_date(value: str) -> bool:
    """Check whether a value looks like DD/MM/YYYY."""

    return bool(
        DATE_PATTERN.match(
            value.strip()
        )
    )


# ============================================================
# AMOUNT CHECK
# ============================================================

def is_amount(value: str) -> bool:
    """Check whether a value is a numeric amount."""

    cleaned = (
        value
        .replace(",", "")
        .strip()
    )

    try:

        float(cleaned)

        return True

    except ValueError:

        return False


# ============================================================
# INTEGER CHECK
# ============================================================

def is_integer(value: str) -> bool:
    """Check whether a value is an integer."""

    return bool(
        INTEGER_PATTERN.match(
            value.strip()
        )
    )


# ============================================================
# FIELD MAPPING
# ============================================================

def map_row_to_fields(
    row: List[str]
) -> Optional[Dict]:
    """
    Convert a detected OCR row into structured fields.

    Supported structures:

    Document #001:
        No | Customer | Date | Product | Quantity | Amount

    Document #002:
        Customer | Date | Product | Amount
    """

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if len(row) < 4:

        return None


    # --------------------------------------------------------
    # Find DATE
    # --------------------------------------------------------

    date_index = None

    for index, value in enumerate(row):

        if is_date(value):

            date_index = index

            break


    if date_index is None:

        return None


    # --------------------------------------------------------
    # Find AMOUNT
    #
    # Amount is normally the final numeric value.
    # --------------------------------------------------------

    amount_index = None

    for index in range(
        len(row) - 1,
        date_index,
        -1
    ):

        if is_amount(row[index]):

            amount_index = index

            break


    if amount_index is None:

        return None


    # --------------------------------------------------------
    # CUSTOMER
    # --------------------------------------------------------

    customer_parts = row[
        :date_index
    ]


    # Remove serial number if present.
    #
    # Example:
    #
    # ["1", "Rahul", "Patil"]
    #
    # becomes:
    #
    # ["Rahul", "Patil"]
    #

    if (
        customer_parts
        and is_integer(customer_parts[0])
    ):

        customer_parts = customer_parts[1:]


    customer = " ".join(
        customer_parts
    ).strip()


    # --------------------------------------------------------
    # PRODUCT
    # --------------------------------------------------------

    product_parts = row[
        date_index + 1:
        amount_index
    ]


    # --------------------------------------------------------
    # REMOVE QUANTITY
    #
    # Document #001 has:
    #
    # Laptop 1 55000
    #
    # The final integer before the amount is
    # the quantity.
    #
    # Document #002 has:
    #
    # Monitor 15000
    #
    # Here there is no separate quantity.
    #
    # We therefore remove the final integer only
    # when there is more than one product token.
    # --------------------------------------------------------

    if (
        len(product_parts) >= 2
        and is_integer(product_parts[-1])
    ):

        product_parts = product_parts[:-1]


    product = " ".join(
        product_parts
    ).strip()


    # --------------------------------------------------------
    # FINAL VALIDATION
    # --------------------------------------------------------

    if not customer:

        return None


    if not product:

        return None


    # --------------------------------------------------------
    # RETURN STRUCTURED RECORD
    # --------------------------------------------------------

    return {
        "customer": customer,
        "date": row[date_index],
        "product": product,
        "amount": row[amount_index],
    }
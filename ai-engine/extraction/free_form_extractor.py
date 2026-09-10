import re
from typing import Dict, List


DATE_PATTERN = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")

AMOUNT_PATTERN = re.compile(
    r"\b\d+(?:,\d{3})*(?:\.\d+)?\b"
)


PRODUCT_PATTERNS = [
    # English
    r"\bpurchased\s+(?:a|an|the)\s+([A-Za-z][A-Za-z0-9_-]*)",
    r"\bpurchased\s+([A-Za-z][A-Za-z0-9_-]*)",
    r"\bbought\s+(?:a|an|the)\s+([A-Za-z][A-Za-z0-9_-]*)",
    r"\bbought\s+([A-Za-z][A-Za-z0-9_-]*)",
    r"\bitem\s+was\s+([A-Za-z][A-Za-z0-9_-]*)",
    r"\bproduct\s+was\s+([A-Za-z][A-Za-z0-9_-]*)",

    # German
    r"\bkaufte\s+(?:einen|eine|ein|den|die|das)\s+([A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß0-9_-]*)",
    r"\bkaufte\s+([A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß0-9_-]*)",
    r"\bprodukt\s+war\s+([A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß0-9_-]*)",

    # Spanish
    r"\bcompr[oó]\s+(?:un|una|el|la)\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9_-]*)",
    r"\bcompr[oó]\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9_-]*)",
    r"\bel\s+producto\s+fue\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9_-]*)",
    r"\bel\s+art[ií]culo\s+fue\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9_-]*)",
]


def _extract_date(text: str) -> str:
    match = DATE_PATTERN.search(text)

    if match:
        return match.group(0)

    return ""


def _extract_amount(text: str) -> str:
    text_without_dates = DATE_PATTERN.sub("", text)

    matches = AMOUNT_PATTERN.findall(
        text_without_dates
    )

    candidates = []

    for value in matches:

        try:
            candidates.append(
                (
                    float(value.replace(",", "")),
                    value
                )
            )

        except ValueError:
            continue

    if not candidates:
        return ""

    candidates.sort(reverse=True)

    return candidates[0][1].replace(",", "")


def _extract_product(text: str) -> str:

    for pattern in PRODUCT_PATTERNS:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(1).strip()

    return ""


def _extract_customer(text: str) -> str:
    """
    Extract a two-word person's name.

    Works with Latin-script names commonly appearing
    in English, German and Spanish free-form documents.
    """

    name_pattern = re.compile(
        r"\b("
        r"[A-ZÄÖÜÁÉÍÓÚÑ][A-Za-zÄÖÜäöüßÁÉÍÓÚÜÑáéíóúüñ]+"
        r"(?:\s+"
        r"[A-ZÄÖÜÁÉÍÓÚÑ][A-Za-zÄÖÜäöüßÁÉÍÓÚÜÑáéíóúüñ]+"
        r")+"
        r")\b"
    )

    matches = name_pattern.findall(text)

    ignored = {
        "Payment Was",
        "The Item",
        "Customer Purchase",
        "Customer Information",
        "Zahlung Wurde",
        "Kunden Information",
        "La Compra",
        "El Cliente",
        "El Producto",
    }

    for name in matches:

        if name not in ignored:
            return name.strip()

    return ""


def _find_candidate_sentences(
    text: str
) -> List[str]:

    text = text.replace(
        "\r",
        "\n"
    )

    raw_parts = re.split(
        r"\n+",
        text
    )

    sentences = []

    for part in raw_parts:

        part = part.strip()

        if not part:
            continue

        sub_parts = re.split(
            r"(?<=[.!?])\s+",
            part
        )

        for sentence in sub_parts:

            sentence = sentence.strip()

            if sentence:
                sentences.append(
                    sentence
                )

    return sentences


def extract_free_form_records(
    text: str
) -> List[Dict]:
    """
    Extract structured purchase records from
    English, German and Spanish free-form text.
    """

    sentences = _find_candidate_sentences(
        text
    )

    records = []

    current_record = {
        "customer": "",
        "date": "",
        "product": "",
        "amount": "",
    }

    def save_current_record():

        nonlocal current_record

        required_fields = [
            "customer",
            "date",
            "product",
            "amount",
        ]

        if all(
            current_record[field].strip()
            for field in required_fields
        ):

            records.append(
                current_record.copy()
            )

        current_record = {
            "customer": "",
            "date": "",
            "product": "",
            "amount": "",
        }

    for sentence in sentences:

        customer = _extract_customer(
            sentence
        )

        date = _extract_date(
            sentence
        )

        product = _extract_product(
            sentence
        )

        amount = _extract_amount(
            sentence
        )

        if customer:

            if current_record["customer"]:
                save_current_record()

            current_record["customer"] = customer

        if date:
            current_record["date"] = date

        if product:
            current_record["product"] = product

        if amount:
            current_record["amount"] = amount

        if all(
            current_record[field].strip()
            for field in [
                "customer",
                "date",
                "product",
                "amount",
            ]
        ):

            save_current_record()

    if current_record["customer"]:
        save_current_record()

    return records


def extract_free_form_record(
    text: str
) -> Dict:

    records = extract_free_form_records(
        text
    )

    if records:
        return records[0]

    return {}


if __name__ == "__main__":

    test_documents = {

        "ENGLISH": """
        Rahul Patil visited on 14/08/2026.
        He purchased a Laptop for 55000.
        Payment was completed.
        """,

        "GERMAN": """
        Rahul Patil besuchte uns am 14/08/2026.
        Er kaufte einen Laptop für 55000.
        Die Zahlung wurde abgeschlossen.
        """,

        "SPANISH": """
        Rahul Patil visitó el 14/08/2026.
        Compró un Laptop por 55000.
        El pago fue completado.
        """,
    }

    print()
    print("MULTILINGUAL FREE-FORM EXTRACTION TEST")
    print("=" * 50)

    for language, text in test_documents.items():

        print()
        print(f"{language}")
        print("-" * 50)

        records = extract_free_form_records(
            text
        )

        for index, record in enumerate(
            records,
            start=1
        ):

            print(
                f"Record {index}:"
            )

            print(record)

        print(
            f"Records extracted: "
            f"{len(records)}"
        )

    print()
    print("=" * 50)

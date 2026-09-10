import re
from typing import Dict, List


FIELD_ALIASES = {
    "customer": {
        "customer",
        "kunde",
        "cliente",
        "client",
        "klant",
        "клиент",
        "клієнт",
        "klient",
        "müşteri",
        "πελάτης",
        "ग्राहक",
        "গ্রাহক",
        "வாடிக்கையாளர்",
        "కస్టమర్",
        "ગ્રાહક",
        "ಗ್ರಾಹಕ",
        "ഉപഭോക്താവ്",
    },

    "date": {
        "date",
        "datum",
        "fecha",
        "data",
        "datum",
        "дата",
        "tarih",
        "ημερομηνία",
        "दिनांक",
        "तारीख",
        "তারিখ",
        "தேதி",
        "తేదీ",
        "તારીખ",
        "ದಿನಾಂಕ",
        "തീയതി",
    },

    "product": {
        "product",
        "produkt",
        "producto",
        "produit",
        "prodotto",
        "produto",
        "товар",
        "ürün",
        "προϊόν",
        "उत्पाद",
        "उत्पादन",
        "পণ্য",
        "தயாரிப்பு",
        "ఉత్పత్తి",
        "ઉત્પાદન",
        "ಉತ್ಪನ್ನ",
        "ഉൽപ്പന്നം",
    },

    "amount": {
        "amount",
        "betrag",
        "importe",
        "montant",
        "importo",
        "valor",
        "bedrag",
        "сумма",
        "сума",
        "kwota",
        "tutar",
        "ποσό",
        "राशि",
        "रक्कम",
        "পরিমাণ",
        "தொகை",
        "మొత్తం",
        "રકમ",
        "ಮೊತ್ತ",
        "തുക",
    },

    "city": {
        "city",
        "stadt",
        "ciudad",
        "ville",
        "città",
        "cidade",
        "stad",
        "город",
        "місто",
        "miasto",
        "şehir",
        "πόλη",
        "शहर",
        "শহর",
        "நகரம்",
        "నగరం",
        "શહેર",
        "ನಗರ",
        "നഗരം",
    },

    "status": {
        "status",
        "state",
        "estado",
        "statut",
        "stato",
        "статус",
        "durum",
        "κατάσταση",
        "स्थिति",
        "স্থিতি",
        "நிலை",
        "స్థితి",
        "સ્થિતિ",
        "ಸ್ಥಿತಿ",
        "നില",
    },
}


ALIAS_TO_FIELD = {
    alias.lower(): field
    for field, aliases in FIELD_ALIASES.items()
    for alias in aliases
}


def _clean_separator(text: str) -> str:
    return re.sub(
        r"^[\s:=>]+|[\s:=>]+$",
        "",
        text.strip(),
    )


def _is_separator(text: str) -> bool:
    cleaned = text.strip()

    return cleaned in {
        ":",
        ">",
        "=",
        ":=",
        "=:",
        "->",
    }


def _normalize_label(text: str) -> str:
    text = _clean_separator(text)

    text = text.lower().strip()

    return text


def _map_label_to_field(label: str):
    normalized = _normalize_label(label)

    return ALIAS_TO_FIELD.get(normalized)


def _split_attached_separator(
    text: str
):
    """
    Handles OCR tokens such as:
        Kunde:
        Datum:
        Product:
        Amount:

    Returns:
        (label, separator)
    """

    text = text.strip()

    match = re.match(
        r"^(.+?)(:|:=|=:|=|>|->)$",
        text
    )

    if not match:
        return None

    label = match.group(1).strip()
    separator = match.group(2)

    return label, separator


def _extract_label_and_separator(
    words: List[Dict]
):
    """
    Supports both OCR formats:

        Kunde :
        Kunde:

    Returns:
        label, separator_x, value_words
    """

    if not words:
        return None

    # Case 1:
    # Separator is a separate OCR token.
    for index, word in enumerate(words):

        text = word.get("text", "").strip()

        if _is_separator(text):

            label_words = words[:index]

            if not label_words:
                continue

            label = " ".join(
                item.get("text", "")
                for item in label_words
            ).strip()

            separator_x = (
                word.get("left", 0)
                + word.get("width", 0)
            )

            value_words = words[index + 1:]

            return (
                label,
                separator_x,
                value_words,
            )

    # Case 2:
    # Separator is attached to the label.
    for index, word in enumerate(words):

        text = word.get("text", "")

        attached = _split_attached_separator(
            text
        )

        if attached is None:
            continue

        label_part, separator = attached

        label_words = words[:index]

        if label_part:
            label_words.append(
                {
                    **word,
                    "text": label_part,
                }
            )

        label = " ".join(
            item.get("text", "")
            for item in label_words
        ).strip()

        separator_x = (
            word.get("left", 0)
            + word.get("width", 0)
        )

        value_words = words[index + 1:]

        return (
            label,
            separator_x,
            value_words,
        )

    return None


def extract_form_fields(
    lines: List[List[Dict]]
) -> Dict:

    fields = {}

    for line in lines:

        if not line:
            continue

        extracted = (
            _extract_label_and_separator(
                line
            )
        )

        if extracted is None:
            continue

        (
            label,
            separator_x,
            value_words,
        ) = extracted

        label = _clean_separator(
            label
        )

        if not label:
            continue

        internal_field = (
            _map_label_to_field(label)
        )

        if internal_field is None:
            continue

        # Remove any separator-like tokens
        # that may still appear in the value.
        value_words = [
            word
            for word in value_words
            if not _is_separator(
                word.get("text", "")
            )
        ]

        # Keep only words positioned after
        # the separator.
        positioned_value_words = [
            word
            for word in value_words
            if word.get("left", 0)
            >= separator_x
        ]

        if positioned_value_words:
            value_words = positioned_value_words

        if not value_words:
            continue

        value = " ".join(
            word.get("text", "")
            for word in value_words
        ).strip()

        if not value:
            continue

        confidences = []

        for word in value_words:

            try:
                confidence = float(
                    word.get(
                        "confidence",
                        0
                    )
                )

                confidences.append(
                    confidence
                )

            except (
                TypeError,
                ValueError
            ):
                continue

        if confidences:

            confidence = (
                sum(confidences)
                / len(confidences)
            )

        else:

            confidence = 0.0

        fields[internal_field] = {
            "label": label,
            "value": value,
            "confidence": round(
                confidence,
                2
            ),
        }

    return {
        "fields": fields,
        "field_count": len(fields),
    }
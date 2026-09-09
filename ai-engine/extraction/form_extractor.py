import re
from typing import Dict, List


# ============================================================
# FORM EXTRACTOR
# ============================================================

def _clean_separator(text: str) -> str:
    """
    Remove separator characters from the beginning
    and end of text.
    """

    return re.sub(
        r"^[\s:=>]+|[\s:=>]+$",
        "",
        text.strip()
    )


# ============================================================
# SEPARATOR DETECTION
# ============================================================

def _is_separator(text: str) -> bool:
    """
    Detect OCR tokens that represent a field separator.
    """

    cleaned = text.strip()

    return cleaned in {
        ":",
        ">",
        "=",
        ":=",
        "=:" ,
        "->"
    }


# ============================================================
# VALUE WORD EXTRACTION
# ============================================================

def _group_value_words(
    words: List[Dict],
    separator_x: float
) -> List[Dict]:
    """
    Extract words appearing after the field separator.
    """

    value_words = []

    for word in words:

        if _is_separator(
            word.get("text", "")
        ):
            continue

        if word.get(
            "left",
            0
        ) > separator_x:

            value_words.append(
                word
            )

    value_words.sort(
        key=lambda item: item.get(
            "left",
            0
        )
    )

    return value_words


# ============================================================
# FORM FIELD EXTRACTION
# ============================================================

def extract_form_fields(
    lines: List[List[Dict]]
) -> Dict:
    """
    Extract label-value pairs from FORM layout.

    Expected input:

        [
            [word, word, word],
            [word, word, word],
            ...
        ]

    Example:

        Customer : Rahul Patil

    becomes:

        {
            "Customer": {
                "value": "Rahul Patil",
                "confidence": 95.5
            }
        }
    """

    fields = {}


    # ========================================================
    # PROCESS EACH OCR ROW
    # ========================================================

    for line in lines:

        # ----------------------------------------------------
        # group_words_into_rows() returns a list of words
        # directly, not {"words": [...]}
        # ----------------------------------------------------

        words = line

        if not words:
            continue


        # ====================================================
        # FIND SEPARATOR
        # ====================================================

        separator = None

        for word in words:

            if _is_separator(
                word.get(
                    "text",
                    ""
                )
            ):

                separator = word

                break


        if separator is None:
            continue


        # ====================================================
        # SEPARATOR POSITION
        # ====================================================

        separator_x = (
            separator.get(
                "left",
                0
            )
            +
            separator.get(
                "width",
                0
            )
        )


        # ====================================================
        # EXTRACT LABEL
        # ====================================================

        label_words = []

        for word in words:

            if word.get(
                "left",
                0
            ) < separator.get(
                "left",
                0
            ):

                label_words.append(
                    word
                )


        label_words.sort(
            key=lambda item: item.get(
                "left",
                0
            )
        )


        if not label_words:
            continue


        label = " ".join(
            word.get(
                "text",
                ""
            )
            for word in label_words
        ).strip()


        label = _clean_separator(
            label
        )


        if not label:
            continue


        # ====================================================
        # EXTRACT VALUE
        # ====================================================

        value_words = _group_value_words(
            words,
            separator_x
        )


        if not value_words:
            continue


        value = " ".join(
            word.get(
                "text",
                ""
            )
            for word in value_words
        ).strip()


        if not value:
            continue


        # ====================================================
        # FIELD CONFIDENCE
        # ====================================================

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
                /
                len(confidences)
            )

        else:

            confidence = 0.0


        # ====================================================
        # STORE FIELD
        # ====================================================

        fields[label] = {

            "value": value,

            "confidence": round(
                confidence,
                2
            )
        }


    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {

        "fields": fields,

        "field_count": len(
            fields
        )
    }
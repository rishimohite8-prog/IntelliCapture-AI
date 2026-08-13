from typing import Dict, List


# ============================================================
# CONFIDENCE THRESHOLDS
# ============================================================

HIGH_CONFIDENCE = 85.0
MEDIUM_CONFIDENCE = 65.0


# ============================================================
# QUALITY CLASSIFICATION
# ============================================================

def classify_confidence(
    confidence: float
) -> str:
    """
    Convert a numeric confidence score into
    a human-readable quality level.
    """

    confidence = normalize_confidence(
        confidence
    )

    if confidence >= HIGH_CONFIDENCE:
        return "HIGH"

    if confidence >= MEDIUM_CONFIDENCE:
        return "MEDIUM"

    return "LOW"


# ============================================================
# SAFE CONFIDENCE
# ============================================================

def normalize_confidence(
    confidence: float
) -> float:
    """
    Keep confidence between 0 and 100.
    """

    try:
        confidence = float(confidence)

    except (
        TypeError,
        ValueError
    ):

        return 0.0

    if confidence < 0:
        return 0.0

    if confidence > 100:
        return 100.0

    return round(
        confidence,
        2
    )


# ============================================================
# ROW CONFIDENCE
# ============================================================

def calculate_row_confidence(
    row: List[Dict]
) -> float:
    """
    Calculate average OCR confidence for a row.

    Each OCR word contains:

        text
        confidence
        left
        top
        width
        height
    """

    if not row:
        return 0.0

    confidences = []

    for word in row:

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

    if not confidences:

        return 0.0

    average = (
        sum(confidences)
        / len(confidences)
    )

    return normalize_confidence(
        average
    )


# ============================================================
# FIELD WORD MATCHING
# ============================================================

def _find_field_words(
    field_value: str,
    row: List[Dict]
) -> List[Dict]:
    """
    Find OCR words belonging to an extracted field.

    Matching is performed using the individual words
    contained in the extracted field value.

    Example:

        field_value = "Rahul Patil"

    searches for:

        Rahul
        Patil
    """

    if not field_value:

        return []

    target_words = [
        word.lower()
        for word in str(
            field_value
        ).split()
        if word.strip()
    ]

    if not target_words:

        return []

    matched_words = []

    used_indexes = set()

    for target in target_words:

        for index, word in enumerate(row):

            if index in used_indexes:

                continue

            ocr_text = str(
                word.get(
                    "text",
                    ""
                )
            ).strip().lower()

            if not ocr_text:

                continue

            # Exact match
            if ocr_text == target:

                matched_words.append(
                    word
                )

                used_indexes.add(
                    index
                )

                break

    return matched_words


# ============================================================
# FIELD CONFIDENCE
# ============================================================

def calculate_field_confidence(
    field_value: str,
    row: List[Dict]
) -> float:
    """
    Calculate confidence for one extracted field.

    The confidence is based on the OCR confidence
    of the words that make up that field.

    If no matching OCR words are found, confidence
    falls back to the row confidence.
    """

    matched_words = _find_field_words(
        field_value,
        row
    )

    if not matched_words:

        return calculate_row_confidence(
            row
        )

    confidences = []

    for word in matched_words:

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

    if not confidences:

        return calculate_row_confidence(
            row
        )

    average = (
        sum(confidences)
        / len(confidences)
    )

    return normalize_confidence(
        average
    )


# ============================================================
# BUILD FIELD CONFIDENCE
# ============================================================

def build_field_confidence(
    field_value: str,
    row: List[Dict]
) -> Dict:
    """
    Build confidence metadata for one field.
    """

    confidence = calculate_field_confidence(
        field_value,
        row
    )

    quality = classify_confidence(
        confidence
    )

    return {
        "value": field_value,
        "confidence": confidence,
        "quality": quality,
        "requires_review": quality != "HIGH"
    }


# ============================================================
# RECORD CONFIDENCE
# ============================================================

def build_record_confidence(
    record: Dict,
    row: List[Dict]
) -> Dict:
    """
    Build detailed confidence metadata
    for an extracted record.

    The original record is NOT modified.
    """

    row_confidence = calculate_row_confidence(
        row
    )

    field_confidences = {}

    for field in [
        "customer",
        "date",
        "product",
        "amount"
    ]:

        field_confidences[field] = (
            build_field_confidence(
                str(
                    record.get(
                        field,
                        ""
                    )
                ),
                row
            )
        )

    requires_review = any(
        field["requires_review"]
        for field in field_confidences.values()
    )

    return {
        "confidence": row_confidence,
        "quality": classify_confidence(
            row_confidence
        ),
        "word_count": len(row),
        "requires_review": requires_review,
        "fields": field_confidences
    }


# ============================================================
# DOCUMENT CONFIDENCE SUMMARY
# ============================================================

def build_document_confidence_summary(
    record_confidences: List[Dict]
) -> Dict:
    """
    Build a summary for the complete document.
    """

    if not record_confidences:

        return {
            "average_confidence": 0.0,
            "quality": "LOW",
            "records_review_required": 0,
            "fields_review_required": 0,
            "total_records": 0
        }

    values = [
        item["confidence"]
        for item in record_confidences
    ]

    average = (
        sum(values)
        / len(values)
    )

    record_review_count = sum(
        1
        for item in record_confidences
        if item["requires_review"]
    )

    field_review_count = 0

    for item in record_confidences:

        fields = item.get(
            "fields",
            {}
        )

        for field in fields.values():

            if field.get(
                "requires_review",
                False
            ):

                field_review_count += 1

    normalized_average = normalize_confidence(
        average
    )

    return {
        "average_confidence": normalized_average,
        "quality": classify_confidence(
            normalized_average
        ),
        "records_review_required": record_review_count,
        "fields_review_required": field_review_count,
        "total_records": len(
            record_confidences
        )
    }
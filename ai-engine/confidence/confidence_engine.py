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

    confidence = float(confidence)

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
# RECORD CONFIDENCE
# ============================================================

def build_record_confidence(
    record: Dict,
    row: List[Dict]
) -> Dict:
    """
    Build confidence metadata for an extracted record.

    The original record is NOT modified.

    This keeps the existing golden-document
    extraction output compatible.
    """

    confidence = calculate_row_confidence(
        row
    )

    quality = classify_confidence(
        confidence
    )

    return {
        "confidence": confidence,
        "quality": quality,
        "word_count": len(row),
        "requires_review": quality == "LOW"
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

    review_count = sum(
        1
        for item in record_confidences
        if item["requires_review"]
    )

    normalized_average = normalize_confidence(
        average
    )

    return {
        "average_confidence": normalized_average,
        "quality": classify_confidence(
            normalized_average
        ),
        "records_review_required": review_count,
        "total_records": len(
            record_confidences
        )
    }
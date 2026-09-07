from typing import Dict, List, Optional

from pydantic import BaseModel


# ============================================================
# FIELD CONFIDENCE
# ============================================================

class FieldConfidence(BaseModel):
    value: str
    confidence: float
    quality: str
    requires_review: bool


# ============================================================
# RECORD CONFIDENCE
# ============================================================

class RecordConfidence(BaseModel):
    confidence: float
    quality: str
    word_count: int
    requires_review: bool

    fields: Dict[
        str,
        FieldConfidence
    ]


# ============================================================
# CONFIDENCE SUMMARY
# ============================================================

class ConfidenceSummary(BaseModel):
    average_confidence: float
    quality: str
    records_review_required: int
    fields_review_required: int
    total_records: int


# ============================================================
# DOCUMENT CONFIDENCE
# ============================================================

class DocumentConfidence(BaseModel):
    records: List[
        RecordConfidence
    ]

    summary: ConfidenceSummary


# ============================================================
# EXTRACTED RECORD
# ============================================================

class ExtractedRecord(BaseModel):
    customer: str
    date: str
    product: str
    amount: str


# ============================================================
# DOCUMENT RESPONSE
# ============================================================

class DocumentResponse(BaseModel):
    success: bool
    document_id: str
    filename: str
    records_extracted: int

    records: List[
        ExtractedRecord
    ]

    confidence: Optional[
        DocumentConfidence
    ] = None
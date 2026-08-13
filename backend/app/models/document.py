from typing import List
from pydantic import BaseModel


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
    records: List[ExtractedRecord]
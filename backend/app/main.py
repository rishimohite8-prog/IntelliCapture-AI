from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.services.document_service import process_uploaded_file
from backend.app.models.document import DocumentResponse

from database.storage.database import (
    get_document,
    list_documents,
    update_record,
    get_records_for_review,
    update_record_review_status,
)


# ============================================================
# REQUEST MODELS
# ============================================================

class RecordUpdateRequest(BaseModel):
    customer: str
    date: str
    product: str
    amount: str


class ReviewStatusRequest(BaseModel):
    review_status: str


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="IntelliCapture-AI API",
    description="AI-powered document intelligence and data extraction platform",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "success": True,
        "message": "IntelliCapture-AI API is running",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "success": True,
        "status": "healthy",
    }


# ============================================================
# PROCESS DOCUMENT
# ============================================================

@app.post(
    "/api/v1/process",
    response_model=DocumentResponse,
)
async def process_document(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No filename provided",
            )

        file_content = await file.read()

        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty",
            )

        result = process_uploaded_file(
            filename=file.filename,
            file_content=file_content,
        )

        return result

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(error)}",
        )


# ============================================================
# LIST DOCUMENTS
# ============================================================

@app.get("/api/v1/documents")
def get_documents():
    try:
        documents = list_documents()

        return {
            "success": True,
            "total_documents": len(documents),
            "documents": documents,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve documents: {str(error)}",
        )


# ============================================================
# GET DOCUMENT DETAILS
# ============================================================

@app.get("/api/v1/documents/{document_id}")
def get_document_details(document_id: str):
    try:
        document = get_document(document_id)

        if document is None:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}",
            )

        # get_document() currently returns:
        #
        # {
        #     "document": {...},
        #     "records": [...]
        # }
        #
        # The API should expose the database document fields
        # and records at the same level.

        document_data = document.get("document", {})
        records = document.get("records", [])

        return {
            "success": True,
            "document": {
                **document_data,
                "records": records,
            },
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve document: {str(error)}",
        )


# ============================================================
# UPDATE DOCUMENT RECORD
# ============================================================

@app.put(
    "/api/v1/documents/{document_id}/records/{record_id}"
)
def update_document_record(
    document_id: str,
    record_id: int,
    data: RecordUpdateRequest,
):
    try:
        updated_record = update_record(
            record_id=record_id,
            document_id=document_id,
            customer=data.customer,
            date=data.date,
            product=data.product,
            amount=data.amount,
        )

        if updated_record is None:
            raise HTTPException(
                status_code=404,
                detail=f"Record not found: {record_id}",
            )

        return {
            "success": True,
            "message": "Record updated successfully.",
            "record": updated_record,
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update record: {str(error)}",
        )


# ============================================================
# HUMAN REVIEW QUEUE
# ============================================================

@app.get("/api/v1/review/queue")
def get_review_queue():
    try:
        records = get_records_for_review()

        return {
            "success": True,
            "total_records": len(records),
            "records": records,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve review queue: {str(error)}",
        )


# ============================================================
# UPDATE REVIEW STATUS
# ============================================================

@app.put(
    "/api/v1/records/{record_id}/review-status"
)
def update_review_status(
    record_id: int,
    data: ReviewStatusRequest,
):
    try:
        status = data.review_status.strip().upper()

        allowed_statuses = {
            "PENDING",
            "APPROVED",
            "REJECTED",
        }

        if status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid review status. "
                    "Use PENDING, APPROVED, or REJECTED."
                ),
            )

        updated_record = update_record_review_status(
            record_id=record_id,
            review_status=status,
        )

        if updated_record is None:
            raise HTTPException(
                status_code=404,
                detail=f"Record not found: {record_id}",
            )

        return {
            "success": True,
            "message": (
                f"Record review status updated to {status}."
            ),
            "record": updated_record,
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update review status: {str(error)}",
        )
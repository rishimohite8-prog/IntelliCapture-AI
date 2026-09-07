from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.services.document_service import (
    process_uploaded_file
)

from backend.app.models.document import (
    DocumentResponse
)

from database.storage.database import (
    get_document,
    list_documents,
    update_record
)


# ============================================================
# RECORD UPDATE REQUEST MODEL
# ============================================================

class RecordUpdateRequest(BaseModel):

    customer: str

    date: str

    product: str

    amount: str


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="IntelliCapture-AI",
    description=(
        "Intelligent document digitization API "
        "for converting physical records into structured data."
    ),
    version="0.1.0",
)


# ============================================================
# CORS CONFIGURATION
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
        "project": "IntelliCapture-AI",
        "status": "online",
        "version": "0.1.0",
        "message": "Document intelligence API is running."
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ============================================================
# PROCESS DOCUMENT
# ============================================================

@app.post(
    "/api/v1/process",
    response_model=DocumentResponse
)
async def process_document(
    file: UploadFile = File(...)
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file was provided."
        )

    try:

        file_content = await file.read()

        if not file_content:

            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty."
            )

        result = process_uploaded_file(
            filename=file.filename,
            file_content=file_content
        )

        response = DocumentResponse(
            success=True,
            document_id=result["document_id"],
            filename=result["filename"],
            records_extracted=len(
                result["records"]
            ),
            records=result["records"],
            confidence=result["confidence"]
        )

        return response

    except HTTPException:

        raise

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Document processing failed: "
                f"{str(error)}"
            )
        )


# ============================================================
# LIST DOCUMENTS
# ============================================================

@app.get(
    "/api/v1/documents"
)
def get_documents():

    try:

        documents = list_documents()

        return {
            "success": True,
            "total_documents": len(documents),
            "documents": documents
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to retrieve documents: "
                f"{str(error)}"
            )
        )


# ============================================================
# GET DOCUMENT
# ============================================================

@app.get(
    "/api/v1/documents/{document_id}"
)
def get_single_document(
    document_id: str
):

    try:

        result = get_document(
            document_id
        )

        if result is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Document not found: "
                    f"{document_id}"
                )
            )

        return {
            "success": True,
            "document": result["document"],
            "records": result["records"]
        }

    except HTTPException:

        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to retrieve document: "
                f"{str(error)}"
            )
        )


# ============================================================
# UPDATE RECORD
# ============================================================

@app.put(
    "/api/v1/documents/{document_id}/records/{record_id}"
)
def update_document_record(
    document_id: str,
    record_id: int,
    data: RecordUpdateRequest
):

    try:

        # ----------------------------------------------------
        # Verify document exists
        # ----------------------------------------------------

        document = get_document(
            document_id
        )

        if document is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Document not found: "
                    f"{document_id}"
                )
            )

        # ----------------------------------------------------
        # Verify record belongs to document
        # ----------------------------------------------------

        record_exists = False

        for record in document["records"]:

            if record["id"] == record_id:

                record_exists = True

                break

        if not record_exists:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Record {record_id} "
                    f"not found in document "
                    f"{document_id}."
                )
            )

        # ----------------------------------------------------
        # Validate values
        # ----------------------------------------------------

        customer = data.customer.strip()

        date = data.date.strip()

        product = data.product.strip()

        amount = data.amount.strip()

        if not customer:

            raise HTTPException(
                status_code=400,
                detail="Customer cannot be empty."
            )

        if not date:

            raise HTTPException(
                status_code=400,
                detail="Date cannot be empty."
            )

        if not product:

            raise HTTPException(
                status_code=400,
                detail="Product cannot be empty."
            )

        if not amount:

            raise HTTPException(
                status_code=400,
                detail="Amount cannot be empty."
            )

        # ----------------------------------------------------
        # Update record
        # ----------------------------------------------------

        updated_record = update_record(
            record_id=record_id,
            customer=customer,
            date=date,
            product=product,
            amount=amount
        )

        if updated_record is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Record not found: "
                    f"{record_id}"
                )
            )

        # ----------------------------------------------------
        # Return updated record
        # ----------------------------------------------------

        return {
            "success": True,
            "message": "Record updated successfully.",
            "document_id": document_id,
            "record": updated_record
        }

    except HTTPException:

        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to update record: "
                f"{str(error)}"
            )
        )
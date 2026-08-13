from fastapi import FastAPI, File, UploadFile, HTTPException

from backend.app.services.document_service import (
    process_uploaded_file
)

from backend.app.models.document import (
    DocumentResponse
)


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
# ROOT ENDPOINT
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
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ============================================================
# DOCUMENT PROCESSING
# ============================================================

@app.post(
    "/api/v1/process",
    response_model=DocumentResponse
)
async def process_document(
    file: UploadFile = File(...)
):

    # --------------------------------------------------------
    # Validate filename
    # --------------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file was provided."
        )


    try:

        # ----------------------------------------------------
        # Read uploaded file
        # ----------------------------------------------------

        file_content = await file.read()


        # ----------------------------------------------------
        # Validate that something was uploaded
        # ----------------------------------------------------

        if not file_content:

            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty."
            )


        # ----------------------------------------------------
        # Process document
        # ----------------------------------------------------

        result = process_uploaded_file(
            filename=file.filename,
            file_content=file_content
        )


        # ----------------------------------------------------
        # Build structured API response
        # ----------------------------------------------------

        return DocumentResponse(
            success=True,
            document_id=result["document_id"],
            filename=result["filename"],
            records_extracted=len(
                result["records"]
            ),
            records=result["records"]
        )


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
from pathlib import Path
from database.storage.database import save_document
import sys
import shutil
import tempfile


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)

AI_ENGINE_PATH = (
    PROJECT_ROOT
    / "ai-engine"
)

if str(AI_ENGINE_PATH) not in sys.path:

    sys.path.insert(
        0,
        str(AI_ENGINE_PATH)
    )


# ============================================================
# DATABASE
# ============================================================

from database.storage.database import (
    save_document
)


# ============================================================
# INTELLICAPTURE EXTRACTION ENGINE
# ============================================================

from extraction.pipeline import (
    process_document
)


# ============================================================
# UPLOAD CONFIGURATION
# ============================================================

MAX_FILE_SIZE = (
    10 * 1024 * 1024
)

ALLOWED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tif",
    ".tiff"
}


# ============================================================
# PROCESS UPLOADED FILE
# ============================================================

def process_uploaded_file(
    filename: str,
    file_content: bytes
) -> dict:
    """
    Process an uploaded physical document.

    Pipeline:

        Upload
          ↓
        OCR
          ↓
        Extraction
          ↓
        Validation
          ↓
        Confidence
          ↓
        SQLite
          ↓
        API
    """

    # ========================================================
    # SAFE FILENAME
    # ========================================================

    original_filename = Path(
        filename
    ).name


    # ========================================================
    # VALIDATE FILENAME
    # ========================================================

    if not original_filename:

        raise ValueError(
            "Filename cannot be empty."
        )


    # ========================================================
    # DETERMINE EXTENSION
    # ========================================================

    extension = Path(
        original_filename
    ).suffix.lower()


    # ========================================================
    # VALIDATE FILE TYPE
    # ========================================================

    if extension not in ALLOWED_EXTENSIONS:

        raise ValueError(
            "Unsupported file type. "
            "Allowed formats: "
            "PNG, JPG, JPEG, BMP, TIF, TIFF."
        )


    # ========================================================
    # VALIDATE FILE CONTENT
    # ========================================================

    if not file_content:

        raise ValueError(
            "Uploaded file is empty."
        )


    # ========================================================
    # VALIDATE FILE SIZE
    # ========================================================

    file_size = len(
        file_content
    )

    if file_size > MAX_FILE_SIZE:

        raise ValueError(
            "File size exceeds the 10 MB limit."
        )


    # ========================================================
    # DOCUMENT ID
    # ========================================================

    document_id = Path(
        original_filename
    ).stem


    # ========================================================
    # TEMPORARY DIRECTORY
    # ========================================================

    temp_directory = Path(
        tempfile.mkdtemp(
            prefix="intellicapture_"
        )
    )

    temp_file = (
        temp_directory
        / f"{document_id}{extension}"
    )


    try:

        # ====================================================
        # SAVE TEMPORARY UPLOAD
        # ====================================================

        with temp_file.open(
            "wb"
        ) as file:

            file.write(
                file_content
            )


        # ====================================================
        # RUN EXTRACTION PIPELINE
        # ====================================================

        result = process_document(
            temp_file
        )
        # ========================================================
        # SAVE PROCESSED DOCUMENT TO DATABASE
        # ========================================================

        database_document = {
            "document_id": document_id,
            "filename": original_filename,
            "records": result.get(
                "records",
                []
            ),
            "confidence": result.get(
               "confidence",
               {}
            )
        }

        save_document(
            database_document
        )

        # ====================================================
        # BUILD DATABASE DOCUMENT
        # ====================================================

        database_document = {

            "document_id": document_id,

            "filename": original_filename,

            "records": result.get(
                "records",
                []
            ),

            "confidence": result.get(
                "confidence",
                {}
            )
        }


        # ====================================================
        # SAVE TO SQLITE
        # ====================================================

        database_id = save_document(
            database_document
        )


        print(
            f"Document saved to database. "
            f"Database ID: {database_id}"
        )


        # ====================================================
        # RETURN STRUCTURED RESULT
        # ====================================================

        return database_document


    finally:

        # ====================================================
        # CLEAN TEMPORARY FILES
        # ====================================================

        shutil.rmtree(
            temp_directory,
            ignore_errors=True
        )
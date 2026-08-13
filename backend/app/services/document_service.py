from pathlib import Path
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
)  # 10 MB


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

    Returns:
        document_id
        filename
        records
        confidence
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
        # SAVE UPLOADED DOCUMENT
        # ====================================================

        with temp_file.open(
            "wb"
        ) as file:

            file.write(
                file_content
            )


        # ====================================================
        # RUN INTELLICAPTURE PIPELINE
        # ====================================================

        result = process_document(
            temp_file
        )


        # ====================================================
        # EXTRACT RESULTS
        # ====================================================

        records = result.get(
            "records",
            []
        )

        confidence = result.get(
            "confidence",
            {}
        )


        # ====================================================
        # RETURN STRUCTURED RESULT
        # ====================================================

        return {
            "document_id": document_id,
            "filename": original_filename,
            "records": records,
            "confidence": confidence
        }


    finally:

        # ====================================================
        # CLEAN TEMPORARY DIRECTORY
        # ====================================================

        shutil.rmtree(
            temp_directory,
            ignore_errors=True
        )
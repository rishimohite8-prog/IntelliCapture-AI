from pathlib import Path
import sys
import shutil
import tempfile


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

AI_ENGINE_PATH = PROJECT_ROOT / "ai-engine"

if str(AI_ENGINE_PATH) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_PATH))


# ============================================================
# INTELLICAPTURE EXTRACTION ENGINE
# ============================================================

from extraction.pipeline import process_document


# ============================================================
# UPLOAD CONFIGURATION
# ============================================================

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


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

    # --------------------------------------------------------
    # Safe filename
    # --------------------------------------------------------

    original_filename = Path(
        filename
    ).name


    # --------------------------------------------------------
    # Validate filename
    # --------------------------------------------------------

    if not original_filename:

        raise ValueError(
            "Filename cannot be empty."
        )


    # --------------------------------------------------------
    # Determine extension
    # --------------------------------------------------------

    extension = Path(
        original_filename
    ).suffix.lower()


    # --------------------------------------------------------
    # Validate file type
    # --------------------------------------------------------

    if extension not in ALLOWED_EXTENSIONS:

        raise ValueError(
            "Unsupported file type. "
            "Allowed formats: "
            "PNG, JPG, JPEG, BMP, TIF, TIFF."
        )


    # --------------------------------------------------------
    # Validate file content
    # --------------------------------------------------------

    if not file_content:

        raise ValueError(
            "Uploaded file is empty."
        )


    # --------------------------------------------------------
    # Validate file size
    # --------------------------------------------------------

    file_size = len(
        file_content
    )

    if file_size > MAX_FILE_SIZE:

        raise ValueError(
            "File size exceeds the 10 MB limit."
        )


    # --------------------------------------------------------
    # Document ID
    # --------------------------------------------------------

    document_id = Path(
        original_filename
    ).stem


    # --------------------------------------------------------
    # Temporary directory
    # --------------------------------------------------------

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

        # ----------------------------------------------------
        # Save uploaded document
        # ----------------------------------------------------

        with temp_file.open(
            "wb"
        ) as file:

            file.write(
                file_content
            )


        # ----------------------------------------------------
        # Run IntelliCapture pipeline
        # ----------------------------------------------------

        result = process_document(
            temp_file
        )


        # ----------------------------------------------------
        # Return structured result
        # ----------------------------------------------------

        return {
            "document_id": document_id,
            "filename": original_filename,
            "records": result["records"]
        }


    finally:

        # ----------------------------------------------------
        # Clean temporary directory
        # ----------------------------------------------------

        shutil.rmtree(
            temp_directory,
            ignore_errors=True
        )
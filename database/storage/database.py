import sqlite3
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================
# DATABASE PATH
# ============================================================

DATABASE_DIR = Path(__file__).resolve().parent

DATABASE_FILE = DATABASE_DIR / "intellicapture.db"


# ============================================================
# REVIEW STATUS
# ============================================================

REVIEW_PENDING = "PENDING"
REVIEW_APPROVED = "APPROVED"
REVIEW_REJECTED = "REJECTED"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection() -> sqlite3.Connection:
    """
    Create a connection to the IntelliCapture SQLite database.
    """

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database() -> None:
    """
    Create all required database tables and safely migrate
    existing databases when new review fields are introduced.
    """

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # ----------------------------------------------------
        # DOCUMENTS TABLE
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                document_id TEXT NOT NULL UNIQUE,

                filename TEXT NOT NULL,

                records_extracted INTEGER NOT NULL DEFAULT 0,

                average_confidence REAL NOT NULL DEFAULT 0,

                quality TEXT NOT NULL DEFAULT 'LOW',

                records_review_required INTEGER NOT NULL DEFAULT 0,

                fields_review_required INTEGER NOT NULL DEFAULT 0,

                review_status TEXT NOT NULL DEFAULT 'PENDING',

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

            )
            """
        )

        # ----------------------------------------------------
        # RECORDS TABLE
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS records (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                document_id TEXT NOT NULL,

                customer TEXT NOT NULL,

                date TEXT NOT NULL,

                product TEXT NOT NULL,

                amount TEXT NOT NULL,

                confidence REAL NOT NULL DEFAULT 0,

                quality TEXT NOT NULL DEFAULT 'LOW',

                requires_review INTEGER NOT NULL DEFAULT 0,

                review_status TEXT NOT NULL DEFAULT 'PENDING',

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (
                    document_id
                )
                REFERENCES documents (
                    document_id
                )

            )
            """
        )

        # ----------------------------------------------------
        # SAFE MIGRATION FOR EXISTING DATABASES
        # ----------------------------------------------------

        cursor.execute(
            """
            PRAGMA table_info(documents)
            """
        )

        document_columns = {
            row["name"]
            for row in cursor.fetchall()
        }

        if "review_status" not in document_columns:

            cursor.execute(
                """
                ALTER TABLE documents
                ADD COLUMN review_status TEXT NOT NULL DEFAULT 'PENDING'
                """
            )

        # ----------------------------------------------------

        cursor.execute(
            """
            PRAGMA table_info(records)
            """
        )

        record_columns = {
            row["name"]
            for row in cursor.fetchall()
        }

        if "review_status" not in record_columns:

            cursor.execute(
                """
                ALTER TABLE records
                ADD COLUMN review_status TEXT NOT NULL DEFAULT 'PENDING'
                """
            )

        connection.commit()

    finally:

        connection.close()


# ============================================================
# SAVE DOCUMENT
# ============================================================

def save_document(
    document: Dict
) -> int:
    """
    Save a processed document and its extracted records.

    Returns the database row ID.
    """

    initialize_database()

    connection = get_connection()

    try:

        cursor = connection.cursor()

        confidence = document.get(
            "confidence",
            {}
        )

        summary = confidence.get(
            "summary",
            {}
        )

        filename = document.get(
            "filename",
            f"{document['document_id']}.png"
        )

        records = document.get(
            "records",
            []
        )

        average_confidence = summary.get(
            "average_confidence",
            0
        )

        quality = summary.get(
            "quality",
            "LOW"
        )

        records_review_required = summary.get(
            "records_review_required",
            0
        )

        fields_review_required = summary.get(
            "fields_review_required",
            0
        )

        # ----------------------------------------------------
        # Check whether document already exists
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM documents
            WHERE document_id = ?
            """,
            (
                document["document_id"],
            )
        )

        existing_document = cursor.fetchone()

        # ----------------------------------------------------
        # UPDATE existing document
        # ----------------------------------------------------

        if existing_document:

            cursor.execute(
                """
                UPDATE documents

                SET
                    filename = ?,
                    records_extracted = ?,
                    average_confidence = ?,
                    quality = ?,
                    records_review_required = ?,
                    fields_review_required = ?

                WHERE document_id = ?
                """,
                (
                    filename,
                    len(records),
                    average_confidence,
                    quality,
                    records_review_required,
                    fields_review_required,
                    document["document_id"]
                )
            )

        # ----------------------------------------------------
        # INSERT new document
        # ----------------------------------------------------

        else:

            cursor.execute(
                """
                INSERT INTO documents (

                    document_id,
                    filename,
                    records_extracted,
                    average_confidence,
                    quality,
                    records_review_required,
                    fields_review_required,
                    review_status

                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document["document_id"],
                    filename,
                    len(records),
                    average_confidence,
                    quality,
                    records_review_required,
                    fields_review_required,
                    REVIEW_PENDING
                )
            )

        # ----------------------------------------------------
        # Remove previous records
        # ----------------------------------------------------

        cursor.execute(
            """
            DELETE FROM records
            WHERE document_id = ?
            """,
            (
                document["document_id"],
            )
        )

        # ----------------------------------------------------
        # Confidence records
        # ----------------------------------------------------

        confidence_records = confidence.get(
            "records",
            []
        )

        # ----------------------------------------------------
        # Save extracted records
        # ----------------------------------------------------

        for index, record in enumerate(
            records
        ):

            record_confidence = {}

            if index < len(
                confidence_records
            ):

                record_confidence = (
                    confidence_records[index]
                )

            cursor.execute(
                """
                INSERT INTO records (

                    document_id,
                    customer,
                    date,
                    product,
                    amount,
                    confidence,
                    quality,
                    requires_review,
                    review_status

                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document["document_id"],
                    record["customer"],
                    record["date"],
                    record["product"],
                    record["amount"],
                    record_confidence.get(
                        "confidence",
                        0
                    ),
                    record_confidence.get(
                        "quality",
                        "LOW"
                    ),
                    int(
                        record_confidence.get(
                            "requires_review",
                            False
                        )
                    ),
                    REVIEW_PENDING
                )
            )

        connection.commit()

        # ----------------------------------------------------
        # Return document database ID
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM documents
            WHERE document_id = ?
            """,
            (
                document["document_id"],
            )
        )

        saved_document = cursor.fetchone()

        return saved_document["id"]

    finally:

        connection.close()


# ============================================================
# GET DOCUMENT
# ============================================================

def get_document(
    document_id: str
) -> Optional[Dict]:
    """
    Retrieve a document and all its extracted records.
    """

    initialize_database()

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM documents
            WHERE document_id = ?
            """,
            (
                document_id,
            )
        )

        document_row = cursor.fetchone()

        if document_row is None:

            return None

        cursor.execute(
            """
            SELECT *
            FROM records
            WHERE document_id = ?
            ORDER BY id
            """,
            (
                document_id,
            )
        )

        record_rows = cursor.fetchall()

        return {
            "document": dict(
                document_row
            ),
            "records": [
                dict(row)
                for row in record_rows
            ]
        }

    finally:

        connection.close()


# ============================================================
# LIST DOCUMENTS
# ============================================================

def list_documents() -> List[Dict]:
    """
    Return all processed documents.
    """

    initialize_database()

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM documents
            ORDER BY created_at DESC
            """
        )

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


# ============================================================
# UPDATE RECORD
# ============================================================

def update_record(
    record_id: int,
    customer: str,
    date: str,
    product: str,
    amount: str
) -> Optional[Dict]:
    """
    Update an extracted record.

    Returns the updated record.
    Returns None if the record does not exist.
    """

    initialize_database()

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # ----------------------------------------------------
        # Check whether record exists
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM records
            WHERE id = ?
            """,
            (
                record_id,
            )
        )

        existing_record = cursor.fetchone()

        if existing_record is None:

            return None

        # ----------------------------------------------------
        # Update record
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE records

            SET
                customer = ?,
                date = ?,
                product = ?,
                amount = ?

            WHERE id = ?
            """,
            (
                customer,
                date,
                product,
                amount,
                record_id
            )
        )

        connection.commit()

        # ----------------------------------------------------
        # Retrieve updated record
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM records
            WHERE id = ?
            """,
            (
                record_id,
            )
        )

        updated_record = cursor.fetchone()

        if updated_record is None:

            return None

        return dict(
            updated_record
        )

    finally:

        connection.close()

# ============================================================
# UPDATE RECORD REVIEW STATUS
# ============================================================

def update_record_review_status(
    record_id: int,
    review_status: str
) -> Optional[Dict]:
    """
    Update the review status of a record.

    Allowed statuses:
    PENDING
    APPROVED
    REJECTED
    """

    allowed_statuses = {
        "PENDING",
        "APPROVED",
        "REJECTED"
    }

    review_status = review_status.upper()

    if review_status not in allowed_statuses:

        raise ValueError(
            f"Invalid review status: {review_status}"
        )

    initialize_database()

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM records
            WHERE id = ?
            """,
            (
                record_id,
            )
        )

        existing_record = cursor.fetchone()

        if existing_record is None:

            return None

        cursor.execute(
            """
            UPDATE records

            SET review_status = ?

            WHERE id = ?
            """,
            (
                review_status,
                record_id
            )
        )

        connection.commit()

        cursor.execute(
            """
            SELECT *
            FROM records
            WHERE id = ?
            """,
            (
                record_id,
            )
        )

        updated_record = cursor.fetchone()

        if updated_record is None:

            return None

        return dict(
            updated_record
        )

    finally:

        connection.close()


# ============================================================
# GET RECORDS REQUIRING REVIEW
# ============================================================

def get_records_for_review() -> List[Dict]:
    """
    Return records that require human review
    and are still pending.
    """

    initialize_database()

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *

            FROM records

            WHERE
                requires_review = 1

                AND review_status = 'PENDING'

            ORDER BY
                confidence ASC,
                id ASC
            """
        )

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()
        
# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Initializing IntelliCapture database..."
    )

    initialize_database()

    print(
        "Database created at:"
    )

    print(
        DATABASE_FILE
    )

    print(
        "Database initialization successful."
    )
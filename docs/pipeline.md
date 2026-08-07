# IntelliCapture AI — Document Processing Pipeline

## Initial Use Case

The first production use case focuses on extracting structured data from photographed or uploaded tabular records.

## Pipeline

1. File validation
2. Image quality assessment
3. Image preprocessing
4. OCR
5. Layout and table detection
6. Structured data extraction
7. Validation
8. Confidence scoring
9. Human review
10. Database storage
11. Excel / CSV / JSON export

## Design Principle

OCR and intelligent extraction are separate stages.

OCR identifies text and positional information.

The extraction layer interprets the document structure and converts the information into structured data.

## Human-in-the-Loop

The system will not assume that every AI extraction is correct.

Low-confidence values should be highlighted for human review before export.

## Golden Test

A controlled test document with known expected output will be maintained to evaluate extraction accuracy and prevent regressions.

## Initial Output

The primary output for the MVP will be Excel (.xlsx).

Additional outputs:

- CSV
- JSON
# IntelliCapture AI — Evaluation Strategy

## Golden Document #001

Document type:

Sales Register

Purpose:

Evaluate the ability of IntelliCapture AI to extract structured tabular data from a document image.

## Ground Truth

The expected output is stored in:

datasets/golden/document_001/expected/expected.json

## Evaluation Categories

### 1. OCR Accuracy

How accurately does the system recognize the text?

### 2. Structural Accuracy

Does the system correctly identify:

- Rows
- Columns
- Headers
- Cell relationships

### 3. Field Accuracy

Are values assigned to the correct fields?

### 4. Data Type Accuracy

Are:

- Dates recognized as dates?
- Quantities recognized as numbers?
- Amounts recognized as numbers?

### 5. Overall Record Accuracy

Percentage of complete records extracted correctly.

## Initial Target

For a clean printed document:

Target extraction accuracy: >= 95%

The target will be evaluated separately for more difficult documents.

## Human Review

Values with insufficient confidence should be presented to the user for verification rather than silently accepted.

## Regression Testing

Golden documents will be reused whenever the extraction pipeline changes.

A change should not reduce performance on previously validated documents.
import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const REVIEW_PENDING = "PENDING";
const REVIEW_APPROVED = "APPROVED";
const REVIEW_REJECTED = "REJECTED";


function normalizeConfidence(value) {
  const number = Number(value);

  if (Number.isNaN(number)) {
    return 0;
  }

  return Math.max(0, Math.min(100, number));
}


function normalizeReviewStatus(status) {
  const normalized = String(status || REVIEW_PENDING).toUpperCase();

  if (
    normalized === REVIEW_APPROVED ||
    normalized === REVIEW_REJECTED ||
    normalized === REVIEW_PENDING
  ) {
    return normalized;
  }

  return REVIEW_PENDING;
}


function requiresHumanReview(record) {
  return (
    record?.requires_review === true ||
    Number(record?.requires_review) === 1
  );
}


function getQualityClass(quality) {
  const normalized = String(quality || "").toUpperCase();

  if (normalized === "HIGH") {
    return "quality-high";
  }

  if (normalized === "MEDIUM") {
    return "quality-medium";
  }

  return "quality-low";
}


function getReviewClass(status) {
  const normalized = normalizeReviewStatus(status);

  if (normalized === REVIEW_APPROVED) {
    return "review-approved";
  }

  if (normalized === REVIEW_REJECTED) {
    return "review-rejected";
  }

  return "review-pending";
}


function getReviewLabel(status) {
  const normalized = normalizeReviewStatus(status);

  if (normalized === REVIEW_APPROVED) {
    return "APPROVED";
  }

  if (normalized === REVIEW_REJECTED) {
    return "REJECTED";
  }

  return "PENDING";
}


function normalizeRecord(record) {
  return {
    ...record,
    confidence: normalizeConfidence(record?.confidence),
    review_status: normalizeReviewStatus(record?.review_status),
  };
}


function normalizeDocument(document) {
  if (!document) {
    return null;
  }

  return {
    ...document,
    average_confidence: normalizeConfidence(
      document.average_confidence
    ),
    records: Array.isArray(document.records)
      ? document.records.map(normalizeRecord)
      : [],
  };
}


function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);

  const [documents, setDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);

  const [reviewQueue, setReviewQueue] = useState([]);

  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [reviewLoading, setReviewLoading] = useState(false);

  const [updateLoading, setUpdateLoading] = useState(null);
  const [reviewActionLoading, setReviewActionLoading] = useState(null);

  const [error, setError] = useState("");

  const [activePage, setActivePage] = useState("process");

  const [editingRecordId, setEditingRecordId] = useState(null);

  const [editForm, setEditForm] = useState({
    customer: "",
    date: "",
    product: "",
    amount: "",
  });


  useEffect(() => {
    loadDocuments();
    loadReviewQueue();
  }, []);


  async function loadDocuments() {
    try {
      setHistoryLoading(true);

      const response = await fetch(
        `${API_URL}/api/v1/documents`
      );

      if (!response.ok) {
        throw new Error("Failed to load document history.");
      }

      const data = await response.json();

      const normalizedDocuments = Array.isArray(data.documents)
        ? data.documents.map((document) => ({
            ...document,
            average_confidence: normalizeConfidence(
              document.average_confidence
            ),
          }))
        : [];

      setDocuments(normalizedDocuments);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setHistoryLoading(false);
    }
  }


  async function loadReviewQueue() {
    try {
      setReviewLoading(true);

      const response = await fetch(
        `${API_URL}/api/v1/review/queue`
      );

      if (!response.ok) {
        throw new Error("Failed to load human review queue.");
      }

      const data = await response.json();

      const records = Array.isArray(data.records)
        ? data.records.map(normalizeRecord)
        : [];

      setReviewQueue(records);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setReviewLoading(false);
    }
  }


  async function loadDocumentDetails(documentId) {
    const response = await fetch(
      `${API_URL}/api/v1/documents/${documentId}`
    );

    if (!response.ok) {
      throw new Error("Failed to load document details.");
    }

    const data = await response.json();

    return normalizeDocument(data.document);
  }


  async function viewDocument(documentId) {
    try {
      setError("");

      const document = await loadDocumentDetails(documentId);

      setSelectedDocument(document);
      setActivePage("details");
    } catch (requestError) {
      setError(requestError.message);
    }
  }


  async function processDocument() {
    if (!file) {
      setError("Please select a document first.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setResult(null);

      const formData = new FormData();

      formData.append("file", file);

      const response = await fetch(
        `${API_URL}/api/v1/process`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Document processing failed."
        );
      }

      setResult(data);

      await loadDocuments();
      await loadReviewQueue();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }


  function startEditing(record) {
    setEditingRecordId(record.id);

    setEditForm({
      customer: record.customer || "",
      date: record.date || "",
      product: record.product || "",
      amount:
        record.amount === null ||
        record.amount === undefined
          ? ""
          : String(record.amount),
    });
  }


  function cancelEditing() {
    setEditingRecordId(null);

    setEditForm({
      customer: "",
      date: "",
      product: "",
      amount: "",
    });
  }


  async function saveRecord(recordId) {
    if (!selectedDocument) {
      return;
    }

    try {
      setUpdateLoading(recordId);
      setError("");

      const response = await fetch(
        `${API_URL}/api/v1/documents/${selectedDocument.document_id}/records/${recordId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            customer: editForm.customer.trim(),
            date: editForm.date.trim(),
            product: editForm.product.trim(),
            amount: editForm.amount.trim(),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to update record."
        );
      }

      const updatedDocument = await loadDocumentDetails(
        selectedDocument.document_id
      );

      setSelectedDocument(updatedDocument);

      await loadDocuments();
      await loadReviewQueue();

      cancelEditing();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setUpdateLoading(null);
    }
  }


  async function updateReviewStatus(recordId, reviewStatus) {
    try {
      const loadingKey = `${recordId}-${reviewStatus}`;

      setReviewActionLoading(loadingKey);
      setError("");

      const response = await fetch(
        `${API_URL}/api/v1/records/${recordId}/review-status`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            review_status: reviewStatus,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Failed to update review status."
        );
      }

      await loadReviewQueue();
      await loadDocuments();

      if (selectedDocument) {
        const refreshedDocument =
          await loadDocumentDetails(
            selectedDocument.document_id
          );

        setSelectedDocument(refreshedDocument);
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setReviewActionLoading(null);
    }
  }


  function exportCSV(document) {
    if (!document?.records?.length) {
      return;
    }

    const headers = [
      "Customer",
      "Date",
      "Product",
      "Amount",
      "Confidence",
      "Quality",
      "Requires Review",
      "Review Status",
    ];

    const rows = document.records.map((record) => [
      record.customer ?? "",
      record.date ?? "",
      record.product ?? "",
      record.amount ?? "",
      normalizeConfidence(record.confidence).toFixed(1),
      record.quality ?? "",
      requiresHumanReview(record)
        ? "YES"
        : "NO",
      normalizeReviewStatus(record.review_status),
    ]);

    const csvContent = [
      headers,
      ...rows,
    ]
      .map((row) =>
        row
          .map((value) => {
            const text = String(value);
            return `"${text.replace(/"/g, '""')}"`;
          })
          .join(",")
      )
      .join("\n");

    const blob = new Blob(
      [csvContent],
      {
        type: "text/csv;charset=utf-8;",
      }
    );

    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");

    link.href = url;

    link.download =
      `${document.filename || document.document_id}_extracted.csv`;

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  }


  function renderReviewStatus(record) {
    const status = normalizeReviewStatus(
      record?.review_status
    );

    return (
      <div>
        <span
          className={`review-badge ${getReviewClass(status)}`}
        >
          {getReviewLabel(status)}
        </span>

        {requiresHumanReview(record) && (
          <div className="review-required-text">
            Human review required
          </div>
        )}
      </div>
    );
  }


  function renderUploadPage() {
    const records = result?.records || [];

    return (
      <div className="page">
        <div className="hero-section">
          <div className="hero-badge">
            AI DOCUMENT INTELLIGENCE
          </div>

          <h1>
            Turn physical records
            <br />
            into <span>digital assets.</span>
          </h1>

          <p>
            Upload a scanned register, form, or document.
            IntelliCapture-AI extracts structured data,
            evaluates confidence, and routes uncertain
            records for human review.
          </p>
        </div>

        <div className="upload-card">
          <div className="upload-icon">
            ↑
          </div>

          <div className="upload-area">
            <input
              type="file"
              accept="image/*,.pdf"
              onChange={(event) => {
                const selectedFile =
                  event.target.files?.[0] || null;

                setFile(selectedFile);
                setError("");
              }}
            />

            {file ? (
              <div className="selected-file">
                <strong>{file.name}</strong>
                <span>
                  {(file.size / 1024).toFixed(1)} KB
                </span>
              </div>
            ) : (
              <>
                <strong>
                  Drop your document here
                </strong>

                <span>
                  or click to browse
                </span>
              </>
            )}
          </div>

          <button
            className="primary-button process-button"
            onClick={processDocument}
            disabled={loading || !file}
          >
            {loading
              ? "Processing..."
              : "Process Document"}
          </button>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {result && (
          <div className="result-section">
            <div className="section-header">
              <div>
                <div className="section-label">
                  EXTRACTION COMPLETE
                </div>

                <h2>
                  {result.filename ||
                    file?.name ||
                    "Processed Document"}
                </h2>
              </div>
            </div>

            <div className="summary-grid">
              <div className="summary-card">
                <span>Records Extracted</span>
                <strong>
                  {result.records?.length || 0}
                </strong>
              </div>

              <div className="summary-card">
                <span>Average Confidence</span>
                <strong>
                  {normalizeConfidence(
                    result.average_confidence
                  ).toFixed(1)}
                  %
                </strong>
              </div>

              <div className="summary-card">
                <span>Quality</span>
                <strong
                  className={getQualityClass(
                    result.quality
                  )}
                >
                  {result.quality || "UNKNOWN"}
                </strong>
              </div>

              <div className="summary-card">
                <span>Review Required</span>
                <strong>
                  {result.records?.filter(
                    requiresHumanReview
                  ).length || 0}
                </strong>
              </div>
            </div>

            <div className="table-card">
              <div className="section-heading">
                Extracted Records
              </div>

              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Customer</th>
                      <th>Date</th>
                      <th>Product</th>
                      <th>Amount</th>
                      <th>Confidence</th>
                      <th>Quality</th>
                      <th>Review Status</th>
                    </tr>
                  </thead>

                  <tbody>
                    {records.map((record, index) => (
                      <tr key={record.id || index}>
                        <td>
                          {record.customer}
                        </td>

                        <td>
                          {record.date}
                        </td>

                        <td>
                          {record.product}
                        </td>

                        <td>
                          {record.amount}
                        </td>

                        <td>
                          {normalizeConfidence(
                            record.confidence
                          ).toFixed(1)}
                          %
                        </td>

                        <td>
                          <span
                            className={`quality-badge ${getQualityClass(
                              record.quality
                            )}`}
                          >
                            {record.quality ||
                              "UNKNOWN"}
                          </span>
                        </td>

                        <td>
                          {renderReviewStatus(record)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }


  function renderHistoryPage() {
    return (
      <div className="page">
        <div className="page-header">
          <div>
            <div className="section-label">
              DOCUMENT LIBRARY
            </div>

            <h1>Document History</h1>

            <p>
              View previously processed documents
              and inspect their extracted records.
            </p>
          </div>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {historyLoading ? (
          <div className="loading-card">
            Loading document history...
          </div>
        ) : documents.length === 0 ? (
          <div className="empty-card">
            <div className="empty-icon">
              ◫
            </div>

            <h3>No documents yet</h3>

            <p>
              Process your first document to see it
              appear here.
            </p>
          </div>
        ) : (
          <div className="history-grid">
            {documents.map((document) => (
              <div
                className="history-card"
                key={document.document_id}
              >
                <div className="history-card-header">
                  <div className="document-icon">
                    DOC
                  </div>

                  <div>
                    <div className="document-id">
                      {document.document_id}
                    </div>

                    <strong>
                      {document.filename}
                    </strong>
                  </div>
                </div>

                <div className="history-stats">
                  <div>
                    <span>Records</span>
                    <strong>
                      {document.records_extracted || 0}
                    </strong>
                  </div>

                  <div>
                    <span>Confidence</span>
                    <strong>
                      {normalizeConfidence(
                        document.average_confidence
                      ).toFixed(1)}
                      %
                    </strong>
                  </div>

                  <div>
                    <span>Review</span>
                    <strong>
                      {document.records_review_required ||
                        0}
                    </strong>
                  </div>
                </div>

                <button
                  className="view-button"
                  onClick={() =>
                    viewDocument(
                      document.document_id
                    )
                  }
                >
                  View Document →
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }


  function renderReviewPage() {
    return (
      <div className="page">
        <div className="page-header">
          <div>
            <div className="section-label">
              HUMAN-IN-THE-LOOP
            </div>

            <h1>Human Review</h1>

            <p>
              Review records flagged by IntelliCapture-AI
              before they become trusted digital data.
            </p>
          </div>

          <div className="header-actions">
            <button
              className="secondary-button"
              onClick={loadReviewQueue}
              disabled={reviewLoading}
            >
              {reviewLoading
                ? "Refreshing..."
                : "Refresh Queue"}
            </button>
          </div>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <div className="summary-grid">
          <div className="summary-card">
            <span>Pending Review</span>
            <strong>
              {reviewQueue.length}
            </strong>
          </div>

          <div className="summary-card">
            <span>Lowest Confidence</span>
            <strong>
              {reviewQueue.length
                ? `${normalizeConfidence(
                    reviewQueue[0].confidence
                  ).toFixed(1)}%`
                : "—"}
            </strong>
          </div>

          <div className="summary-card">
            <span>Workflow</span>
            <strong>
              HUMAN
            </strong>
          </div>

          <div className="summary-card">
            <span>Status</span>
            <strong
              className={
                reviewQueue.length
                  ? "quality-medium"
                  : "quality-high"
              }
            >
              {reviewQueue.length
                ? "ACTION NEEDED"
                : "CLEAR"}
            </strong>
          </div>
        </div>

        {reviewLoading ? (
          <div className="loading-card">
            Loading review queue...
          </div>
        ) : reviewQueue.length === 0 ? (
          <div className="empty-card">
            <div className="empty-icon">
              ✓
            </div>

            <h3>
              Review queue is clear
            </h3>

            <p>
              There are currently no extracted
              records waiting for human review.
            </p>
          </div>
        ) : (
          <div className="review-queue">
            {reviewQueue.map((record) => {
              const approveKey =
                `${record.id}-${REVIEW_APPROVED}`;

              const rejectKey =
                `${record.id}-${REVIEW_REJECTED}`;

              return (
                <div
                  className="review-queue-card"
                  key={record.id}
                >
                  <div className="review-queue-header">
                    <div>
                      <div className="section-label">
                        RECORD #{record.id}
                      </div>

                      <h3>
                        {record.customer ||
                          "Unknown Customer"}
                      </h3>

                      <span className="review-document-id">
                        {record.document_id}
                      </span>
                    </div>

                    <div className="review-confidence">
                      <span>Confidence</span>

                      <strong>
                        {normalizeConfidence(
                          record.confidence
                        ).toFixed(1)}
                        %
                      </strong>
                    </div>
                  </div>

                  <div className="review-record-grid">
                    <div>
                      <span>Customer</span>
                      <strong>
                        {record.customer || "—"}
                      </strong>
                    </div>

                    <div>
                      <span>Date</span>
                      <strong>
                        {record.date || "—"}
                      </strong>
                    </div>

                    <div>
                      <span>Product</span>
                      <strong>
                        {record.product || "—"}
                      </strong>
                    </div>

                    <div>
                      <span>Amount</span>
                      <strong>
                        {record.amount || "—"}
                      </strong>
                    </div>

                    <div>
                      <span>Extraction Quality</span>
                      <strong
                        className={getQualityClass(
                          record.quality
                        )}
                      >
                        {record.quality || "UNKNOWN"}
                      </strong>
                    </div>

                    <div>
                      <span>Review Status</span>
                      {renderReviewStatus(record)}
                    </div>
                  </div>

                  <div className="review-actions">
                    <button
                      className="view-button"
                      onClick={() =>
                        viewDocument(
                          record.document_id
                        )
                      }
                    >
                      Open Document
                    </button>

                    <button
                      className="review-reject-button"
                      onClick={() =>
                        updateReviewStatus(
                          record.id,
                          REVIEW_REJECTED
                        )
                      }
                      disabled={
                        reviewActionLoading ===
                        rejectKey
                      }
                    >
                      {reviewActionLoading ===
                      rejectKey
                        ? "Rejecting..."
                        : "Reject"}
                    </button>

                    <button
                      className="review-approve-button"
                      onClick={() =>
                        updateReviewStatus(
                          record.id,
                          REVIEW_APPROVED
                        )
                      }
                      disabled={
                        reviewActionLoading ===
                        approveKey
                      }
                    >
                      {reviewActionLoading ===
                      approveKey
                        ? "Approving..."
                        : "Approve"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  }


  function renderDetailsPage() {
    if (!selectedDocument) {
      return (
        <div className="page">
          <div className="empty-card">
            <h3>
              No document selected
            </h3>

            <p>
              Select a document from history.
            </p>
          </div>
        </div>
      );
    }

    const records =
      selectedDocument.records || [];

    const averageConfidence =
      normalizeConfidence(
        selectedDocument.average_confidence
      );

    return (
      <div className="page">
        <div className="page-header">
          <div>
            <div className="section-label">
              DOCUMENT DETAILS
            </div>

            <h1>
              {selectedDocument.filename}
            </h1>

            <p>
              {selectedDocument.document_id}
            </p>
          </div>

          <div className="header-actions">
            <button
              className="secondary-button"
              onClick={() =>
                exportCSV(selectedDocument)
              }
            >
              Export CSV
            </button>
          </div>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <div className="summary-grid">
          <div className="summary-card">
            <span>Records</span>

            <strong>
              {records.length}
            </strong>
          </div>

          <div className="summary-card">
            <span>Average Confidence</span>

            <strong>
              {averageConfidence.toFixed(1)}%
            </strong>
          </div>

          <div className="summary-card">
            <span>Quality</span>

            <strong
              className={getQualityClass(
                selectedDocument.quality
              )}
            >
              {selectedDocument.quality ||
                "UNKNOWN"}
            </strong>
          </div>

          <div className="summary-card">
            <span>Needs Review</span>

            <strong>
              {records.filter(
                requiresHumanReview
              ).length}
            </strong>
          </div>
        </div>

        <div className="table-card">
          <div className="section-heading">
            Extracted Records
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Customer</th>
                  <th>Date</th>
                  <th>Product</th>
                  <th>Amount</th>
                  <th>Confidence</th>
                  <th>Quality</th>
                  <th>Review Status</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {records.map((record) => {
                  const isEditing =
                    editingRecordId === record.id;

                  const approveKey =
                    `${record.id}-${REVIEW_APPROVED}`;

                  const rejectKey =
                    `${record.id}-${REVIEW_REJECTED}`;

                  return (
                    <tr key={record.id}>
                      <td>
                        {isEditing ? (
                          <input
                            value={editForm.customer}
                            onChange={(event) =>
                              setEditForm({
                                ...editForm,
                                customer:
                                  event.target.value,
                              })
                            }
                          />
                        ) : (
                          record.customer
                        )}
                      </td>

                      <td>
                        {isEditing ? (
                          <input
                            value={editForm.date}
                            onChange={(event) =>
                              setEditForm({
                                ...editForm,
                                date:
                                  event.target.value,
                              })
                            }
                          />
                        ) : (
                          record.date
                        )}
                      </td>

                      <td>
                        {isEditing ? (
                          <input
                            value={editForm.product}
                            onChange={(event) =>
                              setEditForm({
                                ...editForm,
                                product:
                                  event.target.value,
                              })
                            }
                          />
                        ) : (
                          record.product
                        )}
                      </td>

                      <td>
                        {isEditing ? (
                          <input
                            value={editForm.amount}
                            onChange={(event) =>
                              setEditForm({
                                ...editForm,
                                amount:
                                  event.target.value,
                              })
                            }
                          />
                        ) : (
                          record.amount
                        )}
                      </td>

                      <td>
                        {normalizeConfidence(
                          record.confidence
                        ).toFixed(1)}
                        %
                      </td>

                      <td>
                        <span
                          className={`quality-badge ${getQualityClass(
                            record.quality
                          )}`}
                        >
                          {record.quality ||
                            "UNKNOWN"}
                        </span>
                      </td>

                      <td>
                        {renderReviewStatus(record)}
                      </td>

                      <td>
                        {isEditing ? (
                          <div className="action-buttons">
                            <button
                              className="small-button"
                              onClick={() =>
                                saveRecord(record.id)
                              }
                              disabled={
                                updateLoading ===
                                record.id
                              }
                            >
                              {updateLoading ===
                              record.id
                                ? "Saving..."
                                : "Save"}
                            </button>

                            <button
                              className="small-button"
                              onClick={
                                cancelEditing
                              }
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <div className="action-buttons">
                            <button
                              className="small-button"
                              onClick={() =>
                                startEditing(record)
                              }
                            >
                              Edit
                            </button>

                            {normalizeReviewStatus(
                              record.review_status
                            ) ===
                              REVIEW_PENDING && (
                              <>
                                <button
                                  className="small-button review-action-small approve"
                                  onClick={() =>
                                    updateReviewStatus(
                                      record.id,
                                      REVIEW_APPROVED
                                    )
                                  }
                                  disabled={
                                    reviewActionLoading ===
                                    approveKey
                                  }
                                >
                                  {reviewActionLoading ===
                                  approveKey
                                    ? "..."
                                    : "Approve"}
                                </button>

                                <button
                                  className="small-button review-action-small reject"
                                  onClick={() =>
                                    updateReviewStatus(
                                      record.id,
                                      REVIEW_REJECTED
                                    )
                                  }
                                  disabled={
                                    reviewActionLoading ===
                                    rejectKey
                                  }
                                >
                                  {reviewActionLoading ===
                                  rejectKey
                                    ? "..."
                                    : "Reject"}
                                </button>
                              </>
                            )}
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="confidence-card">
          <div className="section-heading">
            Confidence Analysis
          </div>

          <div className="confidence-overview">
            <div className="confidence-main">
              <span>
                Overall Confidence
              </span>

              <strong>
                {averageConfidence.toFixed(1)}%
              </strong>

              <div className="confidence-bar">
                <div
                  className="confidence-fill"
                  style={{
                    width: `${averageConfidence}%`,
                  }}
                />
              </div>
            </div>

            <div className="confidence-stat">
              <span>High Quality</span>

              <strong>
                {
                  records.filter(
                    (record) =>
                      String(
                        record.quality
                      ).toUpperCase() ===
                      "HIGH"
                  ).length
                }
              </strong>
            </div>

            <div className="confidence-stat">
              <span>Needs Review</span>

              <strong>
                {
                  records.filter(
                    requiresHumanReview
                  ).length
                }
              </strong>
            </div>
          </div>

          <div className="confidence-grid">
            {records.map((record) => (
              <div
                className="confidence-record"
                key={record.id}
              >
                <div className="confidence-header">
                  <strong>
                    {record.customer ||
                      `Record ${record.id}`}
                  </strong>

                  <span>
                    {normalizeConfidence(
                      record.confidence
                    ).toFixed(1)}
                    %
                  </span>
                </div>

                <div className="field-list">
                  <div className="field-row">
                    <span>Customer</span>
                    <strong>
                      {record.customer ||
                        "Missing"}
                    </strong>
                  </div>

                  <div className="field-row">
                    <span>Date</span>
                    <strong>
                      {record.date ||
                        "Missing"}
                    </strong>
                  </div>

                  <div className="field-row">
                    <span>Product</span>
                    <strong>
                      {record.product ||
                        "Missing"}
                    </strong>
                  </div>

                  <div className="field-row">
                    <span>Amount</span>
                    <strong>
                      {record.amount ||
                        "Missing"}
                    </strong>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }


  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">
            IC
          </div>

          <div>
            <strong>
              IntelliCapture
            </strong>

            <span>
              AI
            </span>
          </div>
        </div>

        <nav className="navigation">
          <button
            className={`nav-item ${
              activePage === "process"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setActivePage("process")
            }
          >
            <span>＋</span>
            Process Document
          </button>

          <button
            className={`nav-item ${
              activePage === "review"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setActivePage("review")
            }
          >
            <span>✓</span>

            Human Review

            {reviewQueue.length > 0 && (
              <span className="review-count">
                {reviewQueue.length}
              </span>
            )}
          </button>

          <button
            className={`nav-item ${
              activePage === "history"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setActivePage("history")
            }
          >
            <span>◫</span>
            Document History
          </button>
        </nav>

        <div className="sidebar-footer">
          <span>
            IntelliCapture-AI
          </span>

          <small>
            Document Intelligence Platform
          </small>
        </div>
      </aside>

      <main className="main-content">
        {activePage === "process" &&
          renderUploadPage()}

        {activePage === "history" &&
          renderHistoryPage()}

        {activePage === "review" &&
          renderReviewPage()}

        {activePage === "details" &&
          renderDetailsPage()}
      </main>
    </div>
  );
}


export default App;
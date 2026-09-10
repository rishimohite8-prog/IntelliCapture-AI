import React, { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);

  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [updateLoading, setUpdateLoading] = useState(false);

  const [error, setError] = useState("");

  const [activePage, setActivePage] = useState("upload");

  const [editingRecordId, setEditingRecordId] = useState(null);

  const [editForm, setEditForm] = useState({
    customer: "",
    date: "",
    product: "",
    amount: "",
  });

  // ============================================================
  // QUALITY HELPERS
  // ============================================================

  const getQualityFromConfidence = (confidence) => {
    const value = Number(confidence);

    if (!Number.isFinite(value)) {
      return "LOW";
    }

    if (value >= 85) {
      return "HIGH";
    }

    if (value >= 65) {
      return "MEDIUM";
    }

    return "LOW";
  };

  const getQualityClass = (quality, confidence = null) => {
    let normalized = String(quality || "").toUpperCase();

    if (
      !["HIGH", "MEDIUM", "LOW"].includes(normalized) &&
      confidence !== null
    ) {
      normalized = getQualityFromConfidence(confidence);
    }

    if (normalized === "HIGH") {
      return "quality-high";
    }

    if (normalized === "MEDIUM") {
      return "quality-medium";
    }

    return "quality-low";
  };

  // ============================================================
  // CONFIDENCE HELPERS
  // ============================================================

  const getConfidenceRecord = (confidenceData, index) => {
    return confidenceData?.records?.[index] || null;
  };

  const getRecordConfidence = (
    record,
    confidenceRecord
  ) => {
    if (
      record?.confidence !== undefined &&
      record?.confidence !== null &&
      Number(record.confidence) > 0
    ) {
      return Number(record.confidence);
    }

    if (
      confidenceRecord?.confidence !== undefined &&
      confidenceRecord?.confidence !== null
    ) {
      return Number(confidenceRecord.confidence);
    }

    return 0;
  };

  const getRecordQuality = (
    record,
    confidenceRecord
  ) => {
    const confidence = getRecordConfidence(
      record,
      confidenceRecord
    );

    const databaseQuality = String(
      record?.quality || ""
    ).toUpperCase();

    if (
      ["HIGH", "MEDIUM", "LOW"].includes(
        databaseQuality
      ) &&
      confidence > 0
    ) {
      return databaseQuality;
    }

    const confidenceQuality = String(
      confidenceRecord?.quality || ""
    ).toUpperCase();

    if (
      ["HIGH", "MEDIUM", "LOW"].includes(
        confidenceQuality
      )
    ) {
      return confidenceQuality;
    }

    return getQualityFromConfidence(confidence);
  };

  const getRequiresReview = (
    record,
    confidenceRecord
  ) => {
    if (
      record?.requires_review !== undefined &&
      record?.requires_review !== null
    ) {
      return Boolean(record.requires_review);
    }

    if (
      confidenceRecord?.requires_review !== undefined
    ) {
      return Boolean(
        confidenceRecord.requires_review
      );
    }

    const confidence = getRecordConfidence(
      record,
      confidenceRecord
    );

    return confidence < 85;
  };

  // ============================================================
  // LOAD DOCUMENT HISTORY
  // ============================================================

  const loadDocuments = async () => {
    try {
      setHistoryLoading(true);
      setError("");

      const response = await axios.get(
        `${API_URL}/api/v1/documents`
      );

      const data = response.data || [];

      const normalizedDocuments = data.map(
        (document) => {
          const confidence = Number(
            document.average_confidence
          );

          const quality =
            document.quality &&
            String(document.quality).toUpperCase() !==
              "UNKNOWN"
              ? document.quality
              : getQualityFromConfidence(
                  confidence
                );

          return {
            ...document,
            average_confidence:
              Number.isFinite(confidence)
                ? confidence
                : 0,
            quality,
            records_review_required:
              Number(
                document.records_review_required
              ) || 0,
          };
        }
      );

      setDocuments(normalizedDocuments);
    } catch (err) {
      console.error(err);

      setError(
        err?.response?.data?.detail ||
          "Failed to load document history."
      );
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  // ============================================================
  // FILE SELECTION
  // ============================================================

  const handleFileChange = (event) => {
    const selectedFile =
      event.target.files?.[0];

    if (!selectedFile) {
      return;
    }

    setFile(selectedFile);
    setResult(null);
    setSelectedDocument(null);
    setError("");
  };

  // ============================================================
  // PROCESS DOCUMENT
  // ============================================================

  const processDocument = async () => {
    if (!file) {
      setError(
        "Please select a document first."
      );
      return;
    }

    try {
      setLoading(true);
      setError("");
      setResult(null);

      const formData = new FormData();

      formData.append("file", file);

      const response = await axios.post(
        `${API_URL}/api/v1/process`,
        formData,
        {
          headers: {
            "Content-Type":
              "multipart/form-data",
          },
        }
      );

      const data = response.data || {};

      // Keep the backend confidence structure.
      setResult(data);

      await loadDocuments();
    } catch (err) {
      console.error(err);

      setError(
        err?.response?.data?.detail ||
          "Document processing failed."
      );
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // VIEW DOCUMENT
  // ============================================================

  const viewDocument = async (
    documentId
  ) => {
    try {
      setHistoryLoading(true);
      setError("");
      setEditingRecordId(null);

      const response = await axios.get(
        `${API_URL}/api/v1/documents/${documentId}`
      );

      const data = response.data || {};

      /*
       * Backend returns:
       *
       * {
       *   document: {...},
       *   records: [...]
       * }
       */

      const documentInfo =
        data.document || data;

      const records =
        data.records ||
        documentInfo.records ||
        [];

      const averageConfidence = Number(
        documentInfo.average_confidence
      );

      const normalizedDocument = {
        ...documentInfo,
        records,
        average_confidence:
          Number.isFinite(
            averageConfidence
          )
            ? averageConfidence
            : 0,
        quality:
          documentInfo.quality &&
          String(
            documentInfo.quality
          ).toUpperCase() !== "UNKNOWN"
            ? documentInfo.quality
            : getQualityFromConfidence(
                averageConfidence
              ),
      };

      setSelectedDocument(
        normalizedDocument
      );

      setActivePage("details");
    } catch (err) {
      console.error(err);

      setError(
        err?.response?.data?.detail ||
          "Failed to load document."
      );
    } finally {
      setHistoryLoading(false);
    }
  };

  // ============================================================
  // START EDIT
  // ============================================================

  const startEditRecord = (
    record
  ) => {
    setEditingRecordId(record.id);

    setEditForm({
      customer: record.customer ?? "",
      date: record.date ?? "",
      product: record.product ?? "",
      amount: record.amount ?? "",
    });
  };

  // ============================================================
  // CANCEL EDIT
  // ============================================================

  const cancelEditRecord = () => {
    setEditingRecordId(null);

    setEditForm({
      customer: "",
      date: "",
      product: "",
      amount: "",
    });
  };

  // ============================================================
  // EDIT CHANGE
  // ============================================================

  const handleEditChange = (
    event
  ) => {
    const {
      name,
      value,
    } = event.target;

    setEditForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  // ============================================================
  // UPDATE RECORD
  // ============================================================

  const updateRecord = async (
    recordId
  ) => {
    if (!selectedDocument?.document_id) {
      setError(
        "Document information is missing."
      );
      return;
    }

    try {
      setUpdateLoading(true);
      setError("");

      const payload = {
        customer: editForm.customer,
        date: editForm.date,
        product: editForm.product,
        amount:
          editForm.amount === ""
            ? null
            : Number(editForm.amount),
      };

      await axios.put(
        `${API_URL}/api/v1/documents/${selectedDocument.document_id}/records/${recordId}`,
        payload
      );

      await viewDocument(
        selectedDocument.document_id
      );

      await loadDocuments();

      setEditingRecordId(null);
    } catch (err) {
      console.error(err);

      setError(
        err?.response?.data?.detail ||
          "Failed to update record."
      );
    } finally {
      setUpdateLoading(false);
    }
  };

  // ============================================================
  // CSV EXPORT
  // ============================================================

  const exportCSV = (
    documentData
  ) => {
    if (
      !documentData?.records?.length
    ) {
      setError(
        "No records available for CSV export."
      );
      return;
    }

    const confidenceData =
      documentData.confidence;

    const headers = [
      "ID",
      "Customer",
      "Date",
      "Product",
      "Amount",
      "Confidence",
      "Quality",
      "Review Status",
    ];

    const rows =
      documentData.records.map(
        (record, index) => {
          const confidenceRecord =
            getConfidenceRecord(
              confidenceData,
              index
            );

          const confidence =
            getRecordConfidence(
              record,
              confidenceRecord
            );

          const quality =
            getRecordQuality(
              record,
              confidenceRecord
            );

          const requiresReview =
            getRequiresReview(
              record,
              confidenceRecord
            );

          return [
            record.id ?? index + 1,
            record.customer ?? "",
            record.date ?? "",
            record.product ?? "",
            record.amount ?? "",
            confidence
              ? confidence.toFixed(2)
              : "",
            quality,
            requiresReview
              ? "NEEDS REVIEW"
              : "NO REVIEW NEEDED",
          ];
        }
      );

    const csvContent = [
      headers,
      ...rows,
    ]
      .map((row) =>
        row
          .map((value) => {
            const stringValue =
              String(value ?? "");

            return `"${stringValue.replace(
              /"/g,
              '""'
            )}"`;
          })
          .join(",")
      )
      .join("\n");

    const blob = new Blob(
      [csvContent],
      {
        type:
          "text/csv;charset=utf-8;",
      }
    );

    const url =
      URL.createObjectURL(blob);

    const link =
      document.createElement("a");

    link.href = url;

    link.download = `${
      documentData.filename ||
      documentData.document_id ||
      "intellicapture"
    }_extracted.csv`;

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  };

  // ============================================================
  // NAVIGATION
  // ============================================================

  const openUploadPage = () => {
    setActivePage("upload");
    setError("");
  };

  const openHistoryPage = async () => {
    setActivePage("history");
    setError("");

    await loadDocuments();
  };

  // ============================================================
  // UPLOAD PAGE
  // ============================================================

  const renderUploadPage = () => {
    const confidenceData =
      result?.confidence;

    const summary =
      confidenceData?.summary || {};

    const averageConfidence =
      Number(
        summary.average_confidence
      );

    const documentQuality =
      summary.quality &&
      String(summary.quality)
        .toUpperCase() !== "UNKNOWN"
        ? summary.quality
        : getQualityFromConfidence(
            averageConfidence
          );

    const reviewRequired =
      Number(
        summary.records_review_required
      ) || 0;

    return (
      <div className="page">

        <div className="hero-section">
          <div className="hero-badge">
            AI DOCUMENT INTELLIGENCE
          </div>

          <h1>
            Turn Physical Records
            <br />
            Into{" "}
            <span>Digital Assets.</span>
          </h1>

          <p>
            Upload a physical document and let
            IntelliCapture-AI extract structured,
            validated and confidence-scored data.
          </p>
        </div>

        <div className="upload-card">

          <div className="upload-icon">
            📄
          </div>

          <h2>
            Upload Document
          </h2>

          <p>
            Upload a register, form, bill, or
            document image for AI-powered
            extraction.
          </p>

          <div className="upload-area">

            <input
              type="file"
              accept="image/*,.pdf"
              onChange={
                handleFileChange
              }
            />

            {file && (
              <div className="selected-file">
                <strong>
                  Selected:
                </strong>{" "}
                {file.name}
              </div>
            )}
          </div>

          <button
            className="primary-button process-button"
            onClick={
              processDocument
            }
            disabled={
              !file || loading
            }
          >
            {loading
              ? "Processing Document..."
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
                  PROCESSING RESULT
                </div>

                <h2>
                  Extracted Information
                </h2>

                <p>
                  Structured data and confidence
                  analysis generated by the
                  IntelliCapture pipeline.
                </p>
              </div>

              <button
                className="secondary-button"
                onClick={() =>
                  exportCSV(result)
                }
              >
                Export CSV
              </button>
            </div>

            <div className="summary-grid">

              <div className="summary-card">
                <span>
                  DOCUMENT ID
                </span>

                <strong>
                  {result.document_id ||
                    "N/A"}
                </strong>
              </div>

              <div className="summary-card">
                <span>
                  RECORDS EXTRACTED
                </span>

                <strong>
                  {result.records_extracted ??
                    result.records?.length ??
                    0}
                </strong>
              </div>

              <div className="summary-card">
                <span>
                  AVERAGE CONFIDENCE
                </span>

                <strong>
                  {Number.isFinite(
                    averageConfidence
                  )
                    ? `${averageConfidence.toFixed(
                        2
                      )}%`
                    : "0.00%"}
                </strong>
              </div>

              <div className="summary-card">
                <span>
                  DOCUMENT QUALITY
                </span>

                <span
                  className={`quality-badge ${getQualityClass(
                    documentQuality,
                    averageConfidence
                  )}`}
                >
                  {documentQuality}
                </span>
              </div>

            </div>

            <div className="table-card">

              <div className="section-heading">
                <div>
                  <h2>
                    Extracted Records
                  </h2>

                  <p>
                    Review extracted values and
                    confidence status.
                  </p>
                </div>
              </div>

              <div className="table-wrapper">

                <table>

                  <thead>
                    <tr>
                      <th>ID</th>
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

                    {(result.records || []).map(
                      (
                        record,
                        index
                      ) => {

                        const confidenceRecord =
                          getConfidenceRecord(
                            confidenceData,
                            index
                          );

                        const confidence =
                          getRecordConfidence(
                            record,
                            confidenceRecord
                          );

                        const quality =
                          getRecordQuality(
                            record,
                            confidenceRecord
                          );

                        const requiresReview =
                          getRequiresReview(
                            record,
                            confidenceRecord
                          );

                        return (
                          <tr
                            key={
                              record.id ||
                              index
                            }
                          >

                            <td>
                              {record.id ??
                                index + 1}
                            </td>

                            <td>
                              {record.customer ??
                                "-"}
                            </td>

                            <td>
                              {record.date ??
                                "-"}
                            </td>

                            <td>
                              {record.product ??
                                "-"}
                            </td>

                            <td>
                              ₹{" "}
                              {record.amount ??
                                "-"}
                            </td>

                            <td>
                              {confidence.toFixed(
                                2
                              )}
                              %
                            </td>

                            <td>
                              <span
                                className={`quality-badge ${getQualityClass(
                                  quality,
                                  confidence
                                )}`}
                              >
                                {quality}
                              </span>
                            </td>

                            <td>
                              <span
                                className={`review-badge ${
                                  requiresReview
                                    ? "review-needed"
                                    : "review-clear"
                                }`}
                              >
                                {requiresReview
                                  ? "NEEDS REVIEW"
                                  : "NO REVIEW NEEDED"}
                              </span>
                            </td>

                          </tr>
                        );
                      }
                    )}

                  </tbody>

                </table>

              </div>

            </div>

            <div className="confidence-card">

              <div className="section-heading">
                <div>
                  <h2>
                    Confidence Analysis
                  </h2>

                  <p>
                    Field-level confidence generated
                    by the extraction engine.
                  </p>
                </div>
              </div>

              <div className="confidence-overview">

                <div className="confidence-main">

                  <span>
                    OVERALL CONFIDENCE
                  </span>

                  <strong>
                    {Number.isFinite(
                      averageConfidence
                    )
                      ? `${averageConfidence.toFixed(
                          2
                        )}%`
                      : "0.00%"}
                  </strong>

                  <div className="confidence-bar">
                    <div
                      className="confidence-fill"
                      style={{
                        width: `${Math.min(
                          Math.max(
                            averageConfidence,
                            0
                          ),
                          100
                        )}%`,
                      }}
                    />
                  </div>

                </div>

                <div className="confidence-stat">
                  <span>
                    QUALITY
                  </span>

                  <span
                    className={`quality-badge ${getQualityClass(
                      documentQuality,
                      averageConfidence
                    )}`}
                  >
                    {documentQuality}
                  </span>
                </div>

                <div className="confidence-stat">
                  <span>
                    REVIEW REQUIRED
                  </span>

                  <strong>
                    {reviewRequired}
                  </strong>
                </div>

              </div>

              <div className="confidence-grid">

                {(
                  confidenceData?.records ||
                  []
                ).map(
                  (
                    confidenceRecord,
                    index
                  ) => {

                    const sourceRecord =
                      result.records?.[
                        index
                      ];

                    return (
                      <div
                        className="confidence-record"
                        key={index}
                      >

                        <div className="confidence-header">

                          <strong>
                            {sourceRecord?.customer ||
                              `Record ${
                                index + 1
                              }`}
                          </strong>

                          <span
                            className={`quality-badge ${getQualityClass(
                              confidenceRecord.quality,
                              confidenceRecord.confidence
                            )}`}
                          >
                            {Number(
                              confidenceRecord.confidence ||
                                0
                            ).toFixed(2)}
                            %
                          </span>

                        </div>

                        <div className="field-list">

                          {Object.entries(
                            confidenceRecord.fields ||
                              {}
                          ).map(
                            (
                              [
                                field,
                                data,
                              ]
                            ) => (
                              <div
                                className="field-row"
                                key={field}
                              >
                                <span>
                                  {field}
                                </span>

                                <span>
                                  {Number(
                                    data?.confidence ||
                                      0
                                  ).toFixed(
                                    2
                                  )}
                                  %
                                </span>
                              </div>
                            )
                          )}

                        </div>

                      </div>
                    );
                  }
                )}

              </div>

            </div>

          </div>
        )}

      </div>
    );
  };

  // ============================================================
  // HISTORY PAGE
  // ============================================================

  const renderHistoryPage = () => {
    return (
      <div className="page">

        <div className="page-header">

          <div>
            <div className="section-label">
              ARCHIVE
            </div>

            <h1>
              Document History
            </h1>

            <p>
              Previously processed documents
              and extraction results.
            </p>
          </div>

          <button
            className="secondary-button"
            onClick={
              loadDocuments
            }
            disabled={
              historyLoading
            }
          >
            {historyLoading
              ? "Refreshing..."
              : "Refresh"}
          </button>

        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {historyLoading &&
        documents.length === 0 ? (
          <div className="loading-card">
            Loading document history...
          </div>
        ) : documents.length === 0 ? (
          <div className="empty-card">
            <div className="empty-icon">
              📂
            </div>

            <h3>
              No documents yet
            </h3>

            <p>
              Process a document to see it
              appear here.
            </p>
          </div>
        ) : (
          <div className="history-grid">

            {documents.map(
              (document) => {

                const confidence =
                  Number(
                    document.average_confidence
                  ) || 0;

                const quality =
                  document.quality ||
                  getQualityFromConfidence(
                    confidence
                  );

                return (
                  <div
                    className="history-card"
                    key={
                      document.document_id
                    }
                  >

                    <div className="history-card-header">

                      <div className="document-icon">
                        📄
                      </div>

                      <span
                        className={`quality-badge ${getQualityClass(
                          quality,
                          confidence
                        )}`}
                      >
                        {quality}
                      </span>

                    </div>

                    <h3>
                      {document.filename ||
                        document.document_id}
                    </h3>

                    <div className="document-id">
                      ID:{" "}
                      {
                        document.document_id
                      }
                    </div>

                    <div className="history-stats">

                      <div>
                        <span>
                          Records
                        </span>

                        <strong>
                          {document.records_extracted ??
                            0}
                        </strong>
                      </div>

                      <div>
                        <span>
                          Confidence
                        </span>

                        <strong>
                          {confidence.toFixed(
                            2
                          )}
                          %
                        </strong>
                      </div>

                      <div>
                        <span>
                          Review
                        </span>

                        <strong>
                          {document.records_review_required ??
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
                );
              }
            )}

          </div>
        )}

      </div>
    );
  };

  // ============================================================
  // DETAILS PAGE
  // ============================================================

  const renderDetailsPage = () => {
    if (!selectedDocument) {
      return (
        <div className="page">

          <div className="empty-card">

            <h2>
              No document selected
            </h2>

            <button
              className="primary-button"
              onClick={
                openHistoryPage
              }
            >
              Back to History
            </button>

          </div>

        </div>
      );
    }

    const documentConfidence =
      Number(
        selectedDocument.average_confidence
      ) || 0;

    const documentQuality =
      selectedDocument.quality ||
      getQualityFromConfidence(
        documentConfidence
      );

    return (
      <div className="page">

        <div className="page-header">

          <div>

            <div className="section-label">
              DOCUMENT DETAILS
            </div>

            <h1>
              {selectedDocument.filename ||
                selectedDocument.document_id}
            </h1>

            <p>
              ID:{" "}
              {
                selectedDocument.document_id
              }
            </p>

          </div>

          <div className="header-actions">

            <button
              className="secondary-button"
              onClick={() =>
                exportCSV(
                  selectedDocument
                )
              }
            >
              Export CSV
            </button>

            <button
              className="secondary-button"
              onClick={
                openHistoryPage
              }
            >
              ← Back
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
            <span>
              DOCUMENT ID
            </span>

            <strong>
              {
                selectedDocument.document_id
              }
            </strong>
          </div>

          <div className="summary-card">
            <span>
              RECORDS EXTRACTED
            </span>

            <strong>
              {selectedDocument.records?.length ??
                selectedDocument.records_extracted ??
                0}
            </strong>
          </div>

          <div className="summary-card">
            <span>
              AVERAGE CONFIDENCE
            </span>

            <strong>
              {documentConfidence.toFixed(
                2
              )}
              %
            </strong>
          </div>

          <div className="summary-card">
            <span>
              DOCUMENT QUALITY
            </span>

            <span
              className={`quality-badge ${getQualityClass(
                documentQuality,
                documentConfidence
              )}`}
            >
              {documentQuality}
            </span>
          </div>

        </div>

        <div className="table-card">

          <div className="section-heading">

            <div>
              <h2>
                Extracted Records
              </h2>

              <p>
                Review, correct and verify
                extracted information.
              </p>
            </div>

          </div>

          <div className="table-wrapper">

            <table>

              <thead>

                <tr>
                  <th>ID</th>
                  <th>Customer</th>
                  <th>Date</th>
                  <th>Product</th>
                  <th>Amount</th>
                  <th>Confidence</th>
                  <th>Quality</th>
                  <th>Review Status</th>
                  <th>Action</th>
                </tr>

              </thead>

              <tbody>

                {(selectedDocument.records ||
                  []
                ).map(
                  (
                    record,
                    index
                  ) => {

                    const confidence =
                      Number(
                        record.confidence
                      ) || 0;

                    const quality =
                      record.quality &&
                      String(
                        record.quality
                      ).toUpperCase() !==
                        "UNKNOWN"
                        ? record.quality
                        : getQualityFromConfidence(
                            confidence
                          );

                    const requiresReview =
                      getRequiresReview(
                        record,
                        null
                      );

                    const isEditing =
                      editingRecordId ===
                      record.id;

                    return (
                      <tr
                        key={
                          record.id ||
                          index
                        }
                      >

                        <td>
                          {record.id ??
                            index + 1}
                        </td>

                        <td>

                          {isEditing ? (
                            <input
                              type="text"
                              name="customer"
                              value={
                                editForm.customer
                              }
                              onChange={
                                handleEditChange
                              }
                            />
                          ) : (
                            record.customer ??
                            "-"
                          )}

                        </td>

                        <td>

                          {isEditing ? (
                            <input
                              type="text"
                              name="date"
                              value={
                                editForm.date
                              }
                              onChange={
                                handleEditChange
                              }
                            />
                          ) : (
                            record.date ??
                            "-"
                          )}

                        </td>

                        <td>

                          {isEditing ? (
                            <input
                              type="text"
                              name="product"
                              value={
                                editForm.product
                              }
                              onChange={
                                handleEditChange
                              }
                            />
                          ) : (
                            record.product ??
                            "-"
                          )}

                        </td>

                        <td>

                          {isEditing ? (
                            <input
                              type="number"
                              name="amount"
                              value={
                                editForm.amount
                              }
                              onChange={
                                handleEditChange
                              }
                            />
                          ) : (
                            <>
                              ₹{" "}
                              {record.amount ??
                                "-"}
                            </>
                          )}

                        </td>

                        <td>
                          {confidence.toFixed(
                            2
                          )}
                          %
                        </td>

                        <td>

                          <span
                            className={`quality-badge ${getQualityClass(
                              quality,
                              confidence
                            )}`}
                          >
                            {quality}
                          </span>

                        </td>

                        <td>

                          <span
                            className={`review-badge ${
                              requiresReview
                                ? "review-needed"
                                : "review-clear"
                            }`}
                          >
                            {requiresReview
                              ? "NEEDS REVIEW"
                              : "NO REVIEW NEEDED"}
                          </span>

                        </td>

                        <td>

                          {isEditing ? (
                            <div className="action-buttons">

                              <button
                                className="primary-button small-button"
                                onClick={() =>
                                  updateRecord(
                                    record.id
                                  )
                                }
                                disabled={
                                  updateLoading
                                }
                              >
                                {updateLoading
                                  ? "Saving..."
                                  : "Save"}
                              </button>

                              <button
                                className="secondary-button small-button"
                                onClick={
                                  cancelEditRecord
                                }
                                disabled={
                                  updateLoading
                                }
                              >
                                Cancel
                              </button>

                            </div>
                          ) : (
                            <button
                              className="secondary-button small-button"
                              onClick={() =>
                                startEditRecord(
                                  record
                                )
                              }
                            >
                              Edit
                            </button>
                          )}

                        </td>

                      </tr>
                    );
                  }
                )}

              </tbody>

            </table>

          </div>

        </div>

        <div className="confidence-card">

          <div className="section-heading">

            <div>
              <h2>
                Processing Information
              </h2>

              <p>
                Confidence and review status
                for this document.
              </p>
            </div>

          </div>

          <div className="confidence-overview">

            <div className="confidence-main">

              <span>
                AVERAGE CONFIDENCE
              </span>

              <strong>
                {documentConfidence.toFixed(
                  2
                )}
                %
              </strong>

              <div className="confidence-bar">

                <div
                  className="confidence-fill"
                  style={{
                    width: `${Math.min(
                      Math.max(
                        documentConfidence,
                        0
                      ),
                      100
                    )}%`,
                  }}
                />

              </div>

            </div>

            <div className="confidence-stat">

              <span>
                DOCUMENT QUALITY
              </span>

              <span
                className={`quality-badge ${getQualityClass(
                  documentQuality,
                  documentConfidence
                )}`}
              >
                {documentQuality}
              </span>

            </div>

            <div className="confidence-stat">

              <span>
                RECORDS REQUIRING REVIEW
              </span>

              <strong>
                {
                  selectedDocument.records_review_required ??
                  0
                }
              </strong>

            </div>

          </div>

        </div>

      </div>
    );
  };

  // ============================================================
  // MAIN APPLICATION
  // ============================================================

  return (
    <div className="app-container">

      <aside className="sidebar">

        <div className="brand">

          <div className="brand-logo">
            IC
          </div>

          <div>
            <h2>
              IntelliCapture
            </h2>

            <span>
              AI Document Intelligence
            </span>
          </div>

        </div>

        <nav className="navigation">

          <button
            className={`nav-item ${
              activePage === "upload"
                ? "active"
                : ""
            }`}
            onClick={
              openUploadPage
            }
          >
            <span>📄</span>
            <span>
              Process Document
            </span>
          </button>

          <button
            className={`nav-item ${
              activePage === "history" ||
              activePage === "details"
                ? "active"
                : ""
            }`}
            onClick={
              openHistoryPage
            }
          >
            <span>🗂️</span>
            <span>
              Document History
            </span>
          </button>

        </nav>

        <div className="sidebar-footer">

          <span>
            IntelliCapture-AI
          </span>

          <small>
            Physical records → Digital assets
          </small>

        </div>

      </aside>

      <main className="main-content">

        {activePage === "upload" &&
          renderUploadPage()}

        {activePage === "history" &&
          renderHistoryPage()}

        {activePage === "details" &&
          renderDetailsPage()}

      </main>

    </div>
  );
}

export default App;
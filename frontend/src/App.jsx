import { useEffect, useState } from "react";
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

  // ============================================================
  // EDIT RECORD STATE
  // ============================================================

  const [editingRecordId, setEditingRecordId] = useState(null);

  const [editForm, setEditForm] = useState({
    customer: "",
    date: "",
    product: "",
    amount: "",
  });

  // ============================================================
  // LOAD DOCUMENT HISTORY
  // ============================================================

  const loadDocuments = async () => {
    try {
      setHistoryLoading(true);

      const response = await axios.get(
        `${API_URL}/api/v1/documents`
      );

      setDocuments(
        response.data?.documents || []
      );
    } catch (err) {
      console.error(
        "Failed to load documents:",
        err
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
      event.target.files[0];

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

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();

      formData.append(
        "file",
        file
      );

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

      setResult(
        response.data
      );

      await loadDocuments();

      setActivePage("upload");
    } catch (err) {
      console.error(err);

      const message =
        err.response?.data?.detail ||
        "Document processing failed.";

      setError(message);
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // LOAD SINGLE DOCUMENT
  // ============================================================

  const viewDocument = async (
    documentId
  ) => {
    try {
      setHistoryLoading(true);
      setError("");

      const response =
        await axios.get(
          `${API_URL}/api/v1/documents/${documentId}`
        );

      setSelectedDocument(
        response.data
      );

      setActivePage("details");
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Failed to load document."
      );
    } finally {
      setHistoryLoading(false);
    }
  };

  // ============================================================
  // QUALITY CLASS
  // ============================================================

  const getQualityClass = (
    quality
  ) => {
    if (quality === "HIGH") {
      return "quality-high";
    }

    if (quality === "MEDIUM") {
      return "quality-medium";
    }

    return "quality-low";
  };

  // ============================================================
  // START EDIT RECORD
  // ============================================================

  const startEditRecord = (
    record
  ) => {
    setEditingRecordId(
      record.id
    );

    setEditForm({
      customer:
        record.customer || "",

      date:
        record.date || "",

      product:
        record.product || "",

      amount:
        record.amount || "",
    });

    setError("");
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

    setError("");
  };

  // ============================================================
  // HANDLE EDIT INPUT
  // ============================================================

  const handleEditChange = (
    event
  ) => {
    const {
      name,
      value,
    } = event.target;

    setEditForm(
      (previous) => ({
        ...previous,
        [name]: value,
      })
    );
  };

  // ============================================================
  // UPDATE RECORD
  // ============================================================

  const updateRecord = async (
    documentId,
    recordId
  ) => {
    try {
      setUpdateLoading(true);
      setError("");

      const response =
        await axios.put(
          `${API_URL}/api/v1/documents/${documentId}/records/${recordId}`,
          {
            customer:
              editForm.customer,

            date:
              editForm.date,

            product:
              editForm.product,

            amount:
              editForm.amount,
          }
        );

      console.log(
        "Record updated successfully:",
        response.data
      );

      // Reload the document
      await viewDocument(
        documentId
      );

      // Exit edit mode
      setEditingRecordId(null);

      setEditForm({
        customer: "",
        date: "",
        product: "",
        amount: "",
      });

      // Refresh document history
      await loadDocuments();

    } catch (err) {
      console.error(
        "Failed to update record:",
        err
      );

      const message =
        err.response?.data?.detail ||
        "Failed to update record.";

      setError(message);
    } finally {
      setUpdateLoading(false);
    }
  };

  // ============================================================
  // CSV EXPORT
  // ============================================================

  const exportCSV = () => {
    if (
      !result?.records?.length
    ) {
      return;
    }

    const headers = [
      "Customer",
      "Date",
      "Product",
      "Amount",
      "Confidence",
      "Quality",
    ];

    const rows =
      result.records.map(
        (
          record,
          index
        ) => {
          const confidenceRecord =
            result.confidence
              ?.records?.[
              index
            ];

          return [
            record.customer,
            record.date,
            record.product,
            record.amount,
            confidenceRecord
              ?.confidence ?? "",
            confidenceRecord
              ?.quality ?? "",
          ];
        }
      );

    const csvContent = [
      headers,
      ...rows,
    ]
      .map(
        (row) =>
          row
            .map(
              (value) =>
                `"${String(
                  value ?? ""
                ).replace(
                  /"/g,
                  '""'
                )}"`
            )
            .join(",")
      )
      .join("\n");

    const blob =
      new Blob(
        [csvContent],
        {
          type:
            "text/csv;charset=utf-8;",
        }
      );

    const url =
      URL.createObjectURL(
        blob
      );

    const link =
      document.createElement(
        "a"
      );

    link.href = url;

    link.download =
      `${
        result.document_id ||
        "intellicapture"
      }_export.csv`;

    document.body.appendChild(
      link
    );

    link.click();

    document.body.removeChild(
      link
    );

    URL.revokeObjectURL(
      url
    );
  };

  // ============================================================
  // NAVIGATION
  // ============================================================

  const showUploadPage = () => {
    setActivePage("upload");
    setError("");
  };

  const showHistoryPage = () => {
    setActivePage("history");
    setError("");
    loadDocuments();
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="app">

      {/* ======================================================
          HEADER
      ====================================================== */}

      <header className="header">

        <div>
          <h1>
            IntelliCapture-AI
          </h1>

          <p>
            Turn physical records into
            digital assets.
          </p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          API Connected
        </div>

      </header>


      {/* ======================================================
          NAVIGATION
      ====================================================== */}

      <div className="navigation">

        <button
          className={`nav-button ${
            activePage === "upload"
              ? "active"
              : ""
          }`}
          onClick={
            showUploadPage
          }
        >
          Upload
        </button>

        <button
          className={`nav-button ${
            activePage === "history"
              ? "active"
              : ""
          }`}
          onClick={
            showHistoryPage
          }
        >
          Document History
        </button>

      </div>


      {/* ======================================================
          GLOBAL ERROR
      ====================================================== */}

      {error && (
        <div className="global-error">
          <div className="error">
            {error}
          </div>
        </div>
      )}


      {/* ======================================================
          UPLOAD PAGE
      ====================================================== */}

      {activePage === "upload" && (
        <>

          <section className="upload-card">

            <div className="upload-content">

              <div className="upload-icon">
                📄
              </div>

              <h2>
                Upload Document
              </h2>

              <p>
                Upload a physical record
                image and let IntelliCapture
                extract structured data.
              </p>

              <label className="file-input">

                <input
                  type="file"
                  accept=".png,.jpg,.jpeg,.bmp,.tif,.tiff"
                  onChange={
                    handleFileChange
                  }
                />

                <span>
                  {file
                    ? file.name
                    : "Choose document"}
                </span>

              </label>

              {file && (
                <p className="selected-file">
                  Selected:{" "}
                  {file.name}
                </p>
              )}

              <button
                className="process-button"
                onClick={
                  processDocument
                }
                disabled={
                  !file ||
                  loading
                }
              >
                {loading
                  ? "Processing..."
                  : "Process Document"}
              </button>

            </div>

          </section>


          {/* ==================================================
              RESULTS
          ================================================== */}

          {result && (

            <section className="results">

              {/* SUMMARY */}

              <div className="summary-grid">

                <div className="summary-card">

                  <span>
                    Document
                  </span>

                  <strong>
                    {
                      result.document_id
                    }
                  </strong>

                </div>


                <div className="summary-card">

                  <span>
                    Records Extracted
                  </span>

                  <strong>
                    {
                      result.records_extracted
                    }
                  </strong>

                </div>


                <div className="summary-card">

                  <span>
                    Average Confidence
                  </span>

                  <strong>
                    {
                      result.confidence
                        ?.summary
                        ?.average_confidence ??
                      0
                    }%
                  </strong>

                </div>


                <div className="summary-card">

                  <span>
                    Quality
                  </span>

                  <strong
                    className={getQualityClass(
                      result.confidence
                        ?.summary
                        ?.quality
                    )}
                  >
                    {
                      result.confidence
                        ?.summary
                        ?.quality ??
                      "UNKNOWN"
                    }
                  </strong>

                </div>

              </div>


              {/* EXTRACTED RECORDS */}

              <div className="table-card">

                <div className="section-heading">

                  <div>
                    <h2>
                      Extracted Records
                    </h2>

                    <p>
                      Structured data detected
                      from the uploaded document.
                    </p>
                  </div>

                  <button
                    className="secondary-button"
                    onClick={
                      exportCSV
                    }
                  >
                    Export CSV
                  </button>

                </div>


                <div className="table-wrapper">

                  <table>

                    <thead>

                      <tr>
                        <th>#</th>
                        <th>
                          Customer
                        </th>
                        <th>
                          Date
                        </th>
                        <th>
                          Product
                        </th>
                        <th>
                          Amount
                        </th>
                        <th>
                          Confidence
                        </th>
                        <th>
                          Quality
                        </th>
                      </tr>

                    </thead>


                    <tbody>

                      {result.records.map(
                        (
                          record,
                          index
                        ) => {

                          const confidenceRecord =
                            result
                              .confidence
                              ?.records?.[
                              index
                            ];

                          return (
                            <tr
                              key={
                                record.id ||
                                index
                              }
                            >

                              <td>
                                {index + 1}
                              </td>

                              <td>
                                {
                                  record.customer
                                }
                              </td>

                              <td>
                                {
                                  record.date
                                }
                              </td>

                              <td>
                                {
                                  record.product
                                }
                              </td>

                              <td>
                                ₹
                                {
                                  record.amount
                                }
                              </td>

                              <td>
                                {
                                  confidenceRecord
                                    ?.confidence ??
                                  0
                                }%
                              </td>

                              <td>

                                <span
                                  className={`quality-badge ${getQualityClass(
                                    confidenceRecord
                                      ?.quality
                                  )}`}
                                >
                                  {
                                    confidenceRecord
                                      ?.quality ??
                                    "UNKNOWN"
                                  }
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


              {/* CONFIDENCE ANALYSIS */}

              {result.confidence && (

                <div className="confidence-card">

                  <div className="section-heading">

                    <div>

                      <h2>
                        Confidence Analysis
                      </h2>

                      <p>
                        Field-level OCR
                        confidence generated
                        by the extraction engine.
                      </p>

                    </div>

                  </div>


                  <div className="confidence-grid">

                    {result.confidence.records.map(
                      (
                        record,
                        index
                      ) => (

                        <div
                          className="confidence-record"
                          key={
                            index
                          }
                        >

                          <div className="confidence-header">

                            <strong>
                              {
                                result.records[
                                  index
                                ]?.customer ??
                                `Record ${
                                  index + 1
                                }`
                              }
                            </strong>

                            <span
                              className={getQualityClass(
                                record.quality
                              )}
                            >
                              {
                                record.confidence
                              }%
                            </span>

                          </div>


                          <div className="field-list">

                            {Object.entries(
                              record.fields ||
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
                                  key={
                                    field
                                  }
                                >

                                  <span>
                                    {
                                      field
                                    }
                                  </span>

                                  <span>
                                    {
                                      data?.confidence ??
                                      0
                                    }%
                                  </span>

                                </div>

                              )
                            )}

                          </div>

                        </div>

                      )
                    )}

                  </div>

                </div>

              )}

            </section>

          )}

        </>
      )}


      {/* ======================================================
          HISTORY PAGE
      ====================================================== */}

      {activePage === "history" && (

        <section className="results">

          <div className="table-card">

            <div className="section-heading">

              <div>
                <h2>
                  Document History
                </h2>

                <p>
                  Previously processed
                  documents stored in
                  IntelliCapture.
                </p>
              </div>

              <button
                className="secondary-button"
                onClick={
                  loadDocuments
                }
              >
                Refresh
              </button>

            </div>


            {historyLoading ? (

              <div className="loading-card">
                Loading documents...
              </div>

            ) : documents.length === 0 ? (

              <div className="empty-card">

                <h3>
                  No documents yet
                </h3>

                <p>
                  Process a document to
                  see it here.
                </p>

              </div>

            ) : (

              <div className="history-grid">

                {documents.map(
                  (document) => (

                    <div
                      className="history-card"
                      key={
                        document.document_id
                      }
                    >

                      <div className="history-card-header">

                        <span className="document-icon">
                          📄
                        </span>

                        <span
                          className={`quality-badge ${getQualityClass(
                            document.quality
                          )}`}
                        >
                          {
                            document.quality
                          }
                        </span>

                      </div>


                      <h3>
                        {
                          document.filename
                        }
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
                            {
                              document.records_extracted
                            }
                          </strong>
                        </div>


                        <div>
                          <span>
                            Confidence
                          </span>

                          <strong>
                            {
                              document.average_confidence
                            }%
                          </strong>
                        </div>


                        <div>
                          <span>
                            Review
                          </span>

                          <strong>
                            {
                              document.records_review_required
                            }
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
                        View Document
                      </button>

                    </div>

                  )
                )}

              </div>

            )}

          </div>

        </section>

      )}


      {/* ======================================================
          DOCUMENT DETAILS PAGE
      ====================================================== */}

      {activePage === "details" &&
        selectedDocument && (

          <section className="results">

            <div className="table-card">

              {/* DETAILS HEADER */}

              <div className="section-heading">

                <div>

                  <h2>
                    Document Details
                  </h2>

                  <p>
                    {
                      selectedDocument
                        .document
                        ?.filename
                    }
                  </p>

                </div>

                <button
                  className="secondary-button"
                  onClick={
                    showHistoryPage
                  }
                >
                  ← Back to History
                </button>

              </div>


              {/* DOCUMENT SUMMARY */}

              <div
                className="summary-grid"
                style={{
                  padding: "24px",
                  marginBottom: 0,
                }}
              >

                <div className="summary-card">

                  <span>
                    Document ID
                  </span>

                  <strong>
                    {
                      selectedDocument
                        .document
                        ?.document_id
                    }
                  </strong>

                </div>


                <div className="summary-card">

                  <span>
                    Records
                  </span>

                  <strong>
                    {
                      selectedDocument
                        .records
                        ?.length || 0
                    }
                  </strong>

                </div>


                <div className="summary-card">

                  <span>
                    Confidence
                  </span>

                  <strong>
                    {
                      selectedDocument
                        .document
                        ?.average_confidence ??
                      0
                    }%
                  </strong>

                </div>


                <div className="summary-card">

                  <span>
                    Quality
                  </span>

                  <strong
                    className={getQualityClass(
                      selectedDocument
                        .document
                        ?.quality
                    )}
                  >
                    {
                      selectedDocument
                        .document
                        ?.quality ??
                      "UNKNOWN"
                    }
                  </strong>

                </div>

              </div>


              {/* RECORDS TABLE */}

              <div className="table-wrapper">

                <table>

                  <thead>

                    <tr>
                      <th>
                        ID
                      </th>

                      <th>
                        Customer
                      </th>

                      <th>
                        Date
                      </th>

                      <th>
                        Product
                      </th>

                      <th>
                        Amount
                      </th>

                      <th>
                        Confidence
                      </th>

                      <th>
                        Quality
                      </th>

                      <th>
                        Action
                      </th>
                    </tr>

                  </thead>


                  <tbody>

                    {(
                      selectedDocument
                        .records || []
                    ).map(
                      (
                        record,
                        index
                      ) => {

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

                            {/* ID */}

                            <td>
                              {
                                record.id
                              }
                            </td>


                            {/* CUSTOMER */}

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
                                  style={{
                                    width:
                                      "100%",
                                    padding:
                                      "8px",
                                    borderRadius:
                                      "7px",
                                    border:
                                      "1px solid #334155",
                                    background:
                                      "#111827",
                                    color:
                                      "#ffffff",
                                  }}
                                />

                              ) : (

                                record.customer

                              )}

                            </td>


                            {/* DATE */}

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
                                  style={{
                                    width:
                                      "100%",
                                    padding:
                                      "8px",
                                    borderRadius:
                                      "7px",
                                    border:
                                      "1px solid #334155",
                                    background:
                                      "#111827",
                                    color:
                                      "#ffffff",
                                  }}
                                />

                              ) : (

                                record.date

                              )}

                            </td>


                            {/* PRODUCT */}

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
                                  style={{
                                    width:
                                      "100%",
                                    padding:
                                      "8px",
                                    borderRadius:
                                      "7px",
                                    border:
                                      "1px solid #334155",
                                    background:
                                      "#111827",
                                    color:
                                      "#ffffff",
                                  }}
                                />

                              ) : (

                                record.product

                              )}

                            </td>


                            {/* AMOUNT */}

                            <td>

                              {isEditing ? (

                                <input
                                  type="text"
                                  name="amount"
                                  value={
                                    editForm.amount
                                  }
                                  onChange={
                                    handleEditChange
                                  }
                                  style={{
                                    width:
                                      "100%",
                                    padding:
                                      "8px",
                                    borderRadius:
                                      "7px",
                                    border:
                                      "1px solid #334155",
                                    background:
                                      "#111827",
                                    color:
                                      "#ffffff",
                                  }}
                                />

                              ) : (

                                <>
                                  ₹
                                  {
                                    record.amount
                                  }
                                </>

                              )}

                            </td>


                            {/* CONFIDENCE */}

                            <td>
                              {
                                record.confidence ??
                                0
                              }%
                            </td>


                            {/* QUALITY */}

                            <td>

                              <span
                                className={`quality-badge ${getQualityClass(
                                  record.quality
                                )}`}
                              >
                                {
                                  record.quality ??
                                  "UNKNOWN"
                                }
                              </span>

                            </td>


                            {/* ACTION */}

                            <td>

                              {isEditing ? (

                                <div
                                  style={{
                                    display:
                                      "flex",
                                    gap:
                                      "8px",
                                    flexWrap:
                                      "wrap",
                                  }}
                                >

                                  <button
                                    className="view-button"
                                    disabled={
                                      updateLoading
                                    }
                                    onClick={() =>
                                      updateRecord(
                                        selectedDocument
                                          .document
                                          ?.document_id,
                                        record.id
                                      )
                                    }
                                  >
                                    {updateLoading
                                      ? "Saving..."
                                      : "Save"}
                                  </button>


                                  <button
                                    className="secondary-button"
                                    disabled={
                                      updateLoading
                                    }
                                    onClick={
                                      cancelEditRecord
                                    }
                                  >
                                    Cancel
                                  </button>

                                </div>

                              ) : (

                                <button
                                  className="secondary-button"
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


            {/* ==================================================
                DOCUMENT INFORMATION
            ================================================== */}

            <div className="confidence-card">

              <div className="section-heading">

                <div>

                  <h2>
                    Processing Information
                  </h2>

                  <p>
                    Information generated by
                    the IntelliCapture processing
                    pipeline.
                  </p>

                </div>

              </div>


              <div
                style={{
                  padding: "24px",
                  display: "grid",
                  gridTemplateColumns:
                    "repeat(auto-fit, minmax(220px, 1fr))",
                  gap: "16px",
                }}
              >

                <div className="summary-card">

                  <span>
                    Filename
                  </span>

                  <strong>
                    {
                      selectedDocument
                        .document
                        ?.filename ||
                      "N/A"
                    }
                  </strong>

                </div>


                <div className="summary-card">

                  <span>
                    Document ID
                  </span>

                  <strong>
                    {
                      selectedDocument
                        .document
                        ?.document_id ||
                      "N/A"
                    }
                  </strong>

                </div>


                <div className="summary-card">

                  <span>
                    Records Requiring Review
                  </span>

                  <strong>
                    {
                      selectedDocument
                        .document
                        ?.records_review_required ??
                      0
                    }
                  </strong>

                </div>

              </div>

            </div>

          </section>

        )}

    </div>
  );
}

export default App;
"use client";

import { useMemo, useRef, useState } from "react";

import { ciGate, compareExperiments, runExperiment, uploadExperiment } from "../lib/api";

type CompareResult = {
  baseline_experiment_id: string;
  candidate_experiment_id: string;
  regression_detected: boolean;
  delta_mean_score: number;
};

type GateResult = {
  experiment_id: string;
  mean_score: number;
  regression_detected: boolean;
  deployment_allowed: boolean;
};

export default function HomePage() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadExperimentId, setUploadExperimentId] = useState<string | null>(null);
  const [runExperimentId, setRunExperimentId] = useState("");
  const [runResults, setRunResults] = useState<Record<string, unknown>[] | null>(null);
  const [selectedResult, setSelectedResult] = useState<Record<string, unknown> | null>(null);
  const [rubricJson, setRubricJson] = useState(
    JSON.stringify(
      {
        factuality: { min: 0, max: 5 },
        relevance: { min: 0, max: 5 },
        clarity: { min: 0, max: 5 },
        safety: { type: "pass_fail" }
      },
      null,
      2
    )
  );
  const [runResultStatus, setRunResultStatus] = useState<string | null>(null);
  const [baselineId, setBaselineId] = useState("");
  const [candidateId, setCandidateId] = useState("");
  const [gateExperimentId, setGateExperimentId] = useState("");
  const [compareResult, setCompareResult] = useState<CompareResult | null>(null);
  const [gateResult, setGateResult] = useState<GateResult | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  const parsedRubric = useMemo(() => {
    try {
      return JSON.parse(rubricJson) as Record<string, unknown>;
    } catch {
      return null;
    }
  }, [rubricJson]);

  const handleUpload = async (fileOverride?: File | null) => {
    const file = fileOverride ?? selectedFile;
    if (!file) {
      setStatus("Please choose a CSV file first.");
      return;
    }
    if (uploadError) {
      setStatus(uploadError);
      return;
    }
    setUploadError(null);
    setStatus("Uploading dataset...");
    try {
      const result = await uploadExperiment({ file });
      setUploadExperimentId(result.experiment_id);
      setRunExperimentId(result.experiment_id);
      setStatus("Upload complete.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Upload failed");
    }
  };

  const handleRun = async () => {
    if (!runExperimentId) {
      setStatus("Experiment ID is required to run.");
      return;
    }
    if (!parsedRubric) {
      setStatus("Rubric JSON is invalid.");
      return;
    }
    setStatus("Running evaluation...");
    setRunResultStatus(null);
    setRunResults(null);
    setSelectedResult(null);
    try {
      const result = await runExperiment({
        experimentId: runExperimentId,
        rubric: parsedRubric
      });
      setRunResultStatus(result.status);
      setRunResults(result.results ?? []);
      setStatus("Evaluation complete.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Run failed");
    }
  };

  const handleDownloadResults = () => {
    if (!runResults) {
      return;
    }
    const blob = new Blob([JSON.stringify(runResults, null, 2)], {
      type: "application/json"
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `evaluation-results-${runExperimentId || "latest"}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const selectedRubric =
    selectedResult && typeof selectedResult.rubric_scores === "object" && selectedResult.rubric_scores !== null
      ? (selectedResult.rubric_scores as Record<string, unknown>)
      : null;

  const validateCsv = async (file: File): Promise<string | null> => {
    if (!file.name.toLowerCase().endsWith(".csv")) {
      return "Only .csv files are supported.";
    }
    const headerLine = await file.text().then((text) => text.split(/\r?\n/)[0] ?? "");
    const headers = headerLine
      .split(",")
      .map((header) => header.trim().replace(/^"|"$/g, ""))
      .filter(Boolean);
    const required = ["prompt", "model_output"];
    const missing = required.filter((header) => !headers.includes(header));
    if (missing.length > 0) {
      return `Missing required columns: ${missing.join(", ")}`;
    }
    return null;
  };

  const handleFileSelected = async (file: File | null) => {
    setSelectedFile(file);
    setUploadError(null);
    if (!file) {
      return;
    }
    const error = await validateCsv(file);
    if (error) {
      setUploadError(error);
    }
  };

  const handleDrop = async (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
    const file = event.dataTransfer.files?.[0] ?? null;
    await handleFileSelected(file);
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleCreateExperimentClick = () => {
    if (!selectedFile) {
      fileInputRef.current?.click();
      return;
    }
    void handleUpload();
  };

  const handleCompare = async () => {
    setStatus("Comparing experiments...");
    setCompareResult(null);
    try {
      const result = await compareExperiments({ baselineId, candidateId });
      setCompareResult(result);
      setStatus(null);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Compare failed");
    }
  };

  const handleGate = async () => {
    setStatus("Checking CI gate...");
    setGateResult(null);
    try {
      const result = await ciGate({ experimentId: gateExperimentId });
      setGateResult(result);
      setStatus(null);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Gate check failed");
    }
  };

  return (
    <main className="page">
      <div className="background-glow" aria-hidden="true" />
      <header className="hero">
        <div className="hero-text">
          <p className="eyebrow">LLM Evaluation-as-a-Service</p>
          <h1>Run rigorous LLM evals without fragile scripts.</h1>
          <p className="subhead">
            Rubric-driven scoring, regression detection, and CI gates for every model
            iteration. Designed for fast teams that ship with confidence.
          </p>
          <div className="hero-actions">
            <button className="primary" onClick={handleCreateExperimentClick}>
              Create Experiment
            </button>
            <button className="ghost">View Baseline</button>
          </div>
          <div className="hero-meta">
            <span>Judge model: OpenAI</span>
            <span>Vector store: pgvector</span>
            <span>Deploy gate: enabled</span>
          </div>
        </div>
        <div className="hero-card">
          <div className="card-header">
            <h2>Evaluation Run</h2>
            <span className="status">In Queue</span>
          </div>
          <div className="card-body">
            <div className="metric">
              <span>Mean score</span>
              <strong>4.31</strong>
            </div>
            <div className="metric">
              <span>Safety fail rate</span>
              <strong>0.8%</strong>
            </div>
            <div className="metric">
              <span>Regression check</span>
              <strong className="ok">Pass</strong>
            </div>
          </div>
          <div className="card-footer">
            <button className="secondary">Open Results</button>
            <button className="link">Download JSON</button>
          </div>
        </div>
      </header>

      <section className="grid">
        <article className="panel">
          <h3>Upload Dataset</h3>
          <p>CSV with prompt, model_output, reference_output (optional).</p>
          <div
            className={`upload-box ${isDragOver ? "drag-over" : ""}`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <span>{selectedFile ? selectedFile.name : "Drag a CSV file or browse"}</span>
            <label className="ghost button-like">
              Browse
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={(event) => handleFileSelected(event.target.files?.[0] ?? null)}
              />
            </label>
          </div>
          <button className="secondary" onClick={() => void handleUpload()}>
            Upload & Create Experiment
          </button>
          {uploadError ? <p className="error">{uploadError}</p> : null}
          {uploadExperimentId ? (
            <p className="muted">Created experiment: {uploadExperimentId}</p>
          ) : null}
        </article>

        <article className="panel">
          <h3>Run Evaluation</h3>
          <p>Trigger rubric-based scoring on an experiment.</p>
          <div className="form-grid">
            <label>
              <span>Experiment ID</span>
              <input
                value={runExperimentId}
                onChange={(event) => setRunExperimentId(event.target.value)}
                placeholder="experiment-uuid"
              />
            </label>
            <label>
              <span>Rubric JSON</span>
              <textarea
                value={rubricJson}
                onChange={(event) => setRubricJson(event.target.value)}
                rows={8}
              />
            </label>
            <button className="secondary" onClick={handleRun}>
              Run Evaluation
            </button>
          </div>
          {runResultStatus ? <p className="muted">Status: {runResultStatus}</p> : null}
        </article>

        <article className="panel">
          <h3>Regression Gate</h3>
          <p>Compare candidate vs baseline and block unsafe drops.</p>
          <div className="form-grid">
            <label>
              <span>Baseline ID</span>
              <input
                value={baselineId}
                onChange={(event) => setBaselineId(event.target.value)}
                placeholder="baseline-uuid"
              />
            </label>
            <label>
              <span>Candidate ID</span>
              <input
                value={candidateId}
                onChange={(event) => setCandidateId(event.target.value)}
                placeholder="candidate-uuid"
              />
            </label>
            <button className="secondary" onClick={handleCompare}>
              Compare
            </button>
            <label>
              <span>Gate Experiment ID</span>
              <input
                value={gateExperimentId}
                onChange={(event) => setGateExperimentId(event.target.value)}
                placeholder="experiment-uuid"
              />
            </label>
            <button className="secondary" onClick={handleGate}>
              Run CI Gate
            </button>
          </div>
          <div className="result-grid">
            {compareResult ? (
              <div className="result">
                <div>
                  <span>Delta mean score</span>
                  <strong>{compareResult.delta_mean_score.toFixed(3)}</strong>
                </div>
                <div>
                  <span>Regression</span>
                  <strong className={compareResult.regression_detected ? "bad" : "ok"}>
                    {compareResult.regression_detected ? "Detected" : "None"}
                  </strong>
                </div>
              </div>
            ) : null}
            {gateResult ? (
              <div className="result">
                <div>
                  <span>Mean score</span>
                  <strong>{gateResult.mean_score.toFixed(3)}</strong>
                </div>
                <div>
                  <span>Deployment</span>
                  <strong className={gateResult.deployment_allowed ? "ok" : "bad"}>
                    {gateResult.deployment_allowed ? "Allowed" : "Blocked"}
                  </strong>
                </div>
              </div>
            ) : null}
          </div>
        </article>
      </section>

      {runResults && runResults.length > 0 ? (
        <section className="panel results-panel">
          <div className="panel-header">
            <h3>Evaluation Results</h3>
            <span className="muted">Showing {runResults.length} rows</span>
            <button className="ghost" onClick={handleDownloadResults}>
              Download JSON
            </button>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Overall</th>
                  <th>Safety</th>
                  <th>Rubric Scores</th>
                  <th>Reasoning</th>
                </tr>
              </thead>
              <tbody>
                {runResults.map((row, index) => {
                  const overall = row.overall_score;
                  const rubricScores =
                    typeof row.rubric_scores === "object" && row.rubric_scores !== null
                      ? (row.rubric_scores as Record<string, unknown>)
                      : null;
                  const safety = row.safety ?? rubricScores?.safety;
                  const reasoning = row.reasoning;
                  const rubricText = rubricScores
                    ? JSON.stringify(rubricScores)
                    : "-";
                  return (
                    <tr
                      key={`result-${index}`}
                      className="clickable"
                      onClick={() => setSelectedResult(row)}
                    >
                      <td>{index + 1}</td>
                      <td>{typeof overall === "number" ? overall.toFixed(2) : "-"}</td>
                      <td className={safety === "fail" ? "bad" : "ok"}>
                        {typeof safety === "string" ? safety : "-"}
                      </td>
                      <td className="rubric-cell">{rubricText}</td>
                      <td className="reasoning">
                        {typeof reasoning === "string" ? reasoning : "-"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {selectedResult ? (
        <div className="drawer-backdrop" onClick={() => setSelectedResult(null)}>
          <aside className="drawer" onClick={(event) => event.stopPropagation()}>
            <div className="drawer-header">
              <h3>Result Detail</h3>
              <button className="ghost" onClick={() => setSelectedResult(null)}>
                Close
              </button>
            </div>
            <div className="drawer-body">
              <div>
                <span className="muted">Item ID</span>
                <strong>{String(selectedResult.item_id ?? "-")}</strong>
              </div>
              <div>
                <span className="muted">Overall Score</span>
                <strong>
                  {typeof selectedResult.overall_score === "number"
                    ? selectedResult.overall_score.toFixed(3)
                    : "-"}
                </strong>
              </div>
              <div>
                <span className="muted">Rubric Scores</span>
                <pre>
                  {selectedRubric ? JSON.stringify(selectedRubric, null, 2) : "-"}
                </pre>
              </div>
              <div>
                <span className="muted">Reasoning</span>
                <p>{typeof selectedResult.reasoning === "string" ? selectedResult.reasoning : "-"}</p>
              </div>
            </div>
          </aside>
        </div>
      ) : null}

      {status ? <div className="status-banner">{status}</div> : null}
    </main>
  );
}

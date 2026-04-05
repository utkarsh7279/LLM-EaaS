type ComparePayload = {
  baselineId: string;
  candidateId: string;
};

type GatePayload = {
  experimentId: string;
};

type UploadPayload = {
  file: File;
};

type RunPayload = {
  experimentId: string;
  rubric: Record<string, unknown>;
  temperature?: number;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {})
    }
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function compareExperiments(payload: ComparePayload) {
  if (!payload.baselineId || !payload.candidateId) {
    throw new Error("Baseline and candidate IDs are required");
  }
  const query = new URLSearchParams({
    baseline: payload.baselineId,
    candidate: payload.candidateId
  });
  return fetchJson<{
    baseline_experiment_id: string;
    candidate_experiment_id: string;
    regression_detected: boolean;
    delta_mean_score: number;
  }>(`/experiments/compare?${query.toString()}`);
}

export async function ciGate(payload: GatePayload) {
  if (!payload.experimentId) {
    throw new Error("Experiment ID is required");
  }
  return fetchJson<{
    experiment_id: string;
    mean_score: number;
    regression_detected: boolean;
    deployment_allowed: boolean;
  }>(`/experiments/${payload.experimentId}/ci-gate`);
}

export async function uploadExperiment(payload: UploadPayload) {
  if (!payload.file) {
    throw new Error("CSV file is required");
  }
  const formData = new FormData();
  formData.append("file", payload.file);

  const response = await fetch(`${API_BASE}/experiments/upload`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Upload failed: ${response.status}`);
  }

  return response.json() as Promise<{ experiment_id: string }>;
}

export async function runExperiment(payload: RunPayload) {
  if (!payload.experimentId) {
    throw new Error("Experiment ID is required");
  }
  return fetchJson<{
    experiment_id: string;
    status: string;
    metrics: Record<string, unknown>;
    results: Record<string, unknown>[];
  }>("/experiments/run", {
    method: "POST",
    body: JSON.stringify({
      experiment_id: payload.experimentId,
      rubric: payload.rubric,
      temperature: payload.temperature ?? 0.2
    })
  });
}

/**
 * Geomatrix API Client
 * Browser calls use same-origin Next.js API routes.
 * Server-side calls may use NEXT_PUBLIC_API_URL when explicitly configured.
 */

const BASE =
  typeof window !== 'undefined'
    ? ''
    : (process.env.NEXT_PUBLIC_API_URL ?? '');

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body || `Request failed with status ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export interface ApiProject {
  id: string;
  project_code: string;
  name: string;
  state: string;
  district: string;
  authority: string;
  project_type: string;
  description?: string;
  latitude?: number;
  longitude?: number;
  land_required: number;
  land_acquired: number;
  affected_families: number;
  current_stage?: string;
  status?: string;
  compensation_status?: string;
  objection_count?: number;
  legal_case_count?: number;
  rr_status?: string;
  env_clearance_status?: string;
  forest_clearance_status?: string;
  crz_status?: string;
  doc_completeness_pct?: number;
  approval_pending?: boolean;
  overdue_milestones?: number;
  risk_score?: number;
  risk_level?: string;
  delay_probability?: number;
  predicted_delay_days?: number;
  confidence?: number;
  primary_driver?: string;
  source_url?: string;
  source_name?: string;
  source_record_id?: string;
  validation_status?: string;
  data_classification?: string;
  imported_at?: string;
  updated_at?: string;
}

export interface ProjectCreatePayload {
  project_code: string;
  name: string;
  state: string;
  district: string;
  authority: string;
  project_type: string;
  description?: string;
  latitude?: number;
  longitude?: number;
  land_required?: number;
  land_acquired?: number;
  affected_families?: number;
  current_stage?: string;
  status?: string;
  compensation_status?: string;
  objection_count?: number;
  legal_case_count?: number;
  rr_status?: string;
  env_clearance_status?: string;
  forest_clearance_status?: string;
  crz_status?: string;
  doc_completeness_pct?: number;
  approval_pending?: boolean;
  overdue_milestones?: number;
}

export interface ShapFeature {
  feature: string;
  display_name?: string;
  shap_value: number;
  direction: 'up' | 'down';
  description: string;
  feature_value?: number;
}

export interface PredictionResult {
  status: string;
  risk_score: number | null;
  risk_level: string | null;
  delay_probability: number | null;
  predicted_delay_days?: number | null;
  confidence: number | null;
  model_run_id?: string | null;
  model_version?: string | null;
  message: string;
  shap_features: ShapFeature[];
}

export interface DashboardSummary {
  total_projects: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  total_land_ha: number;
  total_families: number;
  avg_risk_score?: number | null;
  alerts_open: number;
  data_available: boolean;
  message: string;
}

export interface ApiAlert {
  id: string;
  project_id: string;
  project_name?: string;
  severity: string;
  reason: string;
  detected_at: string;
  recommended_action?: string;
  status: string;
}

export interface IngestResult {
  source: string;
  records_fetched: number;
  records_saved: number;
  records_skipped: number;
  errors: string[];
  status: string;
}

export interface IngestionLogEntry {
  id: string;
  source: string;
  source_url?: string;
  started_at: string;
  finished_at?: string;
  records_fetched: number;
  records_saved: number;
  records_skipped: number;
  errors?: unknown;
  status: string;
}

export interface ModelStatus {
  trained: boolean;
  algorithm?: string | null;
  trained_at?: string | null;
  n_samples?: number | null;
  precision?: number | null;
  recall?: number | null;
  f1_score?: number | null;
  roc_auc?: number | null;
  accuracy?: number | null;
  rmse?: number | null;
  feature_names?: string[] | null;
  feature_importance?: Record<string, number> | null;
  cv_folds?: number | null;
  cv_roc_auc_mean?: number | null;
  cv_roc_auc_std?: number | null;
  cv_f1_mean?: number | null;
  cv_f1_std?: number | null;
  n_unique_classes?: number | null;
  class_counts?: Record<string, number> | null;
  model_version?: string | null;
  dataset_fingerprint?: string | null;
  regression_target_available?: boolean | null;
  message: string;
}

export interface TrainingDataSummary {
  total_records: number;
  delayed_count: number;
  on_time_count: number;
  ready_to_train: boolean;
  message: string;
}

export interface TrainResponse {
  success: boolean;
  message: string;
  model_run_id?: string;
  metrics?: Record<string, number | null>;
}

export interface GeoJsonFeatureCollection {
  type: 'FeatureCollection';
  features: Array<{
    type: 'Feature';
    geometry: { type: 'Point'; coordinates: [number, number] };
    properties: Record<string, unknown>;
  }>;
}

export interface ProjectValidation {
  project_id: string;
  missing_fields: string[];
  can_predict: boolean;
  message: string;
}

export async function fetchProjects(params?: {
  state?: string;
  district?: string;
  stage?: string;
  risk_level?: string;
  limit?: number;
}): Promise<ApiProject[]> {
  const qs = new URLSearchParams();
  if (params?.state) qs.set('state', params.state);
  if (params?.district) qs.set('district', params.district);
  if (params?.stage) qs.set('stage', params.stage);
  if (params?.risk_level) qs.set('risk_level', params.risk_level);
  if (params?.limit) qs.set('limit', String(params.limit));
  return apiFetch<ApiProject[]>(`/api/projects${qs.toString() ? '?' + qs.toString() : ''}`);
}

export async function fetchProject(id: string): Promise<ApiProject> {
  return apiFetch<ApiProject>(`/api/projects/${encodeURIComponent(id)}`);
}

export async function createProject(data: ProjectCreatePayload): Promise<ApiProject> {
  return apiFetch<ApiProject>('/api/projects', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateProject(id: string, data: Partial<ProjectCreatePayload>): Promise<ApiProject> {
  return apiFetch<ApiProject>(`/api/projects/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteProject(id: string): Promise<void> {
  const res = await fetch(`${BASE}/api/projects/${encodeURIComponent(id)}`, { method: 'DELETE' });
  if (!res.ok) {
    throw new ApiError(res.status, await res.text());
  }
}

export async function validateProject(id: string): Promise<ProjectValidation> {
  return apiFetch<ProjectValidation>(`/api/projects/${encodeURIComponent(id)}/validate`);
}

export async function runPrediction(projectId: string): Promise<{ project_id: string; prediction: PredictionResult }> {
  return apiFetch(`/api/projects/${encodeURIComponent(projectId)}/predict-risk`, { method: 'POST' });
}

export async function fetchExplanation(projectId: string): Promise<{ project_id: string; shap_features: ShapFeature[] }> {
  return apiFetch(`/api/projects/${encodeURIComponent(projectId)}/explain`);
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  return apiFetch<DashboardSummary>('/api/projects/dashboard-summary');
}

export async function fetchAlerts(status = 'Open', limit = 100): Promise<ApiAlert[]> {
  return apiFetch<ApiAlert[]>(`/api/alerts?status=${encodeURIComponent(status)}&limit=${limit}`);
}

export async function fetchAlertsSummary() {
  return apiFetch<{ total: number; open: number; critical: number; high: number }>('/api/alerts/summary');
}

export async function fetchGeojson(riskLevel?: string): Promise<GeoJsonFeatureCollection> {
  const qs = riskLevel ? `?risk_level=${encodeURIComponent(riskLevel)}` : '';
  return apiFetch<GeoJsonFeatureCollection>(`/api/map/geojson${qs}`);
}

export async function uploadFile(file: File, dataType: 'projects' | 'historical'): Promise<IngestResult> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE}/api/ingest/upload?data_type=${encodeURIComponent(dataType)}`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) {
    throw new ApiError(res.status, await res.text());
  }
  return res.json() as Promise<IngestResult>;
}

export async function fetchIngestionLog(limit = 20): Promise<IngestionLogEntry[]> {
  return apiFetch<IngestionLogEntry[]>(`/api/ingest/log?limit=${limit}`);
}

export async function fetchModelStatus(): Promise<ModelStatus> {
  return apiFetch<ModelStatus>('/api/model/status');
}

export async function fetchTrainingDataSummary(): Promise<TrainingDataSummary> {
  return apiFetch<TrainingDataSummary>('/api/model/training-data');
}

export async function trainModel(algorithm: 'RandomForest' | 'XGBoost' = 'RandomForest'): Promise<TrainResponse> {
  return apiFetch<TrainResponse>(`/api/model/train?algorithm=${encodeURIComponent(algorithm)}`, { method: 'POST' });
}

export async function explainWithGemini(payload: {
  project: Record<string, unknown>;
  prediction?: Record<string, unknown>;
  shap_features?: ShapFeature[];
}): Promise<{ status: string; label: string; summary: string; source: string }> {
  return apiFetch('/api/gemini/explain', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

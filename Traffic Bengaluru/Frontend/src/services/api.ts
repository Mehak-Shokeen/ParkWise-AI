import axios from 'axios';
import type {
  AnalyticsResponse,
  HealthResponse,
  HotspotsResponse,
  OverviewResponse,
  PredictRequest,
  PredictResponse,
} from '../types';

const api = axios.create({
  baseURL: '',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// ─── Health ───────────────────────────────────────────────────────────────────

export const fetchHealth = (): Promise<HealthResponse> =>
  api.get<HealthResponse>('/health').then((r) => r.data);

// ─── Overview ─────────────────────────────────────────────────────────────────

export const fetchOverview = (): Promise<OverviewResponse> =>
  api.get<OverviewResponse>('/api/overview').then((r) => r.data);

// ─── Hotspots ─────────────────────────────────────────────────────────────────

export interface HotspotParams {
  limit?: number;
  min_severity?: string;
  station?: string;
}

export const fetchHotspots = (params?: HotspotParams): Promise<HotspotsResponse> =>
  api.get<HotspotsResponse>('/api/hotspots', { params }).then((r) => r.data);

// ─── Analytics ────────────────────────────────────────────────────────────────

export const fetchAnalytics = (): Promise<AnalyticsResponse> =>
  api.get<AnalyticsResponse>('/api/analytics').then((r) => r.data);

// ─── Predict ──────────────────────────────────────────────────────────────────

export const postPredict = (body: PredictRequest): Promise<PredictResponse> =>
  api.post<PredictResponse>('/api/predict', body).then((r) => r.data);

export default api;

// ─── Prediction ──────────────────────────────────────────────────────────────

export interface Recommendation {
  action: string;
  message: string;
  icon: string;
  priority: number;
  notification: boolean;
  challan: boolean;
  towing: boolean;
  officer: boolean;
}

export interface PredictRequest {
  location_type: string;
  illegal_vehicle_count: number;
  traffic_volume: number;
  average_speed: number;
  parking_occupancy: number;
  road_width: number;
  historical_violation_count: number;
  nearby_event: number;
  day_of_week: number;
  time_of_day: string;
}

export interface PredictResponse {
  severity: string;
  confidence: number;
  pci_score: number;
  pci_category: string;
  recommendation: Recommendation;
  all_probabilities: Record<string, number> | null;
}

// ─── Hotspots ─────────────────────────────────────────────────────────────────

export interface HotspotItem {
  hotspot_id: string;
  latitude: number;
  longitude: number;
  location_label: string;
  police_station: string;
  severity: 'Low' | 'Medium' | 'High' | 'Critical';
  confidence: number;
  pci_score: number;
  violation_count: number;
  recommendation: Recommendation;
  priority_score: number;
}

export interface HotspotsResponse {
  hotspots: HotspotItem[];
  total_clusters: number;
  returned: number;
}

// ─── Overview ─────────────────────────────────────────────────────────────────

export interface OverviewResponse {
  active_violations: number;
  critical_hotspots: number;
  officers_deployed: number;
  average_pci: number;
  estimated_congestion_reduction_pct: number;
}

// ─── Analytics ────────────────────────────────────────────────────────────────

export interface FeatureImportanceItem {
  feature: string;
  importance: number;
}

export interface AnalyticsResponse {
  violations_by_station: Array<{ station: string; count: number }>;
  violations_by_hour: Array<{ hour: number; count: number }>;
  violations_by_day: Array<{ day: string; count: number }>;
  severity_distribution: Record<string, number>;
  feature_importance: FeatureImportanceItem[];
  total_violations: number;
}

// ─── Health ───────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  cache_loaded: boolean;
}

// ─── Model Metrics (from model_metrics.csv) ───────────────────────────────────

export interface ModelMetric {
  Model: string;
  Accuracy: number;
  Precision: number;
  Recall: number;
  F1_Score: number;
}

// ─── Severity ─────────────────────────────────────────────────────────────────

export type Severity = 'Low' | 'Medium' | 'High' | 'Critical';

export const SEVERITY_COLORS: Record<Severity, string> = {
  Low: '#22C55E',
  Medium: '#FACC15',
  High: '#F97316',
  Critical: '#EF4444',
};

export const SEVERITY_BG: Record<Severity, string> = {
  Low: 'bg-low/20 text-low border-low/30',
  Medium: 'bg-medium/20 text-medium border-medium/30',
  High: 'bg-high/20 text-high border-high/30',
  Critical: 'bg-critical/20 text-critical border-critical/30',
};

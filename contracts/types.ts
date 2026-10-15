/** Hand-checked client types corresponding to contracts/openapi_mvp.yaml. */
export type RacingCode = 'THOROUGHBRED' | 'HARNESS' | 'GREYHOUND';
export type DataMode = 'SYNTHETIC_ONLY' | 'SCRAPED_PUBLIC' | 'LICENSED';

export interface HealthResponse {
  status: 'ok';
}

export interface SystemStatusResponse {
  app: 'racing-intelligence-lab';
  environment: string;
  data_mode: DataMode;
  external_connectivity: boolean;
  model_status: 'NOT_TRAINED' | 'ILLUSTRATIVE_ONLY' | 'MODEL_VALIDATED';
  wagering_enabled: false;
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    correlation_id: string;
    details?: Record<string, unknown>;
  };
}

export interface PageMeta {
  limit: number;
  next_cursor: string | null;
  as_of: string;
}

export interface CodeSummary {
  code: RacingCode;
  label: string;
  data_mode: DataMode;
}

export interface Meeting {
  meeting_id: string;
  code: RacingCode;
  name: string;
  country: 'AUS';
  scheduled_date: string;
  data_mode: DataMode;
}

export interface Race {
  race_id: string;
  meeting_id: string;
  race_number: number;
  status: 'SCHEDULED' | 'ACCEPTANCES' | 'FINAL_FIELDS' | 'OFFICIAL' | 'ABANDONED' | 'POSTPONED';
  field_revision: string;
  data_mode: DataMode;
  source_receipt_id?: string;
  as_of?: string;
}

export interface Entry {
  entry_id: string;
  race_id: string;
  participant_id: string;
  number: number;
  name?: string;
  status: 'ACTIVE' | 'SCRATCHED' | 'RESERVE' | 'COUPLED';
  data_mode: DataMode;
}

export interface Forecast {
  forecast_id: string;
  race_id: string;
  field_revision: string;
  cutoff: string;
  model_version: string;
  probabilities: Record<string, number>;
  data_mode: DataMode;
  diagnostic_flags?: string[];
}

export type SelectionType = 'WIN' | 'PLACE' | 'PASS';

export interface SelectionCreate {
  race_id: string;
  entry_id?: string | null;
  selection_type: SelectionType;
  rationale: string;
  forecast_id?: string | null;
}

export interface Selection extends SelectionCreate {
  selection_id: string;
  created_at: string;
  data_mode: DataMode;
}

export interface Page<T> {
  items: T[];
  meta: PageMeta;
}

import { useEffect, useMemo, useState, type FormEvent } from 'react';

export type NexusApiRequest = (path: string, init?: RequestInit, requiredScope?: string) => Promise<Response>;

type Code = 'ALL' | 'THOROUGHBRED' | 'HARNESS' | 'GREYHOUND';
type Status = 'LIVE' | 'DEMO' | 'NO_RACING' | 'NO_DATA' | 'UNAVAILABLE' | 'LOADING' | 'STALE' | 'QUARANTINED' | 'UNSUPPORTED' | 'AUTH_DENIED';
type WorkspaceId = 'COMMAND' | 'MEETINGS' | 'RACE' | 'TACTICAL' | 'RUNNER' | 'COMPARE' | 'MODEL' | 'SCENARIO' | 'MARKETS' | 'EVIDENCE' | 'ASSISTANT' | 'NOTEBOOK' | 'WATCHLISTS' | 'REPORTS_SETTINGS';
type DataMode = 'LOADING' | 'SYNTHETIC_ONLY' | 'LICENSED';

type CommandItem = {
  id: string;
  code: Exclude<Code, 'ALL'>;
  label: string;
  status: Status;
  meeting?: string;
  races?: number;
  localTime?: string;
  sourceAge: string;
  note: string;
};

type EvidenceTab = 'FIELD' | 'PROVENANCE' | 'FORECAST' | 'MARKET';
type AssistantAnswerKind = 'EVIDENCE' | 'DISCREPANCY' | 'NOT_AVAILABLE';

type AssistantCitation = {
  sourceId: string;
  modelId: string;
  observedAt: string;
  limitation: string;
};

type AssistantAnswer = {
  kind: AssistantAnswerKind;
  title: string;
  body: string;
  citations: AssistantCitation[];
  noteDraft: string;
};

type ResearchRace = {
  code: Exclude<Code, 'ALL'>;
  meeting: string;
  raceLabel: string;
  fieldRevision: string;
  fieldState: string;
  observedAt: string;
  publishedAt: string;
  codePanelTitle: string;
  specialtyLabel: string;
  specialtyExplanation: string;
  entries: Array<{ number: number; name: string; status: 'ACTIVE' | 'SCRATCHED' | 'RESERVE' }>;
  comparisonRows: Array<{ number: number; name: string; status: 'ACTIVE' | 'SCRATCHED' | 'RESERVE'; distance: string; context: string; recentForm: string }>;
  forecasts: ForecastAssessment[];
  featureAvailability: FeatureAvailability[];
  evaluation: EvaluationSummary;
};

type ForecastAssessment = {
  modelId: string;
  label: string;
  family: 'FORM_ONLY' | 'MARKET_ONLY' | 'COMBINED';
  status: 'READY' | 'ABSTAIN';
  modelVersion: string;
  probabilities: Record<number, number>;
  uncertainty: string;
  missing: string;
  disagreement: string;
};

type FeatureAvailability = {
  name: string;
  source: string;
  status: 'AVAILABLE' | 'MISSING' | 'RESTRICTED';
  detail: string;
};

type EvaluationSummary = {
  walkForward: string;
  calibration: string;
  metrics: Array<{ model: string; logLoss: string; brier: string; topRanked: string }>;
  ablation: Array<{ family: string; delta: string; status: string }>;
};

const codes: Array<{ value: Code; label: string }> = [
  { value: 'ALL', label: 'All codes' },
  { value: 'THOROUGHBRED', label: 'Thoroughbred' },
  { value: 'HARNESS', label: 'Harness' },
  { value: 'GREYHOUND', label: 'Greyhound' },
];

const workspaces: Array<{ value: WorkspaceId; label: string; short: string }> = [
  { value: 'COMMAND', label: 'Command Centre', short: 'Today' },
  { value: 'MEETINGS', label: 'Meeting discovery', short: 'Meetings' },
  { value: 'RACE', label: 'Race intelligence', short: 'Race' },
  { value: 'TACTICAL', label: 'Tactical track', short: 'Tactical' },
  { value: 'RUNNER', label: 'Runner intelligence', short: 'Runner' },
  { value: 'COMPARE', label: 'Runner comparison', short: 'Compare' },
  { value: 'MODEL', label: 'Model laboratory', short: 'Models' },
  { value: 'SCENARIO', label: 'Scenario studio', short: 'Scenarios' },
  { value: 'MARKETS', label: 'Markets', short: 'Markets' },
  { value: 'EVIDENCE', label: 'Evidence', short: 'Evidence' },
  { value: 'ASSISTANT', label: 'Research assistant', short: 'Assistant' },
  { value: 'NOTEBOOK', label: 'Notebook', short: 'Notebook' },
  { value: 'WATCHLISTS', label: 'Watchlists and alerts', short: 'Watchlists' },
  { value: 'REPORTS_SETTINGS', label: 'Reports and settings', short: 'Reports' },
];

const workspacePreviewCopy: Record<WorkspaceId, { eyebrow: string; title: string; description: string; signal: string; metrics: string[] }> = {
  COMMAND: { eyebrow: 'OPERATIONS SURFACE', title: 'Today / Command Centre', description: 'A calm starting point for the next verified racing decision: source health first, then meetings, then evidence.', signal: 'CURRENT RECEIPT', metrics: ['Meetings', 'Races', 'Receipts'] },
  MEETINGS: { eyebrow: 'DISCOVERY SURFACE', title: 'Meeting discovery', description: 'Scan the day by code, jurisdiction, schedule and evidence state before opening a canonical race.', signal: 'INDEXED', metrics: ['Codes', 'Meetings', 'Freshness'] },
  RACE: { eyebrow: 'ANALYSIS SURFACE', title: 'Race intelligence', description: 'Move from the meeting record to a single race context with field revision, provenance and bounded evidence.', signal: 'FIELD-R2', metrics: ['Field', 'Revision', 'Evidence'] },
  TACTICAL: { eyebrow: 'VISUAL ANALYSIS', title: 'Tactical track', description: 'A side-on race reading surface for pace, position and uncertainty. No movement is inferred when the source is absent.', signal: 'ILLUSTRATIVE', metrics: ['Pace', 'Position', 'Confidence'] },
  RUNNER: { eyebrow: 'PARTICIPANT SURFACE', title: 'Runner intelligence', description: 'Keep the runner record, code-specific inputs and provenance attached to the same field revision.', signal: 'SOURCE-LINKED', metrics: ['Runners', 'Inputs', 'History'] },
  COMPARE: { eyebrow: 'COMPARISON SURFACE', title: 'Runner comparison', description: 'Compare only like-for-like runners and show where evidence is missing instead of filling gaps with estimates.', signal: 'NO INVENTION', metrics: ['Selected', 'Comparable', 'Missing'] },
  MODEL: { eyebrow: 'ASSURANCE SURFACE', title: 'Model laboratory', description: 'Inspect model family, version, uncertainty and evaluation without turning illustrative outputs into advice.', signal: 'NOT VALIDATED', metrics: ['Models', 'Folds', 'Drift'] },
  SCENARIO: { eyebrow: 'SCENARIO SURFACE', title: 'Scenario studio', description: 'Test changes against a fixed field revision and preserve the difference between a scenario and an observed result.', signal: 'PAPER ONLY', metrics: ['Cases', 'Inputs', 'Impact'] },
  MARKETS: { eyebrow: 'PAPER ANALYSIS', title: 'Markets', description: 'Market context remains paper analysis only; rights, timestamp and comparability stay visible at every step.', signal: 'RIGHTS-BOUND', metrics: ['Quotes', 'Freshness', 'Rights'] },
  EVIDENCE: { eyebrow: 'PROVENANCE SURFACE', title: 'Evidence', description: 'Trace every assertion to a source receipt, observed time, rights state and model claim.', signal: 'APPEND-ONLY', metrics: ['Receipts', 'Revisions', 'Claims'] },
  ASSISTANT: { eyebrow: 'RESEARCH SURFACE', title: 'Research assistant', description: 'Ask bounded questions and receive citations, limitations and explicit NOT_AVAILABLE outcomes.', signal: 'CITATIONS REQUIRED', metrics: ['Sources', 'Answers', 'Limits'] },
  NOTEBOOK: { eyebrow: 'WORKING MEMORY', title: 'Notebook', description: 'Keep approved local notes attached to the evidence that supports them, with no hidden promotion path.', signal: 'LOCAL ONLY', metrics: ['Notes', 'Sources', 'Approval'] },
  WATCHLISTS: { eyebrow: 'MONITORING SURFACE', title: 'Watchlists and alerts', description: 'Follow changes to canonical records without confusing a notification with a forecast or wager signal.', signal: 'NO AUTO-ACTION', metrics: ['Lists', 'Changes', 'Alerts'] },
  REPORTS_SETTINGS: { eyebrow: 'CONTROL SURFACE', title: 'Reports and settings', description: 'Review rights, access, export boundaries and release evidence from one explicit control surface.', signal: 'OWNER CONTROL', metrics: ['Access', 'Rights', 'Audit'] },
};

const statuses: Array<{ value: Status | 'ALL'; label: string }> = [
  { value: 'ALL', label: 'All states' },
  { value: 'LIVE', label: 'Live provider' },
  { value: 'DEMO', label: 'Demo fixture' },
  { value: 'LOADING', label: 'Loading' },
  { value: 'STALE', label: 'Stale snapshot' },
  { value: 'NO_RACING', label: 'No racing' },
  { value: 'NO_DATA', label: 'No data' },
  { value: 'QUARANTINED', label: 'Quarantined' },
  { value: 'UNSUPPORTED', label: 'Unsupported' },
  { value: 'UNAVAILABLE', label: 'Unavailable' },
  { value: 'AUTH_DENIED', label: 'Auth denied' },
];

const syntheticForecasts: ForecastAssessment[] = [
  { modelId: 'B0_UNIFORM', label: 'B0 · Uniform', family: 'FORM_ONLY', status: 'READY', modelVersion: 'b0-uniform-v2', probabilities: { 1: 0.5, 3: 0.5 }, uncertainty: 'No fitted uncertainty; uniform reference', missing: 'None', disagreement: 'Reference only' },
  { modelId: 'B1_FORM_BASELINE', label: 'B1 · Form', family: 'FORM_ONLY', status: 'READY', modelVersion: 'b1-form-v2', probabilities: { 1: 0.62, 3: 0.38 }, uncertainty: 'Illustrative interval ±0.12', missing: 'Sectionals unavailable', disagreement: '+0.12 vs market for runner 1' },
  { modelId: 'B2_MARKET_BASELINE', label: 'B2 · Market', family: 'MARKET_ONLY', status: 'READY', modelVersion: 'b2-market-v1', probabilities: { 1: 0.58, 3: 0.42 }, uncertainty: 'Market spread retained', missing: 'None in synthetic fixture', disagreement: 'Market reference' },
  { modelId: 'B3_LIGHTGBM', label: 'B3 · LightGBM', family: 'FORM_ONLY', status: 'READY', modelVersion: 'b3-lightgbm-synthetic', probabilities: { 1: 0.64, 3: 0.36 }, uncertainty: 'Synthetic-only; not calibrated', missing: 'Sectionals unavailable', disagreement: '+0.06 vs B1 for runner 1' },
  { modelId: 'B4_MARKET_INFORMED_ENSEMBLE', label: 'B4 · Combined', family: 'COMBINED', status: 'READY', modelVersion: 'b4-ensemble-v1', probabilities: { 1: 0.61, 3: 0.39 }, uncertainty: 'Synthetic-only; calibration pending', missing: 'Sectionals unavailable', disagreement: '+0.03 vs market for runner 1' },
];

const syntheticFeatureAvailability: FeatureAvailability[] = [
  { name: 'Recent form and prior performance', source: 'synthetic://form/history-v1', status: 'AVAILABLE', detail: 'Pre-race receipt present' },
  { name: 'Distance and track suitability', source: 'synthetic://context/suitability-v1', status: 'AVAILABLE', detail: 'Race-normalised fixture value' },
  { name: 'Raw and adjusted speed', source: 'synthetic://speed/adjusted-v1', status: 'AVAILABLE', detail: 'Illustrative only' },
  { name: 'Sectional and finishing speed', source: '—', status: 'MISSING', detail: 'No verified pre-race source' },
  { name: 'Class, field strength and pace', source: 'synthetic://race/context-v1', status: 'AVAILABLE', detail: 'No post-race fields used' },
  { name: 'Barrier, participant and fitness effects', source: 'synthetic://runner/context-v1', status: 'AVAILABLE', detail: 'Code-specific manifest' },
  { name: 'Betfair price movement and liquidity', source: 'synthetic://betfair/mock-v1', status: 'AVAILABLE', detail: 'Read-only synthetic market' },
  { name: 'Starting price / post-race result', source: '—', status: 'RESTRICTED', detail: 'Never eligible for pre-race forecasts' },
];

const syntheticEvaluation: EvaluationSummary = {
  walkForward: 'READY · 3 synthetic test folds · no real historical claim',
  calibration: 'Illustrative reliability bins only · calibration pending',
  metrics: [
    { model: 'B0', logLoss: '0.693', brier: '0.500', topRanked: '50.0%' },
    { model: 'B1', logLoss: '0.313', brier: '0.145', topRanked: '100.0%' },
    { model: 'B2', logLoss: '0.414', brier: '0.229', topRanked: '100.0%' },
    { model: 'B3', logLoss: 'illustrative', brier: 'illustrative', topRanked: 'not validated' },
    { model: 'B4', logLoss: '0.361', brier: '0.183', topRanked: '100.0%' },
  ],
  ablation: [
    { family: 'Form features', delta: 'B1 reference', status: 'Synthetic only' },
    { family: 'Market features', delta: 'B2 reference', status: 'Synthetic only' },
    { family: 'Betfair liquidity', delta: 'Not isolated', status: 'Rights/history pending' },
    { family: 'Sectionals', delta: 'Not available', status: 'No source evidence' },
  ],
};

const commandItems: CommandItem[] = [
  {
    id: 'tb-demo', code: 'THOROUGHBRED', label: 'Thoroughbred', status: 'DEMO',
    meeting: 'Fictional Thoroughbred Park', races: 2, localTime: '15 Jan 2026, 14:00 AEDT',
    sourceAge: 'Simulated fixture time', note: 'Two fictional races with revisions, a correction and edge cases.',
  },
  {
    id: 'harness-demo', code: 'HARNESS', label: 'Harness', status: 'DEMO',
    meeting: 'Fictional Harness Circuit', races: 2, localTime: '15 Jan 2026, 14:00 AEDT',
    sourceAge: 'Simulated fixture time', note: 'Two fictional races with sections, reserves and synthetic quotes.',
  },
  {
    id: 'greyhound-demo', code: 'GREYHOUND', label: 'Greyhound', status: 'DEMO',
    meeting: 'Fictional Greyhound Track', races: 2, localTime: '15 Jan 2026, 14:00 AEDT',
    sourceAge: 'Simulated fixture time', note: 'Two fictional races with split times, scratchings and abstention cases.',
  },
  {
    id: 'no-racing', code: 'GREYHOUND', label: 'Greyhound', status: 'NO_RACING',
    sourceAge: 'No source requested', note: 'Use this state when the selected date has no scheduled fixture.',
  },
  {
    id: 'no-data', code: 'HARNESS', label: 'Harness', status: 'NO_DATA',
    sourceAge: 'No receipt available', note: 'No evidence is shown and no values are inferred for this state.',
  },
  {
    id: 'unavailable', code: 'THOROUGHBRED', label: 'Thoroughbred', status: 'UNAVAILABLE',
    sourceAge: 'Source disabled', note: 'This state is used when a source is disabled or not entitled.',
  },
  {
    id: 'loading', code: 'THOROUGHBRED', label: 'Thoroughbred', status: 'LOADING',
    sourceAge: 'Request in progress', note: 'The source request is still running. No partial values are displayed.',
  },
  {
    id: 'stale', code: 'HARNESS', label: 'Harness', status: 'STALE',
    sourceAge: 'Last receipt 46 minutes ago', note: 'The last receipt is outside the freshness window. Treat this snapshot as stale.',
  },
  {
    id: 'quarantined', code: 'GREYHOUND', label: 'Greyhound', status: 'QUARANTINED',
    sourceAge: 'Receipt held for review', note: 'The receipt failed validation and is quarantined until its reason is resolved.',
  },
  {
    id: 'unsupported', code: 'THOROUGHBRED', label: 'Thoroughbred', status: 'UNSUPPORTED',
    sourceAge: 'Capability not supported', note: 'This requested view is outside the current synthetic fixture capability.',
  },
  {
    id: 'auth-denied', code: 'HARNESS', label: 'Harness', status: 'AUTH_DENIED',
    sourceAge: 'Scope not granted', note: 'The local capability scope does not permit this evidence view.',
  },
];

const researchRaces: Record<Exclude<Code, 'ALL'>, ResearchRace> = {
  THOROUGHBRED: {
    code: 'THOROUGHBRED', meeting: 'Fictional Thoroughbred Park', raceLabel: 'Race 1 · Fictional Maiden',
    fieldRevision: 'field-r2', fieldState: 'FINAL_FIELDS', observedAt: '15 Jan 2026, 14:00 AEDT', publishedAt: '15 Jan 2026, 13:50 AEDT',
    codePanelTitle: 'Thoroughbred panel · pace and class', specialtyLabel: 'Pace-map inputs',
    specialtyExplanation: 'No verified early-speed or sectional source is present in this synthetic fixture; no pace ranking is inferred.',
    entries: [
      { number: 1, name: 'Fictional Thoroughbred Runner 1-1', status: 'ACTIVE' },
      { number: 2, name: 'Fictional Thoroughbred Runner 1-2', status: 'SCRATCHED' },
      { number: 3, name: 'Fictional Thoroughbred Runner 1-3', status: 'ACTIVE' },
      { number: 4, name: 'Fictional Thoroughbred Runner 1-4', status: 'RESERVE' },
    ],
    comparisonRows: [
      { number: 1, name: 'Fictional Thoroughbred Runner 1-1', status: 'ACTIVE', distance: '1200 m', context: 'Fictional maiden · dry track', recentForm: '2 starts · illustrative' },
      { number: 2, name: 'Fictional Thoroughbred Runner 1-2', status: 'SCRATCHED', distance: '1200 m', context: 'Fictional maiden · dry track', recentForm: 'Withdrawn before field' },
      { number: 3, name: 'Fictional Thoroughbred Runner 1-3', status: 'ACTIVE', distance: '1200 m', context: 'Fictional maiden · dry track', recentForm: '2 starts · illustrative' },
      { number: 4, name: 'Fictional Thoroughbred Runner 1-4', status: 'RESERVE', distance: '1200 m', context: 'Fictional maiden · dry track', recentForm: 'Reserve · not started' },
    ],
    forecasts: syntheticForecasts, featureAvailability: syntheticFeatureAvailability, evaluation: syntheticEvaluation,
  },
  HARNESS: {
    code: 'HARNESS', meeting: 'Fictional Harness Circuit', raceLabel: 'Race 1 · Fictional Pace',
    fieldRevision: 'field-r2', fieldState: 'FINAL_FIELDS', observedAt: '15 Jan 2026, 14:00 AEDT', publishedAt: '15 Jan 2026, 13:50 AEDT',
    codePanelTitle: 'Harness panel · gait and sectionals', specialtyLabel: 'Gait and sectional inputs',
    specialtyExplanation: 'No verified gait, pressure or sectional source is present in this synthetic fixture; no speed figure is inferred.',
    entries: [
      { number: 1, name: 'Fictional Harness Runner 1-1', status: 'ACTIVE' },
      { number: 2, name: 'Fictional Harness Runner 1-2', status: 'SCRATCHED' },
      { number: 3, name: 'Fictional Harness Runner 1-3', status: 'ACTIVE' },
      { number: 4, name: 'Fictional Harness Runner 1-4', status: 'RESERVE' },
    ],
    comparisonRows: [
      { number: 1, name: 'Fictional Harness Runner 1-1', status: 'ACTIVE', distance: '1800 m', context: 'Fictional pace · standing start', recentForm: '2 starts · illustrative' },
      { number: 2, name: 'Fictional Harness Runner 1-2', status: 'SCRATCHED', distance: '1800 m', context: 'Fictional pace · standing start', recentForm: 'Withdrawn before field' },
      { number: 3, name: 'Fictional Harness Runner 1-3', status: 'ACTIVE', distance: '1800 m', context: 'Fictional pace · standing start', recentForm: '2 starts · illustrative' },
      { number: 4, name: 'Fictional Harness Runner 1-4', status: 'RESERVE', distance: '1800 m', context: 'Fictional pace · standing start', recentForm: 'Reserve · not started' },
    ],
    forecasts: syntheticForecasts, featureAvailability: syntheticFeatureAvailability, evaluation: syntheticEvaluation,
  },
  GREYHOUND: {
    code: 'GREYHOUND', meeting: 'Fictional Greyhound Track', raceLabel: 'Race 1 · Fictional Sprint',
    fieldRevision: 'field-r2', fieldState: 'FINAL_FIELDS', observedAt: '15 Jan 2026, 14:00 AEDT', publishedAt: '15 Jan 2026, 13:50 AEDT',
    codePanelTitle: 'Greyhound panel · box and interference', specialtyLabel: 'Box and interference inputs',
    specialtyExplanation: 'No verified box-draw interaction or interference source is present in this synthetic fixture; no lane adjustment is inferred.',
    entries: [
      { number: 1, name: 'Fictional Greyhound Runner 1-1', status: 'ACTIVE' },
      { number: 2, name: 'Fictional Greyhound Runner 1-2', status: 'SCRATCHED' },
      { number: 3, name: 'Fictional Greyhound Runner 1-3', status: 'ACTIVE' },
      { number: 4, name: 'Fictional Greyhound Runner 1-4', status: 'RESERVE' },
    ],
    comparisonRows: [
      { number: 1, name: 'Fictional Greyhound Runner 1-1', status: 'ACTIVE', distance: '520 m', context: 'Fictional sprint · boxed start', recentForm: '2 starts · illustrative' },
      { number: 2, name: 'Fictional Greyhound Runner 1-2', status: 'SCRATCHED', distance: '520 m', context: 'Fictional sprint · boxed start', recentForm: 'Withdrawn before field' },
      { number: 3, name: 'Fictional Greyhound Runner 1-3', status: 'ACTIVE', distance: '520 m', context: 'Fictional sprint · boxed start', recentForm: '2 starts · illustrative' },
      { number: 4, name: 'Fictional Greyhound Runner 1-4', status: 'RESERVE', distance: '520 m', context: 'Fictional sprint · boxed start', recentForm: 'Reserve · not started' },
    ],
    forecasts: syntheticForecasts, featureAvailability: syntheticFeatureAvailability, evaluation: syntheticEvaluation,
  },
};

const statusText: Record<Status, string> = {
  LIVE: 'Live provider',
  DEMO: 'Fictional demo', NO_RACING: 'No racing', NO_DATA: 'No data', UNAVAILABLE: 'Unavailable',
  LOADING: 'Loading', STALE: 'Stale snapshot', QUARANTINED: 'Quarantined', UNSUPPORTED: 'Unsupported', AUTH_DENIED: 'Auth denied',
};

function localNow(): string {
  return new Intl.DateTimeFormat('en-AU', {
    dateStyle: 'medium', timeStyle: 'short', timeZone: 'Australia/Sydney',
  }).format(new Date());
}

type LiveMeeting = {
  meeting_id: string;
  code: Exclude<Code, 'ALL'>;
  name: string;
  country: string;
  scheduled_date: string;
  data_mode: 'LICENSED';
};

type ApiPage<T> = { items: T[] };
type LiveRace = {
  race_id: string;
  meeting_id: string;
  race_number: number;
  status: string;
  field_revision: string;
  data_mode: 'LICENSED';
  source_receipt_id?: string | null;
};
type LiveEntry = {
  entry_id: string;
  race_id: string;
  participant_id: string;
  number: number;
  name?: string | null;
  status: string;
  data_mode: 'LICENSED';
};

type LiveIngestionHealth = {
  status: 'DISABLED' | 'NO_DATA' | 'HEALTHY' | 'STALE' | 'FAILED';
  provider?: string | null;
  operation?: string | null;
  last_success_at?: string | null;
  last_attempt_at?: string | null;
  response_age_seconds?: number | null;
  freshness_threshold_seconds?: number | null;
  coverage: { meetings: number; races: number; entries: number; results: number };
  failure_code?: 'INGESTION_FAILED' | 'DATABASE_UNAVAILABLE' | null;
};

export function liveIngestionStatusCopy(status: LiveIngestionHealth): { label: string; detail: string } {
  const coverage = `${status.coverage.meetings} meetings · ${status.coverage.races} races · ${status.coverage.entries} entries · ${status.coverage.results} results`;
  if (status.status === 'HEALTHY') {
    const age = status.response_age_seconds == null ? 'response age unavailable' : `${Math.floor(status.response_age_seconds / 60)}m ${status.response_age_seconds % 60}s response age`;
    return { label: 'HEALTHY · live receipt current', detail: `${age} · ${coverage}` };
  }
  if (status.status === 'STALE') return { label: 'STALE · live receipt outside freshness window', detail: coverage };
  if (status.status === 'FAILED') return { label: 'FAILED · latest ingestion did not complete', detail: `${status.failure_code ?? 'bounded failure'} · ${coverage}` };
  if (status.status === 'NO_DATA') return { label: 'NO DATA · no approved live receipt', detail: coverage };
  return { label: 'DISABLED · licensed ingestion is not active', detail: coverage };
}

function formatSydneyDateTime(value: string): string {
  return new Intl.DateTimeFormat('en-AU', {
    dateStyle: 'medium', timeStyle: 'short', timeZone: 'Australia/Sydney',
  }).format(new Date(value));
}

function liveEntryStateLabel(status: string): string {
  return status.replaceAll('_', ' ').toLowerCase().replace(/^./, (character) => character.toUpperCase());
}

export function liveCommandItems(meetings: LiveMeeting[]): CommandItem[] {
  return meetings.map((meeting) => ({
    id: meeting.meeting_id,
    code: meeting.code,
    label: meeting.code === 'THOROUGHBRED' ? 'Thoroughbred' : meeting.code,
    status: 'LIVE',
    meeting: meeting.name,
    localTime: new Intl.DateTimeFormat('en-AU', {
      dateStyle: 'medium', timeStyle: 'short', timeZone: 'Australia/Sydney',
    }).format(new Date(meeting.scheduled_date)),
    sourceAge: 'Canonical licensed receipt',
    note: `${meeting.country} meeting from the live read-only provider lane. Open the canonical race and entry view.`,
  }));
}

function answerAssistantQuestion(question: string): AssistantAnswer {
  const normalized = question.trim().toLowerCase();
  if (normalized.includes('discrep') || normalized.includes('differ') || normalized.includes('scratch')) {
    return {
      kind: 'DISCREPANCY',
      title: 'The forecast and field use different revisions.',
      body: 'The archived forecast references field-r1, while the current field is field-r2 after a scratching. The forecast remains immutable and is invalidated; no replacement probability was estimated for the changed field.',
      citations: [{ sourceId: 'synthetic://thoroughbred/race-001', modelId: 'B1_FORM_HEURISTIC', observedAt: '15 Jan 2026, 14:00 AEDT', limitation: 'Illustrative model archive; not validated.' }],
      noteDraft: 'Discrepancy: forecast field-r1 was invalidated after the field changed to field-r2; no replacement probability was estimated.',
    };
  }
  if (normalized.includes('section') || normalized.includes('speed') || normalized.includes('latest') || normalized.includes('current')) {
    return {
      kind: 'NOT_AVAILABLE',
      title: 'NOT_AVAILABLE · verified specialty evidence is absent.',
      body: 'No verified sectional-speed source is present in this synthetic fixture. The assistant will not estimate a current value or present an unsupported currentness claim.',
      citations: [{ sourceId: 'synthetic://thoroughbred/race-001', modelId: 'B0_UNIFORM', observedAt: '15 Jan 2026, 14:00 AEDT', limitation: 'No verified sectional or live source is available.' }],
      noteDraft: 'NOT_AVAILABLE: no verified sectional-speed source was available; no value was estimated.',
    };
  }
  return {
    kind: 'EVIDENCE',
    title: 'Evidence is available for the synthetic field record.',
    body: 'The field is a fictional, synthetic record at revision field-r2. The receipt and publication timestamps are shown below; this is provenance evidence, not a live or official racing claim.',
    citations: [{ sourceId: 'synthetic://thoroughbred/race-001', modelId: 'B0_UNIFORM', observedAt: '15 Jan 2026, 14:00 AEDT', limitation: 'Synthetic-only fixture; no live-source or validation claim.' }],
    noteDraft: 'Evidence note: field-r2 is a synthetic fixture record observed 15 Jan 2026 at 14:00 AEDT.',
  };
}

export default function App({ apiRequest }: { apiRequest?: NexusApiRequest } = {}) {
  const [activeWorkspace, setActiveWorkspace] = useState<WorkspaceId>('COMMAND');
  const [selectedCode, setSelectedCode] = useState<Code>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<Status | 'ALL'>('ALL');
  const [showStateExamples, setShowStateExamples] = useState(true);
  const [selectedRace, setSelectedRace] = useState<Exclude<Code, 'ALL'> | null>(null);
  const [evidenceTab, setEvidenceTab] = useState<EvidenceTab>('FIELD');
  const [apiStatus, setApiStatus] = useState<'idle' | 'checking' | 'ready' | 'denied' | 'unavailable'>('idle');
  const [dataMode, setDataMode] = useState<DataMode>(apiRequest && typeof window !== 'undefined' ? 'LOADING' : 'SYNTHETIC_ONLY');
  const [liveMeetings, setLiveMeetings] = useState<LiveMeeting[]>([]);
  const [liveIngestion, setLiveIngestion] = useState<LiveIngestionHealth | null>(null);
  const [selectedLiveMeeting, setSelectedLiveMeeting] = useState<LiveMeeting | null>(null);
  const visibleItems = useMemo(
    () => (dataMode === 'LICENSED' ? liveCommandItems(liveMeetings) : dataMode === 'LOADING' ? [] : commandItems).filter((item) =>
      (selectedCode === 'ALL' || item.code === selectedCode) &&
      (selectedStatus === 'ALL' || item.status === selectedStatus) &&
      (dataMode === 'LICENSED' || showStateExamples || item.status === 'DEMO')),
    [dataMode, liveMeetings, selectedCode, selectedStatus, showStateExamples],
  );

  useEffect(() => {
    if (!apiRequest) return;
    let active = true;
    setDataMode('LOADING');
    setApiStatus('checking');
    void Promise.all([
      apiRequest('/v1/system/status', undefined, 'races:read'),
      apiRequest('/v1/meetings', undefined, 'races:read'),
    ])
      .then(async ([statusResponse, meetingsResponse]) => {
        if (!active) return;
        const status = statusResponse.ok ? await statusResponse.json() as { data_mode?: string; live_ingestion?: LiveIngestionHealth } : {};
        const licensed = status.data_mode === 'LICENSED';
        if (licensed) setDataMode('LICENSED');
        if (licensed) setLiveIngestion(status.live_ingestion ?? null);
        if (!statusResponse.ok || !meetingsResponse.ok) {
          const response = !statusResponse.ok ? statusResponse : meetingsResponse;
          setApiStatus(response.status === 401 || response.status === 403 ? 'denied' : 'unavailable');
          setDataMode('LOADING');
          return;
        }
        if (!licensed) {
          setApiStatus('ready');
          return;
        }
        const page = await meetingsResponse.json() as ApiPage<LiveMeeting>;
        setDataMode('LICENSED');
        setLiveMeetings(Array.isArray(page.items) ? page.items : []);
        setApiStatus('ready');
      })
      .catch(() => {
        if (active) {
          setApiStatus('unavailable');
          setDataMode('LOADING');
        }
      });
    return () => { active = false; };
  }, [apiRequest]);

  useEffect(() => {
    if (dataMode === 'LICENSED') {
      setSelectedStatus('ALL');
      setShowStateExamples(false);
    }
  }, [dataMode]);

  const activeWorkspaceLabel = workspaces.find((workspace) => workspace.value === activeWorkspace)?.label ?? 'Command Centre';
  const isCommandWorkspace = activeWorkspace === 'COMMAND' || (dataMode === 'LICENSED' && activeWorkspace === 'MEETINGS');

  return (
    <main className="shell nexus-shell">
      <header className="topbar">
        <div className="brand-lockup"><NexusMark /><div><p className="eyebrow">RACING INTELLIGENCE LAB</p><div className="brand-wordmark">NEXUS <span>/ RESEARCH OS</span></div><h1>{activeWorkspace === 'COMMAND' ? 'Today / Command Centre' : activeWorkspaceLabel}</h1></div></div>
        <div className="topbar-meta"><div className="session-chip"><span className="session-pulse" aria-hidden="true" /> PRIVATE OWNER WORKSPACE</div><div className="header-badges">{dataMode === 'LICENSED' ? <><span className="mode-badge">LIVE READ-ONLY</span><span className="mode-badge subdued">LICENSED</span></> : dataMode === 'LOADING' ? <><span className="mode-badge subdued">LIVE CHECK</span><span className="mode-badge subdued">API CHECKING</span></> : <><span className="mode-badge">DEMO ONLY</span><span className="mode-badge subdued">SYNTHETIC_ONLY</span></>}{apiStatus !== 'idle' && dataMode !== 'LOADING' && <span className="mode-badge subdued">API {apiStatus.toUpperCase()}</span>}</div></div>
      </header>
      <nav className="workspace-nav" aria-label="Research workspaces">
        {workspaces.map((workspace) => <button aria-current={activeWorkspace === workspace.value ? 'page' : undefined} className={activeWorkspace === workspace.value ? 'workspace-link active' : 'workspace-link'} key={workspace.value} onClick={() => setActiveWorkspace(workspace.value)} type="button"><span>{workspace.short}</span><small>{workspace.label}</small></button>)}
      </nav>
      {dataMode === 'LOADING' && <LoadingWorkspace apiStatus={apiStatus} />}
      {dataMode !== 'LOADING' && !isCommandWorkspace && <WorkspaceBoundary workspace={activeWorkspace} dataMode={dataMode} onReturn={() => setActiveWorkspace('COMMAND')} />}
      {dataMode !== 'LOADING' && isCommandWorkspace && <>
      <section className="intro" aria-labelledby="intro-title">
        <p className="eyebrow">{dataMode === 'LICENSED' ? 'PRIVATE PROVIDER WORKSPACE' : 'LOCAL RESEARCH WORKSPACE'}</p>
        <h2 id="intro-title">{dataMode === 'LICENSED' ? 'Provider-backed meetings, one honest evidence view.' : 'Three racing codes, one honest evidence view.'}</h2>
        <p>{dataMode === 'LICENSED' ? 'Browse canonical meetings captured from the licensed read-only provider lane. Forecasts, market views and race detail remain unavailable until their own evidence tickets pass.' : 'Browse the fictional fixture pack by code and data state. Every card is explicitly labelled; this screen never presents synthetic records as live racing or validated advice.'}</p>
      </section>
      <section className="command-panel" aria-label="Command centre filters">
        <div className="filter-group"><span className="filter-label">Code</span><div className="filter-row" role="group" aria-label="Filter by racing code">
          {codes.map((code) => <button aria-pressed={selectedCode === code.value} className={`filter-button ${selectedCode === code.value ? 'selected' : ''}`} key={code.value} onClick={() => setSelectedCode(code.value)} type="button">{code.label}</button>)}
        </div></div>
        {dataMode === 'LICENSED' ? <div className="live-filter-note"><span className="filter-label">Data state</span><strong>Live provider · current receipt</strong><small>Availability examples are hidden in licensed mode.</small></div> : <><div className="filter-group"><label className="filter-label" htmlFor="state-filter">Data state</label><select id="state-filter" value={selectedStatus} onChange={(event) => setSelectedStatus(event.target.value as Status | 'ALL')}>
          {statuses.filter((status) => status.value !== 'LIVE').map((status) => <option key={status.value} value={status.value}>{status.label}</option>)}
        </select></div>
        <label className="state-toggle"><input checked={showStateExamples} onChange={(event) => setShowStateExamples(event.target.checked)} type="checkbox" />Show availability examples</label></>}
      </section>
      <section className="summary-strip" aria-label="Workspace status">
        <div><span className="summary-value">{visibleItems.length}</span><span className="summary-label">visible cards</span></div>
        <div><span className="summary-value">{dataMode === 'LICENSED' ? new Set(liveMeetings.map((meeting) => meeting.code)).size : 3}</span><span className="summary-label">codes covered</span></div>
        <div><span className="summary-value">{localNow()}</span><span className="summary-label">local browser time · Australia/Sydney</span></div>
      </section>
      {dataMode === 'LICENSED' && liveIngestion && <LiveIngestionStatusCard status={liveIngestion} />}
      {dataMode === 'SYNTHETIC_ONLY' && <AssistantWorkbench />}
      <section className="code-grid" aria-label="Today command cards">
        {visibleItems.map((item) => <article aria-label={`${item.label} · ${statusText[item.status]}`} className={`code-card status-${item.status.toLowerCase()}`} key={item.id}>
          <div className="card-topline"><span className="status-dot" aria-hidden="true" /><span className="status-pill">{statusText[item.status]}</span></div>
          <h3>{item.label}</h3>{item.meeting && <p className="meeting-name">{item.meeting}</p>}
          <dl className="card-facts">{item.races !== undefined && <><dt>Races</dt><dd>{item.races} fictional races</dd></>}{item.localTime && <><dt>{item.status === 'LIVE' ? 'Scheduled' : 'Fixture time'}</dt><dd>{item.localTime}</dd></>}<dt>{item.status === 'LIVE' ? 'Receipt' : 'Source age'}</dt><dd>{item.sourceAge}</dd></dl>
          <p className="card-note">{item.note}</p>
          {item.status === 'DEMO' && <button aria-label={`Open research view for ${item.label}`} className="research-button" onClick={() => { setSelectedRace(item.code); setEvidenceTab('FIELD'); }} type="button">Open research view</button>}
          {item.status === 'LIVE' && <button aria-label={`Open live meeting for ${item.meeting}`} className="research-button" onClick={() => setSelectedLiveMeeting(liveMeetings.find((meeting) => meeting.meeting_id === item.id) ?? null)} type="button">Open live meeting</button>}
          <span className="card-watermark">{item.status === 'LIVE' ? 'LICENSED · READ-ONLY · NO WAGERING' : 'FICTIONAL · NOT LIVE · NO WAGERING'}</span>
        </article>)}
      </section>
      {visibleItems.length === 0 && <section className="empty-state" aria-live="polite"><p className="eyebrow">NO MATCHING STATES</p><h3>No cards match these filters.</h3><p>Change the code or data-state filter. No racing data is invented to fill an empty view.</p></section>}
      {selectedRace && <ResearchView key={selectedRace} race={researchRaces[selectedRace]} evidenceTab={evidenceTab} onClose={() => setSelectedRace(null)} onTabChange={setEvidenceTab} />}
      {selectedLiveMeeting && apiRequest && <LiveMeetingView meeting={selectedLiveMeeting} apiRequest={apiRequest} onClose={() => setSelectedLiveMeeting(null)} />}
      {dataMode === 'LICENSED' && <section className="licensed-boundary" aria-label="Licensed capability boundary"><div><p className="eyebrow">LICENSED READ-ONLY SCOPE</p><h2>Canonical racing evidence only</h2><p>Forecasts, markets, exports and wagering actions are not enabled for this provider lane.</p></div><div className="capability-list"><span>Races and entries · available</span><span>Forecasts · not available</span><span>Wagering · disabled</span></div></section>}
      </>}
      <footer className="footer"><span>{dataMode === 'LICENSED' ? 'Provider API: licensed staging lane' : dataMode === 'LOADING' ? 'Provider API: establishing secure session' : 'Local API: 127.0.0.1:8000'}</span><span>Data rights: {dataMode === 'LICENSED' ? 'owner-approved private read' : dataMode === 'LOADING' ? 'rights state pending verification' : 'synthetic fixture only'}</span><span>Model: not trained</span></footer>
    </main>
  );
}

function NexusMark() {
  return <svg className="nexus-mark" aria-hidden="true" viewBox="0 0 48 48" role="img"><path d="M24 3 42 13v22L24 45 6 35V13L24 3Z" fill="none" stroke="currentColor" strokeWidth="1.5" /><path d="m14 31 20-14M14 17l20 14M24 9v30" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /><circle cx="24" cy="24" r="4" fill="currentColor" /></svg>;
}

function LoadingWorkspace({ apiStatus }: { apiStatus: 'idle' | 'checking' | 'ready' | 'denied' | 'unavailable' }) {
  const failure = apiStatus === 'denied' || apiStatus === 'unavailable';
  return <section className="loading-workspace" aria-label="Secure provider workspace" aria-live="polite">
    <div className="loading-copy"><p className="eyebrow">SECURE PROVIDER HANDSHAKE</p><h2>{failure ? 'Live workspace is waiting for a verified response.' : 'Establishing the live research surface.'}</h2><p>{failure ? 'No synthetic replacement is shown. Confirm the owner session and API availability before continuing.' : 'Nexus is checking the authenticated provider lane, rights state and current receipt. No racing values are rendered until that check completes.'}</p><div className="loading-status"><span className="loading-spinner" aria-hidden="true" /> {failure ? `API ${apiStatus.toUpperCase()} · no data rendered` : 'API CHECKING · no data rendered'}</div></div>
    <div className="loading-orbit" aria-hidden="true"><span /><span /><span /><b>NEXUS</b></div>
  </section>;
}

function WorkspaceBoundary({ workspace, dataMode, onReturn }: { workspace: WorkspaceId; dataMode: Exclude<DataMode, 'LOADING'>; onReturn: () => void }) {
  const metadata = workspaces.find((item) => item.value === workspace) ?? workspaces[0];
  const preview = workspacePreviewCopy[workspace];
  const liveMessage = dataMode === 'LICENSED'
    ? 'This licensed staging lane currently exposes canonical meetings, races and entries only. No unsupported values are invented to fill the workspace.'
    : 'This workspace is part of the research atlas. Use the Command Centre to open a clearly labelled synthetic race view.';
  return <section className={`workspace-panel workspace-preview workspace-${workspace.toLowerCase()}`} aria-label={`${metadata.label} workspace`}>
    <div className="workspace-heading"><div><p className="eyebrow">WORKSPACE ATLAS · {dataMode === 'LICENSED' ? 'LICENSED READ-ONLY' : 'SYNTHETIC DEMO'}</p><h2>{preview.title}</h2><p className="workspace-subtitle">{preview.description}</p></div><span className={`mode-badge ${dataMode === 'LICENSED' ? 'warning-badge' : 'subdued'}`}>{dataMode === 'LICENSED' ? 'NOT_AVAILABLE' : preview.signal}</span></div>
    <div className="workspace-context" aria-label="Shared research context"><div><span>Mode</span><strong>{dataMode}</strong></div><div><span>Scope</span><strong>{dataMode === 'LICENSED' ? 'READ-ONLY' : 'RESEARCH DEMO'}</strong></div><div><span>Evidence</span><strong>{dataMode === 'LICENSED' ? 'CANONICAL ONLY' : 'FIXTURE LABELLED'}</strong></div><div><span>Wagering</span><strong>DISABLED</strong></div></div>
    {dataMode === 'SYNTHETIC_ONLY' ? <><div className="workspace-preview-grid"><div className="preview-visual"><div className="preview-visual-grid" /><span className="preview-visual-kicker">{preview.eyebrow}</span><strong>{preview.signal}</strong><small>Shared context / field-r2 / source labelled</small></div><div className="preview-metric-list">{preview.metrics.map((metric, index) => <div key={metric}><span>0{index + 1}</span><strong>{metric}</strong><small>{index === 0 ? 'Current workspace lens' : index === 1 ? 'Evidence attached' : 'No value inferred'}</small></div>)}</div></div><div className="state-callout"><strong>Research preview · synthetic only.</strong> {liveMessage}</div></> : <div className="state-callout"><strong>{metadata.label} is bounded in this release.</strong> {liveMessage}</div>}
    <button className="secondary-action" onClick={onReturn} type="button">Return to Command Centre</button>
  </section>;
}

function LiveIngestionStatusCard({ status }: { status: LiveIngestionHealth }) {
  const copy = liveIngestionStatusCopy(status);
  return <section className={`live-health live-health-${status.status.toLowerCase()}`} aria-label="Live ingestion status">
    <div>
      <p className="eyebrow">LICENSED INGESTION MONITOR</p>
      <h2>{copy.label}</h2>
      <p>{copy.detail}</p>
    </div>
    <dl>
      <div><dt>Provider</dt><dd>{status.provider ?? 'not configured'}</dd></div>
      <div><dt>Operation</dt><dd>{status.operation ?? 'not configured'}</dd></div>
      <div><dt>Last successful run</dt><dd>{status.last_success_at ? formatSydneyDateTime(status.last_success_at) : 'not available'}</dd></div>
      <div><dt>Freshness window</dt><dd>{status.freshness_threshold_seconds ? `${Math.floor(status.freshness_threshold_seconds / 60)} minutes` : 'not configured'}</dd></div>
    </dl>
  </section>;
}

function LiveMeetingView({ meeting, apiRequest, onClose }: { meeting: LiveMeeting; apiRequest: NexusApiRequest; onClose: () => void }) {
  const [races, setRaces] = useState<LiveRace[]>([]);
  const [entries, setEntries] = useState<Record<string, LiveEntry[]>>({});
  const [state, setState] = useState<'loading' | 'ready' | 'unavailable'>('loading');

  useEffect(() => {
    let active = true;
    void apiRequest(`/v1/meetings/${encodeURIComponent(meeting.meeting_id)}/races`, undefined, 'races:read')
      .then(async (response) => {
        if (!response.ok) throw new Error('race list unavailable');
        const page = await response.json() as ApiPage<LiveRace>;
        const liveRaces = Array.isArray(page.items) ? page.items : [];
        const entryPages = await Promise.all(liveRaces.map(async (race) => {
          const entryResponse = await apiRequest(`/v1/races/${encodeURIComponent(race.race_id)}/entries`, undefined, 'races:read');
          if (!entryResponse.ok) return [race.race_id, []] as const;
          const entryPage = await entryResponse.json() as ApiPage<LiveEntry>;
          return [race.race_id, Array.isArray(entryPage.items) ? entryPage.items : []] as const;
        }));
        if (!active) return;
        setRaces(liveRaces);
        setEntries(Object.fromEntries(entryPages));
        setState('ready');
      })
      .catch(() => { if (active) setState('unavailable'); });
    return () => { active = false; };
  }, [apiRequest, meeting.meeting_id]);

  return <section className="research-view live-meeting-view" aria-label="Live meeting view">
    <div className="research-heading"><div><p className="eyebrow">LIVE RESEARCH VIEW · READ-ONLY</p><h2>{meeting.name}</h2><p className="research-subtitle">{meeting.country} · canonical licensed meeting</p></div><button className="close-button" onClick={onClose} type="button">Close view</button></div>
    <div className="research-facts"><div><span>Scheduled</span><strong>{formatSydneyDateTime(meeting.scheduled_date)}</strong></div><div><span>Data mode</span><strong>LICENSED</strong></div><div><span>Wagering</span><strong>DISABLED</strong></div></div>
    {state === 'loading' && <div className="empty-state" aria-live="polite"><h3>Loading canonical races</h3><p>No partial provider values are displayed.</p></div>}
    {state === 'unavailable' && <div className="empty-state" aria-live="polite"><h3>Race detail unavailable</h3><p>The canonical race or entry endpoint did not return an approved response. No synthetic replacement is shown.</p></div>}
    {state === 'ready' && races.length === 0 && <div className="empty-state" aria-live="polite"><h3>No canonical races captured</h3><p>The meeting exists, but no race rows are currently available.</p></div>}
    {state === 'ready' && races.map((race) => {
      const raceEntries = entries[race.race_id] ?? [];
      const activeEntries = raceEntries.filter((entry) => entry.status === 'ACTIVE').length;
      const scratchedEntries = raceEntries.filter((entry) => entry.status === 'SCRATCHED').length;
      return <div className="evidence-panel live-race-panel" key={race.race_id}>
        <div className="panel-heading"><div><p className="eyebrow">CANONICAL RACE</p><h3>Race {race.race_number}</h3><p className="panel-note">{race.status} · field {race.field_revision}</p></div><span className="status-pill">LICENSED</span></div>
        <div className="live-race-summary" aria-label={`Race ${race.race_number} field summary`}><div><strong>{raceEntries.length}</strong><span>total entries</span></div><div><strong>{activeEntries}</strong><span>active</span></div><div><strong>{scratchedEntries}</strong><span>scratched</span></div></div>
        <table><caption>Canonical entries · current field revision</caption><thead><tr><th scope="col">No.</th><th scope="col">Participant</th><th scope="col">State</th></tr></thead><tbody>{raceEntries.map((entry) => <tr key={entry.entry_id}><td className="entry-number">{entry.number}</td><td>{entry.name ?? entry.participant_id}</td><td><span className={`entry-state entry-${entry.status.toLowerCase()}`} aria-label={liveEntryStateLabel(entry.status)}>{liveEntryStateLabel(entry.status)}</span></td></tr>)}</tbody></table>
        <div className="provenance-note"><strong>Receipt verified</strong><span>{race.source_receipt_id ?? 'Receipt identifier not exposed'}</span><small>Provider payloads and forecasts are not displayed.</small></div>
      </div>;
    })}
  </section>;
}

function AssistantWorkbench() {
  const [question, setQuestion] = useState('What evidence supports this race?');
  const [answer, setAnswer] = useState<AssistantAnswer>(() => answerAssistantQuestion('evidence'));
  const [noteDraft, setNoteDraft] = useState(answer.noteDraft);
  const [approval, setApproval] = useState(false);
  const [savedNote, setSavedNote] = useState(false);

  const ask = (value: string) => {
    const nextAnswer = answerAssistantQuestion(value);
    setQuestion(value);
    setAnswer(nextAnswer);
    setNoteDraft(nextAnswer.noteDraft);
    setApproval(false);
    setSavedNote(false);
  };

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (question.trim()) ask(question);
  };

  return <section className="assistant-workbench" aria-labelledby="assistant-title">
    <div className="assistant-heading"><div><p className="eyebrow">BOUNDED RESEARCH ASSISTANT · SYNTHETIC DEMO</p><h2 id="assistant-title">Ask an evidence-grounded question.</h2></div><div className="header-badges"><span className="mode-badge subdued">SYNTHETIC_ONLY</span><span className="mode-badge">CITATIONS REQUIRED</span></div></div>
    <p className="assistant-disclaimer">Answers cite source IDs, model IDs, timestamps and limitations. Unknown or missing values return <strong>NOT_AVAILABLE</strong>; nothing is estimated or presented as live, official or validated.</p>
    <div className="assistant-prompts" aria-label="Example questions">
      <button type="button" onClick={() => ask('What evidence supports this race?')}>Evidence for this race</button>
      <button type="button" onClick={() => ask('Why does the forecast differ from the current field?')}>Explain discrepancy</button>
      <button type="button" onClick={() => ask('What is the current sectional speed?')}>Ask for missing value</button>
    </div>
    <form className="assistant-form" onSubmit={submit}><label htmlFor="assistant-question">Question</label><div><input id="assistant-question" value={question} onChange={(event) => setQuestion(event.target.value)} /><button type="submit">Ask</button></div></form>
    <article className={`assistant-answer assistant-${answer.kind.toLowerCase()}`} aria-live="polite">
      <div className="panel-heading"><div><span className="assistant-answer-kind">{answer.kind === 'NOT_AVAILABLE' ? 'NOT_AVAILABLE' : answer.kind}</span><h3>{answer.title}</h3></div></div>
      <p>{answer.body}</p>
      <section className="citation-block" aria-label="Answer citations"><h4>Evidence citations</h4>{answer.citations.map((citation) => <dl key={`${citation.sourceId}-${citation.modelId}`} className="citation-card"><dt>Source ID</dt><dd>{citation.sourceId}</dd><dt>Model ID</dt><dd>{citation.modelId}</dd><dt>Observed</dt><dd>{citation.observedAt}</dd><dt>Limitation</dt><dd>{citation.limitation}</dd></dl>)}</section>
      <section className="note-block" aria-label="User approved note"><h4>Optional local note</h4><textarea aria-label="Note draft" value={noteDraft} onChange={(event) => { setNoteDraft(event.target.value); setSavedNote(false); }} /><label className="approval-row"><input checked={approval} onChange={(event) => setApproval(event.target.checked)} type="checkbox" />I approve saving this note to my local journal.</label><button className="note-button" disabled={!approval || !noteDraft.trim()} onClick={() => setSavedNote(true)} type="button">Save approved note</button>{savedNote && <p className="saved-note" role="status">Saved locally · user approved · no external transmission</p>}</section>
    </article>
  </section>;
}

function ResearchView({ race, evidenceTab, onClose, onTabChange }: { race: ResearchRace; evidenceTab: EvidenceTab; onClose: () => void; onTabChange: (tab: EvidenceTab) => void }) {
  const [selectedNumbers, setSelectedNumbers] = useState<number[]>([1, 3]);
  const selectedRows = race.comparisonRows.filter((row) => selectedNumbers.includes(row.number));
  const toggleRunner = (number: number) => setSelectedNumbers((current) => current.includes(number) ? (current.length > 2 ? current.filter((value) => value !== number) : current) : [...current, number].slice(0, 4));

  return <section className="research-view" aria-label="Race research view">
    <div className="research-heading"><div><p className="eyebrow">RESEARCH VIEW · SYNTHETIC DEMO</p><h2>{race.meeting} · {race.raceLabel}</h2><p className="research-subtitle">Field revision <strong>{race.fieldRevision}</strong> · {race.fieldState} · fictional record</p></div><button className="close-button" onClick={onClose} type="button">Close view</button></div>
    <div className="research-facts"><div><span>Observed</span><strong>{race.observedAt}</strong></div><div><span>Published</span><strong>{race.publishedAt}</strong></div><div><span>Data mode</span><strong>SYNTHETIC_ONLY</strong></div></div>
    <div className="evidence-tabs" role="tablist" aria-label="Race evidence tabs">
      {([['FIELD', 'Field'], ['PROVENANCE', 'Provenance'], ['FORECAST', 'Forecast archive'], ['MARKET', 'Market workbench']] as const).map(([value, label]) => <button aria-selected={evidenceTab === value} className={evidenceTab === value ? 'tab selected' : 'tab'} key={value} onClick={() => onTabChange(value)} role="tab" type="button">{label}</button>)}
    </div>
    {evidenceTab === 'FIELD' && <div className="evidence-panel" role="tabpanel"><div className="panel-heading"><h3>Entries at {race.fieldRevision}</h3><span className="status-pill">Current field</span></div><section className="compare-panel" aria-label="Runner compare"><div className="panel-heading"><div><h3>Runner compare</h3><p className="panel-note">Select 2–4 runners; all rows use the same distance and fixture context.</p></div><span className="compare-count">Compare {selectedRows.length} runners</span></div><div className="runner-picker">{race.entries.map((entry) => <label className="runner-option" key={entry.number}><input checked={selectedNumbers.includes(entry.number)} disabled={selectedNumbers.length === 2 && selectedNumbers.includes(entry.number)} onChange={() => toggleRunner(entry.number)} type="checkbox" /><span>Runner {entry.number} · {entry.status}</span></label>)}</div><table><caption>Matched comparison units</caption><thead><tr><th scope="col">Runner</th><th scope="col">Distance</th><th scope="col">Fixture context</th><th scope="col">Recent form</th></tr></thead><tbody>{selectedRows.map((row) => <tr key={row.number}><td>{row.name}</td><td>{row.distance}</td><td>{row.context}</td><td>{row.recentForm}</td></tr>)}</tbody></table><div className="code-panel"><h4>{race.codePanelTitle}</h4><p><strong>{race.specialtyLabel}:</strong> Not available in fixture.</p><p className="panel-note">{race.specialtyExplanation} No value is invented for the comparison.</p></div></section><table><caption>Fictional entries and field state</caption><thead><tr><th scope="col">No.</th><th scope="col">Participant</th><th scope="col">State</th></tr></thead><tbody>{race.entries.map((entry) => <tr key={entry.number}><td>{entry.number}</td><td>{entry.name}</td><td><span className={`entry-state entry-${entry.status.toLowerCase()}`}>{entry.status}</span></td></tr>)}</tbody></table><p className="panel-note">A scratching created {race.fieldRevision}; the prior forecast is retained but no longer current.</p></div>}
    {evidenceTab === 'PROVENANCE' && <div className="evidence-panel" role="tabpanel"><div className="panel-heading"><h3>Available evidence</h3><span className="status-pill">Receipt verified</span></div><dl className="provenance-facts"><dt>Source receipt</dt><dd>synthetic://{race.code.toLowerCase()}/race-001</dd><dt>First observed</dt><dd>{race.observedAt}</dd><dt>Publication proof</dt><dd>{race.publishedAt}</dd><dt>Rights state</dt><dd>SYNTHETIC · fictional fixture</dd><dt>External connectivity</dt><dd>Disabled</dd></dl></div>}
    {evidenceTab === 'FORECAST' && <ForecastWorkbench race={race} />}
    {evidenceTab === 'MARKET' && <MarketWorkbench />}
  </section>;
}

function ForecastWorkbench({ race }: { race: ResearchRace }) {
  const activeEntries = race.entries.filter((entry) => entry.status === 'ACTIVE');
  return <div className="evidence-panel forecast-workbench" role="tabpanel" aria-label="Forecast comparison workbench">
    <div className="panel-heading"><div><p className="eyebrow">MODEL COMPARISON · SYNTHETIC EVIDENCE</p><h3>Winning-probability assessments</h3></div><span className="status-pill">NOT VALIDATED</span></div>
    <p className="panel-note">All probabilities, fair prices and metrics below are illustrative synthetic outputs. No result represents live racing accuracy, advice or profitability.</p>
    <div className="forecast-grid">
      {race.forecasts.map((forecast) => <article className="forecast-card" key={forecast.modelId}>
        <div className="panel-heading"><div><h4>{forecast.label}</h4><span className="model-family">{forecast.family.replace('_', ' ')}</span></div><span className={forecast.status === 'READY' ? 'status-pill' : 'invalidated-pill'}>{forecast.status}</span></div>
        <dl className="forecast-facts"><dt>Model version</dt><dd>{forecast.modelVersion}</dd><dt>Uncertainty</dt><dd>{forecast.uncertainty}</dd><dt>Missing evidence</dt><dd>{forecast.missing}</dd></dl>
        <table><caption>Race-normalised probabilities</caption><thead><tr><th scope="col">Runner</th><th scope="col">Win probability</th><th scope="col">Fair price</th></tr></thead><tbody>{activeEntries.map((entry) => { const probability = forecast.probabilities[entry.number]; return <tr key={entry.number}><td>Runner {entry.number}</td><td>{probability === undefined ? 'NOT_AVAILABLE' : `${(probability * 100).toFixed(1)}%`}</td><td>{probability === undefined ? '—' : `${(1 / probability).toFixed(2)} decimal`}</td></tr>; })}</tbody></table>
        <p className="model-disagreement"><strong>Model disagreement:</strong> {forecast.disagreement}</p>
      </article>)}
    </div>
    <section className="evaluation-panel" aria-label="Historical evaluation summary"><div className="panel-heading"><div><h3>Walk-forward evaluation</h3><p className="panel-note">Metrics are reproduced from the synthetic research report.</p></div><span className="status-pill">{race.evaluation.walkForward.split(' · ')[0]}</span></div><p>{race.evaluation.walkForward}</p><p>{race.evaluation.calibration}</p><table><caption>Illustrative model metrics</caption><thead><tr><th scope="col">Model</th><th scope="col">Log loss</th><th scope="col">Brier</th><th scope="col">Top-ranked win</th></tr></thead><tbody>{race.evaluation.metrics.map((metric) => <tr key={metric.model}><td>{metric.model}</td><td>{metric.logLoss}</td><td>{metric.brier}</td><td>{metric.topRanked}</td></tr>)}</tbody></table><h4>Feature-family ablation</h4><table><caption>Incremental feature evidence</caption><thead><tr><th scope="col">Family</th><th scope="col">Change</th><th scope="col">Status</th></tr></thead><tbody>{race.evaluation.ablation.map((row) => <tr key={row.family}><td>{row.family}</td><td>{row.delta}</td><td>{row.status}</td></tr>)}</tbody></table></section>
    <section className="feature-availability" aria-label="Feature availability"><div className="panel-heading"><div><h3>Feature availability and provenance</h3><p className="panel-note">Unavailable and restricted features remain unavailable; no values are inferred.</p></div></div><table><caption>Pre-race feature evidence</caption><thead><tr><th scope="col">Feature family</th><th scope="col">State</th><th scope="col">Source / dataset</th><th scope="col">Evidence note</th></tr></thead><tbody>{race.featureAvailability.map((feature) => <tr key={feature.name}><td>{feature.name}</td><td><span className={`entry-state entry-${feature.status.toLowerCase()}`}>{feature.status}</span></td><td>{feature.source}</td><td>{feature.detail}</td></tr>)}</tbody></table></section>
    <section className="evidence-panel archived-forecast"><div className="panel-heading"><h3>Archived forecast</h3><span className="invalidated-pill">INVALIDATED BY FIELD REVISION</span></div><dl className="provenance-facts"><dt>Forecast ID</dt><dd>forecast-{race.code.toLowerCase()}-r1</dd><dt>Model</dt><dd>B1 illustrative · not validated</dd><dt>Forecast field</dt><dd>field-r1 (superseded)</dd><dt>Current field</dt><dd>{race.fieldRevision}</dd><dt>Action</dt><dd>No reuse after scratching; archive remains immutable.</dd></dl></section>
  </div>;
}

function MarketWorkbench() {
  return <div className="evidence-panel market-workbench" role="tabpanel" aria-label="Market workbench">
    <div className="panel-heading"><div><p className="eyebrow">PAPER ANALYSIS · SYNTHETIC FIXTURE</p><h3>Market snapshot</h3></div><span className="status-pill">COMPARABLE</span></div>
    <div className="market-facts">
      <div><span>Source</span><strong>synthetic-fixture</strong></div><div><span>Quote timestamp</span><strong>15 Jan 2026 · 13:55 AEDT</strong></div><div><span>Freshness</span><strong>AVAILABLE · 5 min</strong></div><div><span>Market type</span><strong>WIN · decimal</strong></div><div><span>Overround</span><strong>1.1250</strong></div><div><span>Rights</span><strong>SYNTHETIC</strong></div>
    </div>
    <table><caption>Exact mapped selections · raw prices are permitted for this synthetic fixture</caption><thead><tr><th scope="col">Selection</th><th scope="col">Field revision</th><th scope="col">Price</th><th scope="col">Liquidity</th></tr></thead><tbody><tr><td>Runner 1 · selection-1</td><td>field-r2</td><td>2.00</td><td>100 units</td></tr><tr><td>Runner 3 · selection-3</td><td>field-r2</td><td>4.00</td><td>80 units</td></tr></tbody></table>
    <section className="market-restricted" aria-label="Restricted market example"><div className="panel-heading"><div><h4>Restricted-source safety state</h4><p className="panel-note">A source without display/export permission cannot expose raw prices.</p></div><span className="invalidated-pill">NOT_COMPARABLE</span></div><dl className="provenance-facts"><dt>Comparison</dt><dd>NOT_COMPARABLE · rights gate failed</dd><dt>Raw prices</dt><dd>SUPPRESSED · RESTRICTED</dd><dt>Export</dt><dd>NOT_AVAILABLE · entitlement required</dd></dl><button className="restricted-export" disabled type="button">Export restricted prices</button></section>
    <p className="panel-note market-disclaimer">Paper analysis only. No live odds, order operation, bookmaker credential, or guaranteed-return claim is available from this view.</p>
  </div>;
}

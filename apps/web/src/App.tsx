import { useMemo, useState } from 'react';

type Code = 'ALL' | 'THOROUGHBRED' | 'HARNESS' | 'GREYHOUND';
type Status = 'DEMO' | 'NO_RACING' | 'NO_DATA' | 'UNAVAILABLE' | 'LOADING' | 'STALE' | 'QUARANTINED' | 'UNSUPPORTED' | 'AUTH_DENIED';

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

type EvidenceTab = 'FIELD' | 'PROVENANCE' | 'FORECAST';

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
};

const codes: Array<{ value: Code; label: string }> = [
  { value: 'ALL', label: 'All codes' },
  { value: 'THOROUGHBRED', label: 'Thoroughbred' },
  { value: 'HARNESS', label: 'Harness' },
  { value: 'GREYHOUND', label: 'Greyhound' },
];

const statuses: Array<{ value: Status | 'ALL'; label: string }> = [
  { value: 'ALL', label: 'All states' },
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
  },
};

const statusText: Record<Status, string> = {
  DEMO: 'Fictional demo', NO_RACING: 'No racing', NO_DATA: 'No data', UNAVAILABLE: 'Unavailable',
  LOADING: 'Loading', STALE: 'Stale snapshot', QUARANTINED: 'Quarantined', UNSUPPORTED: 'Unsupported', AUTH_DENIED: 'Auth denied',
};

function localNow(): string {
  return new Intl.DateTimeFormat('en-AU', {
    dateStyle: 'medium', timeStyle: 'short', timeZone: 'Australia/Sydney',
  }).format(new Date());
}

export default function App() {
  const [selectedCode, setSelectedCode] = useState<Code>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<Status | 'ALL'>('ALL');
  const [showStateExamples, setShowStateExamples] = useState(true);
  const [selectedRace, setSelectedRace] = useState<Exclude<Code, 'ALL'> | null>(null);
  const [evidenceTab, setEvidenceTab] = useState<EvidenceTab>('FIELD');
  const visibleItems = useMemo(
    () => commandItems.filter((item) =>
      (selectedCode === 'ALL' || item.code === selectedCode) &&
      (selectedStatus === 'ALL' || item.status === selectedStatus) &&
      (showStateExamples || item.status === 'DEMO')),
    [selectedCode, selectedStatus, showStateExamples],
  );

  return (
    <main className="shell">
      <header className="topbar">
        <div><p className="eyebrow">RACING INTELLIGENCE LAB</p><h1>Today / Command Centre</h1></div>
        <div className="header-badges"><span className="mode-badge">DEMO ONLY</span><span className="mode-badge subdued">SYNTHETIC_ONLY</span></div>
      </header>
      <section className="intro" aria-labelledby="intro-title">
        <p className="eyebrow">LOCAL RESEARCH WORKSPACE</p>
        <h2 id="intro-title">Three racing codes, one honest evidence view.</h2>
        <p>Browse the fictional fixture pack by code and data state. Every card is explicitly labelled; this screen never presents synthetic records as live racing or validated advice.</p>
      </section>
      <section className="command-panel" aria-label="Command centre filters">
        <div className="filter-group"><span className="filter-label">Code</span><div className="filter-row" role="group" aria-label="Filter by racing code">
          {codes.map((code) => <button aria-pressed={selectedCode === code.value} className={`filter-button ${selectedCode === code.value ? 'selected' : ''}`} key={code.value} onClick={() => setSelectedCode(code.value)} type="button">{code.label}</button>)}
        </div></div>
        <div className="filter-group"><label className="filter-label" htmlFor="state-filter">Data state</label><select id="state-filter" value={selectedStatus} onChange={(event) => setSelectedStatus(event.target.value as Status | 'ALL')}>
          {statuses.map((status) => <option key={status.value} value={status.value}>{status.label}</option>)}
        </select></div>
        <label className="state-toggle"><input checked={showStateExamples} onChange={(event) => setShowStateExamples(event.target.checked)} type="checkbox" />Show availability examples</label>
      </section>
      <section className="summary-strip" aria-label="Workspace status">
        <div><span className="summary-value">{visibleItems.length}</span><span className="summary-label">visible cards</span></div>
        <div><span className="summary-value">3</span><span className="summary-label">codes covered</span></div>
        <div><span className="summary-value">{localNow()}</span><span className="summary-label">local browser time · Australia/Sydney</span></div>
      </section>
      <section className="code-grid" aria-label="Today command cards">
        {visibleItems.map((item) => <article aria-label={`${item.label} · ${statusText[item.status]}`} className={`code-card status-${item.status.toLowerCase()}`} key={item.id}>
          <div className="card-topline"><span className="status-dot" aria-hidden="true" /><span className="status-pill">{statusText[item.status]}</span></div>
          <h3>{item.label}</h3>{item.meeting && <p className="meeting-name">{item.meeting}</p>}
          <dl className="card-facts">{item.races !== undefined && <><dt>Races</dt><dd>{item.races} fictional races</dd></>}{item.localTime && <><dt>Fixture time</dt><dd>{item.localTime}</dd></>}<dt>Source age</dt><dd>{item.sourceAge}</dd></dl>
          <p className="card-note">{item.note}</p>
          {item.status === 'DEMO' && <button aria-label={`Open research view for ${item.label}`} className="research-button" onClick={() => { setSelectedRace(item.code); setEvidenceTab('FIELD'); }} type="button">Open research view</button>}
          <span className="card-watermark">FICTIONAL · NOT LIVE · NO WAGERING</span>
        </article>)}
      </section>
      {visibleItems.length === 0 && <section className="empty-state" aria-live="polite"><p className="eyebrow">NO MATCHING STATES</p><h3>No cards match these filters.</h3><p>Change the code or data-state filter. No racing data is invented to fill an empty view.</p></section>}
      {selectedRace && <ResearchView key={selectedRace} race={researchRaces[selectedRace]} evidenceTab={evidenceTab} onClose={() => setSelectedRace(null)} onTabChange={setEvidenceTab} />}
      <footer className="footer"><span>Local API: 127.0.0.1:8000</span><span>Data rights: synthetic fixture only</span><span>Model: not trained</span></footer>
    </main>
  );
}

function ResearchView({ race, evidenceTab, onClose, onTabChange }: { race: ResearchRace; evidenceTab: EvidenceTab; onClose: () => void; onTabChange: (tab: EvidenceTab) => void }) {
  const [selectedNumbers, setSelectedNumbers] = useState<number[]>([1, 3]);
  const selectedRows = race.comparisonRows.filter((row) => selectedNumbers.includes(row.number));
  const toggleRunner = (number: number) => setSelectedNumbers((current) => current.includes(number) ? (current.length > 2 ? current.filter((value) => value !== number) : current) : [...current, number].slice(0, 4));

  return <section className="research-view" aria-label="Race research view">
    <div className="research-heading"><div><p className="eyebrow">RESEARCH VIEW · SYNTHETIC DEMO</p><h2>{race.meeting} · {race.raceLabel}</h2><p className="research-subtitle">Field revision <strong>{race.fieldRevision}</strong> · {race.fieldState} · fictional record</p></div><button className="close-button" onClick={onClose} type="button">Close view</button></div>
    <div className="research-facts"><div><span>Observed</span><strong>{race.observedAt}</strong></div><div><span>Published</span><strong>{race.publishedAt}</strong></div><div><span>Data mode</span><strong>SYNTHETIC_ONLY</strong></div></div>
    <div className="evidence-tabs" role="tablist" aria-label="Race evidence tabs">
      {([['FIELD', 'Field'], ['PROVENANCE', 'Provenance'], ['FORECAST', 'Forecast archive']] as const).map(([value, label]) => <button aria-selected={evidenceTab === value} className={evidenceTab === value ? 'tab selected' : 'tab'} key={value} onClick={() => onTabChange(value)} role="tab" type="button">{label}</button>)}
    </div>
    {evidenceTab === 'FIELD' && <div className="evidence-panel" role="tabpanel"><div className="panel-heading"><h3>Entries at {race.fieldRevision}</h3><span className="status-pill">Current field</span></div><section className="compare-panel" aria-label="Runner compare"><div className="panel-heading"><div><h3>Runner compare</h3><p className="panel-note">Select 2–4 runners; all rows use the same distance and fixture context.</p></div><span className="compare-count">Compare {selectedRows.length} runners</span></div><div className="runner-picker">{race.entries.map((entry) => <label className="runner-option" key={entry.number}><input checked={selectedNumbers.includes(entry.number)} disabled={selectedNumbers.length === 2 && selectedNumbers.includes(entry.number)} onChange={() => toggleRunner(entry.number)} type="checkbox" /><span>Runner {entry.number} · {entry.status}</span></label>)}</div><table><caption>Matched comparison units</caption><thead><tr><th scope="col">Runner</th><th scope="col">Distance</th><th scope="col">Fixture context</th><th scope="col">Recent form</th></tr></thead><tbody>{selectedRows.map((row) => <tr key={row.number}><td>{row.name}</td><td>{row.distance}</td><td>{row.context}</td><td>{row.recentForm}</td></tr>)}</tbody></table><div className="code-panel"><h4>{race.codePanelTitle}</h4><p><strong>{race.specialtyLabel}:</strong> Not available in fixture.</p><p className="panel-note">{race.specialtyExplanation} No value is invented for the comparison.</p></div></section><table><caption>Fictional entries and field state</caption><thead><tr><th scope="col">No.</th><th scope="col">Participant</th><th scope="col">State</th></tr></thead><tbody>{race.entries.map((entry) => <tr key={entry.number}><td>{entry.number}</td><td>{entry.name}</td><td><span className={`entry-state entry-${entry.status.toLowerCase()}`}>{entry.status}</span></td></tr>)}</tbody></table><p className="panel-note">A scratching created {race.fieldRevision}; the prior forecast is retained but no longer current.</p></div>}
    {evidenceTab === 'PROVENANCE' && <div className="evidence-panel" role="tabpanel"><div className="panel-heading"><h3>Available evidence</h3><span className="status-pill">Receipt verified</span></div><dl className="provenance-facts"><dt>Source receipt</dt><dd>synthetic://{race.code.toLowerCase()}/race-001</dd><dt>First observed</dt><dd>{race.observedAt}</dd><dt>Publication proof</dt><dd>{race.publishedAt}</dd><dt>Rights state</dt><dd>SYNTHETIC · fictional fixture</dd><dt>External connectivity</dt><dd>Disabled</dd></dl></div>}
    {evidenceTab === 'FORECAST' && <div className="evidence-panel" role="tabpanel"><div className="panel-heading"><h3>Archived forecast</h3><span className="invalidated-pill">INVALIDATED BY FIELD REVISION</span></div><dl className="provenance-facts"><dt>Forecast ID</dt><dd>forecast-{race.code.toLowerCase()}-r1</dd><dt>Model</dt><dd>B1 illustrative · not validated</dd><dt>Forecast field</dt><dd>field-r1 (superseded)</dd><dt>Current field</dt><dd>{race.fieldRevision}</dd><dt>Action</dt><dd>No reuse after scratching; archive remains immutable.</dd></dl></div>}
  </section>;
}

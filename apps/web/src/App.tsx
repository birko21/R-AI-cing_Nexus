const codes = [
  { name: 'Thoroughbred', status: 'Synthetic demo ready' },
  { name: 'Harness', status: 'Synthetic demo ready' },
  { name: 'Greyhound', status: 'Synthetic demo ready' },
];

export default function App() {
  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">RACING INTELLIGENCE LAB</p>
          <h1>Offline research foundation</h1>
        </div>
        <span className="mode-badge">SYNTHETIC_ONLY</span>
      </header>
      <section className="intro" aria-labelledby="intro-title">
        <p className="eyebrow">G0–G3 FOUNDATION</p>
        <h2 id="intro-title">A transparent starting point for three-code racing research.</h2>
        <p>
          The application is local-only and non-wagering. This shell deliberately shows setup
          status rather than pretending that live racing data or validated predictions exist.
        </p>
      </section>
      <section className="code-grid" aria-label="Racing codes">
        {codes.map((code) => (
          <article className="code-card" key={code.name}>
            <span className="status-dot" aria-hidden="true" />
            <h3>{code.name}</h3>
            <p>{code.status}</p>
          </article>
        ))}
      </section>
      <footer className="footer">
        <span>Local API: 127.0.0.1:8000</span>
        <span>Next: synthetic fixture ingestion</span>
      </footer>
    </main>
  );
}

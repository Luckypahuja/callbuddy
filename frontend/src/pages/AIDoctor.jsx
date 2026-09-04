export default function AIDoctor({ navigate }) {
  return (
    <main className="page placeholder-page">
      <button
        className="back-button"
        onClick={() => navigate("/")}
      >
        ← Back to agents
      </button>

      <p className="eyebrow">AI DOCTOR</p>

      <h1>
        AI Doctor <em>Coming Soon.</em>
      </h1>

      <p className="lead-notice">
        AI-powered visual health assistance is currently under development.
      </p>

      <div className="coming-soon">
        <span>✦</span>

        <div>
          <h2>Coming soon</h2>
          <p>
            This feature is being developed for a future version of
            EchoSphere.
          </p>
        </div>
      </div>
    </main>
  );
}
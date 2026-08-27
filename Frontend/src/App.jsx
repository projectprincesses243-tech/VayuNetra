import './App.css'

function App() {
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">✦</div>

          <div>
            <h1>VAYUNETRA</h1>
            <p>WINGS OF HOPE</p>
          </div>
        </div>

        <div className="system-status">
          <span className="status-dot"></span>
          <span>SYSTEM READY</span>
        </div>
      </header>

      <main className="dashboard">
        <section className="welcome-panel">
          <p className="eyebrow">AUTONOMOUS DISASTER RESPONSE</p>
          <h2>Command Center</h2>
          <p>
            Monitoring rescue systems and awaiting incoming emergency requests.
          </p>

          <div className="ready-message">
            <span className="status-dot"></span>
            Awaiting rescue request
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
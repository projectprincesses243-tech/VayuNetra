function Perception() {
  return (
    <main className="dashboard">

      {/* PAGE HEADER */}
      <section className="hero-section">

        <div>
          <p className="eyebrow">AI PERCEPTION SYSTEM</p>

          <h2>
            Perception <span>Center</span>
          </h2>

          <p className="hero-description">
            Monitor visual and thermal perception outputs
            received from the VayuNetra drone fleet.
          </p>
        </div>

        <div className="mission-status">
          <span className="status-dot"></span>
          Pipeline Standby
        </div>

      </section>


      {/* PERCEPTION STATUS */}
      <section className="dashboard-grid">

        <div className="dashboard-card">

          <div className="card-icon">
            📷
          </div>

          <div>
            <p>RGB CAMERA</p>
            <h3>READY</h3>
            <span>Visual input pipeline</span>
          </div>

        </div>


        <div className="dashboard-card">

          <div className="card-icon">
            🤖
          </div>

          <div>
            <p>YOLO DETECTION</p>
            <h3>READY</h3>
            <span>Object detection output</span>
          </div>

        </div>


        <div className="dashboard-card">

          <div className="card-icon">
            🌡️
          </div>

          <div>
            <p>THERMAL</p>
            <h3>READY</h3>
            <span>Thermal verification</span>
          </div>

        </div>


        <div className="dashboard-card">

          <div className="card-icon">
            👤
          </div>

          <div>
            <p>SURVIVORS</p>
            <h3>0</h3>
            <span>Detected in current mission</span>
          </div>

        </div>

      </section>


      {/* IMAGE INPUT / OUTPUT */}
      <section
        className="operation-grid"
        style={{ marginTop: "18px" }}
      >

        {/* RGB */}
        <div className="map-panel">

          <div className="panel-header">

            <div>
              <p>VISUAL PERCEPTION</p>
              <h3>RGB / YOLO Output</h3>
            </div>

            <span className="map-status">
              NO INPUT
            </span>

          </div>


          <div className="map-placeholder">

            <div className="map-message">

              <div className="map-pin">
                📷
              </div>

              <h3>
                Waiting for Camera Data
              </h3>

              <p>
                YOLO detections and RGB camera
                frames will appear here.
              </p>

            </div>

          </div>

        </div>


        {/* THERMAL */}
        <div className="map-panel">

          <div className="panel-header">

            <div>
              <p>THERMAL PERCEPTION</p>
              <h3>Thermal Verification</h3>
            </div>

            <span className="map-status">
              NO INPUT
            </span>

          </div>


          <div className="map-placeholder">

            <div className="map-message">

              <div className="map-pin">
                🌡️
              </div>

              <h3>
                Waiting for Thermal Data
              </h3>

              <p>
                Thermal image processing and
                verification results will appear here.
              </p>

            </div>

          </div>

        </div>

      </section>


      {/* DETECTION RESULTS */}
      <section
        className="map-panel"
        style={{ marginTop: "18px" }}
      >

        <div className="panel-header">

          <div>
            <p>DETECTION OUTPUT</p>
            <h3>Perception Results</h3>
          </div>

          <span className="map-status">
            AWAITING DATA
          </span>

        </div>


        <div style={{ padding: "25px" }}>

          <div className="action-item">

            <span className="action-indicator waiting"></span>

            <div>
              <strong>No detection results</strong>

              <p>
                Detection results from the perception
                pipeline will be displayed here.
              </p>
            </div>

          </div>


          <div className="action-item">

            <span className="action-indicator waiting"></span>

            <div>
              <strong>No survivor confirmation</strong>

              <p>
                Combined RGB and thermal verification
                results will appear here.
              </p>
            </div>

          </div>

        </div>

      </section>

    </main>
  );
}

export default Perception;
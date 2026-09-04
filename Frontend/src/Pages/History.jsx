import { useEffect, useState } from "react";

import {
  getHistory,
  deleteFromHistory
} from "../data/operationStorage";


function History() {

  const [history, setHistory] =
    useState([]);


  // ==========================================
  // LOAD HISTORY
  // ==========================================

  useEffect(() => {

    setHistory(
      getHistory()
    );

  }, []);


  // ==========================================
  // DELETE OPERATION
  // ==========================================

  const handleDelete = (operationId) => {

    const confirmed =
      window.confirm(
        "Delete this operation from history?"
      );


    if (!confirmed) {
      return;
    }


    deleteFromHistory(
      operationId
    );


    setHistory(
      getHistory()
    );

  };


  // ==========================================
  // FORMAT DATE
  // ==========================================

  const formatDate = (date) => {

    if (!date) {
      return "—";
    }


    return new Date(date)
      .toLocaleString();

  };


  return (

    <main className="dashboard">


      {/* =====================================
          HEADER
      ====================================== */}

      <section className="hero-section">

        <div>

          <p className="eyebrow">
            OPERATION RECORDS
          </p>

          <h2>
            Mission <span>History</span>
          </h2>

          <p className="hero-description">
            Review previously completed and
            stopped VayuNetra rescue operations.
          </p>

        </div>


        <div className="mission-status">

          <span className="status-dot"></span>

          {history.length} Recorded Operations

        </div>

      </section>


      {/* =====================================
          HISTORY TABLE
      ====================================== */}

      <section
        className="map-panel"
        style={{
          marginTop: "18px"
        }}
      >

        <div className="panel-header">

          <div>

            <p>
              OPERATION LOG
            </p>

            <h3>
              Previous Operations
            </h3>

          </div>


          <span className="map-status">
            {history.length} RECORDS
          </span>

        </div>


        <div
          style={{
            padding: "20px"
          }}
        >

          {history.length === 0 ? (

            /* =================================
               EMPTY STATE
            ================================== */

            <div
              style={{
                padding: "50px 20px",
                textAlign: "center",
                border:
                  "1px dashed rgba(255,255,255,0.10)",
                borderRadius: "12px"
              }}
            >

              <div
                style={{
                  fontSize: "35px",
                  marginBottom: "12px"
                }}
              >
                📋
              </div>


              <h3>
                No Previous Operations
              </h3>


              <p
                style={{
                  color: "#697386",
                  fontSize: "12px",
                  marginTop: "8px"
                }}
              >
                Completed or stopped missions
                will appear here.
              </p>

            </div>

          ) : (

            /* =================================
               TABLE
            ================================== */

            <div
              style={{
                width: "100%",
                overflowX: "auto",
                border:
                  "1px solid rgba(255,255,255,0.07)",
                borderRadius: "10px"
              }}
            >

              <table
                style={{
                  width: "100%",
                  minWidth: "1050px",
                  borderCollapse:
                    "collapse",
                  fontSize: "11px"
                }}
              >

                <thead>

                  <tr
                    style={{
                      textAlign: "left",
                      borderBottom:
                        "1px solid rgba(255,255,255,0.08)"
                    }}
                  >

                    <th style={thStyle}>
                      OPERATION ID
                    </th>

                    <th style={thStyle}>
                      OPERATION
                    </th>

                    <th style={thStyle}>
                      DISASTER
                    </th>

                    <th style={thStyle}>
                      LOCATION
                    </th>

                    <th style={thStyle}>
                      DRONES
                    </th>

                    <th style={thStyle}>
                      PROGRESS
                    </th>

                    <th style={thStyle}>
                      STATUS
                    </th>

                    <th style={thStyle}>
                      DATE
                    </th>

                    <th style={thStyle}>
                      ACTION
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {history.map(
                    operation => (

                    <tr
                      key={
                        operation.id
                      }
                      style={{
                        borderBottom:
                          "1px solid rgba(255,255,255,0.05)"
                      }}
                    >

                      {/* OPERATION ID */}

                      <td style={tdStyle}>

                        <strong>
                          {operation.id}
                        </strong>

                      </td>


                      {/* OPERATION */}

                      <td style={tdStyle}>

                        {operation.operation ||
                          "Rescue Operation"}

                      </td>


                      {/* DISASTER */}

                      <td style={tdStyle}>

                        {operation.disaster ||
                          "—"}

                      </td>


                      {/* LOCATION */}

                      <td style={tdStyle}>

                        {operation.location ||
                          "—"}

                      </td>


                      {/* DRONES */}

                      <td style={tdStyle}>

                        {operation
                          .assignedDrones
                          ?.length || 0}

                      </td>


                      {/* PROGRESS */}

                      <td style={tdStyle}>

                        <div
                          style={{
                            display: "flex",
                            alignItems:
                              "center",
                            gap: "8px"
                          }}
                        >

                          <div
                            style={{
                              width: "70px",
                              height: "6px",
                              background:
                                "rgba(255,255,255,0.08)",
                              borderRadius:
                                "10px",
                              overflow:
                                "hidden"
                            }}
                          >

                            <div
                              style={{
                                width:
                                  `${operation.progress || 0}%`,
                                height: "100%",
                                background:
                                  "#8b5cf6",
                                borderRadius:
                                  "10px"
                              }}
                            />

                          </div>


                          <span>
                            {operation.progress || 0}%
                          </span>

                        </div>

                      </td>


                      {/* STATUS */}

                      <td style={tdStyle}>

                        <span
                          style={{
                            display:
                              "inline-block",
                            padding:
                              "5px 8px",
                            borderRadius:
                              "5px",
                            fontSize:
                              "9px",
                            fontWeight:
                              "600",
                            background:
                              operation.status ===
                              "COMPLETED"
                                ? "rgba(34,197,94,0.12)"
                                : "rgba(239,68,68,0.12)",
                            color:
                              operation.status ===
                              "COMPLETED"
                                ? "#4ade80"
                                : "#f87171"
                          }}
                        >
                          {operation.status}
                        </span>

                      </td>


                      {/* DATE */}

                      <td style={tdStyle}>

                        {formatDate(
                          operation.completedAt ||
                          operation.stoppedAt ||
                          operation.startedAt
                        )}

                      </td>


                      {/* DELETE */}

                      <td style={tdStyle}>

                        <button
                          type="button"
                          onClick={() =>
                            handleDelete(
                              operation.id
                            )
                          }
                          style={{
                            cursor:
                              "pointer",
                            padding:
                              "6px 10px",
                            borderRadius:
                              "5px",
                            border:
                              "1px solid rgba(255,80,80,0.35)",
                            background:
                              "rgba(255,80,80,0.08)",
                            color:
                              "#f87171",
                            fontSize:
                              "10px"
                          }}
                        >
                          DELETE
                        </button>

                      </td>

                    </tr>

                  ))}

                </tbody>

              </table>

            </div>

          )}

        </div>

      </section>


      {/* =====================================
          INFORMATION
      ====================================== */}

      <section
        className="map-panel"
        style={{
          marginTop: "18px",
          padding: "20px"
        }}
      >

        <p className="eyebrow">
          OPERATION LIFECYCLE
        </p>


        <div
          style={{
            display: "flex",
            justifyContent:
              "space-between",
            alignItems: "center",
            gap: "15px",
            flexWrap: "wrap",
            marginTop: "10px"
          }}
        >

          <span>
            🚁 Active Mission
          </span>

          <span>
            →
          </span>

          <span>
            ⏹ Stop
          </span>

          <span>
            →
          </span>

          <span>
            📋 History
          </span>


          <span>
            →
          </span>

          <span>
            🗑 Delete
          </span>

        </div>

      </section>

    </main>

  );

}


/* ==========================================
   TABLE STYLES
========================================== */

const thStyle = {

  padding: "12px",

  color: "#858da5",

  fontSize: "9px",

  letterSpacing: "0.8px",

  fontWeight: "600",

  whiteSpace: "nowrap"

};


const tdStyle = {

  padding: "12px",

  color: "#aeb3c7",

  whiteSpace: "nowrap"

};


export default History;
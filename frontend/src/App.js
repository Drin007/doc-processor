import React, { useState, useEffect } from "react";

function App() {
  const [file, setFile] = useState(null);
  const [jobs, setJobs] = useState([]);

  const API = "http://127.0.0.1:8000";

  const fetchJobs = async () => {
    const res = await fetch(`${API}/jobs`);
    const data = await res.json();
    setJobs(data);
  };

  useEffect(() => {
    fetchJobs();

    const interval = setInterval(fetchJobs, 5000);

    const ws = new WebSocket("ws://127.0.0.1:8000/ws");

    ws.onmessage = (event) => {
      console.log("WS:", event.data); // debug

      const [job_id, progress, step] = event.data.split(":");

      setJobs((prev) =>
        prev.map((job) =>
          job.id === Number(job_id)
            ? {
                ...job,
                result: {
                  ...job.result,
                  progress: Number(progress),
                  step,
                },
              }
            : job
        )
      );
    };

    return () => {
      clearInterval(interval);
      ws.close();
    };
  }, []);

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    await fetch(`${API}/upload`, {
      method: "POST",
      body: formData,
    });

    setFile(null);
    fetchJobs();
  };

  const getStatusColor = (status) => {
    if (status === "completed") return "green";
    if (status === "processing") return "orange";
    if (status === "failed") return "red";
    return "gray";
  };

  return (
    <div style={{ padding: "30px", fontFamily: "Arial" }}>
      <h2>🚀 Document Processor</h2>

      <div style={{ marginBottom: "20px" }}>
        <input type="file" onChange={(e) => setFile(e.target.files[0])} />
        <button onClick={handleUpload} style={{ marginLeft: "10px" }}>
          Upload
        </button>
      </div>

      <h3>Jobs</h3>

      {jobs.map((job) => (
        <div
          key={job.id}
          style={{
            border: "1px solid #ddd",
            padding: "15px",
            marginBottom: "10px",
            borderRadius: "8px",
          }}
        >
          <p><b>ID:</b> {job.id}</p>
          <p><b>File:</b> {job.filename}</p>

          <p>
            <b>Status:</b>{" "}
            <span style={{ color: getStatusColor(job.status) }}>
              {job.status}
            </span>
          </p>

          {job.result && (
            <div style={{ marginTop: "10px" }}>
              <b>Result:</b>

              {job.result.progress !== undefined && (
                <div style={{ marginTop: "5px" }}>
                  <div style={{ height: "10px", background: "#eee", borderRadius: "5px" }}>
                    <div
                      style={{
                        width: `${job.result.progress}%`,
                        height: "100%",
                        background: "green",
                        borderRadius: "5px",
                        transition: "0.3s",
                      }}
                    />
                  </div>
                  <small>{job.result.step}</small>
                </div>
              )}

              <pre>{JSON.stringify(job.result, null, 2)}</pre>

              <div style={{ marginTop: "10px" }}>
                {job.status === "failed" && (
                  <button
                    onClick={() => {
                      fetch(`${API}/jobs/${job.id}/retry`, {
                        method: "POST",
                      }).then(fetchJobs);
                    }}
                  >
                    Retry
                  </button>
                )}

                {job.status === "completed" && (
                  <button
                    onClick={() => {
                      const blob = new Blob([JSON.stringify(job.result)], {
                        type: "application/json",
                      });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = `job-${job.id}.json`;
                      a.click();
                    }}
                  >
                    Export JSON
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default App;
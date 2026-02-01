import { useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

export default function ApplyStep({ onDone, onCancel }) {
  const [dryRunResult, setDryRunResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function runDryRun() {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/startup/apply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          apply_deletions: true,
          dry_run: true,
          max_delete: 100,
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }

      const data = await res.json();
      setDryRunResult(data);
    } catch (e) {
      console.error("Dry-run failed:", e);
      setError(e.message || "Dry-run failed");
    } finally {
      setLoading(false);
    }
  }

  async function runRealApply() {
    const ok = window.confirm(
      "This will permanently delete files from disk.\n\nAre you absolutely sure?"
    );
    if (!ok) return;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/startup/apply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          apply_deletions: true,
          dry_run: false,
          max_delete: 100,
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }

      const data = await res.json();
      onDone(data);
    } catch (e) {
      console.error("Apply failed:", e);
      setError(e.message || "Apply failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="apply-step" style={{ padding: 20 }}>
      <h2>Apply Deletions</h2>

      <p>
        This step will permanently delete files marked for deletion.
        Metadata and tags have already been saved to the database.
      </p>

      {error && (
        <pre style={{ color: "red", marginTop: 10 }}>
          {error}
        </pre>
      )}

      <div style={{ marginTop: 20 }}>
        <button onClick={runDryRun} disabled={loading}>
          Dry-run Apply (Preview)
        </button>

        <button
          onClick={runRealApply}
          disabled={!dryRunResult || loading}
          style={{ marginLeft: 10, color: "red" }}
        >
          Real Apply (Delete Files)
        </button>

        <button
          onClick={onCancel}
          disabled={loading}
          style={{ marginLeft: 10 }}
        >
          Cancel
        </button>
      </div>

      {dryRunResult && (
        <div style={{ marginTop: 30 }}>
          <h3>Dry-run Summary</h3>

          <pre style={{ maxHeight: 300, overflow: "auto" }}>
            {JSON.stringify(dryRunResult.summary, null, 2)}
          </pre>

          <p>
            Total candidates:{" "}
            {dryRunResult.summary.total_candidates}
          </p>
        </div>
      )}
    </div>
  );
}

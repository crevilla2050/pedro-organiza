import { useEffect, useState } from "react";
import { t } from "../i18n";
import es from "../i18n/es"; // adjust path if needed

const t = (key, vars = {}) => {
  let s = es[key] || key;
  Object.entries(vars).forEach(([k, v]) => {
    s = s.replace(`{${k}}`, v);
  });
  return s;
};

function AliasClusterList() {
  const [clusters, setClusters] = useState([]);
  const [expanded, setExpanded] = useState({});
  const [selected, setSelected] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/aliases/clusters")
      .then(res => res.json())
      .then(data => {
        setClusters(data);

        // Default: first file in each cluster is kept
        const initialSelection = {};
        data.forEach(cluster => {
          initialSelection[cluster.cluster_id] = new Set(
            cluster.files.length > 0 ? [cluster.files[0].id] : []
          );
        });
        setSelected(initialSelection);

        setLoading(false);
      })
      .catch(err => {
        console.error(t("ERROR_FETCH_ALIAS_CLUSTERS"), err);
        setLoading(false);
      });
  }, []);

  const toggleCluster = (id) => {
    setExpanded(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const toggleFileSelection = (clusterId, fileId) => {
    setSelected(prev => {
      const next = new Set(prev[clusterId] || []);

      if (next.has(fileId)) {
        // Prevent unselecting the last kept file
        if (next.size === 1) return prev;
        next.delete(fileId);
      } else {
        next.add(fileId);
      }

      return {
        ...prev,
        [clusterId]: next
      };
    });
  };

  const previewFile = (file) => {
    // Placeholder for real audio playback
    console.log("Preview:", file);
    alert(
      t("PREVIEW_TRACK", {
        artist: file.artist ?? t("UNKNOWN"),
        title: file.title ?? t("UNKNOWN"),
      })
    );
  };

  if (loading) {
    return (
      <div className="alert alert-info">
        {t("LOADING_ALIAS_CLUSTERS")}
      </div>
    );
  }

  return (
    <div className="mt-5">
      <h3 className="mb-3">
        🔗 {t("ALIAS_CLUSTERS_TITLE")}
      </h3>

      {clusters.map(cluster => {
        const isOpen = expanded[cluster.cluster_id];
        const kept = selected[cluster.cluster_id] || new Set();

        return (
          <div
            key={cluster.cluster_id}
            className="card mb-3"
          >
            <div
              className="card-header d-flex justify-content-between align-items-center"
              style={{ cursor: "pointer" }}
              onClick={() => toggleCluster(cluster.cluster_id)}
            >
              <div>
                <strong>
                  {isOpen ? "▾" : "▸"}{" "}
                  {t("CLUSTER_LABEL", { id: cluster.cluster_id })}
                </strong>{" "}
                <span className="text-muted">
                  ({t("CLUSTER_FILES_COUNT", { count: cluster.size })})
                </span>
              </div>

              <div className="text-muted small">
                {t("CLUSTER_KEEPING_COUNT", {
                  kept: kept.size,
                  total: cluster.size,
                })}
              </div>
            </div>

            {isOpen && (
              <div className="card-body p-0">
                <table className="table table-sm mb-0">
                  <thead>
                    <tr>
                      <th>{t("KEEP")}</th>
                      <th>{t("PREVIEW")}</th>
                      <th>ID</th>
                      <th>{t("ARTIST")}</th>
                      <th>{t("TITLE")}</th>
                      <th>{t("ALBUM")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cluster.files.map(file => (
                      <tr
                        key={file.id}
                        className={kept.has(file.id) ? "" : "table-secondary"}
                      >
                        <td>
                          <input
                            type="checkbox"
                            checked={kept.has(file.id)}
                            onChange={() =>
                              toggleFileSelection(
                                cluster.cluster_id,
                                file.id
                              )
                            }
                          />
                        </td>
                        <td>
                          <button
                            className="btn btn-sm btn-outline-secondary"
                            onClick={() => previewFile(file)}
                            title={t("PREVIEW_TRACK_TITLE")}
                          >
                            ▶
                          </button>
                        </td>
                        <td>{file.id}</td>
                        <td>{file.artist ?? "—"}</td>
                        <td>{file.title ?? "—"}</td>
                        <td>{file.album ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default AliasClusterList;

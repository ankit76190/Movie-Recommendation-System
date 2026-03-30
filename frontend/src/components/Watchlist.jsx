/**
 * Watchlist.jsx
 * -------------
 * Displays the current user's watchlist with remove and CSV-export options.
 */

import React, { useState, useEffect, useCallback } from "react";
import { fetchWatchlist, removeFromWatchlist, downloadWatchlistCSV } from "../services/api";

export default function Watchlist({ username }) {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState(false);

  const load = useCallback(async () => {
    if (!username) return;
    setLoading(true);
    setError("");
    try {
      const data = await fetchWatchlist(username);
      setEntries(data.watchlist || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [username]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleRemove(entry) {
    try {
      await removeFromWatchlist(username, entry.movie_id);
      setEntries((prev) => prev.filter((e) => e.id !== entry.id));
    } catch (err) {
      alert(err.message);
    }
  }

  async function handleExport() {
    if (!username) return;
    setExporting(true);
    try {
      await downloadWatchlistCSV(username);
    } catch (err) {
      alert("Export failed: " + err.message);
    } finally {
      setExporting(false);
    }
  }

  if (!username) {
    return (
      <div className="empty-state">
        <div style={{ fontSize: "2rem" }}>👤</div>
        <p>Select a user above to view their watchlist.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="section-header">
        <h2>Watchlist — {username}</h2>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-ghost" onClick={load} disabled={loading}>
            ↻ Refresh
          </button>
          <button
            className="btn btn-secondary"
            onClick={handleExport}
            disabled={exporting || entries.length === 0}
          >
            {exporting ? "Exporting…" : "⬇ Export CSV"}
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="loading">
          <div className="spinner" />
          Loading watchlist…
        </div>
      ) : entries.length === 0 ? (
        <div className="empty-state">
          <div style={{ fontSize: "2rem" }}>📋</div>
          <p>Your watchlist is empty.</p>
          <p>Browse movies and click "+ Watchlist" to save them here.</p>
        </div>
      ) : (
        <div>
          <p style={{ color: "var(--text-muted)", marginBottom: 12, fontSize: "0.85rem" }}>
            {entries.length} {entries.length === 1 ? "movie" : "movies"} saved
          </p>
          {entries.map((entry) => {
            const movie = entry.movie || {};
            const genres = Array.isArray(movie.genres)
              ? movie.genres.join(", ")
              : movie.genres || "";
            const date = entry.added_at
              ? new Date(entry.added_at).toLocaleDateString()
              : "";

            return (
              <div key={entry.id} className="watchlist-item">
                <div className="watchlist-info">
                  <div className="watchlist-title">
                    {movie.title || `Movie #${entry.movie_id}`}
                  </div>
                  <div className="watchlist-meta">
                    {movie.year && <span>{movie.year}</span>}
                    {genres && <span style={{ marginLeft: 8 }}>{genres}</span>}
                    {movie.avg_rating && (
                      <span className="rating-badge" style={{ marginLeft: 8 }}>
                        ★ {movie.avg_rating.toFixed(1)}
                      </span>
                    )}
                    {date && (
                      <span style={{ marginLeft: 8, color: "var(--text-muted)" }}>
                        Added {date}
                      </span>
                    )}
                  </div>
                  {entry.notes && (
                    <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: 4, fontStyle: "italic" }}>
                      "{entry.notes}"
                    </div>
                  )}
                </div>
                <button
                  className="btn btn-danger"
                  onClick={() => handleRemove(entry)}
                  title="Remove from watchlist"
                >
                  ✕
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

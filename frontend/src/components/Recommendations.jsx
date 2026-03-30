/**
 * Recommendations.jsx
 * --------------------
 * Shows personalised movie recommendations for the active user.
 * Supports three algorithms: SVD, Collaborative Filtering, Content-Based.
 * Falls back to genre-based recommendations when the ML dataset is unavailable.
 */

import React, { useState, useCallback } from "react";
import {
  fetchRecommendations,
  fetchGenreRecommendations,
  addToWatchlist,
} from "../services/api";

const GENRES = [
  "Action", "Adventure", "Animation", "Children", "Comedy",
  "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir",
  "Horror", "Musical", "Mystery", "Romance", "Sci-Fi",
  "Thriller", "War", "Western",
];

const METHODS = [
  { value: "svd", label: "SVD (Matrix Factorisation)" },
  { value: "collaborative", label: "Collaborative Filtering" },
  { value: "content", label: "Content-Based" },
];

function ScoreBar({ score, max = 5 }) {
  const pct = Math.min(100, ((score || 0) / max) * 100);
  return (
    <div className="score-bar-wrap">
      <div className="score-bar" style={{ width: `${pct}%` }} />
    </div>
  );
}

function RecCard({ rec, username }) {
  const [added, setAdded] = useState(false);
  const [adding, setAdding] = useState(false);

  async function handleAdd() {
    if (!username) { alert("Please select a user first."); return; }
    setAdding(true);
    try {
      // Try to find movie in DB by movielens_id
      const { fetchMovies } = await import("../services/api");
      const result = await fetchMovies({ q: rec.title, per_page: 5 });
      const match = result.movies.find(
        (m) =>
          m.movielens_id === rec.movielens_id ||
          m.title.toLowerCase() === rec.title.toLowerCase()
      );
      if (!match) { alert("Movie not found in DB. Import it first."); return; }
      await addToWatchlist(username, match.id);
      setAdded(true);
    } catch (err) {
      if (err.message.includes("already in watchlist")) { setAdded(true); }
      else alert(err.message);
    } finally {
      setAdding(false);
    }
  }

  const scoreLabel = rec.score != null ? rec.score.toFixed(2) : null;

  return (
    <div className="movie-card">
      <div className="movie-title">{rec.title}</div>
      {rec.movielens_id && (
        <div className="movie-meta">ML ID: {rec.movielens_id}</div>
      )}
      {scoreLabel && (
        <>
          <div className="movie-meta">Score: {scoreLabel}</div>
          <ScoreBar score={rec.score} max={5} />
        </>
      )}
      <div className="movie-card-actions">
        <button
          className={`btn ${added ? "btn-ghost" : "btn-secondary"}`}
          onClick={handleAdd}
          disabled={adding || added}
        >
          {adding ? "Adding…" : added ? "✓ Saved" : "+ Watchlist"}
        </button>
      </div>
    </div>
  );
}

export default function Recommendations({ username }) {
  const [recs, setRecs] = useState([]);
  const [method, setMethod] = useState("svd");
  const [n, setN] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Genre fallback
  const [selectedGenres, setSelectedGenres] = useState([]);
  const [genreRecs, setGenreRecs] = useState([]);
  const [genreLoading, setGenreLoading] = useState(false);

  const loadRecs = useCallback(async () => {
    if (!username) { alert("Please select a user first."); return; }
    const user = username.startsWith("alice")
      ? 1
      : username.startsWith("bob")
      ? 2
      : username.startsWith("carol")
      ? 3
      : 1;

    setLoading(true);
    setError("");
    setRecs([]);

    try {
      const data = await fetchRecommendations(user, method, n);
      setRecs(data.recommendations || []);
      if (!data.dataset_ready) {
        setError(
          "MovieLens dataset not downloaded yet. " +
            "Run `python data_loader.py` in the project root, then try again. " +
            "In the meantime, use Genre Recommendations below."
        );
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [username, method, n]);

  async function loadGenreRecs() {
    if (selectedGenres.length === 0) { alert("Select at least one genre."); return; }
    setGenreLoading(true);
    try {
      const data = await fetchGenreRecommendations(selectedGenres, n);
      setGenreRecs(data.recommendations || []);
    } catch (err) {
      alert(err.message);
    } finally {
      setGenreLoading(false);
    }
  }

  function toggleGenre(g) {
    setSelectedGenres((prev) =>
      prev.includes(g) ? prev.filter((x) => x !== g) : [...prev, g]
    );
  }

  return (
    <div>
      {/* ── ML-based recommendations ─────────────────────── */}
      <div className="card">
        <div className="card-title">🤖 ML Recommendations</div>
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: 14 }}>
          Powered by the MovieLens 100K dataset. Requires the dataset to be
          downloaded (see README).
        </p>

        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 14 }}>
          <div className="form-group" style={{ flex: 1, minWidth: 200 }}>
            <label>Algorithm</label>
            <select
              className="form-control"
              value={method}
              onChange={(e) => setMethod(e.target.value)}
            >
              {METHODS.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group" style={{ width: 100 }}>
            <label>Count</label>
            <select
              className="form-control"
              value={n}
              onChange={(e) => setN(Number(e.target.value))}
            >
              {[5, 10, 15, 20].map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
          </div>

          <div className="form-group" style={{ alignSelf: "flex-end", marginBottom: 0 }}>
            <button
              className="btn btn-primary"
              onClick={loadRecs}
              disabled={loading}
            >
              {loading ? "Loading…" : "Get Recommendations"}
            </button>
          </div>
        </div>

        {error && (
          <div className="alert alert-error" style={{ marginBottom: 10 }}>
            {error}
          </div>
        )}

        {recs.length > 0 && (
          <div className="movie-grid">
            {recs.map((r, i) => (
              <RecCard key={r.movielens_id || i} rec={r} username={username} />
            ))}
          </div>
        )}
      </div>

      {/* ── Genre-based fallback ─────────────────────────── */}
      <div className="card">
        <div className="card-title">🎭 Genre Recommendations</div>
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: 14 }}>
          Works with locally imported movies. No ML dataset required.
        </p>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 14 }}>
          {GENRES.map((g) => (
            <button
              key={g}
              className={`btn ${selectedGenres.includes(g) ? "btn-primary" : "btn-ghost"}`}
              style={{ padding: "4px 10px", fontSize: "0.8rem" }}
              onClick={() => toggleGenre(g)}
            >
              {g}
            </button>
          ))}
        </div>

        <button
          className="btn btn-secondary"
          onClick={loadGenreRecs}
          disabled={genreLoading || selectedGenres.length === 0}
        >
          {genreLoading ? "Loading…" : `Find ${selectedGenres.length > 0 ? selectedGenres.join(", ") : "Genre"} Movies`}
        </button>

        {genreRecs.length > 0 && (
          <div className="movie-grid" style={{ marginTop: 16 }}>
            {genreRecs.map((m) => (
              <div key={m.id} className="movie-card">
                <div className="movie-title">{m.title}</div>
                {m.year && <div className="movie-meta">{m.year}</div>}
                {m.avg_rating && (
                  <span className="rating-badge">★ {m.avg_rating.toFixed(1)}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

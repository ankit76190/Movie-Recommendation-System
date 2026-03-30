/**
 * MovieList.jsx
 * -------------
 * Displays a paginated, searchable grid of movies from the database.
 * Lets the active user add any movie to their watchlist.
 */

import React, { useState, useEffect, useCallback } from "react";
import { fetchMovies, addToWatchlist } from "../services/api";

function GenreTags({ genres }) {
  if (!genres || genres.length === 0) return null;
  const list = Array.isArray(genres)
    ? genres
    : genres.split(/[,|]/).map((g) => g.trim());
  return (
    <div>
      {list.slice(0, 4).map((g) => (
        <span key={g} className="genre-tag">
          {g}
        </span>
      ))}
    </div>
  );
}

function MovieCard({ movie, username, onWatchlistAdd }) {
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);

  async function handleAdd() {
    if (!username) {
      alert("Please select a user first.");
      return;
    }
    setAdding(true);
    try {
      await addToWatchlist(username, movie.id);
      setAdded(true);
      if (onWatchlistAdd) onWatchlistAdd(movie);
    } catch (err) {
      if (err.message.includes("already in watchlist")) {
        setAdded(true);
      } else {
        alert(err.message);
      }
    } finally {
      setAdding(false);
    }
  }

  return (
    <div className="movie-card">
      <div className="movie-title">{movie.title}</div>
      <div className="movie-meta">
        {movie.year && <span>{movie.year}</span>}
        {movie.avg_rating && (
          <span className="rating-badge" style={{ marginLeft: 6 }}>
            ★ {movie.avg_rating.toFixed(1)}
          </span>
        )}
      </div>
      <GenreTags genres={movie.genres} />
      <div className="movie-card-actions">
        <button
          className={`btn ${added ? "btn-ghost" : "btn-secondary"}`}
          onClick={handleAdd}
          disabled={adding || added}
          title={added ? "In watchlist" : "Add to watchlist"}
        >
          {adding ? "Adding…" : added ? "✓ Saved" : "+ Watchlist"}
        </button>
      </div>
    </div>
  );
}

export default function MovieList({ username }) {
  const [movies, setMovies] = useState([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const perPage = 20;

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchMovies({ page, per_page: perPage, q: query });
      setMovies(data.movies);
      setTotal(data.total);
      setPages(data.pages);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [page, query]);

  useEffect(() => {
    load();
  }, [load]);

  function handleSearch(e) {
    e.preventDefault();
    setPage(1);
    setQuery(search);
  }

  return (
    <div>
      <div className="section-header">
        <h2>Browse Movies</h2>
        <span className="page-info">{total.toLocaleString()} movies</span>
      </div>

      <form className="search-bar" onSubmit={handleSearch}>
        <input
          className="form-control"
          placeholder="Search by title…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button type="submit" className="btn btn-primary">
          Search
        </button>
        {query && (
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => { setSearch(""); setQuery(""); setPage(1); }}
          >
            Clear
          </button>
        )}
      </form>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="loading">
          <div className="spinner" />
          Loading movies…
        </div>
      ) : movies.length === 0 ? (
        <div className="empty-state">
          <div style={{ fontSize: "2rem" }}>🎬</div>
          <p>No movies found.{" "}
            {query ? "Try a different search term." : "Import movies to get started."}
          </p>
        </div>
      ) : (
        <div className="movie-grid">
          {movies.map((m) => (
            <MovieCard key={m.id} movie={m} username={username} />
          ))}
        </div>
      )}

      {pages > 1 && (
        <div className="pagination">
          <button
            className="btn btn-ghost"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1 || loading}
          >
            ‹ Prev
          </button>
          <span className="page-info">
            Page {page} of {pages}
          </span>
          <button
            className="btn btn-ghost"
            onClick={() => setPage((p) => Math.min(pages, p + 1))}
            disabled={page === pages || loading}
          >
            Next ›
          </button>
        </div>
      )}
    </div>
  );
}

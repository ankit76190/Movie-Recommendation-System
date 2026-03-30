/**
 * api.js
 * ------
 * Thin API client for the Flask backend.
 * All methods return plain JavaScript objects (already parsed JSON).
 */

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000";

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message = body.error || `HTTP ${response.status}`;
    throw new Error(message);
  }

  // CSV export returns a blob, not JSON
  if (options._returnBlob) return response.blob();

  return response.json();
}

// ─────────────────────────────────────────────────────────
// Movies
// ─────────────────────────────────────────────────────────

export const fetchMovies = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/api/movies${qs ? "?" + qs : ""}`);
};

export const fetchMovie = (id) => request(`/api/movies/${id}`);

export const createMovie = (data) =>
  request("/api/movies", { method: "POST", body: JSON.stringify(data) });

export const importMoviesCSV = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return request("/api/movies/import", {
    method: "POST",
    headers: {},           // let browser set multipart Content-Type
    body: formData,
  });
};

export const fetchMovielensMovies = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/api/movies/movielens${qs ? "?" + qs : ""}`);
};

// ─────────────────────────────────────────────────────────
// Users
// ─────────────────────────────────────────────────────────

export const fetchUsers = () => request("/api/users");

export const createUser = (username) =>
  request("/api/users", { method: "POST", body: JSON.stringify({ username }) });

// ─────────────────────────────────────────────────────────
// Watchlist
// ─────────────────────────────────────────────────────────

export const fetchWatchlist = (username) =>
  request(`/api/watchlist/${encodeURIComponent(username)}`);

export const addToWatchlist = (username, movieId, notes = "") =>
  request(`/api/watchlist/${encodeURIComponent(username)}`, {
    method: "POST",
    body: JSON.stringify({ movie_id: movieId, notes }),
  });

export const removeFromWatchlist = (username, movieId) =>
  request(`/api/watchlist/${encodeURIComponent(username)}/${movieId}`, {
    method: "DELETE",
  });

// ─────────────────────────────────────────────────────────
// Export
// ─────────────────────────────────────────────────────────

export const downloadWatchlistCSV = async (username) => {
  const blob = await request(
    `/api/export/watchlist/${encodeURIComponent(username)}`,
    { _returnBlob: true }
  );
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `watchlist_${username}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
};

// ─────────────────────────────────────────────────────────
// Recommendations
// ─────────────────────────────────────────────────────────

export const fetchRecommendations = (userId, method = "svd", n = 10) =>
  request(`/api/recommendations/${userId}?method=${method}&n=${n}`);

export const fetchSimilarMovies = (movieId, n = 10) =>
  request(`/api/recommendations/similar/${movieId}?n=${n}`);

export const fetchGenreRecommendations = (genres, n = 10) => {
  const qs = new URLSearchParams({ genres: genres.join(","), n }).toString();
  return request(`/api/recommendations/genre?${qs}`);
};

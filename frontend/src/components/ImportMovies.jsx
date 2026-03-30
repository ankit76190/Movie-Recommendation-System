/**
 * ImportMovies.jsx
 * -----------------
 * Provides two ways to import movies into the database:
 *   1. Upload a CSV file
 *   2. Create a single movie manually via a form
 */

import React, { useState, useRef } from "react";
import { importMoviesCSV, createMovie } from "../services/api";

const SAMPLE_HEADER = "title,year,genres,avg_rating,movielens_id";
const SAMPLE_ROW1 = "The Matrix (1999),1999,Action|Sci-Fi|Thriller,4.26,";
const SAMPLE_ROW2 = "Inception (2010),2010,Action|Adventure|Sci-Fi,4.37,";

export default function ImportMovies() {
  // CSV upload
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState("");
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef();

  // Manual form
  const [form, setForm] = useState({ title: "", year: "", genres: "", avg_rating: "" });
  const [creating, setCreating] = useState(false);
  const [createMsg, setCreateMsg] = useState("");
  const [createError, setCreateError] = useState("");

  /* ── CSV Upload ────────────────────────────────────────── */

  function handleFileDrop(e) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer?.files[0] || e.target.files?.[0];
    if (f) { setFile(f); setUploadResult(null); setUploadError(""); }
  }

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setUploadResult(null);
    setUploadError("");
    try {
      const result = await importMoviesCSV(file);
      setUploadResult(result);
      setFile(null);
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploading(false);
    }
  }

  /* ── Manual form ───────────────────────────────────────── */

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleCreate(e) {
    e.preventDefault();
    if (!form.title.trim()) { setCreateError("Title is required."); return; }
    setCreating(true);
    setCreateMsg("");
    setCreateError("");
    try {
      const genres = form.genres
        ? form.genres.split(/[,|]/).map((g) => g.trim()).filter(Boolean)
        : [];
      await createMovie({
        title: form.title.trim(),
        year: form.year ? parseInt(form.year, 10) : undefined,
        genres,
        avg_rating: form.avg_rating ? parseFloat(form.avg_rating) : undefined,
      });
      setCreateMsg(`"${form.title}" added successfully!`);
      setForm({ title: "", year: "", genres: "", avg_rating: "" });
    } catch (err) {
      setCreateError(err.message);
    } finally {
      setCreating(false);
    }
  }

  return (
    <div>
      {/* ── CSV Import ───────────────────────────────────── */}
      <div className="card">
        <div className="card-title">📁 Bulk Import via CSV</div>
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: 12 }}>
          Upload a CSV file with columns:{" "}
          <code style={{ color: "#7ec8e3" }}>
            title, year, genres, avg_rating, movielens_id
          </code>
          . Only <code>title</code> is required.
        </p>

        <div className="alert alert-info" style={{ marginBottom: 14 }}>
          <strong>Sample format:</strong>
          <pre style={{ marginTop: 6, fontSize: "0.78rem", whiteSpace: "pre-wrap" }}>
            {SAMPLE_HEADER}{"\n"}{SAMPLE_ROW1}{"\n"}{SAMPLE_ROW2}
          </pre>
        </div>

        <div
          className={`file-drop ${dragging ? "dragging" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleFileDrop}
          onClick={() => fileRef.current.click()}
        >
          <div style={{ fontSize: "1.8rem" }}>📂</div>
          <p>
            {file ? (
              <strong style={{ color: "var(--text)" }}>{file.name}</strong>
            ) : (
              "Drag & drop a CSV file here, or click to browse"
            )}
          </p>
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            style={{ display: "none" }}
            onChange={handleFileDrop}
          />
        </div>

        {file && (
          <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
            <button
              className="btn btn-primary"
              onClick={handleUpload}
              disabled={uploading}
            >
              {uploading ? "Uploading…" : "Upload & Import"}
            </button>
            <button className="btn btn-ghost" onClick={() => setFile(null)}>
              Cancel
            </button>
          </div>
        )}

        {uploadResult && (
          <div className="alert alert-success" style={{ marginTop: 12 }}>
            ✓ Import complete: {uploadResult.inserted} inserted,{" "}
            {uploadResult.updated} updated.
            {uploadResult.errors?.length > 0 && (
              <span> {uploadResult.errors.length} errors.</span>
            )}
          </div>
        )}

        {uploadError && (
          <div className="alert alert-error" style={{ marginTop: 12 }}>
            {uploadError}
          </div>
        )}
      </div>

      {/* ── Manual add ──────────────────────────────────── */}
      <div className="card">
        <div className="card-title">➕ Add a Single Movie</div>
        <form onSubmit={handleCreate}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div className="form-group" style={{ gridColumn: "1 / -1" }}>
              <label>Title *</label>
              <input
                className="form-control"
                name="title"
                value={form.title}
                onChange={handleChange}
                placeholder="e.g. Inception (2010)"
                required
              />
            </div>

            <div className="form-group">
              <label>Year</label>
              <input
                className="form-control"
                name="year"
                type="number"
                min="1888"
                max="2099"
                value={form.year}
                onChange={handleChange}
                placeholder="e.g. 2010"
              />
            </div>

            <div className="form-group">
              <label>Average Rating (1–5)</label>
              <input
                className="form-control"
                name="avg_rating"
                type="number"
                min="1"
                max="5"
                step="0.1"
                value={form.avg_rating}
                onChange={handleChange}
                placeholder="e.g. 4.2"
              />
            </div>

            <div className="form-group" style={{ gridColumn: "1 / -1" }}>
              <label>Genres (comma or pipe separated)</label>
              <input
                className="form-control"
                name="genres"
                value={form.genres}
                onChange={handleChange}
                placeholder="e.g. Action, Sci-Fi, Thriller"
              />
            </div>
          </div>

          {createError && (
            <div className="alert alert-error" style={{ marginBottom: 10 }}>
              {createError}
            </div>
          )}
          {createMsg && (
            <div className="alert alert-success" style={{ marginBottom: 10 }}>
              {createMsg}
            </div>
          )}

          <button className="btn btn-primary" type="submit" disabled={creating}>
            {creating ? "Adding…" : "Add Movie"}
          </button>
        </form>
      </div>
    </div>
  );
}

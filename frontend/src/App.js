/**
 * App.js
 * ------
 * Root application component.
 * Manages the active tab, the current user, and top-level state.
 */

import React, { useState, useEffect } from "react";
import "./App.css";
import MovieList from "./components/MovieList";
import Recommendations from "./components/Recommendations";
import Watchlist from "./components/Watchlist";
import ImportMovies from "./components/ImportMovies";
import { fetchUsers, createUser } from "./services/api";

const TABS = [
  { id: "movies", label: "🎬 Movies" },
  { id: "recommendations", label: "🤖 Recommendations" },
  { id: "watchlist", label: "📋 Watchlist" },
  { id: "import", label: "📁 Import" },
];

export default function App() {
  const [tab, setTab] = useState("movies");
  const [users, setUsers] = useState([]);
  const [username, setUsername] = useState("");
  const [newUsername, setNewUsername] = useState("");
  const [showNewUser, setShowNewUser] = useState(false);
  const [userError, setUserError] = useState("");

  useEffect(() => {
    fetchUsers()
      .then((data) => {
        setUsers(data.users || []);
        if (data.users?.length > 0) {
          setUsername(data.users[0].username);
        }
      })
      .catch(() => {});
  }, []);

  async function handleCreateUser(e) {
    e.preventDefault();
    if (!newUsername.trim()) return;
    setUserError("");
    try {
      const u = await createUser(newUsername.trim());
      setUsers((prev) => [...prev, u]);
      setUsername(u.username);
      setNewUsername("");
      setShowNewUser(false);
    } catch (err) {
      setUserError(err.message);
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎥 MovieRec</h1>

        <nav className="app-nav">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={tab === t.id ? "active" : ""}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>

        <div className="user-section">
          {users.length > 0 && (
            <select
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            >
              {users.map((u) => (
                <option key={u.id} value={u.username}>
                  {u.username}
                </option>
              ))}
            </select>
          )}

          {showNewUser ? (
            <form onSubmit={handleCreateUser} style={{ display: "flex", gap: 4 }}>
              <input
                style={{ background: "var(--surface2)", border: "1px solid var(--border)", color: "var(--text)", padding: "4px 8px", borderRadius: 6, fontSize: "0.875rem" }}
                placeholder="username"
                value={newUsername}
                onChange={(e) => setNewUsername(e.target.value)}
                autoFocus
              />
              <button className="btn btn-primary" type="submit" style={{ padding: "4px 10px" }}>
                Add
              </button>
              <button
                className="btn btn-ghost"
                type="button"
                style={{ padding: "4px 10px" }}
                onClick={() => { setShowNewUser(false); setUserError(""); }}
              >
                ✕
              </button>
            </form>
          ) : (
            <button
              className="btn btn-ghost"
              style={{ padding: "4px 10px", fontSize: "0.8rem" }}
              onClick={() => setShowNewUser(true)}
            >
              + User
            </button>
          )}
        </div>
      </header>

      {userError && (
        <div className="alert alert-error" style={{ margin: "8px 24px 0" }}>
          {userError}
        </div>
      )}

      <main className="app-main">
        {tab === "movies" && <MovieList username={username} />}
        {tab === "recommendations" && <Recommendations username={username} />}
        {tab === "watchlist" && <Watchlist username={username} />}
        {tab === "import" && <ImportMovies />}
      </main>
    </div>
  );
}

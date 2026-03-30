"""
routes/watchlist.py
--------------------
CRUD endpoints for managing a user's watchlist.

GET    /api/users                   – list all users
POST   /api/users                   – create a user
GET    /api/watchlist/<username>    – get watchlist for a user
POST   /api/watchlist/<username>    – add a movie to watchlist
DELETE /api/watchlist/<username>/<movie_id> – remove from watchlist
"""

from flask import Blueprint, jsonify, request
from extensions import db
from models import User, Movie, WatchlistEntry

watchlist_bp = Blueprint("watchlist", __name__)


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

@watchlist_bp.get("/api/users")
def list_users():
    users = User.query.order_by(User.username).all()
    return jsonify({"users": [u.to_dict() for u in users]})


@watchlist_bp.post("/api/users")
def create_user():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    if not username:
        return jsonify({"error": "username is required"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": f"User '{username}' already exists"}), 409

    user = User(
        username=username,
        movielens_user_id=data.get("movielens_user_id"),
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


# ---------------------------------------------------------------------------
# Watchlist CRUD
# ---------------------------------------------------------------------------

@watchlist_bp.get("/api/watchlist/<username>")
def get_watchlist(username: str):
    """Return all watchlist entries for the given user."""
    user = User.query.filter_by(username=username).first_or_404(
        description=f"User '{username}' not found"
    )
    entries = (
        WatchlistEntry.query.filter_by(user_id=user.id)
        .order_by(WatchlistEntry.added_at.desc())
        .all()
    )
    return jsonify(
        {
            "username": username,
            "user_id": user.id,
            "watchlist": [e.to_dict() for e in entries],
            "count": len(entries),
        }
    )


@watchlist_bp.post("/api/watchlist/<username>")
def add_to_watchlist(username: str):
    """
    Add a movie to the user's watchlist.

    Body (JSON):
        movie_id  (int, required) – database movie ID
        notes     (str, optional)
    """
    user = User.query.filter_by(username=username).first_or_404(
        description=f"User '{username}' not found"
    )
    data = request.get_json(silent=True) or {}
    movie_id = data.get("movie_id")
    if not movie_id:
        return jsonify({"error": "movie_id is required"}), 400

    movie = db.get_or_404(Movie, movie_id)

    # Idempotent: return 200 if already in watchlist
    existing = WatchlistEntry.query.filter_by(
        user_id=user.id, movie_id=movie.id
    ).first()
    if existing:
        return jsonify(
            {"message": "Movie already in watchlist", "entry": existing.to_dict()}
        ), 200

    entry = WatchlistEntry(
        user_id=user.id,
        movie_id=movie.id,
        notes=data.get("notes"),
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify(entry.to_dict()), 201


@watchlist_bp.delete("/api/watchlist/<username>/<int:movie_id>")
def remove_from_watchlist(username: str, movie_id: int):
    """Remove a movie from the user's watchlist."""
    user = User.query.filter_by(username=username).first_or_404(
        description=f"User '{username}' not found"
    )
    entry = WatchlistEntry.query.filter_by(
        user_id=user.id, movie_id=movie_id
    ).first_or_404(description="Entry not found in watchlist")

    db.session.delete(entry)
    db.session.commit()
    return jsonify({"message": "Removed from watchlist"}), 200

"""
models.py
---------
SQLAlchemy ORM models for the Movie Recommendation System.

Tables
------
movies        – Stores imported movie metadata.
users         – App-level users (separate from MovieLens user IDs).
watchlist     – Many-to-many relationship between users and movies.
ratings       – Explicit user ratings (used to personalise recommendations).
"""

from datetime import datetime, timezone
from extensions import db


class Movie(db.Model):
    __tablename__ = "movies"

    id = db.Column(db.Integer, primary_key=True)
    # Optional: original ID from MovieLens or another external dataset
    movielens_id = db.Column(db.Integer, unique=True, nullable=True, index=True)
    title = db.Column(db.String(255), nullable=False)
    year = db.Column(db.Integer, nullable=True)
    # Comma-separated list of genres, e.g. "Action,Adventure,Sci-Fi"
    genres = db.Column(db.String(500), nullable=True)
    avg_rating = db.Column(db.Float, nullable=True)
    imdb_url = db.Column(db.String(500), nullable=True)

    watchlist_entries = db.relationship(
        "WatchlistEntry", backref="movie", lazy="dynamic", cascade="all, delete-orphan"
    )
    ratings = db.relationship(
        "Rating", backref="movie", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self):
        genres_raw = self.genres or ""
        # Support both comma-separated and pipe-separated genre strings
        import re
        genres = [g.strip() for g in re.split(r"[,|]", genres_raw) if g.strip()]
        return {
            "id": self.id,
            "movielens_id": self.movielens_id,
            "title": self.title,
            "year": self.year,
            "genres": genres,
            "avg_rating": self.avg_rating,
            "imdb_url": self.imdb_url,
        }


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    # Optional: maps to a MovieLens user ID for recommendation engine
    movielens_user_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    watchlist_entries = db.relationship(
        "WatchlistEntry", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    ratings = db.relationship(
        "Rating", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "movielens_user_id": self.movielens_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WatchlistEntry(db.Model):
    __tablename__ = "watchlist"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False)
    added_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    notes = db.Column(db.String(500), nullable=True)

    __table_args__ = (
        db.UniqueConstraint("user_id", "movie_id", name="uq_user_movie"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "movie_id": self.movie_id,
            "movie": self.movie.to_dict() if self.movie else None,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "notes": self.notes,
        }


class Rating(db.Model):
    __tablename__ = "ratings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    rated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "movie_id", name="uq_user_movie_rating"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "movie_id": self.movie_id,
            "rating": self.rating,
            "rated_at": self.rated_at.isoformat() if self.rated_at else None,
        }

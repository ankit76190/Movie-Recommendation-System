"""
routes/movies.py
----------------
Endpoints for browsing, searching, and importing movies.

GET  /api/movies             – paginated list with optional title search
GET  /api/movies/<id>        – single movie detail
POST /api/movies             – create a single movie
POST /api/movies/import      – bulk-import movies from an uploaded CSV file
GET  /api/movies/movielens   – browse the MovieLens catalogue (ML dataset)
"""

import io
import pandas as pd
from flask import Blueprint, jsonify, request, current_app
from extensions import db
from models import Movie

movies_bp = Blueprint("movies", __name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _paginate_query(query):
    per_page = min(
        request.args.get("per_page", current_app.config["DEFAULT_PAGE_SIZE"], type=int),
        current_app.config["MAX_PAGE_SIZE"],
    )
    page = request.args.get("page", 1, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return pagination, page, per_page


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@movies_bp.get("/api/movies")
def list_movies():
    """Return a paginated, optionally-filtered list of movies from the database."""
    search = request.args.get("q", "").strip()
    genre = request.args.get("genre", "").strip()

    query = Movie.query.order_by(Movie.title)
    if search:
        query = query.filter(Movie.title.ilike(f"%{search}%"))
    if genre:
        query = query.filter(Movie.genres.ilike(f"%{genre}%"))

    pagination, page, per_page = _paginate_query(query)
    return jsonify(
        {
            "movies": [m.to_dict() for m in pagination.items],
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "pages": pagination.pages,
        }
    )


@movies_bp.get("/api/movies/<int:movie_id>")
def get_movie(movie_id):
    """Return a single movie by its database ID."""
    movie = db.get_or_404(Movie, movie_id)
    return jsonify(movie.to_dict())


@movies_bp.post("/api/movies")
def create_movie():
    """Create a single movie record."""
    data = request.get_json(silent=True) or {}
    if not data.get("title"):
        return jsonify({"error": "title is required"}), 400

    movie = Movie(
        title=data["title"],
        year=data.get("year"),
        genres=",".join(data.get("genres", [])) if isinstance(data.get("genres"), list) else data.get("genres"),
        avg_rating=data.get("avg_rating"),
        imdb_url=data.get("imdb_url"),
        movielens_id=data.get("movielens_id"),
    )
    db.session.add(movie)
    db.session.commit()
    return jsonify(movie.to_dict()), 201


@movies_bp.post("/api/movies/import")
def import_movies():
    """
    Bulk-import movies from an uploaded CSV file.

    Expected CSV columns (flexible, extras are ignored):
        title       (required)
        year        (optional)
        genres      (optional, comma-separated inside the cell)
        avg_rating  (optional)
        imdb_url    (optional)
        movielens_id (optional)
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided. Use multipart/form-data with key 'file'."}), 400

    file = request.files["file"]
    if not file.filename.endswith(".csv"):
        return jsonify({"error": "Only CSV files are supported."}), 400

    try:
        df = pd.read_csv(io.StringIO(file.read().decode("utf-8")))
    except Exception as exc:
        return jsonify({"error": f"Failed to parse CSV: {exc}"}), 400

    if "title" not in df.columns:
        return jsonify({"error": "CSV must contain a 'title' column."}), 400

    inserted = 0
    updated = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            title = str(row["title"]).strip()
            if not title:
                continue

            ml_id = int(row["movielens_id"]) if "movielens_id" in df.columns and pd.notna(row.get("movielens_id")) else None

            # Upsert by movielens_id (if provided) or by title
            existing = None
            if ml_id is not None:
                existing = Movie.query.filter_by(movielens_id=ml_id).first()
            if existing is None:
                existing = Movie.query.filter_by(title=title).first()

            genres_raw = row.get("genres", "") if "genres" in df.columns else ""
            genres = str(genres_raw).strip() if pd.notna(genres_raw) else ""

            year_raw = row.get("year") if "year" in df.columns else None
            year = int(year_raw) if year_raw is not None and pd.notna(year_raw) else None

            avg_rating_raw = row.get("avg_rating") if "avg_rating" in df.columns else None
            avg_rating = float(avg_rating_raw) if avg_rating_raw is not None and pd.notna(avg_rating_raw) else None

            imdb_url = str(row["imdb_url"]).strip() if "imdb_url" in df.columns and pd.notna(row.get("imdb_url")) else None

            if existing:
                existing.title = title
                existing.year = year
                existing.genres = genres
                existing.avg_rating = avg_rating
                if imdb_url:
                    existing.imdb_url = imdb_url
                if ml_id is not None:
                    existing.movielens_id = ml_id
                updated += 1
            else:
                movie = Movie(
                    title=title,
                    year=year,
                    genres=genres,
                    avg_rating=avg_rating,
                    imdb_url=imdb_url,
                    movielens_id=ml_id,
                )
                db.session.add(movie)
                inserted += 1
        except Exception as exc:
            errors.append({"row": int(idx), "error": str(exc)})

    db.session.commit()
    return jsonify(
        {
            "inserted": inserted,
            "updated": updated,
            "errors": errors,
            "total_processed": inserted + updated + len(errors),
        }
    ), 201


@movies_bp.get("/api/movies/movielens")
def list_movielens_movies():
    """
    Browse the MovieLens 100K catalogue.
    Requires the dataset to be downloaded (python data_loader.py).
    """
    from services.recommender_service import list_movielens_movies as _list, DataNotReadyError

    search = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = min(
        request.args.get("per_page", current_app.config["DEFAULT_PAGE_SIZE"], type=int),
        current_app.config["MAX_PAGE_SIZE"],
    )

    try:
        result = _list(page=page, per_page=per_page, search=search)
        return jsonify(result)
    except DataNotReadyError as exc:
        return jsonify({"error": str(exc), "dataset_ready": False}), 503

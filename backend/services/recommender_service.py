"""
services/recommender_service.py
--------------------------------
Service layer that wraps the recommendation algorithms from recommender.py
and provides thread-safe, cached access to the recommendation engine.

The MovieLens dataset is loaded lazily on first use.  If the dataset has not
been downloaded yet, calls to the ML-based methods raise DataNotReadyError.
A lighter fallback (genre-based similarity on DB movies) is also provided.
"""

import os
import sys
import re
import threading
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Make the project root importable so we can reuse recommender.py /
# data_loader.py that live one level above backend/.
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class DataNotReadyError(RuntimeError):
    """Raised when the MovieLens dataset has not been downloaded yet."""


# ---------------------------------------------------------------------------
# Thread-safe cache
# ---------------------------------------------------------------------------
_cache: dict = {}
# RLock (reentrant) is required because _ensure_data() may be called from within
# other _ensure_* helpers that have already acquired this lock on the same thread.
# A plain Lock() would deadlock in that scenario.
_lock = threading.RLock()

GENRE_COLS = [
    "unknown", "Action", "Adventure", "Animation", "Children", "Comedy",
    "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror",
    "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western",
]


def _dataset_exists() -> bool:
    """Return True if the MovieLens 100K dataset has already been extracted."""
    extract_dir = os.path.join(PROJECT_ROOT, "data", "ml-100k")
    return os.path.isdir(extract_dir)


def _ensure_data():
    """Load and cache the MovieLens dataset (thread-safe).

    Raises DataNotReadyError immediately if the dataset has not been downloaded
    yet (avoids blocking the API with a long network download).
    """
    if "data" not in _cache:
        with _lock:
            if "data" not in _cache:
                if not _dataset_exists():
                    raise DataNotReadyError(
                        "MovieLens dataset not available. "
                        "Please run: python data_loader.py  (or python main.py) "
                        "to download and prepare the dataset."
                    )
                try:
                    from data_loader import load_all
                    ratings, movies, users = load_all()
                    _cache["data"] = (ratings, movies, users)
                except Exception as exc:
                    raise DataNotReadyError(
                        "Failed to load MovieLens dataset. "
                        "Please re-run: python data_loader.py"
                    ) from exc
    return _cache["data"]


def _ensure_content_recommender():
    if "content_rec" not in _cache:
        with _lock:
            if "content_rec" not in _cache:
                ratings, movies, _ = _ensure_data()
                from recommender import ContentBasedRecommender
                _cache["content_rec"] = ContentBasedRecommender(movies, ratings)
    return _cache["content_rec"]


def _ensure_ubcf_recommender():
    if "ubcf_rec" not in _cache:
        with _lock:
            if "ubcf_rec" not in _cache:
                ratings, movies, _ = _ensure_data()
                from recommender import UserBasedCF
                _cache["ubcf_rec"] = UserBasedCF(ratings, movies)
    return _cache["ubcf_rec"]


def _ensure_svd_recommender():
    if "svd_rec" not in _cache:
        with _lock:
            if "svd_rec" not in _cache:
                ratings, movies, _ = _ensure_data()
                from recommender import SVDRecommender
                svd = SVDRecommender(ratings, movies, n_factors=50)
                svd.fit()
                _cache["svd_rec"] = svd
    return _cache["svd_rec"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_recommendations(user_id: int, method: str = "svd", n: int = 10) -> list:
    """
    Return top-n recommendations for a MovieLens user.

    Parameters
    ----------
    user_id : int  – MovieLens user ID (1–943)
    method  : str  – 'content', 'collaborative', or 'svd'
    n       : int  – number of results
    """
    method = method.lower()
    if method == "content":
        rec = _ensure_content_recommender()
        result = rec.recommend(user_id, n=n)
        return _df_to_list(result, score_col="score")
    elif method == "collaborative":
        rec = _ensure_ubcf_recommender()
        result = rec.recommend(user_id, n=n)
        return _df_to_list(result, score_col="predicted_rating")
    elif method == "svd":
        rec = _ensure_svd_recommender()
        result = rec.recommend(user_id, n=n)
        return _df_to_list(result, score_col="predicted_rating")
    else:
        raise ValueError(f"Unknown method: {method!r}. Choose 'content', 'collaborative', or 'svd'.")


def get_similar_movies(movie_id: int, n: int = 10) -> list:
    """Return top-n movies similar to the given MovieLens movie_id."""
    rec = _ensure_content_recommender()
    result = rec.similar_movies(movie_id, n=n)
    return _df_to_list(result, score_col="similarity")


def get_movie_info(movie_id: int) -> dict | None:
    """Fetch basic info about a MovieLens movie."""
    _, movies, _ = _ensure_data()
    row = movies[movies["movie_id"] == movie_id]
    if row.empty:
        return None
    r = row.iloc[0]
    genres = [g for g in GENRE_COLS if r.get(g, 0) == 1]
    return {
        "movielens_id": int(r["movie_id"]),
        "title": r["title"],
        "year": int(r["year"]) if pd.notna(r.get("year")) else None,
        "genres": genres,
    }


def list_movielens_movies(page: int = 1, per_page: int = 20, search: str = "") -> dict:
    """Return a paginated list of MovieLens movies (optional title search)."""
    _, movies, _ = _ensure_data()
    df = movies[["movie_id", "title", "year"]].copy()
    if search:
        df = df[df["title"].str.contains(search, case=False, na=False)]
    total = len(df)
    start = (page - 1) * per_page
    end = start + per_page
    page_df = df.iloc[start:end]
    items = []
    for _, r in page_df.iterrows():
        items.append({
            "movielens_id": int(r["movie_id"]),
            "title": r["title"],
            "year": int(r["year"]) if pd.notna(r.get("year")) else None,
        })
    return {
        "movies": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


# ---------------------------------------------------------------------------
# Fallback: genre-based similarity on DB movies (no ML dataset required)
# ---------------------------------------------------------------------------

def genre_based_recommendations(genre_list: list, n: int = 10, exclude_ids: list = None) -> list:
    """
    Simple genre-overlap recommendation when ML dataset is unavailable.
    Uses the Movie records already stored in the SQLite database.
    """
    from extensions import db
    from models import Movie
    exclude_ids = set(exclude_ids or [])
    movies = Movie.query.filter(Movie.genres.isnot(None)).all()
    query_set = set(g.strip().lower() for g in genre_list)
    scored = []
    for m in movies:
        if m.id in exclude_ids:
            continue
        m_genres = set(g.strip().lower() for g in re.split(r"[,|]", m.genres or "") if g.strip())
        overlap = len(query_set & m_genres)
        if overlap:
            scored.append((overlap, m))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m.to_dict() for _, m in scored[:n]]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _df_to_list(df: pd.DataFrame, score_col: str) -> list:
    records = []
    for _, row in df.iterrows():
        rec = {
            "movielens_id": int(row["movie_id"]),
            "title": row["title"],
        }
        if score_col in row.index:
            val = row[score_col]
            rec["score"] = float(val) if pd.notna(val) else None
        records.append(rec)
    return records

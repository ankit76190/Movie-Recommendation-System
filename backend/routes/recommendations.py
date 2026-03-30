"""
routes/recommendations.py
--------------------------
Endpoints for generating movie recommendations.

GET /api/recommendations/<user_id>
    Query params:
        method  – 'content' | 'collaborative' | 'svd'  (default: 'svd')
        n       – number of recommendations              (default: 10)

GET /api/recommendations/similar/<movie_id>
    Query params:
        n  – number of similar movies  (default: 10)

GET /api/recommendations/genre
    Query params:
        genres  – comma-separated genre list (fallback when dataset unavailable)
        n       – number of results           (default: 10)
"""

from flask import Blueprint, jsonify, request, current_app
from services.recommender_service import (
    get_recommendations,
    get_similar_movies,
    genre_based_recommendations,
    DataNotReadyError,
)

recommendations_bp = Blueprint("recommendations", __name__)


@recommendations_bp.get("/api/recommendations/<int:user_id>")
def recommend_for_user(user_id: int):
    """
    Return personalised recommendations for a MovieLens user.
    Uses the full ML dataset; falls back to genre-based if unavailable.
    """
    method = request.args.get("method", "svd").lower()
    n = request.args.get("n", current_app.config["DEFAULT_N_RECOMMENDATIONS"], type=int)
    n = max(1, min(n, 50))

    try:
        recs = get_recommendations(user_id, method=method, n=n)
        return jsonify(
            {
                "user_id": user_id,
                "method": method,
                "recommendations": recs,
                "count": len(recs),
                "dataset_ready": True,
            }
        )
    except DataNotReadyError as exc:
        return jsonify(
            {
                "user_id": user_id,
                "method": method,
                "recommendations": [],
                "count": 0,
                "dataset_ready": False,
                "message": str(exc),
            }
        ), 503
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        current_app.logger.exception("Recommendation error for user %s", user_id)
        return jsonify({"error": "Internal error generating recommendations."}), 500


@recommendations_bp.get("/api/recommendations/similar/<int:movie_id>")
def similar_movies(movie_id: int):
    """Return movies similar to the given MovieLens movie ID."""
    n = request.args.get("n", current_app.config["DEFAULT_N_RECOMMENDATIONS"], type=int)
    n = max(1, min(n, 50))

    try:
        similar = get_similar_movies(movie_id, n=n)
        return jsonify(
            {
                "movie_id": movie_id,
                "similar": similar,
                "count": len(similar),
                "dataset_ready": True,
            }
        )
    except DataNotReadyError as exc:
        return jsonify(
            {
                "movie_id": movie_id,
                "similar": [],
                "count": 0,
                "dataset_ready": False,
                "message": str(exc),
            }
        ), 503
    except (IndexError, KeyError):
        return jsonify({"error": f"Movie ID {movie_id} not found in dataset."}), 404
    except Exception as exc:
        current_app.logger.exception("Similar-movies error for movie %s", movie_id)
        return jsonify({"error": "Internal error."}), 500


@recommendations_bp.get("/api/recommendations/genre")
def genre_recommendations():
    """
    Lightweight genre-based recommendations using only the local DB.
    Does not require the MovieLens dataset.
    """
    genres_param = request.args.get("genres", "")
    n = request.args.get("n", current_app.config["DEFAULT_N_RECOMMENDATIONS"], type=int)
    n = max(1, min(n, 50))
    exclude = request.args.get("exclude", "")

    genre_list = [g.strip() for g in genres_param.split(",") if g.strip()]
    if not genre_list:
        return jsonify({"error": "Provide at least one genre via ?genres=Action,Comedy"}), 400

    exclude_ids = [int(x) for x in exclude.split(",") if x.strip().isdigit()]

    recs = genre_based_recommendations(genre_list, n=n, exclude_ids=exclude_ids)
    return jsonify({"genres": genre_list, "recommendations": recs, "count": len(recs)})

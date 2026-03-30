"""
routes/export.py
-----------------
Export endpoints.

GET /api/export/watchlist/<username>  – Download user's watchlist as CSV
"""

import io
import csv
from flask import Blueprint, Response, current_app
from models import User, WatchlistEntry

export_bp = Blueprint("export", __name__)


@export_bp.get("/api/export/watchlist/<username>")
def export_watchlist_csv(username: str):
    """
    Stream the user's watchlist as a downloadable CSV file.

    Columns: id, title, year, genres, avg_rating, notes, added_at
    """
    user = User.query.filter_by(username=username).first_or_404(
        description=f"User '{username}' not found"
    )

    entries = (
        WatchlistEntry.query.filter_by(user_id=user.id)
        .order_by(WatchlistEntry.added_at.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow(["id", "title", "year", "genres", "avg_rating", "notes", "added_at"])

    for entry in entries:
        movie = entry.movie
        if movie is None:
            continue
        writer.writerow(
            [
                movie.id,
                movie.title,
                movie.year or "",
                movie.genres or "",
                movie.avg_rating or "",
                entry.notes or "",
                entry.added_at.isoformat() if entry.added_at else "",
            ]
        )

    output.seek(0)
    filename = f"watchlist_{username}.csv"

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "text/csv; charset=utf-8",
        },
    )

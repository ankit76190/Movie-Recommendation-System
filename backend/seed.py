"""
seed.py
-------
Populates the database with sample movie data from data/sample_movies.csv.

Usage:
    cd backend
    python seed.py
"""

import os
import sys
import pandas as pd

# Make sure Flask app is importable from this directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import Movie, User

SAMPLE_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "sample_movies.csv",
)


def seed_movies(app):
    """Load sample_movies.csv into the database (upsert by movielens_id or title)."""
    if not os.path.exists(SAMPLE_CSV):
        print(f"Sample CSV not found at {SAMPLE_CSV}. Skipping movie seeding.")
        return 0

    df = pd.read_csv(SAMPLE_CSV)
    inserted = 0
    updated = 0

    with app.app_context():
        for _, row in df.iterrows():
            title = str(row.get("title", "")).strip()
            if not title:
                continue

            ml_id = int(row["movielens_id"]) if pd.notna(row.get("movielens_id")) else None

            existing = None
            if ml_id is not None:
                existing = Movie.query.filter_by(movielens_id=ml_id).first()
            if existing is None:
                existing = Movie.query.filter_by(title=title).first()

            genres = str(row.get("genres", "")).strip() if pd.notna(row.get("genres")) else ""
            year = int(row["year"]) if pd.notna(row.get("year")) else None
            avg_rating = float(row["avg_rating"]) if pd.notna(row.get("avg_rating")) else None
            imdb_url = str(row["imdb_url"]).strip() if pd.notna(row.get("imdb_url")) else None

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
                    title=title, year=year, genres=genres,
                    avg_rating=avg_rating, imdb_url=imdb_url, movielens_id=ml_id,
                )
                db.session.add(movie)
                inserted += 1

        db.session.commit()

    print(f"Movies seeded: {inserted} inserted, {updated} updated.")
    return inserted + updated


def seed_demo_users(app):
    """Create a few demo users for testing."""
    demo_users = [
        {"username": "alice", "movielens_user_id": 1},
        {"username": "bob", "movielens_user_id": 2},
        {"username": "carol", "movielens_user_id": 3},
        {"username": "demo", "movielens_user_id": None},
    ]
    count = 0
    with app.app_context():
        for u in demo_users:
            if not User.query.filter_by(username=u["username"]).first():
                db.session.add(User(**u))
                count += 1
        db.session.commit()
    print(f"Demo users seeded: {count} created.")
    return count


if __name__ == "__main__":
    app = create_app("development")
    with app.app_context():
        db.create_all()
    seed_movies(app)
    seed_demo_users(app)
    print("Seeding complete.")

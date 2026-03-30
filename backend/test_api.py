"""
test_api.py
-----------
Unit tests for the Flask REST API.

Run:
    cd backend
    python -m pytest test_api.py -v
"""

import io
import sys
import os
import unittest

# Ensure backend directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import Movie, User, WatchlistEntry


class BaseTestCase(unittest.TestCase):
    """Shared set-up / tear-down for all API tests."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app("testing")
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            db.create_all()
            # Seed a couple of movies and a user
            m1 = Movie(title="The Matrix (1999)", year=1999,
                       genres="Action,Sci-Fi,Thriller", avg_rating=4.26)
            m2 = Movie(title="Inception (2010)", year=2010,
                       genres="Action,Adventure,Sci-Fi,Thriller", avg_rating=4.37)
            m3 = Movie(title="Toy Story (1995)", year=1995,
                       genres="Animation,Children,Comedy", avg_rating=3.88, movielens_id=1)
            u1 = User(username="testuser", movielens_user_id=1)
            db.session.add_all([m1, m2, m3, u1])
            db.session.commit()
            cls.movie_id = m1.id
            cls.movie2_id = m2.id
            cls.user_username = u1.username

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()


class TestHealthCheck(BaseTestCase):
    """Tests for the health-check endpoint."""

    def test_root_returns_ok(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "ok")

    def test_root_has_service_name(self):
        resp = self.client.get("/")
        data = resp.get_json()
        self.assertIn("service", data)


class TestMovieEndpoints(BaseTestCase):
    """Tests for /api/movies endpoints."""

    def test_list_movies_returns_200(self):
        resp = self.client.get("/api/movies")
        self.assertEqual(resp.status_code, 200)

    def test_list_movies_has_pagination(self):
        resp = self.client.get("/api/movies")
        data = resp.get_json()
        self.assertIn("movies", data)
        self.assertIn("total", data)
        self.assertIn("page", data)
        self.assertIn("pages", data)

    def test_list_movies_returns_seeded_data(self):
        resp = self.client.get("/api/movies")
        data = resp.get_json()
        titles = [m["title"] for m in data["movies"]]
        self.assertIn("The Matrix (1999)", titles)

    def test_search_movies(self):
        resp = self.client.get("/api/movies?q=Matrix")
        data = resp.get_json()
        self.assertTrue(len(data["movies"]) >= 1)
        self.assertTrue(all("Matrix" in m["title"] for m in data["movies"]))

    def test_search_no_results(self):
        resp = self.client.get("/api/movies?q=ZZZNonexistent999")
        data = resp.get_json()
        self.assertEqual(data["total"], 0)
        self.assertEqual(data["movies"], [])

    def test_get_single_movie(self):
        resp = self.client.get(f"/api/movies/{self.movie_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["title"], "The Matrix (1999)")
        self.assertIsInstance(data["genres"], list)

    def test_get_nonexistent_movie(self):
        resp = self.client.get("/api/movies/99999")
        self.assertEqual(resp.status_code, 404)

    def test_create_movie(self):
        payload = {
            "title": "Test Movie (2024)",
            "year": 2024,
            "genres": ["Comedy", "Drama"],
            "avg_rating": 3.5,
        }
        resp = self.client.post("/api/movies", json=payload)
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data["title"], "Test Movie (2024)")
        self.assertEqual(data["year"], 2024)

    def test_create_movie_missing_title(self):
        resp = self.client.post("/api/movies", json={"year": 2024})
        self.assertEqual(resp.status_code, 400)

    def test_import_movies_csv(self):
        csv_content = (
            "title,year,genres,avg_rating\n"
            "Import Movie A,2020,Action|Comedy,3.9\n"
            "Import Movie B,2021,Drama,4.1\n"
        )
        data = {"file": (io.BytesIO(csv_content.encode()), "movies.csv")}
        resp = self.client.post(
            "/api/movies/import",
            data=data,
            content_type="multipart/form-data",
        )
        self.assertEqual(resp.status_code, 201)
        result = resp.get_json()
        self.assertEqual(result["inserted"], 2)

    def test_import_movies_no_file(self):
        resp = self.client.post("/api/movies/import")
        self.assertEqual(resp.status_code, 400)

    def test_import_movies_missing_title_column(self):
        csv_content = "name,year\nFoo,2020\n"
        data = {"file": (io.BytesIO(csv_content.encode()), "bad.csv")}
        resp = self.client.post(
            "/api/movies/import",
            data=data,
            content_type="multipart/form-data",
        )
        self.assertEqual(resp.status_code, 400)


class TestWatchlistEndpoints(BaseTestCase):
    """Tests for /api/users and /api/watchlist endpoints."""

    def test_list_users(self):
        resp = self.client.get("/api/users")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("users", data)
        usernames = [u["username"] for u in data["users"]]
        self.assertIn("testuser", usernames)

    def test_create_user(self):
        resp = self.client.post("/api/users", json={"username": "newuser_test"})
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data["username"], "newuser_test")

    def test_create_duplicate_user(self):
        self.client.post("/api/users", json={"username": "dupuser"})
        resp = self.client.post("/api/users", json={"username": "dupuser"})
        self.assertEqual(resp.status_code, 409)

    def test_create_user_missing_username(self):
        resp = self.client.post("/api/users", json={})
        self.assertEqual(resp.status_code, 400)

    def test_get_empty_watchlist(self):
        resp = self.client.get(f"/api/watchlist/{self.user_username}")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["username"], self.user_username)
        self.assertIn("watchlist", data)

    def test_add_to_watchlist(self):
        resp = self.client.post(
            f"/api/watchlist/{self.user_username}",
            json={"movie_id": self.movie_id, "notes": "Must watch!"},
        )
        self.assertIn(resp.status_code, [200, 201])
        data = resp.get_json()
        self.assertEqual(data["movie_id"], self.movie_id)

    def test_add_duplicate_to_watchlist_is_idempotent(self):
        self.client.post(
            f"/api/watchlist/{self.user_username}",
            json={"movie_id": self.movie2_id},
        )
        resp = self.client.post(
            f"/api/watchlist/{self.user_username}",
            json={"movie_id": self.movie2_id},
        )
        self.assertEqual(resp.status_code, 200)  # idempotent

    def test_watchlist_contains_added_movie(self):
        self.client.post(
            f"/api/watchlist/{self.user_username}",
            json={"movie_id": self.movie_id},
        )
        resp = self.client.get(f"/api/watchlist/{self.user_username}")
        data = resp.get_json()
        movie_ids = [e["movie_id"] for e in data["watchlist"]]
        self.assertIn(self.movie_id, movie_ids)

    def test_remove_from_watchlist(self):
        self.client.post(
            f"/api/watchlist/{self.user_username}",
            json={"movie_id": self.movie_id},
        )
        resp = self.client.delete(
            f"/api/watchlist/{self.user_username}/{self.movie_id}"
        )
        self.assertEqual(resp.status_code, 200)

    def test_watchlist_unknown_user(self):
        resp = self.client.get("/api/watchlist/no_such_user")
        self.assertEqual(resp.status_code, 404)

    def test_add_to_watchlist_unknown_movie(self):
        resp = self.client.post(
            f"/api/watchlist/{self.user_username}",
            json={"movie_id": 999999},
        )
        self.assertEqual(resp.status_code, 404)

    def test_add_to_watchlist_missing_movie_id(self):
        resp = self.client.post(
            f"/api/watchlist/{self.user_username}",
            json={"notes": "no id here"},
        )
        self.assertEqual(resp.status_code, 400)


class TestExportEndpoints(BaseTestCase):
    """Tests for /api/export/watchlist CSV export."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Add a movie to the watchlist for export testing
        with cls.app.app_context():
            user = User.query.filter_by(username="testuser").first()
            movie = Movie.query.filter_by(title="The Matrix (1999)").first()
            entry = WatchlistEntry.query.filter_by(
                user_id=user.id, movie_id=movie.id
            ).first()
            if not entry:
                entry = WatchlistEntry(user_id=user.id, movie_id=movie.id,
                                       notes="Classic")
                db.session.add(entry)
                db.session.commit()

    def test_export_csv_returns_200(self):
        resp = self.client.get(f"/api/export/watchlist/{self.user_username}")
        self.assertEqual(resp.status_code, 200)

    def test_export_csv_content_type(self):
        resp = self.client.get(f"/api/export/watchlist/{self.user_username}")
        self.assertIn("text/csv", resp.content_type)

    def test_export_csv_has_header(self):
        resp = self.client.get(f"/api/export/watchlist/{self.user_username}")
        text = resp.data.decode("utf-8")
        self.assertIn("title", text)
        self.assertIn("genres", text)

    def test_export_csv_contains_movie_data(self):
        resp = self.client.get(f"/api/export/watchlist/{self.user_username}")
        text = resp.data.decode("utf-8")
        self.assertIn("Matrix", text)

    def test_export_csv_unknown_user(self):
        resp = self.client.get("/api/export/watchlist/nobody_here")
        self.assertEqual(resp.status_code, 404)

    def test_export_csv_content_disposition(self):
        resp = self.client.get(f"/api/export/watchlist/{self.user_username}")
        cd = resp.headers.get("Content-Disposition", "")
        self.assertIn("attachment", cd)
        self.assertIn(".csv", cd)


class TestRecommendationEndpoints(BaseTestCase):
    """Tests for /api/recommendations endpoints (dataset-independent)."""

    def test_genre_recommendations_basic(self):
        # Genre-based recommendations use DB movies only — always works
        resp = self.client.get("/api/recommendations/genre?genres=Action,Sci-Fi")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("recommendations", data)
        self.assertIn("genres", data)

    def test_genre_recommendations_no_genre_param(self):
        resp = self.client.get("/api/recommendations/genre")
        self.assertEqual(resp.status_code, 400)

    def test_recommendations_svd_no_dataset(self):
        # When dataset is not downloaded, API returns 503 gracefully
        resp = self.client.get("/api/recommendations/1?method=svd")
        self.assertIn(resp.status_code, [200, 503])

    def test_recommendations_invalid_method(self):
        resp = self.client.get("/api/recommendations/1?method=unknown_algo")
        self.assertIn(resp.status_code, [400, 503])

    def test_similar_movies_no_dataset(self):
        resp = self.client.get("/api/recommendations/similar/1")
        self.assertIn(resp.status_code, [200, 503])


if __name__ == "__main__":
    unittest.main(verbosity=2)

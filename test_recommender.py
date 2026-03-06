"""
test_recommender.py
-------------------
Unit tests for the Movie Recommendation System.
Run:  python test_recommender.py
"""

import unittest
import pandas as pd
import numpy as np

from data_loader import (
    load_all, load_ratings, load_movies, load_users,
    preprocess_ratings, preprocess_movies,
    build_user_item_matrix, normalize_ratings,
)
from recommender import ContentBasedRecommender, UserBasedCF, SVDRecommender
from evaluation import compute_rmse_mae, precision_recall_at_k, ndcg_at_k, _train_test_svd


class TestDataLoader(unittest.TestCase):
    """Tests for data loading and preprocessing."""

    @classmethod
    def setUpClass(cls):
        cls.ratings, cls.movies, cls.users = load_all()

    def test_ratings_shape(self):
        self.assertEqual(len(self.ratings), 100_000)
        self.assertListEqual(
            list(self.ratings.columns[:4]),
            ["user_id", "movie_id", "rating", "timestamp"],
        )

    def test_movies_shape(self):
        self.assertEqual(len(self.movies), 1682)
        self.assertIn("title", self.movies.columns)
        self.assertIn("Action", self.movies.columns)

    def test_users_shape(self):
        self.assertEqual(len(self.users), 943)
        self.assertIn("age", self.users.columns)

    def test_no_missing_ratings(self):
        self.assertEqual(self.ratings[["user_id", "movie_id", "rating"]].isna().sum().sum(), 0)

    def test_rating_range(self):
        self.assertGreaterEqual(self.ratings["rating"].min(), 1.0)
        self.assertLessEqual(self.ratings["rating"].max(), 5.0)

    def test_user_item_matrix_shape(self):
        matrix = build_user_item_matrix(self.ratings)
        self.assertEqual(matrix.shape[0], 943)
        self.assertEqual(matrix.shape[1], 1682)

    def test_normalized_matrix_centered(self):
        matrix = build_user_item_matrix(self.ratings)
        normed = normalize_ratings(matrix)
        # Normalized matrix should have both positive and negative values
        all_vals = normed.values.flatten()
        self.assertTrue((all_vals < 0).any(), "Should have negative values")
        self.assertTrue((all_vals > 0).any(), "Should have positive values")
        # The non-zero values should be centered (have both signs)
        nonzero = all_vals[all_vals != 0]
        self.assertTrue((nonzero < 0).sum() > 100, "Should have many negatives")
        self.assertTrue((nonzero > 0).sum() > 100, "Should have many positives")

    def test_year_extraction(self):
        self.assertIn("year", self.movies.columns)
        toy_story = self.movies[self.movies["title"].str.contains("Toy Story")]
        if not toy_story.empty:
            self.assertEqual(toy_story.iloc[0]["year"], 1995.0)


class TestContentBased(unittest.TestCase):
    """Tests for the Content-Based Recommender."""

    @classmethod
    def setUpClass(cls):
        cls.ratings, cls.movies, cls.users = load_all()
        cls.cb = ContentBasedRecommender(cls.movies, cls.ratings)

    def test_similar_movies_returns_n(self):
        result = self.cb.similar_movies(50, n=5)
        self.assertEqual(len(result), 5)

    def test_similar_movies_has_columns(self):
        result = self.cb.similar_movies(50, n=5)
        self.assertIn("movie_id", result.columns)
        self.assertIn("title", result.columns)
        self.assertIn("similarity", result.columns)

    def test_similar_movies_excludes_self(self):
        result = self.cb.similar_movies(50, n=10)
        self.assertNotIn(50, result["movie_id"].values)

    def test_similarity_scores_valid_range(self):
        result = self.cb.similar_movies(50, n=10)
        self.assertTrue((result["similarity"] >= 0).all())
        self.assertTrue((result["similarity"] <= 1).all())

    def test_recommend_returns_n(self):
        recs = self.cb.recommend(1, n=10)
        self.assertEqual(len(recs), 10)

    def test_recommend_excludes_watched(self):
        recs = self.cb.recommend(1, n=10)
        watched = set(self.ratings[self.ratings["user_id"] == 1]["movie_id"])
        overlap = set(recs["movie_id"]) & watched
        self.assertEqual(len(overlap), 0)

    def test_recommend_unknown_user_returns_empty(self):
        recs = self.cb.recommend(99999, n=10)
        self.assertEqual(len(recs), 0)


class TestUserBasedCF(unittest.TestCase):
    """Tests for User-Based Collaborative Filtering."""

    @classmethod
    def setUpClass(cls):
        cls.ratings, cls.movies, cls.users = load_all()
        cls.ubcf = UserBasedCF(cls.ratings, cls.movies)

    def test_similar_users_returns_n(self):
        result = self.ubcf.similar_users(1, n=5)
        self.assertEqual(len(result), 5)

    def test_similar_users_excludes_self(self):
        result = self.ubcf.similar_users(1, n=5)
        self.assertNotIn(1, result.index)

    def test_similarity_scores_in_range(self):
        result = self.ubcf.similar_users(1, n=5)
        self.assertTrue((result >= -1).all())
        self.assertTrue((result <= 1).all())

    def test_recommend_returns_n(self):
        recs = self.ubcf.recommend(1, n=10)
        self.assertLessEqual(len(recs), 10)
        self.assertGreater(len(recs), 0)

    def test_recommend_excludes_watched(self):
        recs = self.ubcf.recommend(1, n=10)
        watched = set(self.ratings[self.ratings["user_id"] == 1]["movie_id"])
        overlap = set(recs["movie_id"]) & watched
        self.assertEqual(len(overlap), 0)

    def test_recommend_has_predicted_rating(self):
        recs = self.ubcf.recommend(1, n=5)
        self.assertIn("predicted_rating", recs.columns)


class TestSVDRecommender(unittest.TestCase):
    """Tests for SVD Matrix Factorization Recommender."""

    @classmethod
    def setUpClass(cls):
        cls.ratings, cls.movies, cls.users = load_all()
        cls.svd = SVDRecommender(cls.ratings, cls.movies, n_factors=20)
        cls.svd.fit()

    def test_fit_marks_trained(self):
        self.assertTrue(self.svd._trained)

    def test_predicted_df_shape(self):
        self.assertEqual(self.svd.predicted_df.shape, (943, 1682))

    def test_predict_single_rating(self):
        pred = self.svd.predict(1, 50)
        self.assertGreaterEqual(pred, 1.0)
        self.assertLessEqual(pred, 5.0)

    def test_recommend_returns_n(self):
        recs = self.svd.recommend(1, n=10)
        self.assertEqual(len(recs), 10)

    def test_recommend_excludes_rated(self):
        recs = self.svd.recommend(1, n=10)
        watched = set(self.ratings[self.ratings["user_id"] == 1]["movie_id"])
        overlap = set(recs["movie_id"]) & watched
        self.assertEqual(len(overlap), 0)

    def test_recommend_has_columns(self):
        recs = self.svd.recommend(1, n=5)
        self.assertIn("movie_id", recs.columns)
        self.assertIn("title", recs.columns)
        self.assertIn("predicted_rating", recs.columns)

    def test_predicted_ratings_in_range(self):
        recs = self.svd.recommend(1, n=10)
        self.assertTrue((recs["predicted_rating"] >= 1.0).all())
        self.assertTrue((recs["predicted_rating"] <= 5.0).all())

    def test_evaluate_returns_metrics(self):
        result = self.svd.evaluate(test_size=0.2)
        self.assertIn("rmse", result)
        self.assertIn("mae", result)
        self.assertGreater(result["rmse"], 0)
        self.assertGreater(result["mae"], 0)
        self.assertLess(result["rmse"], 3.0)  # sanity check


class TestEvaluation(unittest.TestCase):
    """Tests for the evaluation metrics."""

    @classmethod
    def setUpClass(cls):
        cls.ratings, cls.movies, cls.users = load_all()
        cls.test_df, cls.pred_df = _train_test_svd(cls.ratings, n_factors=20)

    def test_rmse_mae_positive(self):
        metrics = compute_rmse_mae(self.test_df, self.pred_df)
        self.assertGreater(metrics["rmse"], 0)
        self.assertGreater(metrics["mae"], 0)

    def test_rmse_greater_than_mae(self):
        metrics = compute_rmse_mae(self.test_df, self.pred_df)
        self.assertGreaterEqual(metrics["rmse"], metrics["mae"])

    def test_precision_recall_in_range(self):
        metrics = precision_recall_at_k(self.test_df, self.pred_df, k=10)
        self.assertGreaterEqual(metrics["precision@k"], 0)
        self.assertLessEqual(metrics["precision@k"], 1)
        self.assertGreaterEqual(metrics["recall@k"], 0)
        self.assertLessEqual(metrics["recall@k"], 1)

    def test_ndcg_in_range(self):
        metrics = ndcg_at_k(self.test_df, self.pred_df, k=10)
        self.assertGreaterEqual(metrics["ndcg@k"], 0)
        self.assertLessEqual(metrics["ndcg@k"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""
recommender.py
--------------
Movie Recommendation Engine implementing three approaches:

1. Content-Based Filtering  — recommends movies similar to what users liked,
   based on genre vectors (cosine similarity).
2. Collaborative Filtering (User-Based) — finds similar users by rating
   patterns and recommends what those neighbors liked.
3. Collaborative Filtering (SVD) — truncated SVD matrix-factorization on the
   user-item matrix using scipy.
"""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse.linalg import svds

from data_loader import (
    build_user_item_matrix,
    normalize_ratings,
)


# ======================================================================
# 1. CONTENT-BASED FILTERING
# ======================================================================

class ContentBasedRecommender:
    """
    Recommends movies based on genre similarity.
    Uses cosine similarity over binary genre vectors.
    """

    GENRE_COLS = [
        "unknown", "Action", "Adventure", "Animation", "Children", "Comedy",
        "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror",
        "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western",
    ]

    def __init__(self, movies: pd.DataFrame, ratings: pd.DataFrame):
        self.movies = movies.copy()
        self.ratings = ratings.copy()
        self._build_similarity_matrix()

    def _build_similarity_matrix(self):
        """Compute pairwise cosine similarity between all movies based on genres."""
        genre_matrix = self.movies.set_index("movie_id")[self.GENRE_COLS].values
        self.sim_matrix = cosine_similarity(genre_matrix)
        self.movie_ids = self.movies["movie_id"].values

    def _movie_idx(self, movie_id: int) -> int:
        return np.where(self.movie_ids == movie_id)[0][0]

    def similar_movies(self, movie_id: int, n: int = 10) -> pd.DataFrame:
        """Return top-n movies most similar to the given movie (by genre)."""
        idx = self._movie_idx(movie_id)
        sim_scores = list(enumerate(self.sim_matrix[idx]))
        sim_scores.sort(key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1: n + 1]
        indices = [i for i, _ in sim_scores]
        scores = [s for _, s in sim_scores]
        result = self.movies.iloc[indices][["movie_id", "title"]].copy()
        result["similarity"] = scores
        return result.reset_index(drop=True)

    def recommend(self, user_id: int, n: int = 10) -> pd.DataFrame:
        """
        Recommend movies for a user based on their highest-rated movies' genres.
        Aggregates genre-similarity scores weighted by user ratings.
        """
        user_ratings = self.ratings[self.ratings["user_id"] == user_id]
        if user_ratings.empty:
            return pd.DataFrame(columns=["movie_id", "title", "score"])

        watched = set(user_ratings["movie_id"].values)
        scores = np.zeros(len(self.movie_ids))

        for _, row in user_ratings.iterrows():
            mid = int(row["movie_id"])
            if mid not in self.movie_ids:
                continue
            idx = self._movie_idx(mid)
            scores += self.sim_matrix[idx] * row["rating"]

        for mid in watched:
            if mid in self.movie_ids:
                scores[self._movie_idx(mid)] = 0

        top_indices = np.argsort(scores)[::-1][:n]
        result = self.movies.iloc[top_indices][["movie_id", "title"]].copy()
        result["score"] = scores[top_indices]
        return result.reset_index(drop=True)


# ======================================================================
# 2. COLLABORATIVE FILTERING — User-Based (Memory-Based)
# ======================================================================

class UserBasedCF:
    """
    User-based collaborative filtering using cosine similarity
    on the mean-centered user-item matrix.
    """

    def __init__(self, ratings: pd.DataFrame, movies: pd.DataFrame):
        self.ratings = ratings
        self.movies = movies
        self.matrix = build_user_item_matrix(ratings)
        self.normalized = normalize_ratings(self.matrix)
        self.user_sim = pd.DataFrame(
            cosine_similarity(self.normalized),
            index=self.matrix.index,
            columns=self.matrix.index,
        )

    def similar_users(self, user_id: int, n: int = 10) -> pd.Series:
        """Return the top-n most similar users."""
        return (
            self.user_sim[user_id]
            .drop(user_id)
            .sort_values(ascending=False)
            .head(n)
        )

    def recommend(self, user_id: int, n: int = 10, k_neighbors: int = 30) -> pd.DataFrame:
        """
        Predict ratings for unseen movies using weighted average of
        k nearest neighbors' ratings, then return top-n recommendations.
        """
        neighbors = self.similar_users(user_id, n=k_neighbors)
        neighbor_ratings = self.matrix.loc[neighbors.index]
        weights = neighbors.values.reshape(-1, 1)

        mask = (neighbor_ratings != 0).astype(float)
        weighted_sum = (neighbor_ratings.values * weights).sum(axis=0)
        weight_total = (mask.values * np.abs(weights)).sum(axis=0)

        with np.errstate(divide="ignore", invalid="ignore"):
            predicted = np.where(weight_total > 0, weighted_sum / weight_total, 0)

        predicted_series = pd.Series(predicted, index=self.matrix.columns)

        watched = self.matrix.loc[user_id]
        predicted_series[watched > 0] = 0

        top_ids = predicted_series.sort_values(ascending=False).head(n).index
        result = self.movies[self.movies["movie_id"].isin(top_ids)][["movie_id", "title"]].copy()
        result["predicted_rating"] = result["movie_id"].map(predicted_series).values
        result = result.sort_values("predicted_rating", ascending=False).reset_index(drop=True)
        return result


# ======================================================================
# 3. COLLABORATIVE FILTERING — SVD (Model-Based via scipy)
# ======================================================================

class SVDRecommender:
    """
    Matrix factorization using truncated SVD (scipy.sparse.linalg.svds).

    Decomposes the mean-centered user-item matrix R ≈ U·Σ·Vᵀ
    and reconstructs predicted ratings for all user-movie pairs.
    """

    def __init__(self, ratings: pd.DataFrame, movies: pd.DataFrame, n_factors: int = 50):
        self.ratings_df = ratings
        self.movies = movies
        self.n_factors = n_factors
        self.matrix = build_user_item_matrix(ratings)
        self._trained = False
        self.predicted_df = None

    def fit(self):
        """Perform truncated SVD and reconstruct the predicted rating matrix."""
        R = self.matrix.values.astype(float)
        # Compute per-user mean (only over rated items)
        rated_mask = R != 0
        counts = rated_mask.sum(axis=1)
        counts[counts == 0] = 1  # avoid division by zero
        self.user_means = (R.sum(axis=1)) / counts

        R_centered = R.copy()
        for i in range(R.shape[0]):
            m = R[i] != 0
            R_centered[i, m] -= self.user_means[i]

        k = min(self.n_factors, min(R_centered.shape) - 1)
        U, sigma, Vt = svds(R_centered, k=k)
        predicted = U @ np.diag(sigma) @ Vt + self.user_means.reshape(-1, 1)

        self.predicted_df = pd.DataFrame(
            predicted, index=self.matrix.index, columns=self.matrix.columns
        )
        self._trained = True
        print(f"SVD fit complete (k={k}, matrix shape={R.shape})")
        return self

    def predict(self, user_id: int, movie_id: int) -> float:
        """Predict a single user-movie rating."""
        if not self._trained:
            self.fit()
        if user_id in self.predicted_df.index and movie_id in self.predicted_df.columns:
            return float(np.clip(self.predicted_df.loc[user_id, movie_id], 1, 5))
        return 0.0

    def recommend(self, user_id: int, n: int = 10) -> pd.DataFrame:
        """Generate top-n recommendations for a user."""
        if not self._trained:
            self.fit()

        preds = self.predicted_df.loc[user_id].copy()
        already_rated = self.matrix.loc[user_id]
        preds[already_rated != 0] = -np.inf

        top = preds.sort_values(ascending=False).head(n)
        result = pd.DataFrame({
            "movie_id": top.index,
            "predicted_rating": np.clip(top.values, 1, 5),
        })
        result = result.merge(self.movies[["movie_id", "title"]], on="movie_id")
        return result[["movie_id", "title", "predicted_rating"]].reset_index(drop=True)

    def evaluate(self, test_size: float = 0.2, seed: int = 42) -> dict:
        """
        Hold out `test_size` fraction of ratings, train on the rest,
        and compute RMSE and MAE on the held-out set.
        """
        rng = np.random.RandomState(seed)
        df = self.ratings_df.copy()
        mask = rng.rand(len(df)) < test_size
        test_df = df[mask]
        train_df = df[~mask]

        train_matrix = train_df.pivot_table(
            index="user_id", columns="movie_id", values="rating", fill_value=0
        )
        train_matrix = train_matrix.reindex(
            index=self.matrix.index, columns=self.matrix.columns, fill_value=0
        )

        R = train_matrix.values.astype(float)
        rated_mask = R != 0
        counts = rated_mask.sum(axis=1)
        counts[counts == 0] = 1
        user_means = R.sum(axis=1) / counts

        R_centered = R.copy()
        for i in range(R.shape[0]):
            m = R[i] != 0
            R_centered[i, m] -= user_means[i]

        k = min(self.n_factors, min(R_centered.shape) - 1)
        U, sigma, Vt = svds(R_centered, k=k)
        predicted = U @ np.diag(sigma) @ Vt + user_means.reshape(-1, 1)

        pred_df = pd.DataFrame(
            predicted, index=train_matrix.index, columns=train_matrix.columns
        )

        sq_errors = []
        abs_errors = []
        for _, row in test_df.iterrows():
            uid, mid, true_r = int(row["user_id"]), int(row["movie_id"]), row["rating"]
            if uid in pred_df.index and mid in pred_df.columns:
                pred_r = np.clip(pred_df.loc[uid, mid], 1, 5)
                sq_errors.append((true_r - pred_r) ** 2)
                abs_errors.append(abs(true_r - pred_r))

        rmse = np.sqrt(np.mean(sq_errors))
        mae = np.mean(abs_errors)
        return {"rmse": rmse, "mae": mae, "n_test": len(sq_errors)}

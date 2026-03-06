"""
evaluation.py
-------------
Evaluation and optimization utilities for the recommendation system.

Metrics implemented:
  - RMSE (Root Mean Squared Error)
  - MAE  (Mean Absolute Error)
  - Precision@K / Recall@K
  - NDCG@K (Normalized Discounted Cumulative Gain)

Optimization:
  - Search over SVD n_factors for best accuracy.
"""

import numpy as np
import pandas as pd
from scipy.sparse.linalg import svds

from data_loader import build_user_item_matrix


# ======================================================================
# Core: train/test SVD and return per-user predictions
# ======================================================================

def _train_test_svd(ratings: pd.DataFrame, n_factors: int = 50,
                    test_size: float = 0.2, seed: int = 42):
    """
    Split ratings into train/test, train SVD on the training set,
    and return (test_df, pred_df) where pred_df is the full predicted matrix.
    """
    rng = np.random.RandomState(seed)
    mask = rng.rand(len(ratings)) < test_size
    test_df = ratings[mask].copy()
    train_df = ratings[~mask].copy()

    full_matrix = build_user_item_matrix(ratings)
    train_matrix = train_df.pivot_table(
        index="user_id", columns="movie_id", values="rating", fill_value=0
    )
    train_matrix = train_matrix.reindex(
        index=full_matrix.index, columns=full_matrix.columns, fill_value=0
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

    k = min(n_factors, min(R_centered.shape) - 1)
    U, sigma, Vt = svds(R_centered, k=k)
    predicted = U @ np.diag(sigma) @ Vt + user_means.reshape(-1, 1)

    pred_df = pd.DataFrame(
        predicted, index=train_matrix.index, columns=train_matrix.columns
    )
    return test_df, pred_df


# ======================================================================
# Accuracy Metrics
# ======================================================================

def compute_rmse_mae(test_df: pd.DataFrame, pred_df: pd.DataFrame) -> dict:
    """Compute RMSE and MAE from test ratings vs predicted matrix."""
    sq_errors = []
    abs_errors = []
    for _, row in test_df.iterrows():
        uid, mid, true_r = int(row["user_id"]), int(row["movie_id"]), row["rating"]
        if uid in pred_df.index and mid in pred_df.columns:
            pred_r = np.clip(pred_df.loc[uid, mid], 1, 5)
            sq_errors.append((true_r - pred_r) ** 2)
            abs_errors.append(abs(true_r - pred_r))

    rmse = np.sqrt(np.mean(sq_errors)) if sq_errors else float("nan")
    mae = np.mean(abs_errors) if abs_errors else float("nan")
    return {"rmse": rmse, "mae": mae}


def precision_recall_at_k(test_df: pd.DataFrame, pred_df: pd.DataFrame,
                          k: int = 10, threshold: float = 3.5) -> dict:
    """
    Precision@K and Recall@K.
    A movie is 'relevant' if true rating >= threshold.
    A recommendation is a 'hit' if predicted >= threshold AND relevant.
    """
    precisions, recalls = [], []

    for uid in test_df["user_id"].unique():
        user_test = test_df[test_df["user_id"] == uid]
        if uid not in pred_df.index:
            continue

        # Get predictions for test items
        items = []
        for _, row in user_test.iterrows():
            mid = int(row["movie_id"])
            if mid in pred_df.columns:
                items.append((mid, np.clip(pred_df.loc[uid, mid], 1, 5), row["rating"]))

        if not items:
            continue

        # Sort by predicted rating, take top-k
        items.sort(key=lambda x: x[1], reverse=True)
        top_k = items[:k]

        n_relevant = sum(1 for _, _, true_r in items if true_r >= threshold)
        n_recommended_relevant = sum(
            1 for _, est, true_r in top_k if est >= threshold and true_r >= threshold
        )
        n_recommended = sum(1 for _, est, _ in top_k if est >= threshold)

        precision = n_recommended_relevant / n_recommended if n_recommended > 0 else 0
        recall = n_recommended_relevant / n_relevant if n_relevant > 0 else 0

        precisions.append(precision)
        recalls.append(recall)

    return {
        "precision@k": np.mean(precisions) if precisions else 0,
        "recall@k": np.mean(recalls) if recalls else 0,
    }


def ndcg_at_k(test_df: pd.DataFrame, pred_df: pd.DataFrame, k: int = 10) -> dict:
    """Normalized Discounted Cumulative Gain @ K."""
    ndcgs = []

    for uid in test_df["user_id"].unique():
        user_test = test_df[test_df["user_id"] == uid]
        if uid not in pred_df.index:
            continue

        items = []
        for _, row in user_test.iterrows():
            mid = int(row["movie_id"])
            if mid in pred_df.columns:
                items.append((np.clip(pred_df.loc[uid, mid], 1, 5), row["rating"]))

        if not items:
            continue

        # Sort by predicted rating
        items.sort(key=lambda x: x[0], reverse=True)
        top_k = items[:k]

        dcg = sum(true_r / np.log2(i + 2) for i, (_, true_r) in enumerate(top_k))
        ideal = sorted(items, key=lambda x: x[1], reverse=True)[:k]
        idcg = sum(true_r / np.log2(i + 2) for i, (_, true_r) in enumerate(ideal))

        ndcgs.append(dcg / idcg if idcg > 0 else 0)

    return {"ndcg@k": np.mean(ndcgs) if ndcgs else 0}


# ======================================================================
# Full Evaluation Pipeline
# ======================================================================

def evaluate_svd(ratings: pd.DataFrame, n_factors: int = 50,
                 test_size: float = 0.2, k: int = 10) -> dict:
    """Train SVD, evaluate on held-out test set with all metrics."""
    test_df, pred_df = _train_test_svd(ratings, n_factors=n_factors,
                                        test_size=test_size)

    metrics = compute_rmse_mae(test_df, pred_df)
    metrics.update(precision_recall_at_k(test_df, pred_df, k=k))
    metrics.update(ndcg_at_k(test_df, pred_df, k=k))

    print("=" * 50)
    print(f"EVALUATION RESULTS (n_factors={n_factors}, k={k})")
    print("=" * 50)
    for name, value in metrics.items():
        print(f"  {name:15s}: {value:.4f}")

    return metrics


# ======================================================================
# Hyper-parameter Optimization
# ======================================================================

def optimize_svd(ratings: pd.DataFrame, test_size: float = 0.2) -> dict:
    """
    Search over n_factors values to find the one with lowest RMSE.
    """
    candidates = [10, 20, 50, 100, 150]
    print("Searching over n_factors:", candidates)
    best_rmse = float("inf")
    best_k = candidates[0]
    results = []

    for n_factors in candidates:
        test_df, pred_df = _train_test_svd(ratings, n_factors=n_factors,
                                            test_size=test_size)
        m = compute_rmse_mae(test_df, pred_df)
        results.append({"n_factors": n_factors, "rmse": m["rmse"], "mae": m["mae"]})
        print(f"  n_factors={n_factors:4d}  RMSE={m['rmse']:.4f}  MAE={m['mae']:.4f}")
        if m["rmse"] < best_rmse:
            best_rmse = m["rmse"]
            best_k = n_factors

    print(f"\nBest n_factors = {best_k} (RMSE = {best_rmse:.4f})")
    return {"best_n_factors": best_k, "best_rmse": best_rmse, "all_results": results}

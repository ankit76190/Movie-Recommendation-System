"""
eda.py
------
Exploratory Data Analysis on MovieLens 100K dataset.
Generates visualizations and prints summary statistics for user-item interactions.

Run standalone:  python eda.py
"""

import os
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for saving figures
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

from data_loader import load_all, build_user_item_matrix

FIGURES_DIR = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)


def dataset_summary(ratings: pd.DataFrame, movies: pd.DataFrame, users: pd.DataFrame):
    """Print high-level dataset statistics."""
    print("=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)
    print(f"Total ratings     : {len(ratings):,}")
    print(f"Unique users      : {ratings['user_id'].nunique()}")
    print(f"Unique movies     : {ratings['movie_id'].nunique()}")
    print(f"Rating range      : {ratings['rating'].min()} – {ratings['rating'].max()}")
    print(f"Mean rating       : {ratings['rating'].mean():.2f}")
    print(f"Median rating     : {ratings['rating'].median():.1f}")
    sparsity = 1 - len(ratings) / (ratings["user_id"].nunique() * ratings["movie_id"].nunique())
    print(f"Sparsity          : {sparsity:.2%}")
    print()


def plot_rating_distribution(ratings: pd.DataFrame):
    """Bar chart of rating value counts."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ratings["rating"].value_counts().sort_index().plot(kind="bar", ax=ax, color="steelblue")
    ax.set_xlabel("Rating")
    ax.set_ylabel("Count")
    ax.set_title("Distribution of Ratings")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "rating_distribution.png"), dpi=150)
    plt.close(fig)
    print("Saved: figures/rating_distribution.png")


def plot_ratings_per_user(ratings: pd.DataFrame):
    """Histogram of how many ratings each user has given."""
    user_counts = ratings.groupby("user_id").size()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(user_counts, bins=50, color="coral", edgecolor="black")
    ax.set_xlabel("Number of Ratings")
    ax.set_ylabel("Number of Users")
    ax.set_title("Ratings per User")
    ax.axvline(user_counts.mean(), color="red", linestyle="--", label=f"Mean={user_counts.mean():.0f}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "ratings_per_user.png"), dpi=150)
    plt.close(fig)
    print("Saved: figures/ratings_per_user.png")


def plot_ratings_per_movie(ratings: pd.DataFrame):
    """Histogram of how many ratings each movie has received."""
    movie_counts = ratings.groupby("movie_id").size()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(movie_counts, bins=50, color="mediumseagreen", edgecolor="black")
    ax.set_xlabel("Number of Ratings")
    ax.set_ylabel("Number of Movies")
    ax.set_title("Ratings per Movie")
    ax.axvline(movie_counts.mean(), color="red", linestyle="--", label=f"Mean={movie_counts.mean():.0f}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "ratings_per_movie.png"), dpi=150)
    plt.close(fig)
    print("Saved: figures/ratings_per_movie.png")


def plot_top_movies(ratings: pd.DataFrame, movies: pd.DataFrame, n: int = 20):
    """Bar chart of the top-n most-rated movies."""
    top = (
        ratings.groupby("movie_id")
        .agg(count=("rating", "size"), mean_rating=("rating", "mean"))
        .sort_values("count", ascending=False)
        .head(n)
    )
    top = top.merge(movies[["movie_id", "title"]], left_index=True, right_on="movie_id")
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(top["title"], top["count"], color="mediumpurple")
    ax.set_xlabel("Number of Ratings")
    ax.set_title(f"Top {n} Most Rated Movies")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "top_movies.png"), dpi=150)
    plt.close(fig)
    print("Saved: figures/top_movies.png")


def plot_genre_popularity(movies: pd.DataFrame, ratings: pd.DataFrame):
    """Bar chart showing total ratings per genre."""
    genre_cols = [
        "unknown", "Action", "Adventure", "Animation", "Children", "Comedy",
        "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror",
        "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western",
    ]
    merged = ratings.merge(movies[["movie_id"] + genre_cols], on="movie_id")
    genre_counts = merged[genre_cols].sum().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(8, 7))
    genre_counts.plot(kind="barh", ax=ax, color="goldenrod")
    ax.set_xlabel("Total Ratings")
    ax.set_title("Genre Popularity (by total ratings)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "genre_popularity.png"), dpi=150)
    plt.close(fig)
    print("Saved: figures/genre_popularity.png")


def plot_user_demographics(users: pd.DataFrame):
    """Age histogram and gender pie chart."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Age distribution
    axes[0].hist(users["age"], bins=30, color="skyblue", edgecolor="black")
    axes[0].set_xlabel("Age")
    axes[0].set_ylabel("Count")
    axes[0].set_title("User Age Distribution")

    # Gender split
    gender_counts = users["gender"].value_counts()
    axes[1].pie(gender_counts, labels=gender_counts.index, autopct="%1.1f%%",
                colors=["#66b3ff", "#ff9999"])
    axes[1].set_title("Gender Distribution")

    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "user_demographics.png"), dpi=150)
    plt.close(fig)
    print("Saved: figures/user_demographics.png")


def plot_rating_heatmap(ratings: pd.DataFrame):
    """Heatmap of a sample of the user-item matrix to visualize sparsity."""
    matrix = build_user_item_matrix(ratings)
    sample = matrix.iloc[:50, :50]  # 50 users × 50 movies
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(sample, cmap="YlOrRd", ax=ax, cbar_kws={"label": "Rating"})
    ax.set_xlabel("Movie ID")
    ax.set_ylabel("User ID")
    ax.set_title("User-Item Matrix Sample (50×50) — Sparsity Visualization")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "user_item_heatmap.png"), dpi=150)
    plt.close(fig)
    print("Saved: figures/user_item_heatmap.png")


def run_eda():
    """Run all EDA analyses."""
    ratings, movies, users = load_all()
    dataset_summary(ratings, movies, users)
    plot_rating_distribution(ratings)
    plot_ratings_per_user(ratings)
    plot_ratings_per_movie(ratings)
    plot_top_movies(ratings, movies)
    plot_genre_popularity(movies, ratings)
    plot_user_demographics(users)
    plot_rating_heatmap(ratings)
    print("\nAll EDA figures saved to figures/")


if __name__ == "__main__":
    run_eda()

"""
data_loader.py
--------------
Handles downloading, loading, and preprocessing the MovieLens 100K dataset.

MovieLens 100K contains:
  - 100,000 ratings (1-5) from 943 users on 1,682 movies
  - User demographic info (age, gender, occupation, zip)
  - Movie metadata (title, release date, genres)
"""

import os
import zipfile
import urllib.request
import pandas as pd
import numpy as np

DATASET_URL = "https://files.grouplens.org/datasets/movielens/ml-100k.zip"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
ZIP_PATH = os.path.join(DATA_DIR, "ml-100k.zip")
EXTRACT_DIR = os.path.join(DATA_DIR, "ml-100k")


def download_dataset():
    """Download the MovieLens 100K dataset if not already present."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.isdir(EXTRACT_DIR):
        print("Dataset already exists. Skipping download.")
        return
    print("Downloading MovieLens 100K dataset...")
    urllib.request.urlretrieve(DATASET_URL, ZIP_PATH)
    print("Extracting...")
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        zf.extractall(DATA_DIR)
    os.remove(ZIP_PATH)
    print("Done.")


def load_ratings() -> pd.DataFrame:
    """Load the ratings file (u.data) into a DataFrame."""
    path = os.path.join(EXTRACT_DIR, "u.data")
    ratings = pd.read_csv(
        path,
        sep="\t",
        names=["user_id", "movie_id", "rating", "timestamp"],
        encoding="latin-1",
    )
    ratings["timestamp"] = pd.to_datetime(ratings["timestamp"], unit="s")
    return ratings


def load_movies() -> pd.DataFrame:
    """Load the movies file (u.item) into a DataFrame."""
    genre_cols = [
        "unknown", "Action", "Adventure", "Animation", "Children", "Comedy",
        "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror",
        "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western",
    ]
    columns = [
        "movie_id", "title", "release_date", "video_release_date",
        "imdb_url",
    ] + genre_cols

    path = os.path.join(EXTRACT_DIR, "u.item")
    movies = pd.read_csv(
        path,
        sep="|",
        names=columns,
        encoding="latin-1",
    )
    movies["release_date"] = pd.to_datetime(movies["release_date"], errors="coerce")
    movies.drop(columns=["video_release_date", "imdb_url"], inplace=True)
    return movies


def load_users() -> pd.DataFrame:
    """Load the users file (u.user) into a DataFrame."""
    path = os.path.join(EXTRACT_DIR, "u.user")
    users = pd.read_csv(
        path,
        sep="|",
        names=["user_id", "age", "gender", "occupation", "zip_code"],
        encoding="latin-1",
    )
    return users


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------

def preprocess_ratings(ratings: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values and basic cleaning for ratings."""
    df = ratings.copy()
    df.dropna(subset=["user_id", "movie_id", "rating"], inplace=True)
    df["user_id"] = df["user_id"].astype(int)
    df["movie_id"] = df["movie_id"].astype(int)
    df["rating"] = df["rating"].astype(float)
    return df


def preprocess_movies(movies: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values and extract year from title."""
    df = movies.copy()
    # Extract year from title like "Toy Story (1995)"
    df["year"] = df["title"].str.extract(r"\((\d{4})\)").astype(float)
    # Fill missing release dates with extracted year
    df["release_date"] = df["release_date"].fillna(
        pd.to_datetime(df["year"], format="%Y", errors="coerce")
    )
    return df


def build_user_item_matrix(ratings: pd.DataFrame) -> pd.DataFrame:
    """
    Build a user-item rating matrix (users × movies).
    Missing ratings are filled with 0.
    """
    matrix = ratings.pivot_table(
        index="user_id", columns="movie_id", values="rating", fill_value=0
    )
    return matrix


def normalize_ratings(matrix: pd.DataFrame) -> pd.DataFrame:
    """Mean-center the user-item matrix (subtract each user's mean rating)."""
    user_mean = matrix.replace(0, np.nan).mean(axis=1)
    normalized = matrix.sub(user_mean, axis=0).fillna(0)
    return normalized


# ---------------------------------------------------------------------------
# Convenience loader
# ---------------------------------------------------------------------------

def load_all():
    """Download (if needed) and return preprocessed DataFrames."""
    download_dataset()
    ratings = preprocess_ratings(load_ratings())
    movies = preprocess_movies(load_movies())
    users = load_users()
    return ratings, movies, users

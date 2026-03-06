# Movie Recommendation System

A comprehensive movie recommendation system built as a **Data Science Minor Project** using the **MovieLens 100K** dataset. Implements three recommendation approaches: Content-Based Filtering, User-Based Collaborative Filtering, and SVD-based Matrix Factorization.

---

## Project Structure

```
Movie Recommendation System/
├── main.py              # Main entry point — runs full pipeline
├── data_loader.py       # Dataset download, loading & preprocessing
├── eda.py               # Exploratory Data Analysis & visualizations
├── recommender.py       # Recommendation engines (3 approaches)
├── evaluation.py        # Metrics (RMSE, MAE, Precision@K, NDCG@K) & optimization
├── requirements.txt     # Python dependencies
├── README.md            # Project documentation (this file)
├── data/                # Auto-created: MovieLens dataset (downloaded at runtime)
└── figures/             # Auto-created: EDA visualizations
```

## Dataset

| Detail          | Value                                                                          |
|-----------------|--------------------------------------------------------------------------------|
| **Name**        | MovieLens 100K                                                                 |
| **Source**      | [GroupLens Research](https://grouplens.org/datasets/movielens/100k/)            |
| **Kaggle**      | [movielens-100k-dataset](https://www.kaggle.com/datasets/grouplens/movielens-100k-dataset) |
| **Size**        | 100,000 ratings from 943 users on 1,682 movies                                |
| **Rating Scale**| 1–5 (integer)                                                                  |
| **Sparsity**    | ~93.7%                                                                         |

The dataset is **auto-downloaded** on first run — no manual download needed.

---

## Setup & Installation

```bash
# 1. Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the full pipeline
python main.py

# Run without grid search (faster):
python main.py --skip-optimize
```

### Dependencies

- Python 3.8+
- pandas, numpy
- scikit-learn
- scikit-surprise
- matplotlib, seaborn

---

## Approach

### 1. Content-Based Filtering
- Represents each movie as a **binary genre vector** (19 genres).
- Computes **cosine similarity** between movie genre profiles.
- For a user, aggregates genre similarity scores weighted by their past ratings.
- **Strength**: No cold-start for items; transparent reasoning.
- **Weakness**: Limited by metadata quality (genres only, no plot/actors).

### 2. User-Based Collaborative Filtering
- Builds a **user-item rating matrix** (943 × 1682).
- **Mean-centers** ratings to remove user bias.
- Computes **user-user cosine similarity**.
- Predictions via **weighted k-NN**: averages neighbors' ratings weighted by similarity.
- **Strength**: Captures nuanced preferences beyond genres.
- **Weakness**: Memory-intensive; doesn't scale well to millions of users.

### 3. SVD Matrix Factorization (scipy)
- Decomposes the mean-centered user-item matrix via **truncated SVD** (`scipy.sparse.linalg.svds`).
- Learns `n_factors` latent dimensions for each user and movie.
- Reconstructs full predicted rating matrix as R ≈ U·Σ·Vᵀ + user_means.
- **Strength**: Best predictive accuracy; scales well; no extra library needed.
- **Weakness**: Less interpretable; cold-start for new users/items.

---

## Pipeline Steps (10 Points)

| # | Step                          | Module           | Description |
|---|-------------------------------|------------------|-------------|
| 1 | Define recommendation type    | `recommender.py` | Content-based + collaborative filtering |
| 2 | Collect movie data            | `data_loader.py` | Auto-downloads MovieLens 100K |
| 3 | Preprocess data               | `data_loader.py` | Missing values, normalization, matrix construction |
| 4 | Exploratory Data Analysis     | `eda.py`         | 7 visualization types + summary statistics |
| 5 | Model user behavior           | `recommender.py` | Cosine similarity on user/item vectors |
| 6 | Build recommendation engine   | `recommender.py` | 3 algorithms: Content-based, User-CF, SVD |
| 7 | Generate recommendations      | `main.py`        | Personalized top-N for any user |
| 8 | Evaluate recommendations      | `evaluation.py`  | RMSE, MAE, Precision@K, Recall@K, NDCG@K |
| 9 | Optimize for scalability      | `evaluation.py`  | Grid search over SVD hyper-parameters |
|10 | Document system               | `README.md`      | Design, approach, limitations |

---

## Evaluation Metrics

| Metric         | Description                                          |
|----------------|------------------------------------------------------|
| **RMSE**       | Root Mean Squared Error of predicted vs actual rating |
| **MAE**        | Mean Absolute Error of predictions                   |
| **Precision@K**| Fraction of top-K recommendations that are relevant  |
| **Recall@K**   | Fraction of relevant items found in top-K            |
| **NDCG@K**     | Normalized Discounted Cumulative Gain (ranking quality) |

---

## EDA Visualizations

Running `python eda.py` or the full pipeline generates these plots in `figures/`:

- `rating_distribution.png` — Distribution of rating values
- `ratings_per_user.png` — How many ratings each user gave
- `ratings_per_movie.png` — How many ratings each movie received
- `top_movies.png` — Top 20 most-rated movies
- `genre_popularity.png` — Total ratings per genre
- `user_demographics.png` — Age & gender distributions
- `user_item_heatmap.png` — Sparsity visualization (50×50 sample)

---

## Limitations

1. **Cold-start problem** — Cannot recommend for new users with no rating history, or new movies with no ratings.
2. **Sparsity** — 93.7% of the user-item matrix is empty, limiting collaborative filtering accuracy.
3. **Limited metadata** — Content-based approach uses only genre tags; richer features (plot, cast, directors) would improve quality.
4. **Explicit feedback only** — Only uses star ratings; implicit signals (clicks, watch time) are ignored.
5. **Static model** — No online learning; must retrain to incorporate new ratings.
6. **Scalability** — User-based CF is O(n²) in users; for production, item-based CF or ALS would be preferred.

---

## References

- [Surprise Library (NicolasHug/Surprise)](https://github.com/NicolasHug/Surprise)
- [Movie Recommendation System (llSourcell)](https://github.com/llSourcell/Movie-Recommendation-System)
- [Implicit Collaborative Filtering (benfred/implicit)](https://github.com/benfred/implicit)
- [GroupLens Research — MovieLens](https://grouplens.org/datasets/movielens/)

---

## Tools & Platforms

- **Language**: Python 3.8+
- **Libraries**: Pandas, NumPy, Scikit-learn, SciPy, Matplotlib, Seaborn
- **Dataset**: MovieLens 100K (GroupLens / Kaggle)

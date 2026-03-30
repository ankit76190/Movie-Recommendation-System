# Movie Recommendation System

A **production-grade** movie recommendation system with a Flask REST API backend, ReactJS frontend, SQLite database, and three recommendation algorithms (Content-Based, User-Based Collaborative Filtering, SVD Matrix Factorisation).

---

## Project Structure

```
Movie-Recommendation-System/
│
├── backend/                    # Flask REST API
│   ├── app.py                  # Application factory
│   ├── config.py               # Dev / Test / Prod configuration
│   ├── extensions.py           # SQLAlchemy + CORS instances
│   ├── models.py               # ORM models: Movie, User, WatchlistEntry, Rating
│   ├── routes/
│   │   ├── movies.py           # GET/POST /api/movies, POST /api/movies/import
│   │   ├── recommendations.py  # GET /api/recommendations/<user_id>
│   │   ├── watchlist.py        # GET/POST/DELETE /api/watchlist/<username>
│   │   └── export.py           # GET /api/export/watchlist/<username>
│   ├── services/
│   │   └── recommender_service.py  # Cached recommendation engine wrapper
│   ├── seed.py                 # Populate DB with sample_movies.csv + demo users
│   ├── test_api.py             # 37 unit tests for the REST API
│   └── requirements.txt        # Python dependencies (Flask, SQLAlchemy, …)
│
├── frontend/                   # ReactJS single-page application
│   ├── public/index.html
│   ├── package.json
│   └── src/
│       ├── App.js              # Root component (tab navigation, user selector)
│       ├── App.css             # Dark-mode styles
│       ├── index.js            # React entry point
│       ├── components/
│       │   ├── MovieList.jsx       # Paginated, searchable movie browser
│       │   ├── Recommendations.jsx # ML + genre-based recommendations
│       │   ├── Watchlist.jsx       # Watchlist viewer + CSV export button
│       │   └── ImportMovies.jsx    # Drag-and-drop CSV upload + manual add
│       └── services/
│           └── api.js              # Fetch-based API client
│
├── data/
│   └── sample_movies.csv       # 110 sample movies for initial seeding
│
├── main.py              # CLI entry point — runs full ML pipeline
├── data_loader.py       # Dataset download, loading & preprocessing
├── eda.py               # Exploratory Data Analysis & visualizations
├── recommender.py       # Recommendation engines (3 algorithms)
├── evaluation.py        # Metrics (RMSE, MAE, Precision@K, NDCG@K) & optimisation
├── test_recommender.py  # Unit tests for ML recommendation algorithms
└── requirements.txt     # Root Python dependencies (for ML pipeline only)
```

---

## Quick Start

### 1 — Backend

```bash
# Install backend dependencies
pip install -r backend/requirements.txt

# (Optional) Seed the database with sample movies and demo users
cd backend
python seed.py
cd ..

# Start the Flask development server (port 5000)
cd backend
python app.py
```

The API is now running at **http://localhost:5000**.

### 2 — Frontend

```bash
cd frontend
npm install
npm start          # Opens http://localhost:3000
```

The React app proxies all `/api/*` calls to `localhost:5000`.

### 3 — (Optional) Download the MovieLens Dataset for ML recommendations

ML-powered recommendations (SVD, Collaborative Filtering, Content-Based) require the MovieLens 100K dataset. Download it once with:

```bash
python data_loader.py
```

The ~5 MB zip is extracted to `data/ml-100k/` automatically.  
Genre-based recommendations work without the dataset.

### 4 — Run the full ML pipeline (CLI)

```bash
pip install -r requirements.txt
python main.py              # Full pipeline with hyper-parameter optimisation
python main.py --skip-optimize   # Faster — skip grid search
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/api/movies` | List movies (paginated, searchable) |
| GET | `/api/movies/<id>` | Get a single movie |
| POST | `/api/movies` | Create a movie (JSON body) |
| POST | `/api/movies/import` | Bulk-import movies from CSV upload |
| GET | `/api/movies/movielens` | Browse ML-100K catalogue (requires dataset) |
| GET | `/api/users` | List all users |
| POST | `/api/users` | Create a user |
| GET | `/api/watchlist/<username>` | Get user's watchlist |
| POST | `/api/watchlist/<username>` | Add movie to watchlist |
| DELETE | `/api/watchlist/<username>/<movie_id>` | Remove movie from watchlist |
| GET | `/api/export/watchlist/<username>` | **Download** watchlist as CSV |
| GET | `/api/recommendations/<user_id>` | ML recommendations (`?method=svd\|collaborative\|content`) |
| GET | `/api/recommendations/similar/<movie_id>` | Movies similar to a given movie |
| GET | `/api/recommendations/genre` | Genre-based recommendations (`?genres=Action,Drama`) |

### Query parameters

- `?page=1&per_page=20` — Pagination (all list endpoints)
- `?q=Matrix` — Title search (movie list)
- `?method=svd&n=10` — Recommendation algorithm and result count

---

## Database Schema

```
movies          – id, movielens_id, title, year, genres, avg_rating, imdb_url
users           – id, username, movielens_user_id, created_at
watchlist       – id, user_id, movie_id, added_at, notes
ratings         – id, user_id, movie_id, rating, rated_at
```

SQLite is used by default.  
Set `DATABASE_URL=postgresql://...` in the environment to switch to PostgreSQL/MySQL.

---

## Running Tests

```bash
# Flask API tests (37 tests, no dataset required)
cd backend
python -m pytest test_api.py -v

# ML recommendation engine tests (requires dataset download)
python test_recommender.py
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | `development` / `testing` / `production` |
| `SECRET_KEY` | `change-me-in-production` | Flask secret key |
| `DATABASE_URL` | `sqlite:///movies_dev.db` | Database connection string |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `PORT` | `5000` | Backend server port |
| `REACT_APP_API_URL` | `http://localhost:5000` | Frontend → API base URL |

---

## Dataset

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

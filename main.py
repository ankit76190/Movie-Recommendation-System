"""
main.py
-------
Main entry point for the Movie Recommendation System.
Runs the full pipeline:
  1. Load & preprocess data
  2. Exploratory Data Analysis
  3. Build recommendation engines (Content-Based, User-Based CF, SVD)
  4. Generate personalized recommendations
  5. Evaluate with accuracy metrics
  6. Optimize hyper-parameters
"""

import sys
from data_loader import load_all
from eda import run_eda
from recommender import ContentBasedRecommender, UserBasedCF, SVDRecommender
from evaluation import evaluate_svd, optimize_svd

DEMO_USER_ID = 1


def separator(title: str):
    print("\n" + "=" * 64)
    print(f"  {title}")
    print("=" * 64 + "\n")


def main():
    # ------------------------------------------------------------------
    # Step 1-3: Load, preprocess, and explore data
    # ------------------------------------------------------------------
    separator("STEP 1-3: DATA LOADING, PREPROCESSING & EDA")
    ratings, movies, users = load_all()
    print(f"Loaded {len(ratings):,} ratings, {len(movies):,} movies, {len(users):,} users.\n")
    run_eda()

    # ------------------------------------------------------------------
    # Step 4: Content-Based Filtering
    # ------------------------------------------------------------------
    separator("STEP 4: CONTENT-BASED RECOMMENDATIONS")
    cb = ContentBasedRecommender(movies, ratings)

    print("Movies similar to 'Star Wars (1977)':")
    print(cb.similar_movies(50, n=10).to_string(index=False))

    print(f"\nContent-Based Recommendations for User {DEMO_USER_ID}:")
    cb_recs = cb.recommend(DEMO_USER_ID, n=10)
    print(cb_recs.to_string(index=False))

    # ------------------------------------------------------------------
    # Step 5: User-Based Collaborative Filtering
    # ------------------------------------------------------------------
    separator("STEP 5: USER-BASED COLLABORATIVE FILTERING")
    ubcf = UserBasedCF(ratings, movies)
    print(f"Top similar users to User {DEMO_USER_ID}:")
    print(ubcf.similar_users(DEMO_USER_ID, n=5).to_string())

    print(f"\nUser-Based CF Recommendations for User {DEMO_USER_ID}:")
    ubcf_recs = ubcf.recommend(DEMO_USER_ID, n=10)
    print(ubcf_recs.to_string(index=False))

    # ------------------------------------------------------------------
    # Step 6: SVD Model-Based Collaborative Filtering
    # ------------------------------------------------------------------
    separator("STEP 6: SVD MODEL-BASED COLLABORATIVE FILTERING")
    svd_rec = SVDRecommender(ratings, movies, n_factors=50)
    svd_rec.fit()

    print(f"\nSVD Recommendations for User {DEMO_USER_ID}:")
    svd_recs = svd_rec.recommend(DEMO_USER_ID, n=10)
    print(svd_recs.to_string(index=False))

    # Evaluate SVD with train/test split
    print("\nSVD Train/Test Evaluation:")
    svd_eval = svd_rec.evaluate(test_size=0.2)
    print(f"  RMSE: {svd_eval['rmse']:.4f}")
    print(f"  MAE : {svd_eval['mae']:.4f}")
    print(f"  Test samples: {svd_eval['n_test']}")

    # ------------------------------------------------------------------
    # Step 7-8: Full Evaluation with all metrics
    # ------------------------------------------------------------------
    separator("STEP 7-8: EVALUATION METRICS")
    eval_metrics = evaluate_svd(ratings, n_factors=50, k=10)

    # ------------------------------------------------------------------
    # Step 9: Optimization
    # ------------------------------------------------------------------
    separator("STEP 9: HYPER-PARAMETER OPTIMIZATION")
    if "--skip-optimize" in sys.argv:
        print("Skipping optimization (run without --skip-optimize to enable).")
    else:
        best = optimize_svd(ratings)
        print(f"\nRe-training SVD with optimal n_factors={best['best_n_factors']}...")
        opt_svd = SVDRecommender(ratings, movies, n_factors=best["best_n_factors"])
        opt_svd.fit()
        print(f"\nOptimized SVD Recommendations for User {DEMO_USER_ID}:")
        print(opt_svd.recommend(DEMO_USER_ID, n=10).to_string(index=False))

    # ------------------------------------------------------------------
    # Step 10: Summary
    # ------------------------------------------------------------------
    separator("STEP 10: SYSTEM SUMMARY")
    print("""
    Movie Recommendation System — Summary
    ======================================

    Three recommendation approaches implemented:

    1. CONTENT-BASED FILTERING
       - Uses movie genre vectors (19 binary features)
       - Cosine similarity between genre profiles
       - Recommends movies matching user's taste profile

    2. USER-BASED COLLABORATIVE FILTERING
       - Builds user-item rating matrix (943 x 1682)
       - Mean-centered normalization to remove user bias
       - Cosine similarity for user-user similarity
       - Weighted k-NN prediction of unseen ratings

    3. SVD MATRIX FACTORIZATION (scipy)
       - Truncated SVD on mean-centered user-item matrix
       - Learns latent factors for users & items
       - Best accuracy (lowest RMSE) among all methods

    Evaluation Metrics Used:
       - RMSE, MAE, Precision@K, Recall@K, NDCG@K

    Scalability:
       - SVD is the most scalable (constant time per prediction)
       - User-based CF is memory-intensive for large datasets
       - Content-based is fast but limited by metadata quality

    Limitations:
       - Cold-start problem for new users/movies
       - Collaborative filtering needs sufficient rating density
       - Content-based limited to genre metadata (no plot/actors)
       - No implicit feedback (only explicit ratings used)
    """)
    print("Done! Check the 'figures/' folder for EDA visualizations.")


if __name__ == "__main__":
    main()

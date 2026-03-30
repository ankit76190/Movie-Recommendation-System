"""
app.py
------
Flask application factory.

Usage
-----
Development:
    export FLASK_ENV=development
    python app.py

Or with the Flask CLI:
    flask --app backend.app run --debug
"""

import os
from flask import Flask, jsonify
from config import config_map
from extensions import db, cors
from routes.movies import movies_bp
from routes.recommendations import recommendations_bp
from routes.watchlist import watchlist_bp
from routes.export import export_bp


def create_app(env: str | None = None) -> Flask:
    """Application factory – creates and configures the Flask app."""
    if env is None:
        env = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_map.get(env, config_map["development"]))

    # ---------------------------------------------------------------------------
    # Extensions
    # ---------------------------------------------------------------------------
    db.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

    # ---------------------------------------------------------------------------
    # Blueprints
    # ---------------------------------------------------------------------------
    app.register_blueprint(movies_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(watchlist_bp)
    app.register_blueprint(export_bp)

    # ---------------------------------------------------------------------------
    # Database initialisation
    # ---------------------------------------------------------------------------
    with app.app_context():
        db.create_all()

    # ---------------------------------------------------------------------------
    # Health-check / root route
    # ---------------------------------------------------------------------------
    @app.get("/")
    def health():
        return jsonify(
            {
                "status": "ok",
                "service": "Movie Recommendation System API",
                "version": "1.0.0",
            }
        )

    # ---------------------------------------------------------------------------
    # Generic error handlers
    # ---------------------------------------------------------------------------
    @app.errorhandler(404)
    def not_found(exc):
        return jsonify({"error": str(exc) or "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(exc):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(exc):
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    application = create_app()
    port = int(os.environ.get("PORT", 5000))
    application.run(host="0.0.0.0", port=port)

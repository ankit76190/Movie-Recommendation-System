"""
config.py
---------
Configuration classes for the Flask application.

Three environments are supported:
  - DevelopmentConfig  (default) – SQLite, debug on
  - TestingConfig                – in-memory SQLite, testing on
  - ProductionConfig             – reads DATABASE_URL from env (PostgreSQL/MySQL)

Usage in app factory:
    app.config.from_object(config_map[os.getenv("FLASK_ENV", "development")])
"""

import os


class Config:
    """Base configuration shared by all environments."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    # Recommendation engine
    DEFAULT_N_RECOMMENDATIONS = 10
    # CORS allowed origins (override in production)
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///movies_dev.db",
    )


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    # Expects DATABASE_URL= postgres://... or mysql://... in production env
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///movies.db")


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}

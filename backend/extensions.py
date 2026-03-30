"""
extensions.py
-------------
Flask extension instances (created once, initialised in app factory).
"""

from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()
cors = CORS()

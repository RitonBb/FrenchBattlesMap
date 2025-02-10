import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import inspect

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask extensions
db = SQLAlchemy(model_class=Base)

# Configure caching
cache_config = {
    'CACHE_TYPE': 'simple',  # Using simple cache for development
    'CACHE_DEFAULT_TIMEOUT': 300,  # Default timeout in seconds
    'CACHE_THRESHOLD': 1000,  # Maximum number of items in the cache
    'CACHE_KEY_PREFIX': 'battles_',  # Prefix for all cache keys
}
cache = Cache(config=cache_config)

# Create Flask app
app = Flask(__name__)

# Configure app
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "historical-battles-secret-key")
# Use SQLite database with absolute path
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///battles.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions with app
db.init_app(app)
cache.init_app(app)

# Import routes after app creation to avoid circular imports
with app.app_context():
    logging.info("Creating database tables...")
    try:
        import models  # Import models to ensure they are registered
        # Check if tables need to be created using inspector
        inspector = inspect(db.engine)
        if not inspector.has_table("battle"):
            # Create all tables with new schema
            db.create_all()
            logging.info("Database tables created successfully")

            # Import routes and initialize database with mock data
            import routes  # noqa: F401
            routes.init_db()  # Initialize database with mock data
        else:
            logging.info("Tables already exist, skipping creation")
            import routes  # noqa: F401
    except Exception as e:
        logging.error(f"Error creating database: {str(e)}")
        raise
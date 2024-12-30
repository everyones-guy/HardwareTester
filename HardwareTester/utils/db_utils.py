import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, IntegrityError, SQLAlchemyError
from HardwareTester.models import Base
#from HardwareTester.models import db
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DatabaseUtils")

def get_database_url():
    """
    Fetch the database URL from environment variables.
    Fallback to SQLite for local development if not set.
    """
    return os.getenv("DATABASE_URL", "sqlite:///app.db")

# New function to initialize the database
def initialize_database(app):
    """
    Initialize the database for the given Flask app.
    This function creates all necessary tables if they don't already exist.
    """
    try:
        with app.app_context():
            Base.create_all()
            print("Database initialized successfully.")
    except SQLAlchemyError as e:
        print(f"Error initializing database: {e}")

class DatabaseManager:
    def __init__(self, db_url=None):
        self.db_url = db_url or get_database_url()
        self.engine = create_engine(self.db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        logger.info(f"Database connected: {self.db_url}")

    def create_tables(self):
        """Create all tables defined in models."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("All tables created successfully.")
        except OperationalError as e:
            logger.error(f"Error creating tables: {e}")

    def drop_tables(self):
        """Drop all tables defined in models."""
        try:
            Base.metadata.drop_all(self.engine)
            logger.info("All tables dropped successfully.")
        except OperationalError as e:
            logger.error(f"Error dropping tables: {e}")

    def reset_database(self):
        """Drop and recreate the database schema."""
        self.drop_tables()
        self.create_tables()

    def get_session(self):
        """Get a new database session."""
        return self.Session()

    def inspect_database(self):
        """Inspect the current database schema."""
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        logger.info(f"Current tables: {tables}")
        return tables

    def add_record(self, record):
        """Add a single record to the database."""
        session = self.get_session()
        try:
            session.add(record)
            session.commit()
            logger.info(f"Record added: {record}")
        except IntegrityError as e:
            session.rollback()
            logger.error(f"Failed to add record: {e}")
        finally:
            session.close()

    def query_records(self, model, filters=None):
        """
        Query records from the database.
        :param model: SQLAlchemy model to query.
        :param filters: Dictionary of filters to apply (e.g., {"id": 1}).
        """
        session = self.get_session()
        try:
            query = session.query(model)
            if filters:
                query = query.filter_by(**filters)
            results = query.all()
            logger.info(f"Records queried: {results}")
            return results
        except Exception as e:
            logger.error(f"Failed to query records: {e}")
            return []
        finally:
            session.close()

    # function to initialize the database
    def initialize_database(app):
        """
        Initialize the database for the given Flask app.
        This function creates all necessary tables if they don't already exist.
        """
        try:
            with app.app_context():
                db.create_all()
                print("Database initialized successfully.")
        except SQLAlchemyError as e:
            print(f"Error initializing database: {e}")
    

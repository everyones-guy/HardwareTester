import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, IntegrityError, SQLAlchemyError
from HardwareTester.extensions import db
from HardwareTester.utils.custom_logger import CustomLogger
from contextlib import contextmanager

# Logging configuration
logger = CustomLogger.get_logger("DatabaseUtils")

def get_database_url() -> str:
    """
    Fetch the database URL from environment variables.
    Fallback to SQLite for local development if not set.
    """
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/hardware_tester")
    if db_url.startswith("sqlite:///") and not os.path.exists(db_url.replace("sqlite:///", "")):
        logger.warning("SQLite database file does not exist; it will be created if needed.")
    return db_url

def initialize_database(app) -> None:
    """
    Initialize the database for the given Flask app.
    Creates all necessary tables if they don't already exist.
    """
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database initialized successfully.")
    except SQLAlchemyError as e:
        logger.error(f"Error initializing database: {e}")
        raise e

class DatabaseManager:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or get_database_url()
        self.engine = create_engine(self.db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        logger.info(f"Database connected: {self.db_url}")

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope for a database session."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction error: {e}")
            raise
        finally:
            session.close()

    def create_tables(self) -> None:
        """Create all tables defined in models."""
        try:
            db.metadata.create_all(self.engine)
            logger.info("All tables created successfully.")
        except OperationalError as e:
            logger.error(f"Error creating tables: {e}")

    def drop_tables(self) -> None:
        """Drop all tables defined in models."""
        try:
            db.metadata.drop_all(self.engine)
            logger.info("All tables dropped successfully.")
        except OperationalError as e:
            logger.error(f"Error dropping tables: {e}")

    def reset_database(self) -> None:
        """Drop and recreate the database schema."""
        self.drop_tables()
        self.create_tables()

    def inspect_database(self) -> list:
        """Inspect the current database schema."""
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        logger.info(f"Current tables: {tables}")
        return tables

    def add_record(self, record) -> None:
        """Add a single record to the database."""
        with self.session_scope() as session:
            session.add(record)
            logger.info(f"Record added: {record}")

    def query_records(self, model, filters: dict = None) -> list:
        """
        Query records from the database.
        :param model: SQLAlchemy model to query.
        :param filters: Dictionary of filters to apply (e.g., {"id": 1}).
        """
        with self.session_scope() as session:
            query = session.query(model)
            if filters:
                query = query.filter_by(**filters)
            results = query.all()
            logger.info(f"Records queried: {results}")
            return results

    def delete_record(self, model, filters: dict) -> None:
        """Delete records from the database."""
        with self.session_scope() as session:
            query = session.query(model).filter_by(**filters)
            deleted_count = query.delete()
            logger.info(f"{deleted_count} record(s) deleted with filters: {filters}")

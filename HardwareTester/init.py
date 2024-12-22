from HardwareTester.utils.db_utils import DatabaseManager

def initialize_database():
    db_manager = DatabaseManager()
    db_manager.create_tables()
    return db_manager


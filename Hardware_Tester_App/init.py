from Hardware_Tester_App.utils.db_utils import DatabaseManager

def initialize_database(app):
    db_manager = DatabaseManager(app)
    db_manager.create_tables()
    return db_manager

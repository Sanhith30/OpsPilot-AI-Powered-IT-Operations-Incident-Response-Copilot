from sqlalchemy import text
def test_database_connection(db_session): assert db_session.execute(text("SELECT 1")).scalar_one()==1

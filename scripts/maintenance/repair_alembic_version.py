import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.begin() as conn:
    print(conn.execute(text("SELECT version_num FROM alembic_version")).fetchall())
    conn.execute(text("DELETE FROM alembic_version"))
    conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('e9cfea332822')"))
    print(conn.execute(text("SELECT version_num FROM alembic_version")).fetchall())

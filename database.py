# database.py
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import pool

load_dotenv()

_db_pool = None

def get_pool():
    """
    Initialize or retrieve a simple connection pool for PostgreSQL.
    """
    global _db_pool
    if _db_pool is None:
        dsn = os.getenv('DATABASE_URL')
        _db_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=dsn
        )
    return _db_pool


def fetch_user_purchases(user_id: int) -> list[dict]:
    """
    Retrieve user purchases from the database.
    Returns a list of dicts representing each purchase record.
    """
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM get_user_purchases(%s);", (user_id,))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
    finally:
        pool.putconn(conn)

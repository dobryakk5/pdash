import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import pool

load_dotenv()

_db_pool = None

def get_pool():
    global _db_pool
    if _db_pool is None:
        dsn = os.getenv('DATABASE_URL')
        _db_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=dsn
        )
    return _db_pool

def get_connection():
    """
    Берём одно соединение из пула.
    """
    return get_pool().getconn()

def fetch_user_purchases(user_id: int) -> list[dict]:
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM get_user_purchasesid(%s);", (user_id,))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
    finally:
        pool.putconn(conn)


def update_user_purchase(user_id: int, purchase_id: int, updates: dict):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            set_clause = ', '.join(f"{k} = %s" for k in updates)
            values = list(updates.values()) + [user_id, purchase_id]
            query = f"UPDATE purchases SET {set_clause} WHERE user_id = %s AND id = %s"
            cur.execute(query, values)
        conn.commit()
    except Exception as e:
        print("Ошибка при сохранении:", repr(e))

        
    finally:
        conn.close()

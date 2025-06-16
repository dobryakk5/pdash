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

def update_purchase(record: dict) -> None:
    """
    Обновляет запись покупки в базе по ключу 'id'.
    record: dict с ключами-именами колонок.
    """
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            purchase_id = record.get('id')
            if purchase_id is None:
                raise ValueError("Record missing 'id' field")
            # Формируем SET часть и параметры
            cols = [k for k in record.keys() if k != 'id']
            set_clause = ", ".join([f"{col} = %s" for col in cols])
            values = [record[col] for col in cols]
            # Добавляем id в параметры
            values.append(purchase_id)
            sql = f"UPDATE purchases SET {set_clause} WHERE id = %s"
            cur.execute(sql, tuple(values))
            conn.commit()
    finally:
        pool.putconn(conn)


def update_user_purchase(user_id: int, purchase_id: int, updates: dict):
    from . import get_connection  # или адаптируй под свою структуру
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            set_clause = ', '.join(f"{k} = %s" for k in updates)
            values = list(updates.values()) + [user_id, purchase_id]
            query = f"UPDATE purchases SET {set_clause} WHERE user_id = %s AND id = %s"
            cur.execute(query, values)
        conn.commit()
    finally:
        conn.close()

# pages/purchases.py
import dash
from dash import html, dcc, dash_table
import plotly.express as px
import pandas as pd
import asyncpg
import os
import asyncio
from dotenv import load_dotenv
from flask import session

# Загружаем DATABASE_URL из .env
load_dotenv()

# Глобальная переменная для пула соединений
_db_pool = None

async def get_pool():
    global _db_pool
    if _db_pool is None:
        dsn = os.getenv('DATABASE_URL')
        _db_pool = await asyncpg.create_pool(dsn)
    return _db_pool

dash.register_page(__name__)

def layout():
    user_id = session.get('user_id')
    if not user_id:
        return html.Div("Пожалуйста, войдите в систему, чтобы просмотреть аналитику.")
    
    # Создаем асинхронную функцию для получения данных
    async def fetch_data():
        pool = await get_pool()
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT id, category, subcategory, price, ts "
                "FROM purchases "
                "WHERE user_id = $1",
                user_id
            )
            return [dict(row) for row in rows]

    # Получаем данные синхронно через event loop
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        purchases_data = loop.run_until_complete(fetch_data())
    except Exception as e:
        return html.Div(f"Ошибка загрузки данных: {str(e)}")

    # Создаем таблицу с редактированием
    return html.Div([
        html.H1("Аналитика"),
        dash_table.DataTable(
            id='purchases-table',
            columns=[
                {"name": "ID", "id": "id", "editable": False},
                {"name": "Категория", "id": "category", "editable": True},
                {"name": "Подкатегория", "id": "subcategory", "editable": True},
                {"name": "Цена", "id": "price", "editable": True, 'type': 'numeric'},
                {"name": "Дата", "id": "ts", "editable": False}
            ],
            data=purchases_data,
            editable=True,
            style_table={'overflowX': 'auto'},
            style_cell={
                'height': 'auto',
                'minWidth': '100px', 'width': '150px', 'maxWidth': '200px',
                'whiteSpace': 'normal'
            },
            page_size=20
        )
    ])
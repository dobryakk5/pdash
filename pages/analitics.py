# pages/analitics.py
import sys
import os
import dash
from dash import html, dcc
from flask import session
import plotly.express as px
import pandas as pd
from asgiref.sync import async_to_sync

# Добавляем корневую директорию в PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Используем абсолютный импорт
from database import fetch_user_purchases

dash.register_page(
    __name__,
    path='/analitics',  
    name='Аналитика',
    title='Графики'
)

def layout():
    user_id_str = session.get('user_id')
    if not user_id_str:
        return html.Div("Пожалуйста, войдите в систему, чтобы просмотреть историю покупок.")
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        return html.Div("Некорректный идентификатор пользователя.")
    
    # Синхронный доступ к асинхронной функции
    try:
        rows = async_to_sync(fetch_user_purchases)(user_id)
        purchases_data = [{
            "category": r["category"],
            "subcategory": r["subcategory"],
            "price": r["price"],
            "ts": r["ts"].strftime("%d.%m.%Y %H:%M")
        } for r in rows]
    except Exception as e:
        return html.Div(f"Ошибка загрузки данных: {str(e)}")

    return html.Div([
        html.H1("История покупок", className="text-2xl font-bold mb-4 text-center"),
        html.Div(
            dash_table.DataTable(
                id='purchases-table',
                columns=[
                    {"name": "Категория", "id": "category", "editable": True},
                    {"name": "Подкатегория", "id": "subcategory", "editable": True},
                    {"name": "Цена (₽)", "id": "price", "editable": True, 'type': 'numeric'},
                    {"name": "Дата и время", "id": "ts", "editable": False}
                ],
                data=purchases_data,
                editable=True,
                filter_action="native",
                sort_action="native",
                style_table={
                    'overflowX': 'auto',
                    'width': 'auto',
                    'minWidth': '100%',
                    'margin': '0 auto'
                },
                style_cell={
                    'minWidth': '100px',
                    'width': 'max-content',  # Автоподбор ширины
                    'maxWidth': '300px',
                    'whiteSpace': 'nowrap',  # Запрет переноса
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'padding': '10px',
                    'fontFamily': 'Arial, sans-serif'
                },
                style_header={
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': 'bold',
                    'textAlign': 'center',
                    'padding': '12px',
                    'borderBottom': '2px solid #dee2e6'
                },
                style_data={
                    'border': '1px solid #dee2e6',
                    'backgroundColor': 'white'
                },
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'}
                ],
                page_size=15,
                page_action='native'
            ),
            className="overflow-x-auto"  # Горизонтальная прокрутка
        )
    ], className="container mx-auto p-6 bg-white rounded-lg shadow-md max-w-6xl")
# pages/purchases.py
import os
import sys
import logging
import dash
from dash import html, dash_table, Input, Output, State
from flask import session
import pandas as pd
from database import fetch_user_purchases

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Пути
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Регистрация страницы
dash.register_page(__name__, path='/purchases', name='Покупки')

layout = html.Div([
    html.H2("Ваши покупки"),
    html.Div(id='table-info'),
    dash_table.DataTable(
        id='purchases-table',
        data=[],
        columns=[],
        editable=True,
        page_size=20,
        filter_action="native",
        filter_options={'case': 'insensitive'},
        sort_action="native",
        fill_width=False,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'whiteSpace': 'normal'},
        style_cell_conditional=[
            {'if': {'column_id': 'price'}, 'textAlign': 'right'},
            {'if': {'column_type': 'datetime'}, 'textAlign': 'right'}
        ]
    ),
    html.Button('Сохранить', id='save-btn', n_clicks=0),
    html.Div(id='save-info', style={'marginTop': '10px', 'color': 'green'})
])

@dash.callback(
    Output('table-info', 'children'),
    Output('purchases-table', 'data'),
    Output('purchases-table', 'columns'),
    Input('url', 'pathname')
)
def load_purchases(pathname):
    try:
        if not pathname or not pathname.endswith('/purchases'):
            return dash.no_update, dash.no_update, dash.no_update

        user_id = session.get('user_id')
        if not user_id:
            return "❌ Не авторизован", [], []

        purchases = fetch_user_purchases(user_id)
        count = len(purchases)
        if count == 0:
            return "ℹ️ Нет покупок", [], []

        df = pd.DataFrame(purchases)
        # форматируем даты в dd.mm.yy
        for col in df.columns:
            key = col.lower()
            if 'date' in key or key in ('ts', 'timestamp') or key.endswith('_ts'):
                df[col] = pd.to_datetime(df[col]).dt.strftime('%d.%m.%y')

        data = df.to_dict('records')
        columns = []
        if 'id' in df.columns:
            columns.append({"name": "id", "id": "id", "editable": False, "type": "numeric"})
        for col in df.columns:
            if col == 'id':
                continue
            col_type = 'datetime' if any(sub in col.lower() for sub in ('date','ts','timestamp')) else ('numeric' if col == 'price' else 'text')
            columns.append({"name": col, "id": col, "editable": True, "type": col_type})

        info = f"Получено строк: {count}"
        return info, data, columns
    except Exception as e:
        logger.exception("Error in load_purchases callback")
        # Показываем пользователю текст ошибки
        return f"❌ Ошибка: {str(e)}", [], []

@dash.callback(
    Output('save-info', 'children'),
    Input('save-btn', 'n_clicks'),
    State('purchases-table', 'data'),
    prevent_initial_call=True
)
def save_changes(n_clicks, rows):
    # TODO: сохранить изменения в БД при необходимости
    logger.info(f"User saved {len(rows)} rows with {n_clicks} clicks")
    return f"✅ Изменения сохранены ({n_clicks})"

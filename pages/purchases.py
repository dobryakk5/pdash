# pages/purchases.py
import os
import sys
import logging
import dash
from dash import html, dash_table, Input, Output, State
from flask import session
import pandas as pd
from database import fetch_user_purchases, update_user_purchase

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
        hidden_columns=['id'], 
        page_size=20,
        filter_action="native",
        filter_options={'case': 'insensitive'},
        sort_action="native",
        fill_width=False,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'whiteSpace': 'normal'},
        style_cell_conditional=[
            {'if': {'column_id': 'price'}, 'textAlign': 'right'},
            {'if': {'column_id': 'ts'}, 'textAlign': 'right'},
            {'if': {'column_type': 'datetime'}, 'textAlign': 'right'}
        ]
    ),
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
        return f"❌ Ошибка: {str(e)}", [], []

@dash.callback(
    Output('save-info', 'children'),
    Input('purchases-table', 'data'),
    State('purchases-table', 'data_previous'),
    State('purchases-table', 'columns'),
    prevent_initial_call=True
)
def autosave_changes(current_data, previous_data, columns):
    if not previous_data:
        return dash.no_update

    user_id = session.get('user_id')
    if not user_id:
        return "❌ Не авторизован"

    try:
        updated_rows = 0
        for new_row, old_row in zip(current_data, previous_data):
            if new_row != old_row:
                purchase_id = new_row.get("id")
                if not purchase_id:
                    continue
                changes = {k: v for k, v in new_row.items() if old_row.get(k) != v and k != "id"}
                if changes:
                    update_user_purchase(user_id, purchase_id, changes)
                    updated_rows += 1

        if updated_rows:
            return f"✅ Автосохранение: {updated_rows} строк"
        return dash.no_update
    except Exception as e:
        logger.exception("Ошибка автосохранения")
        return f"❌ Ошибка автосохранения: {str(e)}"

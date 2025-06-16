# pages/purchases.py
import os, sys, logging, dash
from dash import html, dash_table, Input, Output
from flask import session
import pandas as pd
from database import fetch_user_purchases

# Для логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Подключаем корневую директорию
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

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
        sort_action="native",
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'}
    )
])

@dash.callback(
    Output('table-info', 'children'),
    Output('purchases-table', 'data'),
    Output('purchases-table', 'columns'),
    Input('url', 'pathname'),
)
def load_purchases(pathname):
    logger.info(f"Callback triggered for pathname={pathname!r}")
    if not pathname or not pathname.endswith('/purchases'):
        logger.info("Ignoring callback for other path.")
        return dash.no_update, dash.no_update, dash.no_update

    user_id = session.get('user_id')
    if not user_id:
        logger.warning("Пользователь не авторизован")
        return "❌ Пользователь не авторизован", [], []

    purchases = fetch_user_purchases(user_id)
    count = len(purchases)
    logger.info(f"Fetched {count} rows from the database")

    if count == 0:
        return "ℹ️ У вас пока нет покупок", [], []

    df = pd.DataFrame(purchases)
    data = df.to_dict('records')
    columns = [{"name": col, "id": col, "editable": True} for col in df.columns]
    info = f"Получено строк: {count}"

    return info, data, columns

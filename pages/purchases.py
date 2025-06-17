from dash import html, dash_table, Input, Output, State, no_update, register_page, callback
import pandas as pd
from flask import session
from pdash.database import fetch_user_purchases, update_user_purchase

# Регистрируем страницу в Dash Pages
register_page(__name__, path="/purchases", name="Purchases")

# Layout страницы: таблица заполняется сразу
layout = html.Div([
    html.H2("Мои покупки"),
    html.Div(id='row-count', style={'marginBottom': '1rem'}),
    dash_table.DataTable(
        id='purchases-table',
        data=[],
        columns=[],
        editable=True,
        hidden_columns=['id'],
        page_size=20,
        filter_action='native',
        filter_options={'case': 'insensitive'},
        sort_action='native',
        fill_width=False,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'whiteSpace': 'normal'},
        style_cell_conditional=[
            {'if': {'column_id': 'price'}, 'textAlign': 'right'},
            {'if': {'column_id': 'ts'}, 'textAlign': 'right'},
        ]
    ),
    html.Div(id='save-feedback', style={'marginTop': '1rem', 'color': 'green'})
])

# Callback: загрузка данных при рендере страницы
@callback(
    Output('purchases-table', 'data'),
    Output('purchases-table', 'columns'),
    Output('row-count', 'children'),
    Input('url', 'pathname')
)
def load_purchases(pathname):
    if not pathname.endswith('/purchases'):
        return no_update, no_update, ''

    user_id = session.get('user_id')
    if not user_id:
        return [], [], 'Получено записей: 0'

    # Получаем «сырые» данные — возможно, это список
    data_raw = fetch_user_purchases(user_id)

    # Если это список, превращаем в DataFrame
    if isinstance(data_raw, list):
        df = pd.DataFrame(data_raw)
    else:
        df = data_raw

    # Убеждаемся, что столбцы есть
    df = df[['id', 'category', 'subcategory', 'price', 'ts']]

    # Форматируем timestamp
    df['ts'] = pd.to_datetime(df['ts']).dt.strftime('%d.%m.%Y')

    records = df.to_dict('records')
    columns = [
        {'name': 'ID',          'id': 'id',          'hidden': True},
        {'name': 'Категория',    'id': 'category',    'editable': True},
        {'name': 'Подкатегория', 'id': 'subcategory', 'editable': True},
        {'name': 'Цена',       'id': 'price',       'type': 'numeric', 'editable': True},
        {'name': 'Дата',   'id': 'ts',          'type': 'datetime','editable': False},
    ]
    return records, columns, f"Получено записей: {len(records)}"

# Callback: автосохранение изменений всех полей
@callback(
    Output('save-feedback', 'children', allow_duplicate=True),
    Input('purchases-table', 'data_timestamp'),
    State('purchases-table', 'data'),
    State('purchases-table', 'data_previous'),
    prevent_initial_call=True
)
def autosave_changes(timestamp, current, previous):
    if previous is None:
        return no_update

    for new_row, old_row in zip(current, previous):
        if not new_row.get('id'):
            continue
        changes = {k: v for k, v in new_row.items()
                   if old_row.get(k) != v and k not in ('id', 'user_id', 'ts')}
        if changes:
            key, new_val = next(iter(changes.items()))
            old_val = old_row.get(key)
            update_user_purchase(session.get('user_id'), new_row['id'], {key: new_val})
            return f"Изменено: '{old_val}' --> '{new_val}'"
    return no_update

from dash import State, html, Input, Output, callback, register_page, no_update
from dash_ag_grid import AgGrid
import pandas as pd
from flask import session
from pdash.database import fetch_user_purchases, update_user_purchase
import dash_ag_grid as dag
from pdash.russian_aggrid_locale import LOCALE_RU

register_page(__name__, path="/purchases", name="Purchases")

layout = html.Div([
    html.H2("Мои покупки"),
    html.Div("Загрузка...", id='row-count', style={'marginBottom': '1rem'}),
    dag.AgGrid(
        id='purchases-table',
        columnDefs=[
            {'headerName': 'ID',          'field': 'id',          'hide': True},
            {'headerName': 'Категория',   'field': 'category',    'editable': True},
            {'headerName': 'Подкатегория','field': 'subcategory', 'editable': True},
            {'headerName': 'Цена',        'field': 'price',       'editable': True, 'type': 'rightAligned'},
            {'headerName': 'Дата',        'field': 'ts',          'editable': True},
        ],
        rowData=[],
        getRowId="params.data.id",
        defaultColDef={'resizable': True, 'sortable': True, 'filter': True},
        columnSize="sizeToFit",
        style={'height': '600px', 'width': '100%'},
        className="ag-theme-alpine",
        dashGridOptions={'localeText': LOCALE_RU},
    ),
    html.Div(id='save-feedback', style={'marginTop': '1rem', 'color': 'green'})
])

@callback(
    Output('purchases-table', 'rowData'),
    Output('row-count', 'children'),
    Input('url', 'pathname')
)
def load_data(pathname):
    if not pathname.endswith('/purchases'):
        return no_update, ''
    user_id = session.get('user_id')
    if not user_id:
        return [], 'Получено записей: 0'
    data = fetch_user_purchases(user_id)
    df = pd.DataFrame(data) if isinstance(data, list) else data
    df = df[['id', 'category', 'subcategory', 'price', 'ts']]
    df['ts'] = pd.to_datetime(df['ts']).dt.strftime('%Y-%m-%d')
    recs = df.to_dict('records')
    return recs, f"Получено записей: {len(recs)}"

@callback(
    Output('save-feedback', 'children', allow_duplicate=True),
    Output('purchases-table', 'rowTransaction'),
    Input('purchases-table', 'cellValueChanged'),
    prevent_initial_call=True
)
def autosave_cell(changes):
    user_id = session.get('user_id')
    if not isinstance(changes, list) or len(changes) == 0:
        return no_update, no_update
    ch = changes[0]
    old = ch.get('oldValue')
    new = ch.get('value')
    if new is None:
        return no_update, no_update
    field = ch.get('colId')
    data = ch.get('data', {})
    purchase_id = data.get('id')
    update_user_purchase(user_id, purchase_id, {field: new})
    msg = f"Изменено: '{old}' → '{new}'"
    return msg, {"update": [data]} 
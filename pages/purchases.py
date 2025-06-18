from dash import html, Input, Output, callback, register_page, no_update
import dash_ag_grid as dag
import pandas as pd
from flask import session
from pdash.database import fetch_user_purchases, update_user_purchase
from pdash.russian_aggrid_locale import LOCALE_RU

register_page(__name__, path="/purchases", name="Purchases")

layout = html.Div([
    html.H2("Мои покупки"),
    # Объединяем оба сообщения в один див:
    html.Div(id='message', style={'marginBottom': '1rem', 'color': 'green'}),
    dag.AgGrid(
        id='purchases-table',
        columnDefs=[
            {'headerName': 'ID',           'field': 'id',          'hide': True},
            {'headerName': 'Категория',    'field': 'category',    'editable': True, 'flex': 1, 'minWidth': 100},
            {'headerName': 'Подкатегория', 'field': 'subcategory', 'editable': True, 'flex': 1, 'minWidth': 250},
            {'headerName': 'Цена',         'field': 'price',       'editable': True, 'type': 'rightAligned', 'width': 80},
            {
              'headerName': 'Дата',
              'field': 'ts',
              'editable': True,
              'type': 'rightAligned',
              'minWidth': 110,
              'valueFormatter': {
                  "function": (
                    "(() => {"
                    "  if (!params.value) return '';"
                    "  const date = (params.value instanceof Date) ? params.value : new Date(params.value);"
                    "  return d3.timeFormat('%d.%m.%y')(date);"
                    "})()"
                  )
              },
              'filter': 'agDateColumnFilter',
              'filterParams': {'browserDatePicker': True}
            }
        ],
        columnSize="autoSize",
        columnSizeOptions={"skipHeader": False},
        dashGridOptions={
            'localeText': LOCALE_RU,
            'suppressColumnVirtualisation': True,
            'pagination': True,
            'paginationPageSize': 50,
        },
        rowData=[],
        getRowId="params.data.id",
        defaultColDef={'resizable': True, 'sortable': True, 'filter': True},
        style={'height': '760px', 'width': '100%', 'maxWidth': '700px'},
        className="ag-theme-alpine",
    ),
])

@callback(
    Output('purchases-table', 'rowData'),
    Output('message', 'children'),
    Input('url', 'pathname'),
)
def load_data(pathname):
    if not pathname.endswith('/purchases'):
        return no_update, ''
    user_id = session.get('user_id')
    if not user_id:
        return [], 'Внесено покупок: 0'
    data = fetch_user_purchases(user_id)
    df = pd.DataFrame(data) if isinstance(data, list) else data
    df = df[['id', 'category', 'subcategory', 'price', 'ts']]
    df['ts'] = pd.to_datetime(df['ts']).dt.strftime('%Y-%m-%d')
    recs = df.to_dict('records')
    return recs, f"Внесено покупок: {len(recs)}"

@callback(
    Output('message', 'children', allow_duplicate=True),
    Output('purchases-table', 'rowTransaction'),
    Input('purchases-table', 'cellValueChanged'),
    prevent_initial_call=True
)
def autosave_cell(changes):
    user_id = session.get('user_id')
    if not isinstance(changes, list) or not changes:
        return no_update, no_update
    ch = changes[0]
    old, new = ch.get('oldValue'), ch.get('value')
    if new is None:
        return no_update, no_update
    field = ch.get('colId')
    data = ch.get('data', {})
    purchase_id = data.get('id')
    update_user_purchase(user_id, purchase_id, {field: new})
    msg = f"Изменено: '{old}' → '{new}'"
    # выводим msg вместо начального текста
    return msg, {"update": [data]}

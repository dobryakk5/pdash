# pages/purchases.py
import os, sys
import dash
from dash import html, dcc, dash_table
from flask import session, request
import plotly.express as px
import pandas as pd
from database import fetch_user_purchases

# Добавляем корневую директорию в PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Регистрируем страницу
dash.register_page(__name__, path='/purchases2', name='Покупки')

# Получаем и отображаем данные
def layout():
    user_id = session.get('user_id')
    if not user_id:
        return html.Div(html.H3("Пользователь не авторизован"))

    # Синхронный вызов к базе данных
    purchases = fetch_user_purchases(user_id)
    df = pd.DataFrame(purchases)

    table = dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        page_size=20,
        filter_action="native",
        sort_action="native",
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'}
    )

    fig = px.bar(df, x='item_name', y='amount', title='Суммы покупок по товарам')

    return html.Div([
        html.H2("Ваши покупки"),
        table,
        dcc.Graph(figure=fig)
    ], className="container mx-auto p-6 bg-white rounded-lg shadow-md max-w-6xl")
    
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
                    'width': 'max-content',
                    'maxWidth': '300px',
                    'whiteSpace': 'nowrap',
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
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'},
                    {
                        'if': {'column_id': 'price'},
                        'type': 'numeric',
                        'format': {
                            'specifier': ',.2f',
                            'locale': {'symbol': ['', ' руб.']}
                        }
                    }
                ],
                page_size=15,
                page_action='native',
                
                # РУССКАЯ ЛОКАЛИЗАЦИЯ
                localization={
                    'filter': 'Фильтр',
                    'filterPlaceholder': 'Поиск...',
                    'previous': 'Назад',
                    'next': 'Вперед',
                    'first': 'Первая',
                    'last': 'Последняя',
                    'page': 'Страница',
                    'pageDropDown': 'Страницы',
                    'rowSelect': 'строк',
                    'rowsPerPage': 'Строк на странице:',
                    'selectedRows': 'Выбрано строк:',
                    'sortAscending': '↑ Сортировка по возрастанию',
                    'sortDescending': '↓ Сортировка по убыванию',
                    'resetFilters': 'Сбросить фильтры',
                    'refresh': 'Обновить',
                    'search': 'Поиск',
                    'thousandsSeparator': ' ',
                    'noData': 'Нет данных',
                    'error': 'Ошибка',
                    'loading': 'Загрузка...'
                }
            ),
            className="overflow-x-auto"
        )
    ], className="container mx-auto p-6 bg-white rounded-lg shadow-md max-w-6xl")
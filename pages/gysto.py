from dash import html, dcc, Input, Output, callback, register_page, no_update
import plotly.express as px
import pandas as pd
from flask import session
from pdash.database import fetch_user_purchases

register_page(__name__, path="/gysto", name="gysto")

layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.H2("График покупок по категориям"),
    html.Div(id='gmessage', style={'marginBottom': '1rem'}),

    # Панель фильтров: категория, подкатегория, период
    html.Div([
        html.Div([
            html.Label("Категория:", style={'marginRight': '0.5rem'}),
            dcc.Dropdown(
                id='category-filter',
                options=[{'label': 'Все категории', 'value': ''}],
                value='',
                clearable=False,
                placeholder='Выберите категорию',
                style={'width': '200px'}
            )
        ], style={'marginRight': '1rem'}),

        html.Div([
            html.Label("Подкатегория:", style={'marginRight': '0.5rem'}),
            dcc.Dropdown(
                id='subcategory-filter',
                options=[{'label': 'Все подкатегории', 'value': ''}],
                value='',
                clearable=False,
                placeholder='Выберите подкатегорию',
                style={'width': '200px'}
            )
        ], style={'marginRight': '1rem'}),

        html.Div([
            html.Label("Группировать:", style={'marginRight': '0.5rem'}),
            dcc.Dropdown(
                id='period-filter',
                options=[
                    {'label': 'По дням', 'value': 'D'},
                    {'label': 'По неделям (понедельник)', 'value': 'W-MON'}
                ],
                value='D',
                clearable=False,
                style={'width': '180px'}
            )
        ]),
    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '1rem', 'marginBottom': '1.5rem'}),

    dcc.Loading(
        dcc.Graph(
            id='histogram',
            style={'width': '100%', 'maxWidth': '900px', 'height': '600px'}
        )
    )
])

@callback(
    Output('histogram', 'figure'),
    Output('gmessage', 'children'),
    Output('category-filter', 'options'),
    Output('subcategory-filter', 'options'),
    Output('subcategory-filter', 'value'),
    Input('category-filter', 'value'),
    Input('subcategory-filter', 'value'),
    Input('period-filter', 'value'),
)
def update_graph(selected_cat, selected_subcat, period):
    # Проверка авторизации
    user_id = session.get('user_id')
    if not user_id:
        return (
            px.bar(title='Нет данных: пользователь не авторизован'),
            '',
            no_update,
            no_update,
            ''
        )

    # Загрузка данных
    data = fetch_user_purchases(user_id)
    df = pd.DataFrame(data) if isinstance(data, list) else data
    if df.empty:
        return (
            px.bar(title='Нет покупок для отображения'),
            'Всего покупок: 0',
            no_update,
            no_update,
            ''
        )

    # Преобразуем ts в дату
    df['date'] = pd.to_datetime(df['ts']).dt.date

    # Определяем метку периода
    if period == 'D':
        df['period'] = df['date']
    else:
        # неделя с понедельника, помечаем датой начала недели
        periods = pd.to_datetime(df['date']).dt.to_period('W-SUN')
        df['period'] = periods.dt.start_time.dt.date


    # Формируем опции категорий
    cats = sorted(df['category'].dropna().unique())
    cat_opts = [{'label': 'Все категории', 'value': ''}] + [
        {'label': c, 'value': c} for c in cats
    ]

    # Формируем опции подкатегорий
    if selected_cat:
        subs = sorted(df[df['category'] == selected_cat]['subcategory']
                        .dropna().unique())
        sub_opts = [{'label': 'Все подкатегории', 'value': ''}] + [
            {'label': s, 'value': s} for s in subs
        ]
    else:
        sub_opts = [{'label': 'Все подкатегории', 'value': ''}]
        selected_subcat = ''

    # Сброс подкатегории при сбросе категории
    if not selected_cat:
        selected_subcat = ''

    # Группировка и построение графика
    if selected_cat and selected_subcat:
        # Только выбранная подкатегория
        dff = df[
            (df['category'] == selected_cat) &
            (df['subcategory'] == selected_subcat)
        ]
        grouped = dff.groupby('period', as_index=False).agg(cost=('price','sum'))
        title = f"{selected_cat} → {selected_subcat}"
        color = None

    elif selected_cat:
        # По подкатегориям выбранной категории
        dff = df[df['category'] == selected_cat]
        grouped = dff.groupby(['period','subcategory'], as_index=False).agg(cost=('price','sum'))
        title = f"Расходы в категории «{selected_cat}»"
        color = 'subcategory'

    else:
        # Общий график по категориям
        grouped = df.groupby(['period','category'], as_index=False).agg(cost=('price','sum'))
        title = 'Покупки по категориям'
        color = 'category'

    fig = px.bar(
        grouped,
        x='period',
        y='cost',
        color=color,
        labels={
            'cost': 'Сумма, ₽',
            'period': 'Период',
            'category': 'Категория',
            'subcategory': 'Подкатегория'
        },
        title=title
    )

    fig.update_layout(
        barmode='stack',
        legend=dict(orientation='v', yanchor='top', y=1, xanchor='left', x=1.02),
        xaxis=dict(type='category')
    )

    # Сообщение внизу
    if selected_cat and selected_subcat:
        msg = f"Подкатегория «{selected_subcat}», покупок: {len(dff)}"
    elif selected_cat:
        msg = f"Категория «{selected_cat}», покупок: {len(dff)}"
    else:
        msg = f"Всего покупок: {len(df)}"

    return fig, msg, cat_opts, sub_opts, selected_subcat

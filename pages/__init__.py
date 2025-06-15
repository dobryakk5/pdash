import dash
from dash import html, dcc

dash.register_page(__name__, path='/', name='Home')

layout = html.Div([
    html.H1('Личный кабинет', className='text-center my-4'),
    
    html.Div([
        html.Div([
            html.H3('Ваша статистика'),
            dcc.Graph(
                figure={
                    'data': [{
                        'values': [35, 25, 20, 20],
                        'labels': ['Еда', 'Транспорт', 'Развлечения', 'Одежда'],
                        'type': 'pie',
                        'hole': 0.4,
                        'marker': {'colors': ['#FF6B6B', '#4ECDC4', '#FFD166', '#6A0572']}
                    }],
                    'layout': {
                        'margin': {'t': 20, 'b': 20, 'l': 20, 'r': 20},
                        'showlegend': True
                    }
                }
            )
        ], className='col-md-6'),
        
        html.Div([
            html.H3('Баланс'),
            html.Div([
                html.H4('12,500 руб.', className='display-4 text-success'),
                html.P('Текущий баланс', className='text-muted'),
                html.Button('Пополнить', className='btn btn-primary mt-3')
            ], className='text-center p-4 bg-light rounded')
        ], className='col-md-6')
    ], className='row'),
    
    html.Div([
        dcc.Link('Посмотреть историю покупок →', 
                href='/purchases', 
                className='btn btn-outline-secondary mt-4')
    ], className='text-center')
])
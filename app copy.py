from dash import Dash, dcc, html, Input, Output, callback
import redis
from flask import Flask, session, redirect, request
import os
from dotenv import load_dotenv

# Инициализация Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Создаем Flask и Dash приложения
server = Flask(__name__)
BOT_TOKEN = os.getenv("API_TOKEN")
server.secret_key = BOT_TOKEN  # Важно для сессий!
app = Dash(__name__, server=server)

# Маршрут для обработки токена
@server.route('/auth')
def handle_auth():
    token = request.args.get('token')
    
    if token:
        # Проверяем токен в Redis
        user_id = r.get(f"dash_token:{token}")
        
        if user_id:
            # Удаляем использованный токен
            r.delete(f"dash_token:{token}")
            # Сохраняем user_id в сессии
            session['user_id'] = user_id
            return redirect('/')
    
    return "Неверный или просроченный токен авторизации", 401

# Основной layout приложения
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='content')
])

@callback(
    Output('content', 'children'),
    Input('url', 'pathname')
)
def render_page(pathname):
    # Проверяем авторизацию
    user_id = session.get('user_id')
    
    if not user_id:
        return html.Div([
            html.H1("Требуется авторизация"),
            html.P("Используйте команду /start в Telegram-боте для получения ссылки")
        ])
    
    # Отображаем личный кабинет
    return html.Div([
        html.H1(f"Добро пожаловать, пользователь #{user_id}!"),
        dcc.Graph(
            figure={
                'data': [{'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar'}],
                'layout': {'title': 'Ваши данные'}
            }
        )
    ])

if __name__ == '__main__':
    app.run(debug=True)
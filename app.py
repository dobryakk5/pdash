from dash import Dash, dcc, html, Input, Output, callback
import redis
from flask import Flask, session, redirect, request, url_for
import os
from dotenv import load_dotenv

load_dotenv()

# Инициализация Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
print("Подключение к Redis установлено")

# Создаем Flask и Dash приложения
server = Flask(__name__)
BOT_TOKEN = os.getenv("API_TOKEN")
server.secret_key = BOT_TOKEN or "DEFAULT_SECRET"
app = Dash(__name__, server=server)

print(f"Секретный ключ приложения: {server.secret_key[:5]}...")

# Маршрут для обработки токена
@server.route('/auth')
def handle_auth():
    print("\n" + "="*50)
    print("Начало обработки /auth запроса")
    
    token = request.args.get('token')
    print(f"Получен токен из URL: {token}")
    
    if token:
        redis_key = f"dash_token:{token}"
        print(f"Ключ для поиска в Redis: '{redis_key}'")
        
        user_id = r.get(redis_key)
        print(f"Результат поиска в Redis: '{user_id}'")
        
        if user_id:
            print(f"Найден user_id: {user_id}")
            r.delete(redis_key)
            print(f"Токен удален из Redis")
            session['user_id'] = user_id
            print(f"User_id сохранен в сессии: {session['user_id']}")
            
            # Перенаправляем на защищенный маршрут без параметров
            return redirect(url_for('dash_app'))
    
    print("ОШИБКА: Неверный или просроченный токен")
    return "Неверный или просроченный токен авторизации", 401

# Защищенный маршрут для основного приложения
@server.route('/app')
def dash_app():
    # Проверяем авторизацию перед отображением Dash
    if 'user_id' not in session:
        return redirect(url_for('unauthorized'))
    return app.index()

# Маршрут для неавторизованных пользователей
@server.route('/unauthorized')
def unauthorized():
    return html.Div([
        html.H1("Требуется авторизация"),
        html.P("Используйте команду /start в Telegram-боте для получения ссылки")
    ])

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
    print("\n" + "="*50)
    print(f"Обработка запроса: {pathname}")
    
    # Разрешаем доступ только по пути /app
    if pathname != '/app':
        return redirect('/app')
    
    user_id = session.get('user_id')
    print(f"Текущий user_id в сессии: {user_id}")
    
    if not user_id:
        print("Пользователь не авторизован")
        return redirect('/unauthorized')
    
    print(f"Пользователь #{user_id} авторизован")
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
    print("\n" + "="*50)
    print("Запуск сервера...")
    app.run(debug=True)
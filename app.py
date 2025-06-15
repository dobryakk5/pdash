from dash import Dash, dcc, html, Input, Output, callback
import redis
from flask import Flask, session, redirect, request, url_for
import os
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Инициализация Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
logger.info("Подключение к Redis установлено")

# Создаем Flask и Dash приложения
server = Flask(__name__)
BOT_TOKEN = os.getenv("API_TOKEN")
server.secret_key = BOT_TOKEN or "DEFAULT_SECRET"
app = Dash(__name__, server=server)

logger.info(f"Секретный ключ приложения: {server.secret_key[:5]}...")

# Маршрут для обработки токена
@server.route('/auth')
def handle_auth():
    logger.info("\n" + "="*50)
    logger.info("Начало обработки /auth запроса")
    
    token = request.args.get('token')
    logger.info(f"Получен токен из URL: {token}")
    
    if not token:
        logger.error("ОШИБКА: Токен отсутствует в запросе")
        return "Токен не предоставлен", 400
    
    # Проверяем наличие активной сессии
    if 'user_id' in session:
        logger.warning(f"Пользователь уже авторизован (user_id={session['user_id']})")
        return redirect(url_for('dash_app'))
    
    # Формируем ключ Redis
    redis_key = f"dash_token:{token}"
    logger.info(f"Ключ для поиска в Redis: '{redis_key}'")
    
    # Проверяем токен в Redis
    user_id = r.get(redis_key)
    logger.info(f"Результат поиска в Redis: '{user_id}'")
    
    if user_id:
        logger.info(f"Найден user_id: {user_id}")
        
        # Удаляем использованный токен
        r.delete(redis_key)
        logger.info(f"Токен удален из Redis")
        
        # Сохраняем user_id в сессии
        session['user_id'] = user_id
        logger.info(f"User_id сохранен в сессии: {session['user_id']}")
        
        # Перенаправляем с очисткой параметров
        return redirect(url_for('dash_app'))
    
    logger.error("ОШИБКА: Токен не найден в Redis или истек срок действия")
    return "Неверный или просроченный токен авторизации", 401

# Защищенный маршрут для основного приложения
@server.route('/app')
def dash_app():
    logger.info("\n" + "="*50)
    logger.info(f"Запрос к /app, сессия: user_id={session.get('user_id', 'отсутствует')}")
    return app.index()

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
    logger.info("\n" + "="*50)
    logger.info(f"Обработка пути: {pathname}")
    
    # Если запрос к /auth - обрабатываем отдельно
    if pathname == '/auth':
        token = request.args.get('token', '')
        logger.warning(f"Прямой доступ к /auth с токеном: {token}")
        return html.Div([
            html.H1("Неправильный метод доступа"),
            html.P("Используйте ссылку из Telegram-бота для авторизации")
        ])
    
    # Проверяем авторизацию только для /app
    user_id = session.get('user_id')
    logger.info(f"Текущий user_id в сессии: {user_id}")
    
    if pathname != '/app' or not user_id:
        logger.warning(f"Перенаправление неавторизованного пользователя")
        return html.Div([
            html.H1("Требуется авторизация"),
            html.P("Используйте команду /start в Telegram-боте для получения ссылки"),
            html.P(f"Текущий путь: {pathname}")
        ])
    
    logger.info(f"Пользователь #{user_id} авторизован")
    return html.Div([
        html.H1(f"Добро пожаловать, пользователь #{user_id}!"),
        html.P("Вы успешно авторизованы"),
        dcc.Graph(
            figure={
                'data': [{'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar'}],
                'layout': {'title': 'Ваши данные'}
            }
        ),
        html.Div(id='hidden-div', style={'display': 'none'})
    ])

# Callback для очистки URL после загрузки
@callback(
    Output('hidden-div', 'children'),
    Input('url', 'href')
)
def clear_url(href):
    if 'token=' in href:
        logger.warning(f"Обнаружен токен в URL: {href}")
        return dcc.Location(pathname='/app', id='clear-url')
    return None

if __name__ == '__main__':
    logger.info("\n" + "="*50)
    logger.info("Запуск сервера...")
    app.run(debug=True)
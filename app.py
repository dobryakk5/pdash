from dash import Dash, dcc, html, Input, Output, callback
import redis
from flask import Flask, session, redirect, request, url_for, send_from_directory
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

# Новый маршрут для обработки входа
@server.route('/login')
def handle_login():
    logger.info("\n" + "="*50)
    logger.info("Начало обработки /login запроса")
    
    # Проверяем User-Agent на принадлежность к Telegram Bot
    user_agent = request.headers.get('User-Agent', '').lower()
    if 'telegrambot' in user_agent or 'bot.html' in user_agent:
        logger.warning(f"Запрос от Telegram Bot User-Agent: {user_agent}")
        return "Telegram link preview", 200
    
    token = request.args.get('token')
    logger.info(f"Получен токен из URL: {token}")
    
    if not token:
        logger.warning("Токен не предоставлен")
        return "Токен не предоставлен", 400
    
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
        
        # Перенаправляем на основной интерфейс
        return redirect('/app')
    
    logger.error("ОШИБКА: Токен не найден в Redis или истек срок действия")
    return "Неверная или просроченная ссылка для входа", 401

# Маршрут для favicon
@server.route('/favicon.ico')
def favicon():
    # Логируем запрос, но игнорируем параметры
    logger.info("Запрос favicon.ico")
    return send_from_directory(os.path.join(server.root_path, 'static'),
                              'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Маршрут для обработки токена
@server.route('/auth')
def handle_auth():
    logger.info("\n" + "="*50)
    logger.info("Начало обработки /auth запроса")
    
    # Игнорируем запросы к ресурсам
    if request.path != '/auth' or not request.args.get('token'):
        logger.warning("Запрос к ресурсу, игнорируем токен")
        return redirect('/app')
    
    token = request.args.get('token')
    logger.info(f"Получен токен из URL: {token}")
    
    # Проверяем наличие активной сессии
    if 'user_id' in session:
        logger.warning(f"Пользователь уже авторизован (user_id={session['user_id']})")
        return redirect('/app')
    
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
        return redirect('/app')
    
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
    
    # Разрешаем доступ только по пути /app
    if pathname != '/app':
        logger.warning(f"Перенаправление с {pathname} на /app")
        return redirect('/app')
    
    user_id = session.get('user_id')
    logger.info(f"Текущий user_id в сессии: {user_id}")
    
    if not user_id:
        logger.warning("Пользователь не авторизован")
        return html.Div([
            html.H1("Требуется авторизация"),
            html.P("Используйте команду /start в Telegram-боте для получения ссылки")
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
        # Компонент для очистки URL
        dcc.Location(id='redirect', refresh=True)
    ])

# Callback для очистки URL после загрузки
@callback(
    Output('redirect', 'pathname'),
    Input('url', 'href')
)
def clear_url(href):
    if 'token=' in href:
        logger.warning(f"Обнаружен токен в URL: {href}")
        return '/app'
    return None

if __name__ == '__main__':
    logger.info("\n" + "="*50)
    logger.info("Запуск сервера...")
    
    # Создаем папку static если её нет
    static_dir = os.path.join(server.root_path, 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    app.run(debug=True)
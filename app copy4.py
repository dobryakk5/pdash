from dash import Dash, dcc, html, Input, Output, callback
import redis
from flask import Flask, session, request, send_from_directory, redirect
import os, dash
import logging, sys
import argparse
from auth import AuthManager
from asgiref.wsgi import WsgiToAsgi

# Добавляем корень проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка аргументов командной строки
parser = argparse.ArgumentParser()
parser.add_argument('--admin', action='store_true', help='Enable admin mode without authentication')
args = parser.parse_args()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
logger.info("Подключение к Redis установлено")

# Создаем Flask и Dash приложения
server = Flask(__name__)
BOT_TOKEN = os.getenv("API_TOKEN")
server.secret_key = BOT_TOKEN or "DEFAULT_SECRET"

# Инициализация менеджера авторизации
auth_manager = AuthManager(r, admin_mode=args.admin)

# Конфигурация Dash
app = Dash(
    __name__,
    use_pages=True,
    server=server,
    url_base_pathname='/app/',
    suppress_callback_exceptions=True,
    external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'],
    meta_tags=[{
        'name': 'viewport',
        'content': 'width=device-width, initial-scale=1.0, maximum-scale=1.0'
    }]
)

#from pages import ( analytics, purchases)

logger.info(f"Режим администратора: {'ВКЛЮЧЕН' if args.admin else 'выключен'}")

# Маршрут для корня
@server.route('/')
def root():
    logger.info("Обработка корневого маршрута '/'")
    user_id = auth_manager.get_current_user()
    
    if user_id:
        logger.info(f"Перенаправление авторизованного пользователя {user_id} на /app/purchases")
        return redirect('/app/purchases')
    else:
        logger.warning("Пользователь не авторизован, показ страницы авторизации")
        return """
        <html>
            <head><title>Требуется авторизация</title></head>
            <body>
                <h1>Требуется авторизация</h1>
                <p>Используйте команду /start в Telegram-боте для получения ссылки</p>
            </body>
        </html>
        """

# Маршрут для обработки токена
@server.route('/auth')
def handle_auth():
    return auth_manager.handle_authentication()

# Защищенный маршрут для основного приложения
@server.route('/app/')
@server.route('/app/<path:subpath>')
def dash_app(subpath=None):
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
    
    user_id = auth_manager.get_current_user()
    logger.info(f"Текущий user_id: {user_id}")
    
    if not user_id:
        return html.Div([
            html.P("Требуется авторизация. Используйте команду /start в Telegram-боте для получения ссылки")
        ])
    
    # Перенаправление на страницу покупок
    if pathname == '/app/' or pathname == '/app':
        logger.info("Перенаправление на страницу покупок")
        return dcc.Location(pathname="/app/purchases", id="redirect-to-purchases")
    
    # Генерация навигационной панели
    navbar = html.Div([
        dcc.Link(f"{page['name']} | ", href=f"/app{page['path']}")
        for page in dash.page_registry.values()
    ], style={'padding': '10px', 'backgroundColor': '#f0f0f0'})
    
    # Отображаем страницы приложения
    return html.Div([
        navbar,
        dash.page_container
    ])

asgi_app = WsgiToAsgi(server)

if __name__ == '__main__':
    server.run(debug=True, port=8050)
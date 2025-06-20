from gevent import monkey
monkey.patch_all()

import os
import logging
from logging.handlers import TimedRotatingFileHandler
import argparse
from flask import Flask, session, redirect, request
import redis
from dash import Dash, html, dcc, page_container
from pdash.auth import AuthManager
import dash_bootstrap_components as dbc

# ——————————————— Настройка ———————————————
# Папка для логов
LOG_DIR = os.getenv('LOG_DIR', 'log')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Конфигурация логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Обработчик для ротации логов каждые 7 дней, хранить 4 файла
log_file = os.path.join(LOG_DIR, 'pdash.log')
file_handler = TimedRotatingFileHandler(
    filename=log_file,
    when='D',             # единица: дни
    interval=7,           # каждые 7 дней
    backupCount=4,        # хранить 4 старых файла
    encoding='utf-8'
)
file_handler.suffix = "%Y-%m-%d"
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Консольный обработчик (по желанию)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Flask-приложение
server = Flask(__name__)
server.secret_key = os.getenv("API_TOKEN") or "FALLBACK_SECRET_JHG&^GFY%FHF%Y%Yoajorien;cmo5"
if server.secret_key == "FALLBACK_SECRET_JHG&^GFY%FHF%Y%Yoajorien;cmo5":
    logger.warning("Используется запасной секрет — не для продакшна!")

# Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Парсер аргументов (расскомментировать при необходимости)
# parser = argparse.ArgumentParser()
# parser.add_argument('--admin', action='store_true')
# args = parser.parse_args()

# Менеджер авторизации (admin_mode можно выставлять через --admin)
auth_manager = AuthManager(r, admin_mode=False)  # args.admin)

# Маршрут для авторизации с логированием user_id
def auth_route():
    # Обработка аутентификации
    response = auth_manager.handle_authentication()
    user = auth_manager.get_current_user()
    if user:
        # Предполагается, что user содержит ключ 'id' или 'user_id'
        user_id = session.get('user_id')
        logger.info(f"User authenticated: user_id={user_id}")
    else:
        logger.warning("Authentication attempt without valid user")
    return response

# Регистрируем маршрут вместо add_url_rule
server.add_url_rule('/auth', 'auth', auth_route)

# Использование Dash внутри Flask
app = Dash(
    __name__,
    server=server,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    assets_folder="assets",
    requests_pathname_prefix="/app/",
    routes_pathname_prefix="/app/"
)

# Навигация
nav = dbc.Nav(
    [
        dbc.NavLink("Покупки", href="/app/purchases", active="exact"),
        dbc.NavLink("Графики", href="/app/gysto", active="exact"),
    ]
)

# Макет приложения
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(
        nav,
        style={
            "padding": "0.5rem 1rem",
        }
    ),
    page_container
])

if __name__ == '__main__':
    logger.info("Запуск Dash на порту 8050")
    app.run(debug=False, port=8050)

import os
import sys
import logging
import argparse
from flask import Flask, session
import redis
import dash
from dash import Dash, dcc, html, Input, Output
from .auth import AuthManager

# Добавляем корень проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка аргументов командной строки
parser = argparse.ArgumentParser()
parser.add_argument('--admin', action='store_true', help='Enable admin mode without authentication')
args = parser.parse_args()

# Инициализация логгера
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

# Конфигурация Dash с поддержкой Pages
app = Dash(
    __name__,
    server=server,
    url_base_pathname='/app/',
    use_pages=True,
    suppress_callback_exceptions=True
)

# Макет приложения
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),  # отслеживание URL
    html.Div([
        # Навигация между страницами
        html.Div([
            dcc.Link(f"{page['name']} | ", href=page['relative_path'])
            for page in dash.page_registry.values()
        ], style={'padding': '10px', 'backgroundColor': '#f0f0f0'}),

        # Контейнер для содержимого страниц
        dash.page_container
    ], id='page-content')
])

if __name__ == '__main__':
    app.run(debug=True, port=8050, dev_tools_ui=False, dev_tools_props_check=False)
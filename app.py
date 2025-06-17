import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
import argparse
from flask import Flask, session
import redis
import dash
from dash import Dash, html, dcc, page_container, page_registry
from .auth import AuthManager

# Настройка директорий для логов
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'app.log')

# Настройка логгера с ротацией раз в 7 дней
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Обработчик ротации
handler = TimedRotatingFileHandler(
    filename=LOG_FILE,
    when='D',       # по дням
    interval=7,     # каждые 7 дней
    backupCount=4,  # хранить 4 старых файла (примерно на месяц)
    encoding='utf-8'
)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Также логируем в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# --- Дальше весь ваш существующий код ---

parser = argparse.ArgumentParser()
parser.add_argument('--admin', action='store_true', help='Enable admin mode without authentication')
args = parser.parse_args()

logger.info("Старт приложения")

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
logger.info("Подключение к Redis установлено")

server = Flask(__name__)
BOT_TOKEN = os.getenv("API_TOKEN")
server.secret_key = BOT_TOKEN

auth_manager = AuthManager(r, admin_mode=args.admin)

app = Dash(
    __name__,
    server=server,
    use_pages=True,
    suppress_callback_exceptions=True,
    assets_folder="assets",
    requests_pathname_prefix="/app/",
    routes_pathname_prefix="/app/"
)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        html.Div([
        page_container
    ], id='page-content')
])])

if __name__ == '__main__':
    logger.info("Запуск веб-сервера на порту 8050")
    app.run(debug=True, port=8050, dev_tools_ui=False, dev_tools_props_check=False)

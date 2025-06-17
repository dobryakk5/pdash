import os
import logging
import argparse

from flask import Flask, session, redirect, request
import redis
from dash import Dash, html, dcc, page_container
from pdash.auth import AuthManager

# ——————————————— Настройка ———————————————
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

server = Flask(__name__)
server.secret_key = os.getenv("API_TOKEN") or "DEFAULT_SECRET"

parser = argparse.ArgumentParser()
parser.add_argument('--admin', action='store_true')
args = parser.parse_args()

auth_manager = AuthManager(r, admin_mode=args.admin)

# 1) Роут для авторизации
server.add_url_rule('/auth', 'auth', auth_manager.handle_authentication)

# 2) Защита всех URL, начинающихся с /app
@server.before_request
def protect_dash():
    if request.path.startswith('/app'):
        if auth_manager.get_current_user() is None:
            return redirect('/auth')

# 3) Инициализация Dash
app = Dash(
    __name__,
    server=server,
    use_pages=True,
    suppress_callback_exceptions=True,
    assets_folder="assets",
    requests_pathname_prefix="/app/",
    routes_pathname_prefix="/app/"
)

# 4) layout с page_container
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    page_container
])

if __name__ == '__main__':
    logger.info("Запуск Dash на порту 8050")
    app.run(debug=True, port=8050)

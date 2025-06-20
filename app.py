#from gevent import monkey
#monkey.patch_all()

import os
import logging
import argparse
from flask import Flask, session, redirect, request
import redis
from dash import Dash, html, dcc, page_container
from pdash.auth import AuthManager
import dash_bootstrap_components as dbc


# ——————————————— Настройка ———————————————
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


server = Flask(__name__)
server.secret_key = os.getenv("API_TOKEN") or "FALLBACK_SECRET"
if server.secret_key == "FALLBACK_SECRET":
    logger.warning("Используется запасной секрет — не для продакшна!")

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

parser = argparse.ArgumentParser() 
parser.add_argument('--admin', action='store_true')
args = parser.parse_args()

auth_manager = AuthManager(r, admin_mode=args.admin)

# 1) Роут для авторизации
server.add_url_rule('/auth', 'auth', auth_manager.handle_authentication)

# 2) Защита всех URL, начинающихся с /app
#@server.route('/app/')
#def dash_index():
#    if auth_manager.get_current_user() is None:
 #       return redirect('/auth')
 #   return app.index()

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

nav = dbc.Nav(
    [
        dbc.NavLink("Покупки",     href="/app/purchases", active="exact"),
        dbc.NavLink("Графики", href="/app/gysto",     active="exact"),
    ]
)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(
        nav,
        style={
            "padding": "0.5rem 1rem",
            #"backgroundColor": "#e9e9e8",  
            #"borderBottom": "1px solid #dee2e6"
        }
    ),
    page_container
])

if __name__ == '__main__':
    logger.info("Запуск Dash на порту 8050")
    app.run(debug=False, port=8050)
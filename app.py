from dash import Dash, dcc, html, Input, Output, callback
import redis
from flask import Flask, session, request, send_from_directory
import os, dash
import logging
import argparse
from auth import AuthManager

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
    suppress_callback_exceptions=True,
    external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'],
    meta_tags=[{
        'name': 'viewport',
        'content': 'width=device-width, initial-scale=1.0, maximum-scale=1.0'
    }]
)

logger.info(f"Режим администратора: {'ВКЛЮЧЕН' if args.admin else 'выключен'}")

# Маршрут для favicon
#@server.route('/favicon.ico')
#def favicon():
#    return send_from_directory(os.path.join(server.root_path, 'static'),
 #                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Маршрут для обработки токена
@server.route('/auth')
def handle_auth():
    return auth_manager.handle_authentication()

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
    
    user_id = auth_manager.get_current_user()
    logger.info(f"Текущий user_id: {user_id}")
    
    if not user_id:
        return html.Div([
            html.H1("Требуется авторизация"),
            html.P("Используйте команду /start в Telegram-боте для получения ссылки")
        ])
    
    is_admin = auth_manager.is_admin()

    # Если пользователь впервые заходит по корневому пути, перенаправляем на /app
    if pathname == '/' and is_admin:
        return dcc.Location(pathname="/app", id="redirect-admin")
    
    app.layout = html.Div([
        html.Div([
        dcc.Link(f"{page['name']}", href=page["path"])
        for page in dash.page_registry.values()
        ]),
        dash.page_container
    ])

    return html.Div([
        html.P("Вы успешно авторизованы"),
        dcc.Graph(
            figure={
                'data': [{'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar'}],
                'layout': {'title': 'Ваши данные'}
            }
        ),
        html.Div([
            html.H2("Специальные возможности администратора"),
            html.P("Доступ к расширенным настройкам"),
            html.P("Системные отчеты"),
        ]) if is_admin else None
    ])

if __name__ == '__main__':
    app.run(debug=False, port=8050)
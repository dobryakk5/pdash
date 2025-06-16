# pages/index.py
import dash
from dash import dcc

# Регистрируем страницу на корневом пути
dash.register_page(__name__, path='/', name='Главная')

# При заходе на "/" сразу идёт перенаправление на "/purchases"
layout = dcc.Location(pathname='/app/purchases', id='redirect-index')

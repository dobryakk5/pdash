import logging
from flask import session, request, redirect

logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self, redis_client, admin_mode=False, admin_user_id="7852511755"):
        self.r = redis_client
        self.admin_mode = admin_mode
        self.admin_user_id = admin_user_id
        logger.info(f"Инициализация AuthManager. Режим администратора: {'ВКЛЮЧЕН' if admin_mode else 'выключен'}")

    def handle_authentication(self):
        """Обработка аутентификации через Telegram"""
        # Проверка User-Agent для Telegram
        user_agent = request.headers.get('User-Agent', '').lower()
        if 'telegrambot' in user_agent or 'bot.html' in user_agent:
            logger.warning(f"Запрос от Telegram Bot (User-Agent: {user_agent})")
            return "Telegram link preview", 200
        
        token = request.args.get('token')
        if not token:
            logger.warning("Токен не предоставлен")
            return "Токен не предоставлен", 400
        
        redis_key = f"dash_token:{token}"
        user_id = self.r.get(redis_key)
        
        if user_id:
            self.r.delete(redis_key)
            session['user_id'] = user_id
            logger.info(f"Успешная аутентификация user_id: {user_id}")
            return redirect('/app')
        
        logger.error("ОШИБКА: Токен не найден в Redis или истек срок действия")
        return "Неверная или просроченная ссылка для входа", 401

    def check_admin_access(self):
        """Проверка и установка доступа администратора"""
        if self.admin_mode and 'user_id' not in session:
            session['user_id'] = self.admin_user_id
            logger.info(f"Автоматическая авторизация администратора: user_id={self.admin_user_id}")

    def get_current_user(self):
        """Получение текущего пользователя с обработкой администратора"""
        self.check_admin_access()
        return session.get('user_id')

    def is_admin(self):
        """Проверка, является ли пользователь администратором"""
        user_id = self.get_current_user()
        return user_id == self.admin_user_id
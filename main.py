import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from keyboards import get_main_menu_keyboard
from storage import get_or_create_user, is_admin, get_user_by_id
from handlers.main_menu import router as main_menu_router
from handlers.status_management import router as status_management_router
from handlers.projects import router as projects_router
from handlers.characters import router as characters_router
from handlers.developers import router as developers_router
from handlers.admin import router as admin_router
from handlers.notifications import router as notifications_router
from services.notifications import start_notification_service

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def start_command(message: Message):
    """Обработчик команды /start"""
    # Создаем или обновляем пользователя
    user_id = message.from_user.id
    user = get_or_create_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    
    # Проверяем, является ли пользователь админом
    admin = is_admin(user_id)
    
    await message.answer(
        "👋 Добро пожаловать в Work Bot!\n\n"
        "Выберите действие из меню:",
        reply_markup=get_main_menu_keyboard(is_admin=admin, user_role=user.role)
    )


async def main():
    """Основная функция запуска бота"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не найден! Создайте файл .env и добавьте BOT_TOKEN=your_token")
        return
    
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрация обработчиков
    dp.message.register(start_command, Command("start"))
    dp.include_router(admin_router)  # Админ роутер должен быть первым для перехвата настроек
    dp.include_router(projects_router)  # Важно: projects_router должен быть первым, т.к. перехватывает "Проекты"
    dp.include_router(characters_router)
    dp.include_router(developers_router)
    dp.include_router(notifications_router)
    dp.include_router(main_menu_router)
    dp.include_router(status_management_router)
    
    logger.info("Бот запущен!")
    
    # Запускаем сервис уведомлений в фоне
    notification_task = asyncio.create_task(start_notification_service(bot))
    
    try:
        await dp.start_polling(bot)
    finally:
        notification_task.cancel()
        try:
            await notification_task
        except asyncio.CancelledError:
            pass
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())


import asyncio
import logging
from aiogram import Bot
from storage import (
    get_users_with_tasks,
    get_projects_by_role,
    get_character_by_id,
    get_developer_by_id,
    get_status_by_id
)
from config import BOT_TOKEN

logger = logging.getLogger(__name__)


async def send_notifications(bot: Bot):
    """Отправляет уведомления пользователям с задачами"""
    while True:
        try:
            users = get_users_with_tasks()
            
            for user in users:
                if not user.notifications_enabled:
                    continue
                
                projects = get_projects_by_role(user.role)
                
                if not projects:
                    continue
                
                # Формируем сообщение с задачами
                message_text = f"🔔 У вас есть задачи ({user.role})\n\n"
                message_text += f"Всего задач: {len(projects)}\n\n"
                
                for i, project in enumerate(projects[:5], 1):  # Показываем первые 5
                    character = get_character_by_id(project.character_id)
                    developer = get_developer_by_id(project.developer_id)
                    status = get_status_by_id(project.status_id)
                    
                    character_name = character.name if character else f"ID:{project.character_id}"
                    status_name = status.name if status else f"ID:{project.status_id}"
                    
                    message_text += f"{i}. 📁 {project.name}\n"
                    message_text += f"   🎭 {character_name} | 📊 {status_name}\n\n"
                
                if len(projects) > 5:
                    message_text += f"... и еще {len(projects) - 5} задач"
                
                try:
                    await bot.send_message(
                        chat_id=user.user_id,
                        text=message_text
                    )
                    logger.info(f"Уведомление отправлено пользователю {user.user_id}")
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления пользователю {user.user_id}: {e}")
            
            # Ждем минимальный интервал (5 минут) перед следующей проверкой
            # Реальная частота определяется настройками пользователя
            await asyncio.sleep(5 * 60)  # 5 минут
            
        except Exception as e:
            logger.error(f"Ошибка в цикле уведомлений: {e}")
            await asyncio.sleep(60)  # Ждем минуту перед повтором


async def start_notification_service(bot: Bot):
    """Запускает сервис уведомлений"""
    logger.info("Сервис уведомлений запущен")
    
    # Словарь для отслеживания последнего времени отправки для каждого пользователя
    last_notification_time = {}
    
    while True:
        try:
            users = get_users_with_tasks()
            current_time = asyncio.get_event_loop().time()
            
            for user in users:
                if not user.notifications_enabled:
                    continue
                
                # Проверяем, прошло ли достаточно времени с последнего уведомления
                last_time = last_notification_time.get(user.user_id, 0)
                interval_seconds = user.notification_interval * 60
                
                if current_time - last_time < interval_seconds:
                    continue
                
                projects = get_projects_by_role(user.role)
                if not projects:
                    continue
                
                # Формируем сообщение
                message_text = f"🔔 У вас есть задачи ({user.role})\n\n"
                message_text += f"Всего задач: {len(projects)}\n\n"
                
                for i, project in enumerate(projects[:5], 1):
                    character = get_character_by_id(project.character_id)
                    status = get_status_by_id(project.status_id)
                    
                    character_name = character.name if character else f"ID:{project.character_id}"
                    status_name = status.name if status else f"ID:{project.status_id}"
                    
                    message_text += f"{i}. 📁 {project.name}\n"
                    message_text += f"   🎭 {character_name} | 📊 {status_name}\n\n"
                
                if len(projects) > 5:
                    message_text += f"... и еще {len(projects) - 5} задач"
                
                try:
                    await bot.send_message(
                        chat_id=user.user_id,
                        text=message_text
                    )
                    last_notification_time[user.user_id] = current_time
                    logger.info(f"Уведомление отправлено пользователю {user.user_id} (интервал: {user.notification_interval} мин)")
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления пользователю {user.user_id}: {e}")
            
            # Проверяем каждую минуту
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Ошибка в цикле уведомлений: {e}")
            await asyncio.sleep(60)

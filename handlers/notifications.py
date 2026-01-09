from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards import (
    get_main_menu_keyboard,
    get_notification_settings_keyboard,
    get_notification_interval_keyboard
)
from storage import (
    get_user_by_id,
    update_user_notifications,
    is_admin
)

router = Router()


@router.message(F.text == "🔔 Настройки уведомлений")
async def notification_settings_handler(message: Message):
    """Обработчик для настроек уведомлений"""
    user_id = message.from_user.id
    user = get_user_by_id(user_id)
    
    if not user:
        await message.answer("❌ Пользователь не найден")
        return
    
    status_text = "✅ Включены" if user.notifications_enabled else "❌ Выключены"
    
    await message.answer(
        f"🔔 Настройки уведомлений\n\n"
        f"Статус: {status_text}\n"
        f"Частота: каждые {user.notification_interval} минут\n\n"
        f"Выберите действие:",
        reply_markup=get_notification_settings_keyboard(user)
    )


@router.message(F.text.startswith("🔔 Уведомления:"))
async def toggle_notifications_handler(message: Message):
    """Обработчик переключения уведомлений"""
    user_id = message.from_user.id
    user = get_user_by_id(user_id)
    
    if not user:
        await message.answer("❌ Пользователь не найден")
        return
    
    new_status = not user.notifications_enabled
    update_user_notifications(user_id, enabled=new_status)
    
    status_text = "✅ включены" if new_status else "❌ выключены"
    await message.answer(
        f"🔔 Уведомления {status_text}",
        reply_markup=get_notification_settings_keyboard(get_user_by_id(user_id))
    )


@router.message(F.text.startswith("⏰ Частота:"))
async def change_interval_handler(message: Message):
    """Обработчик изменения частоты уведомлений"""
    user_id = message.from_user.id
    user = get_user_by_id(user_id)
    
    if not user:
        await message.answer("❌ Пользователь не найден")
        return
    
    await message.answer(
        "⏰ Выберите частоту уведомлений:",
        reply_markup=get_notification_interval_keyboard()
    )


@router.callback_query(F.data.startswith("set_interval_"))
async def set_interval_callback(callback: CallbackQuery):
    """Обработчик установки интервала уведомлений"""
    user_id = callback.from_user.id
    interval = int(callback.data.split("_")[-1])
    
    if update_user_notifications(user_id, interval=interval):
        user = get_user_by_id(user_id)
        await callback.message.edit_text(
            f"✅ Частота уведомлений установлена: каждые {interval} минут"
        )
        await callback.answer("Интервал установлен!")
        
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_notification_settings_keyboard(user)
        )
    else:
        await callback.answer("❌ Ошибка при установке интервала", show_alert=True)

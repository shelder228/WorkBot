from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import (
    get_main_menu_keyboard,
    get_developers_management_keyboard,
    get_developers_list_keyboard
)
from storage import (
    get_all_developers,
    add_developer,
    delete_developer,
    get_developer_by_id,
    recalculate_all_developers_stats
)

router = Router()


class DeveloperCreation(StatesGroup):
    waiting_for_name = State()
    waiting_for_username = State()


@router.message(F.text == "👥 Разработчики")
async def developers_management_handler(message: Message):
    """Обработчик для кнопки 'Разработчики'"""
    # Пересчитываем статистику перед показом
    recalculate_all_developers_stats()
    
    developers = get_all_developers()
    
    if not developers:
        await message.answer(
            "👥 Разработчики\n\n"
            "📋 Список разработчиков пуст.\n\n"
            "Выберите действие:",
            reply_markup=get_developers_management_keyboard()
        )
        return
    
    developers_list = "\n\n".join([f"{i+1}. {dev}" for i, dev in enumerate(developers)])
    
    await message.answer(
        f"👥 Разработчики\n\n"
        f"📋 Список разработчиков ({len(developers)}):\n\n{developers_list}\n\n"
        f"Выберите действие:",
        reply_markup=get_developers_management_keyboard()
    )


@router.message(F.text == "📋 Список разработчиков")
async def list_developers_handler(message: Message):
    """Показывает список всех разработчиков"""
    # Пересчитываем статистику перед показом
    recalculate_all_developers_stats()
    
    developers = get_all_developers()
    
    if not developers:
        await message.answer(
            "📋 Список разработчиков пуст.\n\n"
            "Добавьте первого разработчика!",
            reply_markup=get_developers_management_keyboard()
        )
        return
    
    developers_list = "\n\n".join([f"{i+1}. {dev}" for i, dev in enumerate(developers)])
    
    await message.answer(
        f"📋 Список разработчиков ({len(developers)}):\n\n{developers_list}",
        reply_markup=get_developers_management_keyboard()
    )


@router.message(F.text == "➕ Добавить разработчика")
async def add_developer_start(message: Message, state: FSMContext):
    """Начинает процесс добавления разработчика"""
    await state.set_state(DeveloperCreation.waiting_for_name)
    await message.answer(
        "➕ Добавление нового разработчика\n\n"
        "Введите имя разработчика:",
        reply_markup=None
    )


@router.message(DeveloperCreation.waiting_for_name)
async def process_developer_name(message: Message, state: FSMContext):
    """Обрабатывает имя разработчика"""
    developer_name = message.text.strip()
    
    if not developer_name:
        await message.answer("❌ Имя не может быть пустым. Попробуйте снова:")
        return
    
    await state.update_data(name=developer_name)
    await state.set_state(DeveloperCreation.waiting_for_username)
    
    await message.answer(
        f"✅ Имя: {developer_name}\n\n"
        "Введите username разработчика (без @):"
    )


@router.message(DeveloperCreation.waiting_for_username)
async def process_developer_username(message: Message, state: FSMContext):
    """Обрабатывает username разработчика"""
    username = message.text.strip().replace("@", "")
    
    if not username:
        await message.answer("❌ Username не может быть пустым. Попробуйте снова:")
        return
    
    data = await state.get_data()
    developer_name = data.get("name")
    
    try:
        # Создаем разработчика
        new_developer = add_developer(developer_name, username)
        
        await message.answer(
            f"✅ Разработчик успешно добавлен!\n\n"
            f"👤 Имя: {new_developer.name}\n"
            f"📱 Username: @{new_developer.username}\n"
            f"📊 Всего проектов: {new_developer.total_projects}\n"
            f"🆔 ID: {new_developer.id}"
        )
    except ValueError as e:
        await message.answer(f"❌ Ошибка: {e}")
    
    await state.clear()
    
    # Отправляем клавиатуру управления
    await message.answer(
        "Выберите действие:",
        reply_markup=get_developers_management_keyboard()
    )


@router.message(F.text == "🗑️ Удалить разработчика")
async def delete_developer_start(message: Message):
    """Начинает процесс удаления разработчика"""
    developers = get_all_developers()
    
    if not developers:
        await message.answer(
            "❌ Нет разработчиков для удаления.",
            reply_markup=get_developers_management_keyboard()
        )
        return
    
    await message.answer(
        "🗑️ Выберите разработчика для удаления:",
        reply_markup=get_developers_list_keyboard(developers, "delete")
    )


@router.callback_query(F.data.startswith("delete_developer_"))
async def process_delete_developer(callback: CallbackQuery):
    """Обрабатывает удаление разработчика"""
    developer_id = int(callback.data.split("_")[-1])
    developer = get_developer_by_id(developer_id)
    
    if not developer:
        await callback.answer("❌ Разработчик не найден", show_alert=True)
        return
    
    # Удаляем разработчика
    if delete_developer(developer_id):
        await callback.message.edit_text(
            f"✅ Разработчик удален:\n\n"
            f"👤 {developer.name} (@{developer.username})"
        )
        await callback.answer("Разработчик удален!")
    else:
        await callback.answer("❌ Ошибка при удалении", show_alert=True)
    
    # Обновляем список
    developers = get_all_developers()
    if developers:
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_developers_management_keyboard()
        )
    else:
        await callback.message.answer(
            "📋 Список разработчиков пуст.",
            reply_markup=get_developers_management_keyboard()
        )


@router.message(F.text == "🔙 Главное меню")
async def back_to_main_from_developers(message: Message, state: FSMContext):
    """Возврат в главное меню из раздела разработчиков"""
    from storage import get_user_by_id, is_admin
    await state.clear()
    user_id = message.from_user.id
    user = get_user_by_id(user_id)
    user_role = user.role if user else None
    await message.answer(
        "🔙 Главное меню",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin(user_id), user_role=user_role)
    )


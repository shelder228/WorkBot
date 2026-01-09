from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import (
    get_main_menu_keyboard,
    get_status_management_keyboard,
    get_responsible_keyboard,
    get_status_list_keyboard
)
from storage import (
    get_all_statuses,
    add_status,
    delete_status,
    get_status_by_id
)

router = Router()


class StatusCreation(StatesGroup):
    waiting_for_name = State()
    waiting_for_responsible = State()


@router.message(F.text == "⚙️ Управление Статусами")
async def status_management_handler(message: Message):
    """Обработчик для кнопки 'Управление Статусами'"""
    from storage import get_user_by_id, is_admin
    user_id = message.from_user.id
    user = get_user_by_id(user_id)
    
    # Проверяем, что пользователь имеет роль "Лёша" или является админом
    if not user or (user.role != "Лёша" and not is_admin(user_id)):
        await message.answer(
            "❌ У вас нет прав доступа к управлению статусами.\n"
            "Доступ разрешен только для пользователей с ролью 'Лёша'.",
            reply_markup=get_main_menu_keyboard(is_admin=is_admin(user_id), user_role=user.role if user else None)
        )
        return
    
    await message.answer(
        "⚙️ Управление Статусами\n\n"
        "Выберите действие:",
        reply_markup=get_status_management_keyboard()
    )


@router.message(F.text == "🔙 Главное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    """Возврат в главное меню"""
    from storage import get_user_by_id, is_admin
    await state.clear()
    user_id = message.from_user.id
    user = get_user_by_id(user_id)
    user_role = user.role if user else None
    await message.answer(
        "🔙 Главное меню",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin(user_id), user_role=user_role)
    )


@router.message(F.text == "📋 Список статусов")
async def list_statuses_handler(message: Message):
    """Показывает список всех статусов"""
    statuses = get_all_statuses()
    
    if not statuses:
        await message.answer(
            "📋 Список статусов пуст.\n\n"
            "Добавьте первый статус!",
            reply_markup=get_status_management_keyboard()
        )
        return
    
    status_list = "\n".join([f"{i+1}. {status}" for i, status in enumerate(statuses)])
    
    await message.answer(
        f"📋 Список статусов ({len(statuses)}):\n\n{status_list}",
        reply_markup=get_status_management_keyboard()
    )


@router.message(F.text == "➕ Добавить статус")
async def add_status_start(message: Message, state: FSMContext):
    """Начинает процесс добавления статуса"""
    await state.set_state(StatusCreation.waiting_for_name)
    await message.answer(
        "➕ Добавление нового статуса\n\n"
        "Введите название статуса:",
        reply_markup=None
    )


@router.message(StatusCreation.waiting_for_name)
async def process_status_name(message: Message, state: FSMContext):
    """Обрабатывает название статуса"""
    status_name = message.text.strip()
    
    if not status_name:
        await message.answer("❌ Название не может быть пустым. Попробуйте снова:")
        return
    
    await state.update_data(status_name=status_name)
    await state.set_state(StatusCreation.waiting_for_responsible)
    
    await message.answer(
        f"✅ Название: {status_name}\n\n"
        "Теперь выберите ответственного:",
        reply_markup=get_responsible_keyboard()
    )


@router.callback_query(F.data.startswith("responsible_"))
async def process_responsible(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор ответственного"""
    responsible = callback.data.split("_", 1)[1]
    data = await state.get_data()
    status_name = data.get("status_name")
    
    if not status_name:
        await callback.answer("❌ Ошибка: название статуса не найдено", show_alert=True)
        await state.clear()
        return
    
    # Создаем статус
    new_status = add_status(status_name, responsible)
    
    await callback.message.edit_text(
        f"✅ Статус успешно добавлен!\n\n"
        f"📝 Название: {new_status.name}\n"
        f"👤 Ответственный: {new_status.responsible}\n"
        f"🆔 ID: {new_status.id}"
    )
    
    await callback.answer("Статус добавлен!")
    await state.clear()
    
    # Отправляем клавиатуру управления
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_status_management_keyboard()
    )


@router.message(F.text == "🗑️ Удалить статус")
async def delete_status_start(message: Message):
    """Начинает процесс удаления статуса"""
    statuses = get_all_statuses()
    
    if not statuses:
        await message.answer(
            "❌ Нет статусов для удаления.",
            reply_markup=get_status_management_keyboard()
        )
        return
    
    await message.answer(
        "🗑️ Выберите статус для удаления:",
        reply_markup=get_status_list_keyboard(statuses, "delete")
    )


@router.callback_query(F.data.startswith("delete_status_"))
async def process_delete_status(callback: CallbackQuery):
    """Обрабатывает удаление статуса"""
    status_id = int(callback.data.split("_")[-1])
    status = get_status_by_id(status_id)
    
    if not status:
        await callback.answer("❌ Статус не найден", show_alert=True)
        return
    
    # Удаляем статус
    if delete_status(status_id):
        await callback.message.edit_text(
            f"✅ Статус удален:\n\n"
            f"📝 {status.name} ({status.responsible})"
        )
        await callback.answer("Статус удален!")
    else:
        await callback.answer("❌ Ошибка при удалении", show_alert=True)
    
    # Обновляем список
    statuses = get_all_statuses()
    if statuses:
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_status_management_keyboard()
        )
    else:
        await callback.message.answer(
            "📋 Список статусов пуст.",
            reply_markup=get_status_management_keyboard()
        )


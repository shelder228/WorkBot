from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards import (
    get_main_menu_keyboard,
    get_bot_settings_keyboard,
    get_users_list_keyboard,
    get_role_selection_keyboard,
    get_checklist_management_keyboard,
    get_statuses_for_checklist_keyboard,
    get_checklist_creation_keyboard
)
from storage import (
    get_all_users,
    get_user_by_id,
    set_user_role,
    is_admin,
    get_or_create_user,
    get_all_statuses,
    get_checklist_by_status_id,
    create_checklist,
    add_checklist_item,
    delete_checklist_item,
    get_all_checklists,
    get_status_by_id
)
from aiogram.fsm.state import State, StatesGroup

router = Router()


class ChecklistCreation(StatesGroup):
    waiting_for_status = State()
    waiting_for_item_text = State()


@router.message(F.text == "⚙️ Настройка бота")
async def bot_settings_handler(message: Message):
    """Обработчик для кнопки 'Настройка бота'"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer(
            "❌ У вас нет прав доступа к настройкам бота.",
            reply_markup=get_main_menu_keyboard(is_admin=False)
        )
        return
    
    await message.answer(
        "⚙️ Настройка бота\n\n"
        "Выберите действие:",
        reply_markup=get_bot_settings_keyboard()
    )


@router.message(F.text == "👥 Выбор роли")
async def role_selection_handler(message: Message):
    """Обработчик для кнопки 'Выбор роли'"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer(
            "❌ У вас нет прав доступа.",
            reply_markup=get_main_menu_keyboard(is_admin=False)
        )
        return
    
    users = get_all_users()
    
    if not users:
        await message.answer(
            "👥 Выбор роли\n\n"
            "Пока нет пользователей в системе.",
            reply_markup=get_bot_settings_keyboard()
        )
        return
    
    await message.answer(
        "👥 Выбор роли\n\n"
        "Выберите пользователя для назначения роли:",
        reply_markup=get_users_list_keyboard(users, "select_role")
    )


@router.callback_query(F.data.startswith("select_role_"))
async def select_user_for_role(callback: CallbackQuery):
    """Обработчик выбора пользователя для назначения роли"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа", show_alert=True)
        return
    
    target_user_id = int(callback.data.split("_")[-1])
    target_user = get_user_by_id(target_user_id)
    
    if not target_user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"👥 Выбор роли\n\n"
        f"Пользователь: {target_user.first_name or target_user.username or f'ID:{target_user_id}'}\n"
        f"Текущая роль: {target_user.role}\n\n"
        f"Выберите новую роль:"
    )
    await callback.answer()
    
    await callback.message.answer(
        "Выберите роль:",
        reply_markup=get_role_selection_keyboard(target_user_id)
    )


@router.callback_query(F.data.startswith("set_role_"))
async def set_user_role_callback(callback: CallbackQuery):
    """Обработчик установки роли пользователю"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа", show_alert=True)
        return
    
    # Парсим callback_data: set_role_{user_id}_{role}
    parts = callback.data.split("_")
    target_user_id = int(parts[2])
    role = parts[3]  # admin, Игнат, Лёша, user
    
    target_user = get_user_by_id(target_user_id)
    
    if not target_user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    # Устанавливаем роль
    if set_user_role(target_user_id, role):
        role_names = {
            "admin": "Админ",
            "Игнат": "Игнат",
            "Лёша": "Лёша",
            "user": "Пользователь"
        }
        role_name = role_names.get(role, role)
        
        await callback.message.edit_text(
            f"✅ Роль успешно изменена!\n\n"
            f"Пользователь: {target_user.first_name or target_user.username or f'ID:{target_user_id}'}\n"
            f"Новая роль: {role_name}"
        )
        await callback.answer("Роль изменена!")
        
        # Возвращаем к списку пользователей
        users = get_all_users()
        await callback.message.answer(
            "Выберите пользователя для назначения роли:",
            reply_markup=get_users_list_keyboard(users, "select_role")
        )
    else:
        await callback.answer("❌ Ошибка при изменении роли", show_alert=True)


@router.message(F.text == "📋 Управление чек-листами")
async def checklist_management_handler(message: Message):
    """Обработчик для кнопки 'Управление чек-листами'"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer(
            "❌ У вас нет прав доступа.",
            reply_markup=get_main_menu_keyboard(is_admin=False)
        )
        return
    
    await message.answer(
        "📋 Управление чек-листами\n\n"
        "Выберите действие:",
        reply_markup=get_checklist_management_keyboard()
    )


@router.message(F.text == "➕ Добавить чек-лист")
async def add_checklist_start(message: Message, state: FSMContext):
    """Начинает процесс добавления чек-листа"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("❌ У вас нет прав доступа")
        return
    
    statuses = get_all_statuses()
    
    if not statuses:
        await message.answer(
            "❌ Нет доступных статусов.\n"
            "Сначала создайте статусы.",
            reply_markup=get_checklist_management_keyboard()
        )
        return
    
    await state.set_state(ChecklistCreation.waiting_for_status)
    await message.answer(
        "➕ Добавление чек-листа\n\n"
        "Выберите статус для создания чек-листа:",
        reply_markup=get_statuses_for_checklist_keyboard(statuses, "select_checklist_status")
    )


@router.callback_query(F.data.startswith("select_checklist_status_"))
async def select_checklist_status(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора статуса для чек-листа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа", show_alert=True)
        return
    
    status_id = int(callback.data.split("_")[-1])
    status = get_status_by_id(status_id)
    
    if not status:
        await callback.answer("❌ Статус не найден", show_alert=True)
        return
    
    # Создаем чек-лист, если его еще нет
    checklist = get_checklist_by_status_id(status_id)
    if not checklist:
        checklist = create_checklist(status_id)
    
    await state.update_data(status_id=status_id)
    await state.set_state(ChecklistCreation.waiting_for_item_text)
    
    await callback.message.edit_text(
        f"➕ Добавление чек-листа\n\n"
        f"Статус: {status.name}\n\n"
        f"Введите текст пункта чек-листа:"
    )
    await callback.answer()


@router.message(ChecklistCreation.waiting_for_item_text)
async def process_checklist_item(message: Message, state: FSMContext):
    """Обрабатывает текст пункта чек-листа"""
    # Проверяем, не нажата ли кнопка "Готово"
    if message.text == "✅ Готово":
        data = await state.get_data()
        status_id = data.get("status_id")
        status = get_status_by_id(status_id) if status_id else None
        
        checklist = get_checklist_by_status_id(status_id) if status_id else None
        items_count = len(checklist.items) if checklist else 0
        
        await message.answer(
            f"✅ Чек-лист создан!\n\n"
            f"Статус: {status.name if status else f'ID:{status_id}'}\n"
            f"Пунктов: {items_count}",
            reply_markup=get_checklist_management_keyboard()
        )
        await state.clear()
        return
    
    if message.text == "🔙 Назад":
        await state.clear()
        await message.answer(
            "📋 Управление чек-листами\n\n"
            "Выберите действие:",
            reply_markup=get_checklist_management_keyboard()
        )
        return
    
    item_text = message.text.strip()
    
    if not item_text:
        await message.answer("❌ Текст не может быть пустым. Попробуйте снова:")
        return
    
    data = await state.get_data()
    status_id = data.get("status_id")
    
    if not status_id:
        await message.answer("❌ Ошибка: статус не найден")
        await state.clear()
        return
    
    # Добавляем пункт в чек-лист
    new_item = add_checklist_item(status_id, item_text)
    status = get_status_by_id(status_id)
    
    await message.answer(
        f"✅ Пункт добавлен в чек-лист!\n\n"
        f"Статус: {status.name if status else f'ID:{status_id}'}\n"
        f"Пункт: {new_item.text}\n\n"
        f"Введите следующий пункт или нажмите '✅ Готово' для завершения.",
        reply_markup=get_checklist_creation_keyboard()
    )


@router.message(F.text == "📝 Редактировать чек-лист")
async def edit_checklist_handler(message: Message):
    """Обработчик для редактирования чек-листа"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("❌ У вас нет прав доступа")
        return
    
    statuses = get_all_statuses()
    
    if not statuses:
        await message.answer(
            "❌ Нет доступных статусов.",
            reply_markup=get_checklist_management_keyboard()
        )
        return
    
    await message.answer(
        "📝 Редактирование чек-листа\n\n"
        "Выберите статус для редактирования чек-листа:",
        reply_markup=get_statuses_for_checklist_keyboard(statuses, "edit_checklist")
    )


@router.callback_query(F.data.startswith("edit_checklist_"))
async def edit_checklist_callback(callback: CallbackQuery):
    """Обработчик выбора статуса для редактирования чек-листа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа", show_alert=True)
        return
    
    status_id = int(callback.data.split("_")[-1])
    checklist = get_checklist_by_status_id(status_id)
    status = get_status_by_id(status_id)
    
    if not status:
        await callback.answer("❌ Статус не найден", show_alert=True)
        return
    
    if not checklist or not checklist.items:
        await callback.message.edit_text(
            f"📝 Редактирование чек-листа\n\n"
            f"Статус: {status.name}\n\n"
            f"Чек-лист пуст. Добавьте пункты через 'Добавить чек-лист'."
        )
        await callback.answer()
        return
    
    # Показываем чек-лист с возможностью удаления пунктов
    from keyboards import InlineKeyboardButton, InlineKeyboardMarkup
    
    checklist_text = f"📝 Редактирование чек-листа\n\n"
    checklist_text += f"Статус: {status.name}\n\n"
    checklist_text += "Пункты чек-листа:\n\n"
    
    buttons = []
    for i, item in enumerate(checklist.items, 1):
        checklist_text += f"{i}. {item.text}\n"
        buttons.append([InlineKeyboardButton(
            text=f"🗑️ Удалить: {item.text[:30]}...",
            callback_data=f"delete_checklist_item_{status_id}_{item.id}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_checklist_menu"
    )])
    
    await callback.message.edit_text(
        checklist_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_checklist_item_"))
async def delete_checklist_item_callback(callback: CallbackQuery):
    """Обработчик удаления пункта чек-листа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа", show_alert=True)
        return
    
    # Парсим: delete_checklist_item_{status_id}_{item_id}
    parts = callback.data.split("_")
    status_id = int(parts[3])
    item_id = int(parts[4])
    
    if delete_checklist_item(status_id, item_id):
        checklist = get_checklist_by_status_id(status_id)
        status = get_status_by_id(status_id)
        
        if not checklist or not checklist.items:
            await callback.message.edit_text(
                f"✅ Пункт удален!\n\n"
                f"Чек-лист для статуса '{status.name if status else f'ID:{status_id}'}' теперь пуст."
            )
            await callback.answer("Пункт удален!")
            return
        
        from keyboards import InlineKeyboardButton, InlineKeyboardMarkup
        
        checklist_text = f"📝 Редактирование чек-листа\n\n"
        checklist_text += f"Статус: {status.name if status else f'ID:{status_id}'}\n\n"
        checklist_text += "Пункты чек-листа:\n\n"
        
        buttons = []
        for i, item in enumerate(checklist.items, 1):
            checklist_text += f"{i}. {item.text}\n"
            buttons.append([InlineKeyboardButton(
                text=f"🗑️ Удалить: {item.text[:30]}...",
                callback_data=f"delete_checklist_item_{status_id}_{item.id}"
            )])
        
        buttons.append([InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_checklist_menu"
        )])
        
        await callback.message.edit_text(
            checklist_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        await callback.answer("Пункт удален!")
    else:
        await callback.answer("❌ Ошибка при удалении", show_alert=True)


@router.callback_query(F.data == "back_to_checklist_menu")
async def back_to_checklist_menu_callback(callback: CallbackQuery):
    """Возврат в меню управления чек-листами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📋 Управление чек-листами\n\n"
        "Выберите действие:"
    )
    await callback.answer()
    
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_checklist_management_keyboard()
    )


@router.message(F.text == "📋 Список чек-листов")
async def list_checklists_handler(message: Message):
    """Показывает список всех чек-листов"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("❌ У вас нет прав доступа")
        return
    
    checklists = get_all_checklists()
    
    if not checklists:
        await message.answer(
            "📋 Список чек-листов пуст.\n\n"
            "Добавьте первый чек-лист!",
            reply_markup=get_checklist_management_keyboard()
        )
        return
    
    checklists_list = []
    for checklist in checklists:
        status = get_status_by_id(checklist.status_id)
        status_name = status.name if status else f"ID:{checklist.status_id}"
        items_count = len(checklist.items)
        checklists_list.append(f"📋 {status_name}: {items_count} пунктов")
    
    await message.answer(
        f"📋 Список чек-листов ({len(checklists)}):\n\n" + "\n".join(checklists_list),
        reply_markup=get_checklist_management_keyboard()
    )


@router.message(F.text == "🔙 Главное меню")
async def back_to_main_from_admin(message: Message, state: FSMContext):
    """Возврат в главное меню из раздела админа"""
    await state.clear()
    user_id = message.from_user.id
    user = get_user_by_id(user_id)
    user_role = user.role if user else None
    await message.answer(
        "🔙 Главное меню",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin(user_id), user_role=user_role)
    )


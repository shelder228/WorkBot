from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List
from models import ProjectStatus, Character, Developer, User


def get_main_menu_keyboard(is_admin: bool = False, user_role: str = None) -> ReplyKeyboardMarkup:
    """Главное меню с кнопками"""
    buttons = [
        [KeyboardButton(text="📋 Проекты")],
        [KeyboardButton(text="📦 Архив")],
        [KeyboardButton(text="✅ Мои Задачи")],
        [KeyboardButton(text="👥 Разработчики")],
        [KeyboardButton(text="🔔 Настройки уведомлений")]
    ]
    
    # Показываем управление статусами и персонажами только для Лёша
    if user_role == "Лёша":
        buttons.append([KeyboardButton(text="⚙️ Управление Статусами")])
        buttons.append([KeyboardButton(text="🎭 Управление Персонажами")])
    
    if is_admin:
        buttons.append([KeyboardButton(text="⚙️ Настройка бота")])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие из меню"
    )
    return keyboard


def get_status_management_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура управления статусами"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить статус")],
            [KeyboardButton(text="🗑️ Удалить статус")],
            [KeyboardButton(text="📋 Список статусов")],
            [KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_responsible_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для выбора ответственного"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Игнат", callback_data="responsible_Игнат")],
            [InlineKeyboardButton(text="👤 Лёша", callback_data="responsible_Лёша")],
            [InlineKeyboardButton(text="⚪ никто", callback_data="responsible_никто")]
        ]
    )
    return keyboard


def get_status_list_keyboard(statuses: List[ProjectStatus], action: str = "delete", status_counts: dict = None) -> InlineKeyboardMarkup:
    """Клавиатура со списком статусов"""
    buttons = []
    for status in statuses:
        responsible_emoji = {
            "Игнат": "👤",
            "Лёша": "👤",
            "никто": "⚪"
        }
        emoji = responsible_emoji.get(status.responsible, "⚪")
        
        # Если передан словарь с количеством проектов, показываем его
        if status_counts and status.id in status_counts:
            count = status_counts[status.id]
            text = f"{emoji} {status.name} ({status.responsible}) - {count} проектов"
        else:
            text = f"{emoji} {status.name} ({status.responsible})"
        
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=f"{action}_status_{status.id}"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_active_projects_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для меню активных проектов"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Создать")],
            [KeyboardButton(text="🔍 Фильтры")],
            [KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_filters_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура фильтров для проектов (устарела, используется прямой выбор статусов)"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_projects")]
        ]
    )
    return keyboard


def get_notification_settings_keyboard(user) -> ReplyKeyboardMarkup:
    """Клавиатура настроек уведомлений"""
    status_text = "✅ Включены" if user.notifications_enabled else "❌ Выключены"
    interval_text = f"⏰ {user.notification_interval} мин"
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"🔔 Уведомления: {status_text}")],
            [KeyboardButton(text=f"⏰ Частота: {interval_text}")],
            [KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_notification_interval_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора интервала уведомлений"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="5 мин", callback_data="set_interval_5"),
                InlineKeyboardButton(text="10 мин", callback_data="set_interval_10"),
                InlineKeyboardButton(text="15 мин", callback_data="set_interval_15")
            ],
            [
                InlineKeyboardButton(text="20 мин", callback_data="set_interval_20"),
                InlineKeyboardButton(text="25 мин", callback_data="set_interval_25"),
                InlineKeyboardButton(text="30 мин", callback_data="set_interval_30")
            ],
            [
                InlineKeyboardButton(text="60 мин", callback_data="set_interval_60")
            ]
        ]
    )
    return keyboard


def get_characters_list_keyboard(characters: List[Character], action: str = "select") -> InlineKeyboardMarkup:
    """Клавиатура со списком персонажей"""
    buttons = []
    for character in characters:
        buttons.append([InlineKeyboardButton(
            text=character.name,
            callback_data=f"{action}_character_{character.id}"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_developers_list_keyboard(developers: List[Developer], action: str = "select") -> InlineKeyboardMarkup:
    """Клавиатура со списком разработчиков"""
    buttons = []
    for developer in developers:
        text = f"{developer.name} (@{developer.username})"
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=f"{action}_developer_{developer.id}"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_characters_management_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура управления персонажами"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить персонажа")],
            [KeyboardButton(text="🗑️ Удалить персонажа")],
            [KeyboardButton(text="📋 Список персонажей")],
            [KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_developers_management_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура управления разработчиками"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить разработчика")],
            [KeyboardButton(text="🗑️ Удалить разработчика")],
            [KeyboardButton(text="📋 Список разработчиков")],
            [KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_project_actions_keyboard(project_id: int, is_archive: bool = False) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура с действиями для проекта"""
    if is_archive:
        # Для архивных проектов показываем кнопку возврата
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="⬅️ Пред.Статус", callback_data=f"prev_status_{project_id}"),
                    InlineKeyboardButton(text="➡️ След.Статус", callback_data=f"next_status_{project_id}")
                ],
                [
                    InlineKeyboardButton(text="↩️ Вернуть в проекты", callback_data=f"restore_project_{project_id}"),
                    InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_project_{project_id}")
                ]
            ]
        )
    else:
        # Для активных проектов обычные кнопки
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_project_{project_id}"),
                    InlineKeyboardButton(text="⬅️ Пред.Статус", callback_data=f"prev_status_{project_id}")
                ],
                [
                    InlineKeyboardButton(text="➡️ След.Статус", callback_data=f"next_status_{project_id}"),
                    InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_project_{project_id}")
                ]
            ]
        )
    return keyboard


def get_archive_filters_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура фильтров для архива"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Опубликованные", callback_data="filter_archive_published")],
            [InlineKeyboardButton(text="🚫 Заблокированные", callback_data="filter_archive_banned")],
            [InlineKeyboardButton(text="📋 Все архивные", callback_data="filter_archive_all")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main_from_archive")]
        ]
    )
    return keyboard


def get_edit_project_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для выбора поля редактирования проекта"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Название", callback_data=f"edit_field_name_{project_id}")],
            [InlineKeyboardButton(text="🎭 Персонаж", callback_data=f"edit_field_character_{project_id}")],
            [InlineKeyboardButton(text="💻 Разработчик", callback_data=f"edit_field_developer_{project_id}")],
            [InlineKeyboardButton(text="📊 Статус", callback_data=f"edit_field_status_{project_id}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_edit_{project_id}")]
        ]
    )
    return keyboard


def get_statuses_list_keyboard(statuses: List[ProjectStatus], action: str = "select") -> InlineKeyboardMarkup:
    """Клавиатура со списком статусов"""
    buttons = []
    for status in statuses:
        # Форматируем название статуса с указанием ответственного
        if hasattr(status, 'responsible') and status.responsible != "никто":
            status_text = f"{status.name} ({status.responsible})"
        else:
            status_text = status.name
        
        buttons.append([InlineKeyboardButton(
            text=status_text,
            callback_data=f"{action}_status_{status.id}"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_delete_confirm_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для подтверждения удаления проекта"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{project_id}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_delete_{project_id}")
            ]
        ]
    )
    return keyboard


def get_bot_settings_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура настроек бота"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Выбор роли")],
            [KeyboardButton(text="📋 Управление чек-листами")],
            [KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_role_selection_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для выбора роли пользователя"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👑 Админ", callback_data=f"set_role_{user_id}_admin"),
                InlineKeyboardButton(text="👤 Игнат", callback_data=f"set_role_{user_id}_Игнат")
            ],
            [
                InlineKeyboardButton(text="👤 Лёша", callback_data=f"set_role_{user_id}_Лёша"),
                InlineKeyboardButton(text="👤 Пользователь", callback_data=f"set_role_{user_id}_user")
            ]
        ]
    )
    return keyboard


def get_users_list_keyboard(users: List[User], action: str = "select_role") -> InlineKeyboardMarkup:
    """Клавиатура со списком пользователей для выбора роли"""
    buttons = []
    for user in users:
        role_emoji = {
            "admin": "👑",
            "Игнат": "👤",
            "Лёша": "👤",
            "user": "👤"
        }
        emoji = role_emoji.get(user.role, "👤")
        name = user.first_name or user.username or f"ID:{user.user_id}"
        text = f"{emoji} {name} ({user.role})"
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=f"{action}_{user.user_id}"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_checklist_keyboard(status_id: int, project_id: int, checklist_items) -> InlineKeyboardMarkup:
    """Клавиатура с чек-листом"""
    buttons = []
    
    for item in checklist_items:
        checkbox = "✅" if item.checked else "☐"
        text = f"{checkbox} {item.text}"
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=f"toggle_checklist_{status_id}_{project_id}_{item.id}"
        )])
    
    # Кнопка "Перейти на следующий статус" (только если все отмечено)
    all_checked = all(item.checked for item in checklist_items) if checklist_items else True
    if all_checked and checklist_items:
        buttons.append([InlineKeyboardButton(
            text="➡️ Перейти на следующий статус",
            callback_data=f"confirm_next_status_{project_id}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад к проекту",
        callback_data=f"back_to_project_{project_id}"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_checklist_management_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура управления чек-листами"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить чек-лист")],
            [KeyboardButton(text="📝 Редактировать чек-лист")],
            [KeyboardButton(text="📋 Список чек-листов")],
            [KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_checklist_creation_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура при создании чек-листа"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Готово")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_statuses_for_checklist_keyboard(statuses, action: str = "select_checklist") -> InlineKeyboardMarkup:
    """Клавиатура со списком статусов для выбора чек-листа"""
    from models import ProjectStatus
    buttons = []
    for status in statuses:
        responsible_emoji = {
            "Игнат": "👤",
            "Лёша": "👤",
            "никто": "⚪"
        }
        emoji = responsible_emoji.get(status.responsible, "⚪")
        text = f"{emoji} {status.name} ({status.responsible})"
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=f"{action}_{status.id}"
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

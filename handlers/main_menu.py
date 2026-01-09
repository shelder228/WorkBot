from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards import get_main_menu_keyboard, get_project_actions_keyboard, get_archive_filters_keyboard
from storage import (
    get_user_by_id,
    get_projects_by_role,
    get_character_by_id,
    get_developer_by_id,
    get_status_by_id,
    is_admin,
    get_archive_projects,
    get_published_projects,
    get_banned_projects,
    get_all_statuses,
    get_project_by_id,
    update_project_status,
    is_archive_status
)


def format_status_name(status) -> str:
    """Форматирует название статуса с указанием ответственного"""
    if not status:
        return "Неизвестный статус"
    
    if status.responsible != "никто":
        return f"{status.name} ({status.responsible})"
    else:
        return status.name

router = Router()


@router.message(F.text == "📦 Архив")
async def archive_handler(message: Message):
    """Обработчик для кнопки 'Архив'"""
    user_id = message.from_user.id
    user = get_user_by_id(user_id)
    user_role = user.role if user else None
    
    published_projects = get_published_projects()
    banned_projects = get_banned_projects()
    archive_projects = get_archive_projects()
    
    await message.answer(
        f"📦 Архив\n\n"
        f"✅ Опубликовано: {len(published_projects)}\n"
        f"🚫 Заблокировано: {len(banned_projects)}\n\n"
        f"Всего в архиве: {len(archive_projects)}",
        reply_markup=get_archive_filters_keyboard()
    )
    
    # Показываем все архивные проекты
    if archive_projects:
        await _show_archive_projects(message, archive_projects)
    else:
        await message.answer(
            "Архив пуст.",
            reply_markup=get_main_menu_keyboard(is_admin=is_admin(user_id), user_role=user_role)
        )


async def _show_archive_projects(message: Message, projects: list):
    """Вспомогательная функция для отображения архивных проектов"""
    for i, project in enumerate(projects, 1):
        character = get_character_by_id(project.character_id)
        developer = get_developer_by_id(project.developer_id)
        status = get_status_by_id(project.status_id)
        
        character_name = character.name if character else f"ID:{project.character_id}"
        developer_name = developer.name if developer else f"ID:{project.developer_id}"
        developer_username = f"@{developer.username}" if developer and developer.username else ""
        status_name = format_status_name(status) if status else f"ID:{project.status_id}"
        
        # Определяем тип архива
        archive_type = "✅ Опубликован" if status and status.name == "Живой" else "🚫 Заблокирован"
        
        project_text = f"{i}. 📁 {project.name}\n"
        project_text += f"🎭 Персонаж: {character_name}\n"
        project_text += f"💻 Разработчик: {developer_name}"
        if developer_username:
            project_text += f" {developer_username}"
        project_text += f"\n📊 Статус: {status_name}\n"
        project_text += f"{archive_type}"
        
        await message.answer(
            project_text,
            reply_markup=get_project_actions_keyboard(project.id, is_archive=True)
        )


@router.message(F.text == "✅ Мои Задачи")
async def my_tasks_handler(message: Message):
    """Обработчик для кнопки 'Мои Задачи'"""
    user_id = message.from_user.id
    user = get_user_by_id(user_id)
    
    # Проверяем роль пользователя
    if not user or user.role not in ["Игнат", "Лёша"]:
        await message.answer(
            "✅ Мои Задачи\n\n"
            "У вас нет назначенных задач.\n"
            "Задачи назначаются только пользователям с ролями 'Игнат' или 'Лёша'.",
            reply_markup=get_main_menu_keyboard(is_admin=is_admin(user_id), user_role=user.role)
        )
        return
    
    # Получаем проекты для роли пользователя
    projects = get_projects_by_role(user.role)
    
    if not projects:
        await message.answer(
            f"✅ Мои Задачи ({user.role})\n\n"
            "У вас пока нет назначенных задач.",
            reply_markup=get_main_menu_keyboard(is_admin=is_admin(user_id), user_role=user.role)
        )
        return
    
    # Показываем заголовок
    await message.answer(
        f"✅ Мои Задачи ({user.role})\n\n"
        f"Всего задач: {len(projects)}\n",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin(user_id), user_role=user.role)
    )
    
    # Показываем каждый проект отдельным сообщением с кнопками
    for i, project in enumerate(projects, 1):
        character = get_character_by_id(project.character_id)
        developer = get_developer_by_id(project.developer_id)
        status = get_status_by_id(project.status_id)
        
        character_name = character.name if character else f"ID:{project.character_id}"
        developer_name = developer.name if developer else f"ID:{project.developer_id}"
        developer_username = f"@{developer.username}" if developer and developer.username else ""
        status_name = format_status_name(status) if status else f"ID:{project.status_id}"
        
        project_text = f"{i}. 📁 {project.name}\n"
        project_text += f"🎭 Персонаж: {character_name}\n"
        project_text += f"💻 Разработчик: {developer_name}"
        if developer_username:
            project_text += f" {developer_username}"
        project_text += f"\n📊 Статус: {status_name}"
        
        await message.answer(
            project_text,
            reply_markup=get_project_actions_keyboard(project.id, is_archive=False)
        )


@router.callback_query(F.data == "filter_archive_published")
async def filter_archive_published_callback(callback: CallbackQuery):
    """Фильтр архива: только опубликованные"""
    published_projects = get_published_projects()
    
    await callback.message.edit_text(
        f"📦 Архив - Опубликованные\n\n"
        f"Найдено проектов: {len(published_projects)}"
    )
    await callback.answer()
    
    if published_projects:
        await _show_archive_projects(callback.message, published_projects)
    else:
        await callback.message.answer(
            "Опубликованных проектов нет.",
            reply_markup=get_archive_filters_keyboard()
        )


@router.callback_query(F.data == "filter_archive_banned")
async def filter_archive_banned_callback(callback: CallbackQuery):
    """Фильтр архива: только заблокированные"""
    banned_projects = get_banned_projects()
    
    await callback.message.edit_text(
        f"📦 Архив - Заблокированные\n\n"
        f"Найдено проектов: {len(banned_projects)}"
    )
    await callback.answer()
    
    if banned_projects:
        await _show_archive_projects(callback.message, banned_projects)
    else:
        await callback.message.answer(
            "Заблокированных проектов нет.",
            reply_markup=get_archive_filters_keyboard()
        )


@router.callback_query(F.data == "filter_archive_all")
async def filter_archive_all_callback(callback: CallbackQuery):
    """Фильтр архива: все архивные"""
    archive_projects = get_archive_projects()
    published_projects = get_published_projects()
    banned_projects = get_banned_projects()
    
    await callback.message.edit_text(
        f"📦 Архив - Все\n\n"
        f"✅ Опубликовано: {len(published_projects)}\n"
        f"🚫 Заблокировано: {len(banned_projects)}\n\n"
        f"Всего: {len(archive_projects)}"
    )
    await callback.answer()
    
    if archive_projects:
        await _show_archive_projects(callback.message, archive_projects)
    else:
        await callback.message.answer(
            "Архив пуст.",
            reply_markup=get_archive_filters_keyboard()
        )


@router.callback_query(F.data == "back_to_main_from_archive")
async def back_to_main_from_archive_callback(callback: CallbackQuery):
    """Возврат в главное меню из архива"""
    from storage import get_user_by_id, is_admin
    user_id = callback.from_user.id
    user = get_user_by_id(user_id)
    user_role = user.role if user else None
    
    await callback.message.edit_text("🔙 Главное меню")
    await callback.answer()
    
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin(user_id), user_role=user_role)
    )


@router.callback_query(F.data.startswith("restore_project_"))
async def restore_project_callback(callback: CallbackQuery):
    """Обработчик возврата проекта из архива в активные"""
    project_id = int(callback.data.split("_")[-1])
    project = get_project_by_id(project_id)
    
    if not project:
        await callback.answer("❌ Проект не найден", show_alert=True)
        return
    
    # Проверяем, что проект действительно в архиве
    if not is_archive_status(project.status_id):
        await callback.answer("❌ Проект не в архиве", show_alert=True)
        return
    
    # Находим первый не-архивный статус для возврата
    all_statuses = get_all_statuses()
    non_archive_statuses = [s for s in all_statuses if not is_archive_status(s.id)]
    
    if not non_archive_statuses:
        await callback.answer("❌ Нет доступных статусов для возврата", show_alert=True)
        return
    
    # Берем первый статус (самый ранний по ID)
    first_status = min(non_archive_statuses, key=lambda s: s.id)
    
    # Обновляем статус проекта
    if update_project_status(project_id, first_status.id):
        character = get_character_by_id(project.character_id)
        developer = get_developer_by_id(project.developer_id)
        new_status = get_status_by_id(first_status.id)
        
        character_name = character.name if character else f"ID:{project.character_id}"
        developer_name = developer.name if developer else f"ID:{project.developer_id}"
        developer_username = f"@{developer.username}" if developer and developer.username else ""
        status_name = format_status_name(new_status) if new_status else f"ID:{first_status.id}"
        
        await callback.message.edit_text(
            f"✅ Проект возвращен в активные!\n\n"
            f"📁 {project.name}\n"
            f"📊 Новый статус: {status_name}"
        )
        await callback.answer("Проект возвращен!")
        
        # Обновляем список архива
        archive_projects = get_archive_projects()
        published_projects = get_published_projects()
        banned_projects = get_banned_projects()
        
        await callback.message.answer(
            f"📦 Архив\n\n"
            f"✅ Опубликовано: {len(published_projects)}\n"
            f"🚫 Заблокировано: {len(banned_projects)}\n\n"
            f"Всего в архиве: {len(archive_projects)}",
            reply_markup=get_archive_filters_keyboard()
        )
        
        if archive_projects:
            await _show_archive_projects(callback.message, archive_projects)
    else:
        await callback.answer("❌ Ошибка при возврате проекта", show_alert=True)


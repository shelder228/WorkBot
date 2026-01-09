from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from keyboards import (
    get_main_menu_keyboard,
    get_active_projects_keyboard,
    get_characters_list_keyboard,
    get_developers_list_keyboard,
    get_project_actions_keyboard,
    get_delete_confirm_keyboard,
    get_checklist_keyboard,
    get_filters_keyboard,
    get_edit_project_keyboard,
    get_statuses_list_keyboard
)
from storage import (
    get_all_projects,
    get_active_projects,
    get_archive_projects,
    get_published_projects,
    get_banned_projects,
    add_project,
    get_first_status,
    get_all_characters,
    get_all_developers,
    get_all_statuses,
    get_character_by_id,
    get_developer_by_id,
    get_status_by_id,
    get_project_by_id,
    update_project_status,
    update_project,
    delete_project,
    get_next_status_id,
    get_prev_status_id,
    get_checklist_by_status_id,
    reset_checklist,
    is_archive_status
)

router = Router()


def format_status_name(status) -> str:
    """Форматирует название статуса с указанием ответственного"""
    if not status:
        return "Неизвестный статус"
    
    if status.responsible != "никто":
        return f"{status.name} ({status.responsible})"
    else:
        return status.name


class ProjectCreation(StatesGroup):
    waiting_for_name = State()
    waiting_for_character = State()
    waiting_for_developer = State()


class ProjectEdit(StatesGroup):
    waiting_for_field = State()
    waiting_for_name = State()
    waiting_for_character = State()
    waiting_for_developer = State()
    waiting_for_status = State()


@router.message(F.text == "📋 Проекты")
async def active_projects_handler(message: Message, state: FSMContext):
    """Обработчик для кнопки 'Проекты'"""
    # Очищаем состояние, если оно было активно
    current_state = await state.get_state()
    if current_state:
        await state.clear()
    
    # Очищаем фильтры из состояния
    await state.update_data(filter_status_id=None, filter_character_id=None, filter_developer_id=None)
    
    projects = get_active_projects()  # Показываем только активные проекты
    
    if not projects:
        text = "📋 Проекты\n\n" \
               "Проектов пока нет.\n" \
               "Создайте первый проект!"
        await message.answer(
            text,
            reply_markup=get_active_projects_keyboard()
        )
        return
    
    # Показываем заголовок
    await message.answer(
        f"📋 Проекты\n\nВсего проектов: {len(projects)}\n",
        reply_markup=get_active_projects_keyboard()
    )
    
    # Показываем каждый проект отдельным сообщением с кнопками
    await _show_projects(message, projects)


async def _show_projects(message: Message, projects: list):
    """Вспомогательная функция для отображения проектов"""
    for i, project in enumerate(projects, 1):
        character = get_character_by_id(project.character_id)
        developer = get_developer_by_id(project.developer_id)
        status = get_status_by_id(project.status_id)
        
        character_name = character.name if character else f"ID:{project.character_id}"
        developer_name = developer.name if developer else f"ID:{project.developer_id}"
        developer_username = f"@{developer.username}" if developer and developer.username else ""
        
        # Формируем статус с ответственным
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


@router.message(F.text == "🔍 Фильтры")
async def filters_handler(message: Message):
    """Обработчик для кнопки 'Фильтры' - показывает только статусы с проектами"""
    projects = get_active_projects()  # Показываем только активные проекты
    
    if not projects:
        await message.answer(
            "📋 Проекты\n\n"
            "Проектов пока нет.\n"
            "Создайте первый проект!",
            reply_markup=get_active_projects_keyboard()
        )
        return
    
    # Подсчитываем проекты по статусам
    status_counts = {}
    for project in projects:
        status_counts[project.status_id] = status_counts.get(project.status_id, 0) + 1
    
    # Получаем только статусы, в которых есть проекты (больше 0)
    all_statuses = get_all_statuses()
    statuses_with_projects = [s for s in all_statuses if s.id in status_counts and status_counts[s.id] > 0]
    
    if not statuses_with_projects:
        await message.answer(
            "❌ Нет статусов с проектами",
            reply_markup=get_active_projects_keyboard()
        )
        return
    
    from keyboards import get_status_list_keyboard
    await message.answer(
        "🔍 Фильтры проектов\n\n"
        "Выберите статус для просмотра проектов:",
        reply_markup=get_status_list_keyboard(statuses_with_projects, "filter_status", status_counts)
    )


@router.callback_query(F.data == "filter_by_status")
async def filter_by_status_callback(callback: CallbackQuery):
    """Обработчик фильтра по статусу - показывает только статусы с проектами"""
    projects = get_active_projects()  # Показываем только активные проекты
    
    if not projects:
        await callback.answer("❌ Нет проектов", show_alert=True)
        return
    
    # Подсчитываем проекты по статусам
    status_counts = {}
    for project in projects:
        status_counts[project.status_id] = status_counts.get(project.status_id, 0) + 1
    
    # Получаем только статусы, в которых есть проекты
    all_statuses = get_all_statuses()
    statuses_with_projects = [s for s in all_statuses if s.id in status_counts and status_counts[s.id] > 0]
    
    if not statuses_with_projects:
        await callback.answer("❌ Нет статусов с проектами", show_alert=True)
        return
    
    from keyboards import get_status_list_keyboard
    await callback.message.edit_text(
        "🔍 Фильтр по статусу\n\n"
        "Выберите статус для просмотра проектов:",
        reply_markup=get_status_list_keyboard(statuses_with_projects, "filter_status")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("filter_status_"))
async def apply_status_filter(callback: CallbackQuery, state: FSMContext):
    """Применяет фильтр по статусу"""
    status_id = int(callback.data.split("_")[-1])
    await state.update_data(filter_status_id=status_id)
    
    projects = get_active_projects()  # Показываем только активные проекты
    filtered_projects = [p for p in projects if p.status_id == status_id]
    
    status = get_status_by_id(status_id)
    status_name = format_status_name(status) if status else f"ID:{status_id}"
    
    await callback.message.edit_text(
        f"🔍 Фильтр: Статус = {status_name}\n\n"
        f"Найдено проектов: {len(filtered_projects)}"
    )
    await callback.answer()
    
    if filtered_projects:
        await _show_projects(callback.message, filtered_projects)
    else:
        await callback.message.answer(
            "Проекты не найдены.",
            reply_markup=get_active_projects_keyboard()
        )


@router.callback_query(F.data == "filter_by_character")
async def filter_by_character_callback(callback: CallbackQuery):
    """Обработчик фильтра по персонажу"""
    characters = get_all_characters()
    
    if not characters:
        await callback.answer("❌ Нет доступных персонажей", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🔍 Фильтр по персонажу\n\n"
        "Выберите персонажа:",
        reply_markup=get_characters_list_keyboard(characters, "filter_character")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("filter_character_"))
async def apply_character_filter(callback: CallbackQuery, state: FSMContext):
    """Применяет фильтр по персонажу"""
    character_id = int(callback.data.split("_")[-1])
    await state.update_data(filter_character_id=character_id)
    
    projects = get_active_projects()  # Показываем только активные проекты
    filtered_projects = [p for p in projects if p.character_id == character_id]
    
    character = get_character_by_id(character_id)
    character_name = character.name if character else f"ID:{character_id}"
    
    await callback.message.edit_text(
        f"🔍 Фильтр: Персонаж = {character_name}\n\n"
        f"Найдено проектов: {len(filtered_projects)}"
    )
    await callback.answer()
    
    if filtered_projects:
        await _show_projects(callback.message, filtered_projects)
    else:
        await callback.message.answer(
            "Проекты не найдены.",
            reply_markup=get_active_projects_keyboard()
        )


@router.callback_query(F.data == "filter_by_developer")
async def filter_by_developer_callback(callback: CallbackQuery):
    """Обработчик фильтра по разработчику"""
    developers = get_all_developers()
    
    if not developers:
        await callback.answer("❌ Нет доступных разработчиков", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🔍 Фильтр по разработчику\n\n"
        "Выберите разработчика:",
        reply_markup=get_developers_list_keyboard(developers, "filter_developer")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("filter_developer_"))
async def apply_developer_filter(callback: CallbackQuery, state: FSMContext):
    """Применяет фильтр по разработчику"""
    developer_id = int(callback.data.split("_")[-1])
    await state.update_data(filter_developer_id=developer_id)
    
    projects = get_active_projects()  # Показываем только активные проекты
    filtered_projects = [p for p in projects if p.developer_id == developer_id]
    
    developer = get_developer_by_id(developer_id)
    developer_name = developer.name if developer else f"ID:{developer_id}"
    
    await callback.message.edit_text(
        f"🔍 Фильтр: Разработчик = {developer_name}\n\n"
        f"Найдено проектов: {len(filtered_projects)}"
    )
    await callback.answer()
    
    if filtered_projects:
        await _show_projects(callback.message, filtered_projects)
    else:
        await callback.message.answer(
            "Проекты не найдены.",
            reply_markup=get_active_projects_keyboard()
        )


@router.callback_query(F.data == "reset_filters")
async def reset_filters_callback(callback: CallbackQuery, state: FSMContext):
    """Сбрасывает фильтры"""
    await state.update_data(filter_status_id=None, filter_character_id=None, filter_developer_id=None)
    
    projects = get_active_projects()  # Показываем только активные проекты
    
    await callback.message.edit_text(
        f"✅ Фильтры сброшены\n\n"
        f"Всего проектов: {len(projects)}"
    )
    await callback.answer("Фильтры сброшены")
    
    if projects:
        await _show_projects(callback.message, projects)
    else:
        await callback.message.answer(
            "Проектов пока нет.",
            reply_markup=get_active_projects_keyboard()
        )


@router.callback_query(F.data == "back_to_projects")
async def back_to_projects_callback(callback: CallbackQuery):
    """Возврат к списку проектов"""
    await callback.message.edit_text(
        "📋 Проекты"
    )
    await callback.answer()
    
    projects = get_active_projects()  # Показываем только активные проекты
    if projects:
        await _show_projects(callback.message, projects)
    else:
        await callback.message.answer(
            "Проектов пока нет.",
            reply_markup=get_active_projects_keyboard()
        )


@router.message(F.text == "➕ Создать")
async def create_project_start(message: Message, state: FSMContext):
    """Начинает процесс создания проекта"""
    # Получаем первый статус
    first_status = get_first_status()
    
    if not first_status:
        await message.answer(
            "❌ Ошибка: нет доступных статусов.\n"
            "Сначала создайте хотя бы один статус в разделе 'Управление Статусами'.",
            reply_markup=get_active_projects_keyboard()
        )
        return
    
    await state.update_data(status_id=first_status.id, status_name=first_status.name)
    await state.set_state(ProjectCreation.waiting_for_name)
    
    await message.answer(
        "➕ Создание нового проекта\n\n"
        "Введите название проекта:",
        reply_markup=None
    )


@router.message(ProjectCreation.waiting_for_name)
async def process_project_name(message: Message, state: FSMContext):
    """Обрабатывает название проекта"""
    project_name = message.text.strip()
    
    if not project_name:
        await message.answer("❌ Название не может быть пустым. Попробуйте снова:")
        return
    
    await state.update_data(name=project_name)
    await state.set_state(ProjectCreation.waiting_for_character)
    
    # Получаем список персонажей
    characters = get_all_characters()
    
    if not characters:
        await message.answer(
            f"✅ Название: {project_name}\n\n"
            "❌ Нет доступных персонажей.\n"
            "Сначала добавьте персонажей в разделе 'Управление Персонажами'.",
            reply_markup=get_active_projects_keyboard()
        )
        await state.clear()
        return
    
    await message.answer(
        f"✅ Название: {project_name}\n\n"
        "Выберите персонажа:",
        reply_markup=get_characters_list_keyboard(characters, "select")
    )


@router.callback_query(F.data.startswith("select_character_"))
async def process_project_character(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор персонажа проекта"""
    character_id = int(callback.data.split("_")[-1])
    character = get_character_by_id(character_id)
    
    if not character:
        await callback.answer("❌ Персонаж не найден", show_alert=True)
        return
    
    await state.update_data(character_id=character_id, character_name=character.name)
    await state.set_state(ProjectCreation.waiting_for_developer)
    
    data = await state.get_data()
    project_name = data.get("name")
    
    # Получаем список разработчиков
    developers = get_all_developers()
    
    if not developers:
        await callback.message.edit_text(
            f"✅ Название: {project_name}\n"
            f"✅ Персонаж: {character.name}\n\n"
            "❌ Нет доступных разработчиков.\n"
            "Сначала добавьте разработчиков в разделе 'Разработчики'."
        )
        await callback.answer()
        await state.clear()
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_active_projects_keyboard()
        )
        return
    
    await callback.message.edit_text(
        f"✅ Название: {project_name}\n"
        f"✅ Персонаж: {character.name}\n\n"
        "Выберите разработчика:"
    )
    await callback.answer()
    
    await callback.message.answer(
        "Выберите разработчика:",
        reply_markup=get_developers_list_keyboard(developers, "select")
    )


@router.callback_query(F.data.startswith("select_developer_"))
async def process_project_developer(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор разработчика проекта"""
    developer_id = int(callback.data.split("_")[-1])
    developer = get_developer_by_id(developer_id)
    
    if not developer:
        await callback.answer("❌ Разработчик не найден", show_alert=True)
        return
    
    data = await state.get_data()
    name = data.get("name")
    character_id = data.get("character_id")
    character_name = data.get("character_name")
    status_id = data.get("status_id")
    status = get_status_by_id(status_id)
    
    if not status:
        await callback.answer("❌ Статус не найден", show_alert=True)
        await state.clear()
        return
    
    # Создаем проект
    new_project = add_project(name, character_id, developer_id, status_id)
    
    await callback.message.edit_text(
        f"✅ Проект успешно создан!\n\n"
        f"📁 Название: {new_project.name}\n"
        f"🎭 Персонаж: {character_name}\n"
        f"💻 Разработчик: {developer.name} (@{developer.username})\n"
        f"📊 Статус: {format_status_name(status)}\n"
        f"🆔 ID: {new_project.id}"
    )
    
    await callback.answer("Проект создан!")
    await state.clear()
    
    # Возвращаем клавиатуру активных проектов
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_active_projects_keyboard()
    )


@router.message(F.text == "✏️ Редактировать")
async def edit_project_handler(message: Message):
    """Обработчик для кнопки 'Редактировать'"""
    projects = get_active_projects()  # Показываем только активные проекты
    
    if not projects:
        await message.answer(
            "❌ Нет проектов для редактирования.\n"
            "Сначала создайте проект!",
            reply_markup=get_active_projects_keyboard()
        )
        return
    
    await message.answer(
        "✏️ Редактирование проектов\n\n"
        "Функционал редактирования будет добавлен позже.",
        reply_markup=get_active_projects_keyboard()
    )


@router.message(F.text == "🔙 Главное меню")
async def back_to_main_from_projects(message: Message, state: FSMContext):
    """Возврат в главное меню из раздела проектов"""
    from storage import get_user_by_id, is_admin
    await state.clear()
    user_id = message.from_user.id
    user = get_user_by_id(user_id)
    user_role = user.role if user else None
    await message.answer(
        "🔙 Главное меню",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin(user_id), user_role=user_role)
    )


@router.callback_query(F.data.startswith("edit_project_"))
async def edit_project_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Редактировать' проекта"""
    project_id = int(callback.data.split("_")[-1])
    project = get_project_by_id(project_id)
    
    if not project:
        await callback.answer("❌ Проект не найден", show_alert=True)
        return
    
    # Сохраняем ID проекта в состояние
    await state.update_data(project_id=project_id)
    
    # Показываем текущие данные проекта и клавиатуру выбора поля
    character = get_character_by_id(project.character_id)
    developer = get_developer_by_id(project.developer_id)
    status = get_status_by_id(project.status_id)
    
    character_name = character.name if character else f"ID:{project.character_id}"
    developer_name = developer.name if developer else f"ID:{project.developer_id}"
    developer_username = f" @{developer.username}" if developer and developer.username else ""
    status_name = format_status_name(status) if status else f"ID:{project.status_id}"
    
    project_text = f"✏️ Редактирование проекта\n\n"
    project_text += f"📁 Название: {project.name}\n"
    project_text += f"🎭 Персонаж: {character_name}\n"
    project_text += f"💻 Разработчик: {developer_name}{developer_username}\n"
    project_text += f"📊 Статус: {status_name}\n\n"
    project_text += "Выберите, что хотите изменить:"
    
    await callback.message.edit_text(
        project_text,
        reply_markup=get_edit_project_keyboard(project_id)
    )
    await callback.answer()
    await state.set_state(ProjectEdit.waiting_for_field)


@router.callback_query(F.data.startswith("edit_field_name_"))
async def edit_field_name_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора редактирования названия"""
    project_id = int(callback.data.split("_")[-1])
    project = get_project_by_id(project_id)
    
    if not project:
        await callback.answer("❌ Проект не найден", show_alert=True)
        return
    
    await state.update_data(project_id=project_id)
    await state.set_state(ProjectEdit.waiting_for_name)
    
    await callback.message.edit_text(
        f"✏️ Редактирование названия проекта\n\n"
        f"Текущее название: {project.name}\n\n"
        f"Введите новое название:"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field_character_"))
async def edit_field_character_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора редактирования персонажа"""
    project_id = int(callback.data.split("_")[-1])
    project = get_project_by_id(project_id)
    
    if not project:
        await callback.answer("❌ Проект не найден", show_alert=True)
        return
    
    characters = get_all_characters()
    
    if not characters:
        await callback.answer("❌ Нет доступных персонажей", show_alert=True)
        return
    
    await state.update_data(project_id=project_id)
    await state.set_state(ProjectEdit.waiting_for_character)
    
    current_character = get_character_by_id(project.character_id)
    current_character_name = current_character.name if current_character else "Не выбран"
    
    await callback.message.edit_text(
        f"✏️ Редактирование персонажа проекта\n\n"
        f"Текущий персонаж: {current_character_name}\n\n"
        f"Выберите нового персонажа:"
    )
    await callback.answer()
    
    await callback.message.answer(
        "Выберите персонажа:",
        reply_markup=get_characters_list_keyboard(characters, "edit")
    )


@router.callback_query(F.data.startswith("edit_field_developer_"))
async def edit_field_developer_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора редактирования разработчика"""
    project_id = int(callback.data.split("_")[-1])
    project = get_project_by_id(project_id)
    
    if not project:
        await callback.answer("❌ Проект не найден", show_alert=True)
        return
    
    developers = get_all_developers()
    
    if not developers:
        await callback.answer("❌ Нет доступных разработчиков", show_alert=True)
        return
    
    await state.update_data(project_id=project_id)
    await state.set_state(ProjectEdit.waiting_for_developer)
    
    current_developer = get_developer_by_id(project.developer_id)
    current_developer_name = current_developer.name if current_developer else "Не выбран"
    
    await callback.message.edit_text(
        f"✏️ Редактирование разработчика проекта\n\n"
        f"Текущий разработчик: {current_developer_name}\n\n"
        f"Выберите нового разработчика:"
    )
    await callback.answer()
    
    await callback.message.answer(
        "Выберите разработчика:",
        reply_markup=get_developers_list_keyboard(developers, "edit")
    )


@router.callback_query(F.data.startswith("edit_field_status_"))
async def edit_field_status_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора редактирования статуса"""
    project_id = int(callback.data.split("_")[-1])
    project = get_project_by_id(project_id)
    
    if not project:
        await callback.answer("❌ Проект не найден", show_alert=True)
        return
    
    statuses = get_all_statuses()
    
    if not statuses:
        await callback.answer("❌ Нет доступных статусов", show_alert=True)
        return
    
    await state.update_data(project_id=project_id)
    await state.set_state(ProjectEdit.waiting_for_status)
    
    current_status = get_status_by_id(project.status_id)
    current_status_name = format_status_name(current_status) if current_status else "Не выбран"
    
    await callback.message.edit_text(
        f"✏️ Редактирование статуса проекта\n\n"
        f"Текущий статус: {current_status_name}\n\n"
        f"Выберите новый статус:"
    )
    await callback.answer()
    
    await callback.message.answer(
        "Выберите статус:",
        reply_markup=get_statuses_list_keyboard(statuses, "edit")
    )


@router.callback_query(F.data.startswith("cancel_edit_"))
async def cancel_edit_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик отмены редактирования"""
    project_id = int(callback.data.split("_")[-1])
    project = get_project_by_id(project_id)
    
    if not project:
        await callback.answer("❌ Проект не найден", show_alert=True)
        return
    
    await state.clear()
    
    # Показываем проект снова
    character = get_character_by_id(project.character_id)
    developer = get_developer_by_id(project.developer_id)
    status = get_status_by_id(project.status_id)
    
    character_name = character.name if character else f"ID:{project.character_id}"
    developer_name = developer.name if developer else f"ID:{project.developer_id}"
    developer_username = f" @{developer.username}" if developer and developer.username else ""
    status_name = format_status_name(status) if status else f"ID:{project.status_id}"
    
    project_text = f"📁 {project.name}\n"
    project_text += f"🎭 Персонаж: {character_name}\n"
    project_text += f"💻 Разработчик: {developer_name}{developer_username}\n"
    project_text += f"📊 Статус: {status_name}"
    
    is_archive = is_archive_status(project.status_id)
    
    await callback.message.edit_text(
        project_text,
        reply_markup=get_project_actions_keyboard(project_id, is_archive=is_archive)
    )
    await callback.answer("Редактирование отменено")


@router.message(ProjectEdit.waiting_for_name)
async def process_edit_name(message: Message, state: FSMContext):
    """Обрабатывает новое название проекта"""
    data = await state.get_data()
    project_id = data.get("project_id")
    
    if not project_id:
        await message.answer("❌ Ошибка: проект не найден")
        await state.clear()
        return
    
    new_name = message.text.strip()
    
    if not new_name:
        await message.answer("❌ Название не может быть пустым. Попробуйте снова:")
        return
    
    # Обновляем название
    if update_project(project_id, name=new_name):
        project = get_project_by_id(project_id)
        character = get_character_by_id(project.character_id)
        developer = get_developer_by_id(project.developer_id)
        status = get_status_by_id(project.status_id)
        
        character_name = character.name if character else f"ID:{project.character_id}"
        developer_name = developer.name if developer else f"ID:{project.developer_id}"
        developer_username = f" @{developer.username}" if developer and developer.username else ""
        status_name = format_status_name(status) if status else f"ID:{project.status_id}"
        
        project_text = f"✅ Название обновлено!\n\n"
        project_text += f"📁 {project.name}\n"
        project_text += f"🎭 Персонаж: {character_name}\n"
        project_text += f"💻 Разработчик: {developer_name}{developer_username}\n"
        project_text += f"📊 Статус: {status_name}"
        
        is_archive = is_archive_status(project.status_id)
        
        await message.answer(
            project_text,
            reply_markup=get_project_actions_keyboard(project_id, is_archive=is_archive)
        )
        await state.clear()
    else:
        await message.answer("❌ Ошибка при обновлении названия")
        await state.clear()


@router.callback_query(F.data.startswith("edit_character_"))
async def process_edit_character(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор нового персонажа"""
    data = await state.get_data()
    project_id = data.get("project_id")
    
    if not project_id:
        await callback.answer("❌ Ошибка: проект не найден", show_alert=True)
        await state.clear()
        return
    
    character_id = int(callback.data.split("_")[-1])
    character = get_character_by_id(character_id)
    
    if not character:
        await callback.answer("❌ Персонаж не найден", show_alert=True)
        return
    
    # Обновляем персонажа
    if update_project(project_id, character_id=character_id):
        project = get_project_by_id(project_id)
        developer = get_developer_by_id(project.developer_id)
        status = get_status_by_id(project.status_id)
        
        developer_name = developer.name if developer else f"ID:{project.developer_id}"
        developer_username = f" @{developer.username}" if developer and developer.username else ""
        status_name = format_status_name(status) if status else f"ID:{project.status_id}"
        
        project_text = f"✅ Персонаж обновлен!\n\n"
        project_text += f"📁 {project.name}\n"
        project_text += f"🎭 Персонаж: {character.name}\n"
        project_text += f"💻 Разработчик: {developer_name}{developer_username}\n"
        project_text += f"📊 Статус: {status_name}"
        
        is_archive = is_archive_status(project.status_id)
        
        await callback.message.edit_text(
            project_text,
            reply_markup=get_project_actions_keyboard(project_id, is_archive=is_archive)
        )
        await callback.answer("✅ Персонаж обновлен")
        await state.clear()
    else:
        await callback.answer("❌ Ошибка при обновлении персонажа", show_alert=True)
        await state.clear()


@router.callback_query(F.data.startswith("edit_developer_"))
async def process_edit_developer(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор нового разработчика"""
    data = await state.get_data()
    project_id = data.get("project_id")
    
    if not project_id:
        await callback.answer("❌ Ошибка: проект не найден", show_alert=True)
        await state.clear()
        return
    
    developer_id = int(callback.data.split("_")[-1])
    developer = get_developer_by_id(developer_id)
    
    if not developer:
        await callback.answer("❌ Разработчик не найден", show_alert=True)
        return
    
    # Обновляем разработчика
    if update_project(project_id, developer_id=developer_id):
        project = get_project_by_id(project_id)
        character = get_character_by_id(project.character_id)
        status = get_status_by_id(project.status_id)
        
        character_name = character.name if character else f"ID:{project.character_id}"
        developer_username = f" @{developer.username}" if developer and developer.username else ""
        status_name = format_status_name(status) if status else f"ID:{project.status_id}"
        
        project_text = f"✅ Разработчик обновлен!\n\n"
        project_text += f"📁 {project.name}\n"
        project_text += f"🎭 Персонаж: {character_name}\n"
        project_text += f"💻 Разработчик: {developer.name}{developer_username}\n"
        project_text += f"📊 Статус: {status_name}"
        
        is_archive = is_archive_status(project.status_id)
        
        await callback.message.edit_text(
            project_text,
            reply_markup=get_project_actions_keyboard(project_id, is_archive=is_archive)
        )
        await callback.answer("✅ Разработчик обновлен")
        await state.clear()
    else:
        await callback.answer("❌ Ошибка при обновлении разработчика", show_alert=True)
        await state.clear()


@router.callback_query(F.data.startswith("edit_status_"))
async def process_edit_status(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор нового статуса"""
    data = await state.get_data()
    project_id = data.get("project_id")
    
    if not project_id:
        await callback.answer("❌ Ошибка: проект не найден", show_alert=True)
        await state.clear()
        return
    
    status_id = int(callback.data.split("_")[-1])
    status = get_status_by_id(status_id)
    
    if not status:
        await callback.answer("❌ Статус не найден", show_alert=True)
        return
    
    # Обновляем статус
    if update_project(project_id, status_id=status_id):
        project = get_project_by_id(project_id)
        character = get_character_by_id(project.character_id)
        developer = get_developer_by_id(project.developer_id)
        
        character_name = character.name if character else f"ID:{project.character_id}"
        developer_name = developer.name if developer else f"ID:{project.developer_id}"
        developer_username = f" @{developer.username}" if developer and developer.username else ""
        status_name = format_status_name(status)
        
        is_archive = is_archive_status(status_id)
        
        if is_archive:
            project_text = f"📦 Проект перенесен в архив!\n\n"
        else:
            project_text = f"✅ Статус обновлен!\n\n"
        
        project_text += f"📁 {project.name}\n"
        project_text += f"🎭 Персонаж: {character_name}\n"
        project_text += f"💻 Разработчик: {developer_name}{developer_username}\n"
        project_text += f"📊 Статус: {status_name}"
        
        await callback.message.edit_text(
            project_text,
            reply_markup=get_project_actions_keyboard(project_id, is_archive=is_archive)
        )
        await callback.answer("✅ Статус обновлен" if not is_archive else "✅ Проект перенесен в архив")
        await state.clear()
    else:
        await callback.answer("❌ Ошибка при обновлении статуса", show_alert=True)
        await state.clear()


@router.callback_query(F.data.startswith("prev_status_"))
async def prev_status_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Пред.Статус'"""
    project_id = int(callback.data.split("_")[-1])
    project = get_project_by_id(project_id)
    
    if not project:
        await callback.answer("❌ Проект не найден", show_alert=True)
        return
    
    prev_status_id = get_prev_status_id(project.status_id)
    if prev_status_id is None:
        await callback.answer("❌ Нет доступных статусов", show_alert=True)
        return
    
    # Обновляем статус
    if update_project_status(project_id, prev_status_id):
        # Получаем обновленный проект и новый статус
        updated_project = get_project_by_id(project_id)
        new_status = get_status_by_id(prev_status_id)
        character = get_character_by_id(updated_project.character_id)
        developer = get_developer_by_id(updated_project.developer_id)
        
        character_name = character.name if character else f"ID:{updated_project.character_id}"
        developer_name = developer.name if developer else f"ID:{updated_project.developer_id}"
        developer_username = f"@{developer.username}" if developer and developer.username else ""
        status_name = format_status_name(new_status) if new_status else f"ID:{prev_status_id}"
        
        project_text = f"📁 {updated_project.name}\n"
        project_text += f"🎭 Персонаж: {character_name}\n"
        project_text += f"💻 Разработчик: {developer_name}"
        if developer_username:
            project_text += f" {developer_username}"
        project_text += f"\n📊 Статус: {status_name}"
        
        # Определяем, является ли проект архивным после изменения статуса
        is_archive = is_archive_status(prev_status_id)
        
        if is_archive:
            # Проект перенесен в архив - показываем уведомление
            await callback.message.edit_text(
                f"📦 Проект перенесен в архив!\n\n{project_text}",
                reply_markup=get_project_actions_keyboard(project_id, is_archive=is_archive)
            )
            await callback.answer("✅ Проект перенесен в архив")
        else:
            await callback.message.edit_text(
                project_text,
                reply_markup=get_project_actions_keyboard(project_id, is_archive=is_archive)
            )
            await callback.answer("✅ Статус изменен на предыдущий")
    else:
        await callback.answer("❌ Ошибка при обновлении статуса", show_alert=True)


@router.callback_query(F.data.startswith("next_status_"))
async def next_status_callback(callback: CallbackQuery):
    """Обработчик кнопки 'След.Статус' - проверяет чек-лист"""
    project_id = int(callback.data.split("_")[-1])
    project = get_project_by_id(project_id)
    
    if not project:
        await callback.answer("❌ Проект не найден", show_alert=True)
        return
    
    # Проверяем, есть ли чек-лист для текущего статуса
    checklist = get_checklist_by_status_id(project.status_id)
    
    if checklist and checklist.items:
        # Есть чек-лист - показываем его
        status = get_status_by_id(project.status_id)
        status_name = format_status_name(status) if status else f"ID:{project.status_id}"
        
        checklist_text = f"📋 Чек-лист для статуса: {status_name}\n\n"
        checklist_text += "Отметьте все выполненные пункты:\n\n"
        
        for i, item in enumerate(checklist.items, 1):
            checkbox = "✅" if item.checked else "☐"
            checklist_text += f"{i}. {checkbox} {item.text}\n"
        
        all_checked = checklist.is_complete()
        if all_checked:
            checklist_text += "\n✅ Все пункты выполнены! Можете перейти на следующий статус."
        else:
            checklist_text += "\n⚠️ Выполните все пункты для перехода на следующий статус."
        
        await callback.message.edit_text(
            checklist_text,
            reply_markup=get_checklist_keyboard(project.status_id, project_id, checklist.items)
        )
        await callback.answer()
    else:
        # Нет чек-листа - переходим сразу на следующий статус
        next_status_id = get_next_status_id(project.status_id)
        if next_status_id is None:
            await callback.answer("❌ Нет доступных статусов", show_alert=True)
            return
        
        # Обновляем статус
        if update_project_status(project_id, next_status_id):
            # Получаем обновленный проект и новый статус
            updated_project = get_project_by_id(project_id)
            new_status = get_status_by_id(next_status_id)
            character = get_character_by_id(updated_project.character_id)
            developer = get_developer_by_id(updated_project.developer_id)
            
            character_name = character.name if character else f"ID:{updated_project.character_id}"
            developer_name = developer.name if developer else f"ID:{updated_project.developer_id}"
            developer_username = f"@{developer.username}" if developer and developer.username else ""
            status_name = format_status_name(new_status) if new_status else f"ID:{next_status_id}"
            
            project_text = f"📁 {updated_project.name}\n"
            project_text += f"🎭 Персонаж: {character_name}\n"
            project_text += f"💻 Разработчик: {developer_name}"
            if developer_username:
                project_text += f" {developer_username}"
            project_text += f"\n📊 Статус: {status_name}"
            
            # Определяем, является ли проект архивным после изменения статуса
            is_archive = is_archive_status(next_status_id)
            
            if is_archive:
                # Проект перенесен в архив - показываем уведомление
                await callback.message.edit_text(
                    f"📦 Проект перенесен в архив!\n\n{project_text}",
                    reply_markup=get_project_actions_keyboard(project_id, is_archive=is_archive)
                )
                await callback.answer("✅ Проект перенесен в архив")
            else:
                await callback.message.edit_text(
                    project_text,
                    reply_markup=get_project_actions_keyboard(project_id, is_archive=is_archive)
                )
                await callback.answer("✅ Статус изменен на следующий")
        else:
            await callback.answer("❌ Ошибка при обновлении статуса", show_alert=True)


@router.callback_query(F.data.startswith("toggle_checklist_"))
async def toggle_checklist_item_callback(callback: CallbackQuery):
    """Обработчик переключения пункта чек-листа"""
    from storage import toggle_checklist_item
    
    # Парсим: toggle_checklist_{status_id}_{project_id}_{item_id}
    parts = callback.data.split("_")
    status_id = int(parts[2])
    project_id = int(parts[3])
    item_id = int(parts[4])
    
    if toggle_checklist_item(status_id, item_id):
        # Обновляем отображение чек-листа
        checklist = get_checklist_by_status_id(status_id)
        status = get_status_by_id(status_id)
        status_name = status.name if status else f"ID:{status_id}"
        
        checklist_text = f"📋 Чек-лист для статуса: {status_name}\n\n"
        checklist_text += "Отметьте все выполненные пункты:\n\n"
        
        for i, item in enumerate(checklist.items, 1):
            checkbox = "✅" if item.checked else "☐"
            checklist_text += f"{i}. {checkbox} {item.text}\n"
        
        all_checked = checklist.is_complete()
        if all_checked:
            checklist_text += "\n✅ Все пункты выполнены! Можете перейти на следующий статус."
        else:
            checklist_text += "\n⚠️ Выполните все пункты для перехода на следующий статус."
        
        await callback.message.edit_text(
            checklist_text,
            reply_markup=get_checklist_keyboard(status_id, project_id, checklist.items)
        )
        await callback.answer()
    else:
        await callback.answer("❌ Ошибка при обновлении пункта", show_alert=True)


@router.callback_query(F.data.startswith("confirm_next_status_"))
async def confirm_next_status_callback(callback: CallbackQuery):
    """Обработчик подтверждения перехода на следующий статус после выполнения чек-листа"""
    project_id = int(callback.data.split("_")[-1])
    project = get_project_by_id(project_id)
    
    if not project:
        await callback.answer("❌ Проект не найден", show_alert=True)
        return
    
    # Проверяем, что чек-лист выполнен
    checklist = get_checklist_by_status_id(project.status_id)
    if checklist and not checklist.is_complete():
        await callback.answer("❌ Выполните все пункты чек-листа", show_alert=True)
        return
    
    next_status_id = get_next_status_id(project.status_id)
    if next_status_id is None:
        await callback.answer("❌ Нет доступных статусов", show_alert=True)
        return
    
    # Сбрасываем чек-лист для следующего использования
    reset_checklist(project.status_id)
    
    # Обновляем статус
    if update_project_status(project_id, next_status_id):
        # Получаем обновленный проект и новый статус
        updated_project = get_project_by_id(project_id)
        new_status = get_status_by_id(next_status_id)
        character = get_character_by_id(updated_project.character_id)
        developer = get_developer_by_id(updated_project.developer_id)
        
        character_name = character.name if character else f"ID:{updated_project.character_id}"
        developer_name = developer.name if developer else f"ID:{updated_project.developer_id}"
        developer_username = f"@{developer.username}" if developer and developer.username else ""
        status_name = format_status_name(new_status) if new_status else f"ID:{next_status_id}"
        
        project_text = f"📁 {updated_project.name}\n"
        project_text += f"🎭 Персонаж: {character_name}\n"
        project_text += f"💻 Разработчик: {developer_name}"
        if developer_username:
            project_text += f" {developer_username}"
        project_text += f"\n📊 Статус: {status_name}"
        
        # Определяем, является ли проект архивным после изменения статуса
        is_archive = is_archive_status(next_status_id)
        
        if is_archive:
            # Проект перенесен в архив - показываем уведомление
            await callback.message.edit_text(
                f"📦 Проект перенесен в архив!\n\n{project_text}",
                reply_markup=get_project_actions_keyboard(project_id, is_archive=is_archive)
            )
            await callback.answer("✅ Проект перенесен в архив")
        else:
            await callback.message.edit_text(
                project_text,
                reply_markup=get_project_actions_keyboard(project_id, is_archive=is_archive)
            )
            await callback.answer("✅ Статус изменен на следующий")
    else:
        await callback.answer("❌ Ошибка при обновлении статуса", show_alert=True)


@router.callback_query(F.data.startswith("back_to_project_"))
async def back_to_project_callback(callback: CallbackQuery):
    """Обработчик возврата к проекту из чек-листа"""
    project_id = int(callback.data.split("_")[-1])
    project = get_project_by_id(project_id)
    
    if not project:
        await callback.answer("❌ Проект не найден", show_alert=True)
        return
    
    character = get_character_by_id(project.character_id)
    developer = get_developer_by_id(project.developer_id)
    status = get_status_by_id(project.status_id)
    
    character_name = character.name if character else f"ID:{project.character_id}"
    developer_name = developer.name if developer else f"ID:{project.developer_id}"
    developer_username = f"@{developer.username}" if developer and developer.username else ""
    status_name = format_status_name(status) if status else f"ID:{project.status_id}"
    
    project_text = f"📁 {project.name}\n"
    project_text += f"🎭 Персонаж: {character_name}\n"
    project_text += f"💻 Разработчик: {developer_name}"
    if developer_username:
        project_text += f" {developer_username}"
    project_text += f"\n📊 Статус: {status_name}"
    
    await callback.message.edit_text(
        project_text,
        reply_markup=get_project_actions_keyboard(project_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_project_"))
async def delete_project_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Удалить' проекта - показывает подтверждение"""
    project_id = int(callback.data.split("_")[-1])
    project = get_project_by_id(project_id)
    
    if not project:
        await callback.answer("❌ Проект не найден", show_alert=True)
        return
    
    # Показываем подтверждение
    character = get_character_by_id(project.character_id)
    developer = get_developer_by_id(project.developer_id)
    status = get_status_by_id(project.status_id)
    
    character_name = character.name if character else f"ID:{project.character_id}"
    developer_name = developer.name if developer else f"ID:{project.developer_id}"
    status_name = format_status_name(status) if status else f"ID:{project.status_id}"
    
    confirm_text = f"⚠️ Вы уверены, что хотите удалить проект?\n\n"
    confirm_text += f"📁 {project.name}\n"
    confirm_text += f"🎭 Персонаж: {character_name}\n"
    confirm_text += f"💻 Разработчик: {developer_name}\n"
    confirm_text += f"📊 Статус: {status_name}\n\n"
    confirm_text += f"Это действие нельзя отменить!"
    
    await callback.message.edit_text(
        confirm_text,
        reply_markup=get_delete_confirm_keyboard(project_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete_project_callback(callback: CallbackQuery):
    """Обработчик подтверждения удаления проекта"""
    project_id = int(callback.data.split("_")[-1])
    project = get_project_by_id(project_id)
    
    if not project:
        await callback.answer("❌ Проект не найден", show_alert=True)
        return
    
    project_name = project.name
    
    # Удаляем проект
    if delete_project(project_id):
        await callback.message.edit_text(
            f"✅ Проект удален:\n\n"
            f"📁 {project_name}"
        )
        await callback.answer("Проект удален!")
    else:
        await callback.answer("❌ Ошибка при удалении", show_alert=True)


@router.callback_query(F.data.startswith("cancel_delete_"))
async def cancel_delete_project_callback(callback: CallbackQuery):
    """Обработчик отмены удаления проекта"""
    project_id = int(callback.data.split("_")[-1])
    project = get_project_by_id(project_id)
    
    if not project:
        await callback.answer("❌ Проект не найден", show_alert=True)
        return
    
    # Восстанавливаем отображение проекта
    character = get_character_by_id(project.character_id)
    developer = get_developer_by_id(project.developer_id)
    status = get_status_by_id(project.status_id)
    
    character_name = character.name if character else f"ID:{project.character_id}"
    developer_name = developer.name if developer else f"ID:{project.developer_id}"
    developer_username = f"@{developer.username}" if developer and developer.username else ""
    status_name = format_status_name(status) if status else f"ID:{project.status_id}"
    
    project_text = f"📁 {project.name}\n"
    project_text += f"🎭 Персонаж: {character_name}\n"
    project_text += f"💻 Разработчик: {developer_name}"
    if developer_username:
        project_text += f" {developer_username}"
    project_text += f"\n📊 Статус: {status_name}"
    
    await callback.message.edit_text(
        project_text,
        reply_markup=get_project_actions_keyboard(project_id)
    )
    await callback.answer("Удаление отменено")


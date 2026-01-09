from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import (
    get_main_menu_keyboard,
    get_characters_management_keyboard,
    get_characters_list_keyboard
)
from storage import (
    get_all_characters,
    add_character,
    delete_character,
    get_character_by_id
)

router = Router()


class CharacterCreation(StatesGroup):
    waiting_for_name = State()


@router.message(F.text == "🎭 Управление Персонажами")
async def characters_management_handler(message: Message):
    """Обработчик для кнопки 'Управление Персонажами'"""
    from storage import get_user_by_id, is_admin
    user_id = message.from_user.id
    user = get_user_by_id(user_id)
    
    # Проверяем, что пользователь имеет роль "Лёша" или является админом
    if not user or (user.role != "Лёша" and not is_admin(user_id)):
        await message.answer(
            "❌ У вас нет прав доступа к управлению персонажами.\n"
            "Доступ разрешен только для пользователей с ролью 'Лёша'.",
            reply_markup=get_main_menu_keyboard(is_admin=is_admin(user_id), user_role=user.role if user else None)
        )
        return
    
    await message.answer(
        "🎭 Управление Персонажами\n\n"
        "Выберите действие:",
        reply_markup=get_characters_management_keyboard()
    )


@router.message(F.text == "📋 Список персонажей")
async def list_characters_handler(message: Message):
    """Показывает список всех персонажей"""
    characters = get_all_characters()
    
    if not characters:
        await message.answer(
            "📋 Список персонажей пуст.\n\n"
            "Добавьте первого персонажа!",
            reply_markup=get_characters_management_keyboard()
        )
        return
    
    characters_list = "\n".join([f"{i+1}. {char.name}" for i, char in enumerate(characters)])
    
    await message.answer(
        f"📋 Список персонажей ({len(characters)}):\n\n{characters_list}",
        reply_markup=get_characters_management_keyboard()
    )


@router.message(F.text == "➕ Добавить персонажа")
async def add_character_start(message: Message, state: FSMContext):
    """Начинает процесс добавления персонажа"""
    await state.set_state(CharacterCreation.waiting_for_name)
    await message.answer(
        "➕ Добавление нового персонажа\n\n"
        "Введите название персонажа:",
        reply_markup=None
    )


@router.message(CharacterCreation.waiting_for_name)
async def process_character_name(message: Message, state: FSMContext):
    """Обрабатывает название персонажа"""
    character_name = message.text.strip()
    
    if not character_name:
        await message.answer("❌ Название не может быть пустым. Попробуйте снова:")
        return
    
    # Создаем персонажа
    new_character = add_character(character_name)
    
    await message.answer(
        f"✅ Персонаж успешно добавлен!\n\n"
        f"🎭 Название: {new_character.name}\n"
        f"🆔 ID: {new_character.id}"
    )
    
    await state.clear()
    
    # Отправляем клавиатуру управления
    await message.answer(
        "Выберите действие:",
        reply_markup=get_characters_management_keyboard()
    )


@router.message(F.text == "🗑️ Удалить персонажа")
async def delete_character_start(message: Message):
    """Начинает процесс удаления персонажа"""
    characters = get_all_characters()
    
    if not characters:
        await message.answer(
            "❌ Нет персонажей для удаления.",
            reply_markup=get_characters_management_keyboard()
        )
        return
    
    await message.answer(
        "🗑️ Выберите персонажа для удаления:",
        reply_markup=get_characters_list_keyboard(characters, "delete")
    )


@router.callback_query(F.data.startswith("delete_character_"))
async def process_delete_character(callback: CallbackQuery):
    """Обрабатывает удаление персонажа"""
    character_id = int(callback.data.split("_")[-1])
    character = get_character_by_id(character_id)
    
    if not character:
        await callback.answer("❌ Персонаж не найден", show_alert=True)
        return
    
    # Удаляем персонажа
    if delete_character(character_id):
        await callback.message.edit_text(
            f"✅ Персонаж удален:\n\n"
            f"🎭 {character.name}"
        )
        await callback.answer("Персонаж удален!")
    else:
        await callback.answer("❌ Ошибка при удалении", show_alert=True)
    
    # Обновляем список
    characters = get_all_characters()
    if characters:
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_characters_management_keyboard()
        )
    else:
        await callback.message.answer(
            "📋 Список персонажей пуст.",
            reply_markup=get_characters_management_keyboard()
        )


@router.message(F.text == "🔙 Главное меню")
async def back_to_main_from_characters(message: Message, state: FSMContext):
    """Возврат в главное меню из раздела персонажей"""
    from storage import get_user_by_id, is_admin
    await state.clear()
    user_id = message.from_user.id
    user = get_user_by_id(user_id)
    user_role = user.role if user else None
    await message.answer(
        "🔙 Главное меню",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin(user_id), user_role=user_role)
    )


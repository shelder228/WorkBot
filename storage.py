import json
import os
from typing import List, Optional
from models import ProjectStatus, Project, Character, Developer, User, Checklist, ChecklistItem, ResponsiblePerson, UserRole

STATUSES_FILE = "statuses.json"
PROJECTS_FILE = "projects.json"
CHARACTERS_FILE = "characters.json"
DEVELOPERS_FILE = "developers.json"
USERS_FILE = "users.json"
CHECKLISTS_FILE = "checklists.json"


def get_default_statuses() -> List[ProjectStatus]:
    """Возвращает список статусов по умолчанию"""
    return [
        ProjectStatus(id=1, name="Согласование названия", responsible="Игнат"),
        ProjectStatus(id=2, name="Готов к дизайну", responsible="Лёша"),
        ProjectStatus(id=3, name="На дизайне", responsible="никто"),
        ProjectStatus(id=4, name="Можно взять в работу", responsible="никто"),
        ProjectStatus(id=5, name="Готовится к белой выкладки", responsible="Игнат"),
        ProjectStatus(id=6, name="Готовится к белой выкладки", responsible="Лёша"),
        ProjectStatus(id=7, name="Готов к белой выкладки", responsible="Игнат"),
        ProjectStatus(id=8, name="Белая проверка", responsible="никто"),
        ProjectStatus(id=9, name="Готовится к серой выкладки", responsible="Игнат"),
        ProjectStatus(id=10, name="Готовится к серой выкладки", responsible="Лёша"),
        ProjectStatus(id=11, name="Готов к серой выкладки", responsible="Лёша"),
        ProjectStatus(id=12, name="Серая проверка", responsible="никто"),
        ProjectStatus(id=13, name="Живой", responsible="никто"),
        ProjectStatus(id=14, name="Бан", responsible="никто"),
    ]


def load_statuses() -> List[ProjectStatus]:
    """Загружает статусы из файла"""
    if not os.path.exists(STATUSES_FILE):
        # Создаем файл с дефолтными статусами
        default_statuses = get_default_statuses()
        save_statuses(default_statuses)
        return default_statuses
    
    try:
        with open(STATUSES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [ProjectStatus.from_dict(item) for item in data]
    except (json.JSONDecodeError, KeyError, ValueError):
        # Если файл поврежден, создаем заново
        default_statuses = get_default_statuses()
        save_statuses(default_statuses)
        return default_statuses


def save_statuses(statuses: List[ProjectStatus]):
    """Сохраняет статусы в файл"""
    with open(STATUSES_FILE, 'w', encoding='utf-8') as f:
        data = [status.to_dict() for status in statuses]
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_status_by_id(status_id: int) -> Optional[ProjectStatus]:
    """Получает статус по ID"""
    statuses = load_statuses()
    for status in statuses:
        if status.id == status_id:
            return status
    return None


def add_status(name: str, responsible: ResponsiblePerson) -> ProjectStatus:
    """Добавляет новый статус"""
    statuses = load_statuses()
    
    # Находим максимальный ID
    max_id = max([s.id for s in statuses], default=0)
    new_id = max_id + 1
    
    new_status = ProjectStatus(id=new_id, name=name, responsible=responsible)
    statuses.append(new_status)
    save_statuses(statuses)
    
    return new_status


def delete_status(status_id: int) -> bool:
    """Удаляет статус по ID"""
    statuses = load_statuses()
    original_count = len(statuses)
    statuses = [s for s in statuses if s.id != status_id]
    
    if len(statuses) < original_count:
        save_statuses(statuses)
        return True
    return False


def get_all_statuses() -> List[ProjectStatus]:
    """Возвращает все статусы"""
    return load_statuses()


def get_first_status() -> Optional[ProjectStatus]:
    """Возвращает первый статус (самый ранний по ID)"""
    statuses = load_statuses()
    if not statuses:
        return None
    return min(statuses, key=lambda s: s.id)


# ========== Функции для работы с проектами ==========

def load_projects() -> List[Project]:
    """Загружает проекты из файла"""
    if not os.path.exists(PROJECTS_FILE):
        return []
    
    try:
        with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            projects = []
            needs_migration = False
            
            for item in data:
                # Миграция: конвертируем старый формат в новый
                if 'character' in item and isinstance(item['character'], str):
                    # Старый формат: character и developer - строки
                    # Нужно найти или создать соответствующие ID
                    character_name = item['character']
                    developer_name = item['developer']
                    
                    # Ищем персонажа по имени
                    characters = get_all_characters()
                    character_id = None
                    for char in characters:
                        if char.name == character_name:
                            character_id = char.id
                            break
                    
                    # Если персонаж не найден, создаем его
                    if character_id is None:
                        new_char = add_character(character_name)
                        character_id = new_char.id
                    
                    # Ищем разработчика по имени
                    developers = get_all_developers()
                    developer_id = None
                    for dev in developers:
                        if dev.name == developer_name or dev.username == developer_name:
                            developer_id = dev.id
                            break
                    
                    # Если разработчик не найден, создаем его
                    if developer_id is None:
                        # Используем имя как username, если username не указан
                        username = developer_name.replace(' ', '_').lower()
                        try:
                            new_dev = add_developer(developer_name, username)
                            developer_id = new_dev.id
                        except ValueError:
                            # Если уже существует, ищем снова
                            developers = get_all_developers()
                            for dev in developers:
                                if dev.username == username:
                                    developer_id = dev.id
                                    break
                    
                    # Обновляем данные на новый формат
                    item['character_id'] = character_id
                    item['developer_id'] = developer_id
                    # Удаляем старые поля
                    item.pop('character', None)
                    item.pop('developer', None)
                    needs_migration = True
                
                # Создаем проект из обновленных данных
                projects.append(Project.from_dict(item))
            
            # Сохраняем мигрированные данные
            if needs_migration:
                save_projects(projects)
            
            return projects
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        # Если ошибка при загрузке, возвращаем пустой список
        print(f"Ошибка при загрузке проектов: {e}")
        return []


def save_projects(projects: List[Project]):
    """Сохраняет проекты в файл"""
    with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
        data = [project.to_dict() for project in projects]
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_project(name: str, character_id: int, developer_id: int, status_id: int) -> Project:
    """Добавляет новый проект"""
    projects = load_projects()
    
    # Находим максимальный ID
    max_id = max([p.id for p in projects], default=0) if projects else 0
    new_id = max_id + 1
    
    new_project = Project(
        id=new_id,
        name=name,
        character_id=character_id,
        developer_id=developer_id,
        status_id=status_id
    )
    projects.append(new_project)
    save_projects(projects)
    
    # Пересчитываем статистику разработчика
    recalculate_developer_stats(developer_id)
    
    return new_project


def get_project_by_id(project_id: int) -> Optional[Project]:
    """Получает проект по ID"""
    projects = load_projects()
    for project in projects:
        if project.id == project_id:
            return project
    return None


def update_project(project_id: int, name: str = None, character_id: int = None, developer_id: int = None, status_id: int = None) -> bool:
    """Обновляет данные проекта"""
    projects = load_projects()
    old_developer_id = None
    
    for project in projects:
        if project.id == project_id:
            old_developer_id = project.developer_id
            
            if name is not None:
                project.name = name
            if character_id is not None:
                project.character_id = character_id
            if developer_id is not None:
                project.developer_id = developer_id
            if status_id is not None:
                project.status_id = status_id
            
            save_projects(projects)
            
            # Обновляем статистику разработчиков, если изменился разработчик
            if developer_id is not None and developer_id != old_developer_id:
                if old_developer_id:
                    recalculate_developer_stats(old_developer_id)
                recalculate_developer_stats(developer_id)
            elif status_id is not None:
                # Если изменился статус, пересчитываем статистику текущего разработчика
                recalculate_developer_stats(project.developer_id)
            
            return True
    
    return False


def get_all_projects() -> List[Project]:
    """Возвращает все проекты"""
    return load_projects()


def is_archive_status(status_id: int) -> bool:
    """Проверяет, является ли статус архивным (Живой, Бан, Опубликовано, Заблокировано)"""
    status = get_status_by_id(status_id)
    if not status:
        return False
    
    status_name_lower = status.name.lower()
    # Проверяем различные варианты названий архивных статусов
    archive_keywords = ["живой", "бан", "опубликовано", "заблокировано", "опубликован", "заблокирован"]
    
    # Проверяем точное совпадение или наличие ключевых слов
    if status.name in ["Живой", "Бан"]:
        return True
    
    # Проверяем наличие ключевых слов в названии
    for keyword in archive_keywords:
        if keyword in status_name_lower:
            return True
    
    return False


def get_active_projects() -> List[Project]:
    """Возвращает только активные проекты (не в архиве)"""
    all_projects = load_projects()
    return [p for p in all_projects if not is_archive_status(p.status_id)]


def get_archive_projects() -> List[Project]:
    """Возвращает только архивные проекты (Живой или Бан)"""
    all_projects = load_projects()
    return [p for p in all_projects if is_archive_status(p.status_id)]


def get_published_projects() -> List[Project]:
    """Возвращает опубликованные проекты (статус Живой или Опубликовано)"""
    all_projects = load_projects()
    published_statuses = [
        s.id for s in get_all_statuses() 
        if s.name == "Живой" or "опубликовано" in s.name.lower() or "опубликован" in s.name.lower()
    ]
    return [p for p in all_projects if p.status_id in published_statuses]


def get_banned_projects() -> List[Project]:
    """Возвращает заблокированные проекты (статус Бан или Заблокировано)"""
    all_projects = load_projects()
    banned_statuses = [
        s.id for s in get_all_statuses() 
        if s.name == "Бан" or "заблокировано" in s.name.lower() or "заблокирован" in s.name.lower()
    ]
    return [p for p in all_projects if p.status_id in banned_statuses]


def get_projects_by_role(role: str) -> List[Project]:
    """Возвращает проекты, назначенные на определенную роль (Игнат или Лёша)"""
    if role not in ["Игнат", "Лёша"]:
        return []
    
    projects = load_projects()
    statuses = load_statuses()
    
    # Создаем словарь статусов для быстрого поиска
    status_dict = {s.id: s for s in statuses}
    
    # Фильтруем проекты по ответственному в статусе (исключаем архивные)
    filtered_projects = []
    for project in projects:
        status = status_dict.get(project.status_id)
        if status and status.responsible == role and not is_archive_status(project.status_id):
            filtered_projects.append(project)
    
    return filtered_projects


def update_project_status(project_id: int, new_status_id: int) -> bool:
    """Обновляет статус проекта"""
    projects = load_projects()
    old_status_id = None
    developer_id = None
    
    for project in projects:
        if project.id == project_id:
            old_status_id = project.status_id
            developer_id = project.developer_id
            project.status_id = new_status_id
            save_projects(projects)
            break
    
    if old_status_id is None:
        return False
    
    # Обновляем статистику разработчика
    if developer_id:
        recalculate_developer_stats(developer_id)
    
    return True


def delete_project(project_id: int) -> bool:
    """Удаляет проект по ID"""
    projects = load_projects()
    deleted_project = None
    
    for project in projects:
        if project.id == project_id:
            deleted_project = project
            break
    
    if not deleted_project:
        return False
    
    developer_id = deleted_project.developer_id
    
    # Удаляем проект
    projects = [p for p in projects if p.id != project_id]
    save_projects(projects)
    
    # Обновляем статистику разработчика
    if developer_id:
        recalculate_developer_stats(developer_id)
    
    return True


def get_next_status_id(current_status_id: int) -> Optional[int]:
    """Возвращает ID следующего статуса"""
    statuses = get_all_statuses()
    if not statuses:
        return None
    
    # Сортируем статусы по ID
    sorted_statuses = sorted(statuses, key=lambda s: s.id)
    
    # Находим текущий статус
    for i, status in enumerate(sorted_statuses):
        if status.id == current_status_id:
            # Возвращаем следующий статус, если он есть
            if i + 1 < len(sorted_statuses):
                return sorted_statuses[i + 1].id
            # Если это последний, возвращаем первый (циклично)
            return sorted_statuses[0].id
    
    # Если текущий статус не найден, возвращаем первый
    return sorted_statuses[0].id


def get_prev_status_id(current_status_id: int) -> Optional[int]:
    """Возвращает ID предыдущего статуса"""
    statuses = get_all_statuses()
    if not statuses:
        return None
    
    # Сортируем статусы по ID
    sorted_statuses = sorted(statuses, key=lambda s: s.id)
    
    # Находим текущий статус
    for i, status in enumerate(sorted_statuses):
        if status.id == current_status_id:
            # Возвращаем предыдущий статус, если он есть
            if i > 0:
                return sorted_statuses[i - 1].id
            # Если это первый, возвращаем последний (циклично)
            return sorted_statuses[-1].id
    
    # Если текущий статус не найден, возвращаем первый
    return sorted_statuses[0].id


# ========== Функции для работы с персонажами ==========

def load_characters() -> List[Character]:
    """Загружает персонажей из файла"""
    if not os.path.exists(CHARACTERS_FILE):
        return []
    
    try:
        with open(CHARACTERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [Character.from_dict(item) for item in data]
    except (json.JSONDecodeError, KeyError, ValueError):
        return []


def save_characters(characters: List[Character]):
    """Сохраняет персонажей в файл"""
    with open(CHARACTERS_FILE, 'w', encoding='utf-8') as f:
        data = [character.to_dict() for character in characters]
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_character(name: str) -> Character:
    """Добавляет нового персонажа"""
    characters = load_characters()
    
    # Находим максимальный ID
    max_id = max([c.id for c in characters], default=0) if characters else 0
    new_id = max_id + 1
    
    new_character = Character(id=new_id, name=name)
    characters.append(new_character)
    save_characters(characters)
    
    return new_character


def delete_character(character_id: int) -> bool:
    """Удаляет персонажа по ID"""
    characters = load_characters()
    original_count = len(characters)
    characters = [c for c in characters if c.id != character_id]
    
    if len(characters) < original_count:
        save_characters(characters)
        return True
    return False


def get_character_by_id(character_id: int) -> Optional[Character]:
    """Получает персонажа по ID"""
    characters = load_characters()
    for character in characters:
        if character.id == character_id:
            return character
    return None


def get_all_characters() -> List[Character]:
    """Возвращает всех персонажей"""
    return load_characters()


# ========== Функции для работы с разработчиками ==========

def load_developers() -> List[Developer]:
    """Загружает разработчиков из файла"""
    if not os.path.exists(DEVELOPERS_FILE):
        return []
    
    try:
        with open(DEVELOPERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [Developer.from_dict(item) for item in data]
    except (json.JSONDecodeError, KeyError, ValueError):
        return []


def save_developers(developers: List[Developer]):
    """Сохраняет разработчиков в файл"""
    with open(DEVELOPERS_FILE, 'w', encoding='utf-8') as f:
        data = [developer.to_dict() for developer in developers]
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_developer(name: str, username: str) -> Developer:
    """Добавляет нового разработчика"""
    developers = load_developers()
    
    # Проверяем, нет ли уже разработчика с таким username
    for dev in developers:
        if dev.username.lower() == username.lower():
            raise ValueError(f"Разработчик с username @{username} уже существует")
    
    # Находим максимальный ID
    max_id = max([d.id for d in developers], default=0) if developers else 0
    new_id = max_id + 1
    
    new_developer = Developer(
        id=new_id,
        name=name,
        username=username,
        total_projects=0,
        released_projects=0,
        banned_projects=0
    )
    developers.append(new_developer)
    save_developers(developers)
    
    return new_developer


def delete_developer(developer_id: int) -> bool:
    """Удаляет разработчика по ID"""
    developers = load_developers()
    original_count = len(developers)
    developers = [d for d in developers if d.id != developer_id]
    
    if len(developers) < original_count:
        save_developers(developers)
        return True
    return False


def get_developer_by_id(developer_id: int) -> Optional[Developer]:
    """Получает разработчика по ID"""
    developers = load_developers()
    for developer in developers:
        if developer.id == developer_id:
            return developer
    return None


def update_developer(developer: Developer):
    """Обновляет данные разработчика"""
    developers = load_developers()
    for i, d in enumerate(developers):
        if d.id == developer.id:
            developers[i] = developer
            save_developers(developers)
            return
    # Если не найден, добавляем
    developers.append(developer)
    save_developers(developers)


def recalculate_developer_stats(developer_id: int):
    """Пересчитывает статистику разработчика на основе текущих проектов"""
    developer = get_developer_by_id(developer_id)
    if not developer:
        return
    
    projects = load_projects()
    developer_projects = [p for p in projects if p.developer_id == developer_id]
    
    # Подсчитываем статистику
    total_projects = len(developer_projects)
    published_count = 0
    banned_count = 0
    
    for project in developer_projects:
        status = get_status_by_id(project.status_id)
        if status:
            status_name_lower = status.name.lower()
            if status.name == "Живой" or "опубликовано" in status_name_lower or "опубликован" in status_name_lower:
                published_count += 1
            elif status.name == "Бан" or "заблокировано" in status_name_lower or "заблокирован" in status_name_lower:
                banned_count += 1
    
    # Обновляем статистику
    developer.total_projects = total_projects
    developer.released_projects = published_count
    developer.banned_projects = banned_count
    
    update_developer(developer)


def recalculate_all_developers_stats():
    """Пересчитывает статистику всех разработчиков"""
    developers = get_all_developers()
    for developer in developers:
        recalculate_developer_stats(developer.id)


def get_all_developers() -> List[Developer]:
    """Возвращает всех разработчиков"""
    return load_developers()


# ========== Функции для работы с пользователями ==========

def load_users() -> List[User]:
    """Загружает пользователей из файла"""
    if not os.path.exists(USERS_FILE):
        return []
    
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [User.from_dict(item) for item in data]
    except (json.JSONDecodeError, KeyError, ValueError):
        return []


def save_users(users: List[User]):
    """Сохраняет пользователей в файл"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        data = [user.to_dict() for user in users]
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user_by_id(user_id: int) -> Optional[User]:
    """Получает пользователя по ID"""
    users = load_users()
    for user in users:
        if user.user_id == user_id:
            return user
    return None


def get_or_create_user(user_id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> User:
    """Получает пользователя или создает нового"""
    user = get_user_by_id(user_id)
    if user:
        # Обновляем информацию, если изменилась
        if username and user.username != username:
            user.username = username
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            update_user(user)
        return user
    
    # Создаем нового пользователя
    users = load_users()
    new_user = User(
        user_id=user_id,
        username=username,
        first_name=first_name,
        role="user"
    )
    users.append(new_user)
    save_users(users)
    return new_user


def update_user(user: User):
    """Обновляет данные пользователя"""
    users = load_users()
    for i, u in enumerate(users):
        if u.user_id == user.user_id:
            users[i] = user
            save_users(users)
            return
    # Если не найден, добавляем
    users.append(user)
    save_users(users)


def set_user_role(user_id: int, role: UserRole) -> bool:
    """Устанавливает роль пользователю"""
    user = get_user_by_id(user_id)
    if not user:
        return False
    
    user.role = role
    update_user(user)
    return True


def get_all_users() -> List[User]:
    """Возвращает всех пользователей"""
    return load_users()


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    from config import ADMIN_ID
    if user_id == ADMIN_ID:
        return True
    user = get_user_by_id(user_id)
    return user is not None and user.role == "admin"


def update_user_notifications(user_id: int, enabled: bool = None, interval: int = None) -> bool:
    """Обновляет настройки уведомлений пользователя"""
    user = get_user_by_id(user_id)
    if not user:
        return False
    
    if enabled is not None:
        user.notifications_enabled = enabled
    if interval is not None:
        user.notification_interval = interval
    
    update_user(user)
    return True


def get_users_with_tasks() -> List[User]:
    """Возвращает пользователей с ролями Игнат или Лёша, у которых есть задачи"""
    users = get_all_users()
    users_with_tasks = []
    
    for user in users:
        if user.role in ["Игнат", "Лёша"]:
            projects = get_projects_by_role(user.role)
            if projects:
                users_with_tasks.append(user)
    
    return users_with_tasks


# ========== Функции для работы с чек-листами ==========

def load_checklists() -> List[Checklist]:
    """Загружает чек-листы из файла"""
    if not os.path.exists(CHECKLISTS_FILE):
        return []
    
    try:
        with open(CHECKLISTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [Checklist.from_dict(item) for item in data]
    except (json.JSONDecodeError, KeyError, ValueError):
        return []


def save_checklists(checklists: List[Checklist]):
    """Сохраняет чек-листы в файл"""
    with open(CHECKLISTS_FILE, 'w', encoding='utf-8') as f:
        data = [checklist.to_dict() for checklist in checklists]
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_checklist_by_status_id(status_id: int) -> Optional[Checklist]:
    """Получает чек-лист по ID статуса"""
    checklists = load_checklists()
    for checklist in checklists:
        if checklist.status_id == status_id:
            return checklist
    return None


def create_checklist(status_id: int) -> Checklist:
    """Создает новый чек-лист для статуса"""
    checklists = load_checklists()
    
    # Проверяем, не существует ли уже чек-лист для этого статуса
    existing = get_checklist_by_status_id(status_id)
    if existing:
        return existing
    
    new_checklist = Checklist(status_id=status_id, items=[])
    checklists.append(new_checklist)
    save_checklists(checklists)
    return new_checklist


def add_checklist_item(status_id: int, item_text: str) -> ChecklistItem:
    """Добавляет пункт в чек-лист статуса"""
    checklist = get_checklist_by_status_id(status_id)
    if not checklist:
        checklist = create_checklist(status_id)
    
    # Находим максимальный ID
    max_id = max([item.id for item in checklist.items], default=0) if checklist.items else 0
    new_id = max_id + 1
    
    new_item = ChecklistItem(id=new_id, text=item_text, checked=False)
    checklist.items.append(new_item)
    
    checklists = load_checklists()
    for i, c in enumerate(checklists):
        if c.status_id == status_id:
            checklists[i] = checklist
            break
    else:
        checklists.append(checklist)
    
    save_checklists(checklists)
    return new_item


def delete_checklist_item(status_id: int, item_id: int) -> bool:
    """Удаляет пункт из чек-листа"""
    checklist = get_checklist_by_status_id(status_id)
    if not checklist:
        return False
    
    original_count = len(checklist.items)
    checklist.items = [item for item in checklist.items if item.id != item_id]
    
    if len(checklist.items) < original_count:
        checklists = load_checklists()
        for i, c in enumerate(checklists):
            if c.status_id == status_id:
                checklists[i] = checklist
                break
        save_checklists(checklists)
        return True
    return False


def toggle_checklist_item(status_id: int, item_id: int) -> bool:
    """Переключает состояние пункта чек-листа"""
    checklist = get_checklist_by_status_id(status_id)
    if not checklist:
        return False
    
    for item in checklist.items:
        if item.id == item_id:
            item.checked = not item.checked
            
            checklists = load_checklists()
            for i, c in enumerate(checklists):
                if c.status_id == status_id:
                    checklists[i] = checklist
                    break
            save_checklists(checklists)
            return True
    return False


def reset_checklist(status_id: int):
    """Сбрасывает все галочки в чек-листе"""
    checklist = get_checklist_by_status_id(status_id)
    if not checklist:
        return
    
    for item in checklist.items:
        item.checked = False
    
    checklists = load_checklists()
    for i, c in enumerate(checklists):
        if c.status_id == status_id:
            checklists[i] = checklist
            break
    save_checklists(checklists)


def get_all_checklists() -> List[Checklist]:
    """Возвращает все чек-листы"""
    return load_checklists()


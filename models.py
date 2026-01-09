from dataclasses import dataclass, asdict
from typing import Optional, Literal, List
import json
import os


ResponsiblePerson = Literal["Игнат", "Лёша", "никто"]
UserRole = Literal["admin", "Игнат", "Лёша", "user"]


@dataclass
class ProjectStatus:
    """Модель статуса проекта"""
    id: int
    name: str
    responsible: ResponsiblePerson
    
    def __str__(self):
        responsible_emoji = {
            "Игнат": "👤",
            "Лёша": "👤",
            "никто": "⚪"
        }
        emoji = responsible_emoji.get(self.responsible, "⚪")
        return f"{emoji} {self.name} ({self.responsible})"
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


@dataclass
class Character:
    """Модель персонажа"""
    id: int
    name: str
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    
    def __str__(self):
        return self.name


@dataclass
class Developer:
    """Модель разработчика"""
    id: int
    name: str
    username: str
    total_projects: int = 0
    released_projects: int = 0
    banned_projects: int = 0
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    
    def __str__(self):
        return f"{self.name} (@{self.username})\n📊 Всего: {self.total_projects} | ✅ Вышло: {self.released_projects} | 🚫 Забанено: {self.banned_projects}"


@dataclass
class Project:
    """Модель проекта"""
    id: int
    name: str
    character_id: int
    developer_id: int
    status_id: int
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    
    def __str__(self):
        return f"📁 {self.name}\n👤 Персонаж ID: {self.character_id}\n💻 Разработчик ID: {self.developer_id}\n📊 Статус ID: {self.status_id}"


@dataclass
class User:
    """Модель пользователя бота"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    role: UserRole = "user"
    notifications_enabled: bool = True
    notification_interval: int = 30  # минуты: 5, 10, 15, 20, 25, 30, 60
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        # Обработка старых данных без настроек уведомлений
        if "notifications_enabled" not in data:
            data["notifications_enabled"] = True
        if "notification_interval" not in data:
            data["notification_interval"] = 30
        return cls(**data)
    
    def __str__(self):
        role_emoji = {
            "admin": "👑",
            "Игнат": "👤",
            "Лёша": "👤",
            "user": "👤"
        }
        emoji = role_emoji.get(self.role, "👤")
        name = self.first_name or self.username or f"ID:{self.user_id}"
        return f"{emoji} {name} ({self.role})"


@dataclass
class ChecklistItem:
    """Пункт чек-листа"""
    id: int
    text: str
    checked: bool = False
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


@dataclass
class Checklist:
    """Чек-лист для статуса"""
    status_id: int
    items: List[ChecklistItem]
    
    def to_dict(self):
        return {
            "status_id": self.status_id,
            "items": [item.to_dict() for item in self.items]
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        items = [ChecklistItem.from_dict(item) for item in data.get("items", [])]
        return cls(
            status_id=data["status_id"],
            items=items
        )
    
    def is_complete(self) -> bool:
        """Проверяет, все ли пункты отмечены"""
        if not self.items:
            return True
        return all(item.checked for item in self.items)


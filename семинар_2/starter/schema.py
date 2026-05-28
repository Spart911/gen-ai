"""
Pydantic-схема заявки на курсы повышения квалификации (ДПО).
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

CITIES = {
    "Москва",
    "Санкт-Петербург",
    "Новосибирск",
    "Екатеринбург",
    "Казань",
    "Нижний Новгород",
    "Самара",
    "Краснодар",
    "Ростов-на-Дону",
    "Воронеж",
    "Уфа",
    "Красноярск",
}

SPECIALITIES = (
    "учитель начальных классов",
    "воспитатель",
    "логопед",
    "психолог",
    "медсестра",
    "инженер",
    "бухгалтер",
    "юрист",
    "социальный работник",
    "экономист",
)

COURSES = (
    "Педагогика и методика начального образования",
    "Коррекционная педагогика",
    "Менеджмент в образовании",
    "Информационные технологии в образовании",
    "Дошкольная педагогика",
    "Медицинское дело",
    "Бухгалтерский учёт и налогообложение",
    "Правовое обеспечение",
)

# Plausible speciality → course options (used for stratified pairing).
SPECIALITY_COURSE_MAP: dict[str, tuple[str, ...]] = {
    "учитель начальных классов": ("Педагогика и методика начального образования",),
    "воспитатель": ("Дошкольная педагогика",),
    "логопед": ("Коррекционная педагогика",),
    "психолог": ("Коррекционная педагогика", "Менеджмент в образовании"),
    "медсестра": ("Медицинское дело",),
    "инженер": ("Информационные технологии в образовании",),
    "бухгалтер": ("Бухгалтерский учёт и налогообложение",),
    "юрист": ("Правовое обеспечение",),
    "социальный работник": ("Менеджмент в образовании", "Коррекционная педагогика"),
    "экономист": ("Бухгалтерский учёт и налогообложение", "Менеджмент в образовании"),
}


class Address(BaseModel):
    city: str
    district: str = Field(min_length=2, max_length=40)

    @field_validator("city")
    @classmethod
    def city_must_be_in_list(cls, value: str) -> str:
        if value not in CITIES:
            raise ValueError(f"Город «{value}» не из утверждённого списка")
        return value


class Application(BaseModel):
    full_name: str = Field(min_length=5, max_length=80)
    age: int = Field(ge=22, le=65)
    address: Address
    speciality: Literal[
        "учитель начальных классов",
        "воспитатель",
        "логопед",
        "психолог",
        "медсестра",
        "инженер",
        "бухгалтер",
        "юрист",
        "социальный работник",
        "экономист",
    ]  # keep in sync with SPECIALITIES
    desired_course: Literal[
        "Педагогика и методика начального образования",
        "Коррекционная педагогика",
        "Менеджмент в образовании",
        "Информационные технологии в образовании",
        "Дошкольная педагогика",
        "Медицинское дело",
        "Бухгалтерский учёт и налогообложение",
        "Правовое обеспечение",
    ]
    years_of_experience: int = Field(ge=0, le=40)
    graduation_year: int = Field(ge=1980, le=2024)

    @field_validator("graduation_year")
    @classmethod
    def graduation_consistent_with_age(cls, value: int, info) -> int:
        age = info.data.get("age")
        if age is None:
            return value
        current_year = date.today().year
        # Человек не мог окончить вуз позже, чем (возраст − 22) лет назад.
        latest_graduation = current_year - (age - 22)
        if value > latest_graduation:
            raise ValueError(
                f"Год окончания {value} несовместим с возрастом {age}: "
                f"максимум {latest_graduation}"
            )
        # Обычно в вуз поступают не раньше 18 — нижняя граница.
        earliest_graduation = current_year - age + 18
        if value < earliest_graduation:
            raise ValueError(
                f"Год окончания {value} слишком ранний для возраста {age}: "
                f"минимум {earliest_graduation}"
            )
        return value

    @property
    def city(self) -> str:
        return self.address.city

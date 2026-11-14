"""Romanian grammar helpers for generated texts."""

from typing import NamedTuple

from app.models import BusinessType


class TypeNouns(NamedTuple):
    """The Romanian nouns for a business type, as texts need them."""

    singular: str
    plural: str
    plural_definite: str
    offer: str


TYPE_NOUNS: dict[BusinessType, TypeNouns] = {
    "cafenea": TypeNouns("cafenea", "cafenele", "cafenelele", "Meniul"),
    "restaurant": TypeNouns("restaurant", "restaurante", "restaurantele", "Meniul"),
    "bar": TypeNouns("bar", "baruri", "barurile", "Meniul"),
    "salon": TypeNouns("salon", "saloane", "saloanele", "Lista de servicii"),
    "hotel": TypeNouns("hotel", "hoteluri", "hotelurile", "Lista de camere"),
    "magazin": TypeNouns("magazin", "magazine", "magazinele", "Lista de produse"),
    "altceva": TypeNouns("afacere", "afaceri", "afacerile", "Lista de servicii"),
}
"""The nouns for each business type: „o cafenea”, „cafenele”, „cafenelele din jur”, „Meniul și prețurile”."""


def get_count_phrase(count: int, singular: str, plural: str) -> str:
    """Returns a count with its noun in Romanian: „1 recenzie”, „5 recenzii”, „38 de recenzii”."""
    if count == 1:
        return f"1 {singular}"
    last_two_digits = count % 100
    if count == 0 or 1 <= last_two_digits <= 19:
        return f"{count} {plural}"
    return f"{count} de {plural}"


def get_list_phrase(items: list[str]) -> str:
    """Returns items joined the Romanian way: „A”, „A și B”, „A, B și C”."""
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} și {items[-1]}"

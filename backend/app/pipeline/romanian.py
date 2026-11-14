"""Romanian grammar helpers for generated texts."""


def get_count_phrase(count: int, singular: str, plural: str) -> str:
    """Returns a count with its noun in Romanian: „1 recenzie”, „5 recenzii”, „38 de recenzii”."""
    if count == 1:
        return f"1 {singular}"
    last_two_digits = count % 100
    if count == 0 or 1 <= last_two_digits <= 19:
        return f"{count} {plural}"
    return f"{count} de {plural}"

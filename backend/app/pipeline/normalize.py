"""Normalization and comparison of names, addresses, phones and opening hours across sources."""

import re
import unicodedata
from urllib.parse import urlparse

import phonenumbers
from pydantic import BaseModel
from rapidfuzz import fuzz

NAME_MATCH_THRESHOLD = 85
"""The minimum `token_sort_ratio` for two names or street names to count as the same."""

ADDRESS_ABBREVIATIONS = {
    "str": "strada",
    "bd": "bulevardul",
    "bdul": "bulevardul",
    "b-dul": "bulevardul",
    "blvd": "bulevardul",
    "nr": "numarul",
    "sect": "sector",
    "sos": "soseaua",
    "cal": "calea",
    "al": "aleea",
    "dr": "doctor",
}
"""Romanian address abbreviations and their full forms, without diacritics."""

STREET_TYPES = {"strada", "bulevardul", "calea", "soseaua", "aleea", "piata", "splaiul", "intrarea", "drumul"}
"""The words that start a street name."""

LEGAL_SUFFIXES = {"srl", "sa", "pfa", "ii", "if", "snc"}
"""Company-form suffixes ignored when comparing business names."""

INSTAGRAM_RESERVED_PATHS = {"p", "reel", "reels", "stories", "explore", "tv", "accounts"}
"""Instagram paths that aren't profiles (posts, reels, stories)."""

DAY_NAMES: dict[str, int] = {
    "luni": 0,
    "l": 0,
    "lu": 0,
    "mon": 0,
    "monday": 0,
    "marti": 1,
    "ma": 1,
    "tue": 1,
    "tuesday": 1,
    "miercuri": 2,
    "mi": 2,
    "mie": 2,
    "wed": 2,
    "wednesday": 2,
    "joi": 3,
    "j": 3,
    "jo": 3,
    "thu": 3,
    "thursday": 3,
    "vineri": 4,
    "v": 4,
    "vi": 4,
    "fri": 4,
    "friday": 4,
    "sambata": 5,
    "s": 5,
    "sa": 5,
    "sat": 5,
    "saturday": 5,
    "duminica": 6,
    "d": 6,
    "du": 6,
    "sun": 6,
    "sunday": 6,
}
"""Day names and abbreviations (Romanian and English, without diacritics) mapped to 0 = Monday … 6 = Sunday."""

ALL_DAYS_WORDS = ("zilnic", "daily", "everyday", "toate zilele")
"""Phrases that mean every day of the week."""

NON_STOP_WORDS = ("non-stop", "nonstop", "24/7", "24 de ore", "24 hours", "open 24")
"""Phrases that mean open all day, every day."""

CLOSED_WORDS = ("inchis", "closed")
"""Words that mark a day as closed."""

MINUTES_PER_DAY = 24 * 60
"""Minutes in a day, the closing time of a non-stop interval."""

HOURS_TOKEN_PATTERN = re.compile(
    r"(?P<open_hour>\d{1,2})(?:[:.](?P<open_minute>\d{2}))?\s*[-–—]\s*(?P<close_hour>\d{1,2})(?:[:.](?P<close_minute>\d{2}))?"
    rf"|\b(?P<closed>{'|'.join(CLOSED_WORDS)})\b"
)
"""A time range („8:00–20:00”, „9-17”) or a closed word, in diacritic-free text."""

HOURS_SEGMENT_PATTERN = re.compile(r"[;\n|]|,(?=\s*[a-z])")
"""Where hours text splits into parts: „;”, line breaks, „|” and commas followed by a word."""

WeeklyHours = dict[int, list[tuple[int, int]]]
"""Opening intervals per day (0 = Monday), in minutes from midnight; a missing day is unknown, `[]` is closed."""


class AddressParts(BaseModel):
    """The parts of an address that decide whether two addresses are the same place."""

    street: str | None
    number: str | None
    sector: str | None


def strip_diacritics(text: str) -> str:
    """Returns lowercase text without diacritics, with the cedilla forms of ș and ț unified first."""
    unified = text.replace("ş", "ș").replace("Ş", "Ș").replace("ţ", "ț").replace("Ţ", "Ț")
    decomposed = unicodedata.normalize("NFKD", unified)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).lower()


def get_tokens(text: str) -> list[str]:
    """Returns the lowercase, diacritic-free words and numbers of a text, keeping hyphenated words whole."""
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", strip_diacritics(text))


def normalize_address(address: str) -> str:
    """Returns an address in lowercase words without diacritics, with abbreviations expanded."""
    return " ".join(ADDRESS_ABBREVIATIONS.get(token, token) for token in get_tokens(address))


def get_address_parts(address: str) -> AddressParts:
    """Returns the street name, street number and sector of an address."""
    segments = [normalize_address(segment) for segment in address.split(",")]
    sector_match = re.search(r"\bsector (\d)\b", " ".join(segments))
    street_segment = next(
        (segment for segment in segments if segment.split() and segment.split()[0] in STREET_TYPES),
        segments[0] if segments else "",
    )
    number_match = re.search(r"\b(\d+[a-z]?)\b", street_segment)
    street = street_segment[: number_match.start()] if number_match else street_segment
    street = re.sub(r"\bnumarul\b", "", street).strip()
    return AddressParts(
        street=street or None,
        number=number_match.group(1) if number_match else None,
        sector=sector_match.group(1) if sector_match else None,
    )


def addresses_match(first: str, second: str) -> bool:
    """Returns whether two addresses name the same street, number and sector, ignoring formatting and parts only one has."""
    first_parts = get_address_parts(first)
    second_parts = get_address_parts(second)
    both_streets = first_parts.street and second_parts.street
    if both_streets and fuzz.token_sort_ratio(first_parts.street, second_parts.street) < NAME_MATCH_THRESHOLD:
        return False
    if first_parts.number and second_parts.number and first_parts.number != second_parts.number:
        return False
    return not (first_parts.sector and second_parts.sector and first_parts.sector != second_parts.sector)


def normalize_phone(phone: str) -> str | None:
    """Returns a phone number in E.164 (`+40…`), or `None` when it isn't a valid number."""
    try:
        parsed = phonenumbers.parse(phone, "RO")
    except phonenumbers.NumberParseException:
        return None
    if not phonenumbers.is_valid_number(parsed):
        return None
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def format_national_phone(phone: str) -> str | None:
    """Returns a phone number in Romanian national format, e.g. „0721 234 567”, or `None` when it isn't valid."""
    e164 = normalize_phone(phone)
    if e164 is None:
        return None
    return phonenumbers.format_number(phonenumbers.parse(e164), phonenumbers.PhoneNumberFormat.NATIONAL)


def get_name_key(name: str) -> str:
    """Returns a business name without diacritics, quotes, punctuation or a company-form suffix."""
    compact = re.sub(r"\bs\.\s*r\.\s*l\.?|\bs\.\s*a\.", " ", strip_diacritics(name))
    return " ".join(token for token in get_tokens(compact) if token not in LEGAL_SUFFIXES)


def names_match(first: str, second: str) -> bool:
    """Returns whether two business names are the same, ignoring word order, diacritics and company-form suffixes."""
    return fuzz.token_sort_ratio(get_name_key(first), get_name_key(second)) >= NAME_MATCH_THRESHOLD


def names_overlap(first: str, second: str) -> bool:
    """Returns whether two business names match, also when one is only part of the other („Boema”, „Origo Coffee”)."""
    return fuzz.token_set_ratio(get_name_key(first), get_name_key(second)) >= NAME_MATCH_THRESHOLD


def get_instagram_handle(url: str | None) -> str | None:
    """Returns the Instagram handle in a profile link or a typed „@handle”, without the @."""
    if not url or not url.strip():
        return None
    text = url.strip()
    if "instagram.com" not in text:
        match = re.fullmatch(r"@?([A-Za-z0-9_.]+)", text)
        return match.group(1) if match else None
    segments = [segment for segment in urlparse(text if "://" in text else f"https://{text}").path.split("/") if segment]
    if not segments or segments[0] in INSTAGRAM_RESERVED_PATHS:
        return None
    return segments[0].removeprefix("@")


def get_domain(url: str) -> str:
    """Returns a link's host without `www.`, in lowercase; a bare domain counts as a link."""
    return urlparse(url if "://" in url else f"https://{url}").netloc.lower().removeprefix("www.")


def is_on_host(domain: str, host: str) -> bool:
    """Returns whether a domain is a host or one of its subdomains; a host ending in a dot („google.”) takes any country ending."""
    if host.endswith("."):
        return domain.startswith(host) or f".{host}" in domain
    return domain == host or domain.endswith(f".{host}")


def get_minutes(hour: str, minute: str | None) -> int:
    """Returns a time of day in minutes from midnight; 24:00 is the end of the day."""
    return int(hour) * 60 + int(minute or 0)


def get_days(day_text: str) -> list[int]:
    """Returns the days a day expression covers: one day, a range („L–V”, „Luni-Vineri”) or a list."""
    words = re.findall(r"[a-z]+", strip_diacritics(day_text))
    if any(phrase in strip_diacritics(day_text) for phrase in ALL_DAYS_WORDS):
        return list(range(7))
    days = [DAY_NAMES[word] for word in words if word in DAY_NAMES]
    is_range = re.search(r"[a-z]\s*[-–—]\s*[a-z]", strip_diacritics(day_text)) is not None
    if is_range and len(days) == 2:
        start, end = days
        return [(start + offset) % 7 for offset in range((end - start) % 7 + 1)]
    return days


def parse_hours(text: str) -> WeeklyHours:
    """Returns the opening intervals per day read from free text such as „L–V 8:00–20:00; S–D închis” or „non-stop”.

    The text is split at „;”, line breaks and commas before a word; inside each part, a time range applies to the days
    written just before it, and a range with none (a split shift, „8–12, 14–18”) adds to the previous days. „Închis”
    applies to the days before it, or after it („închis luni”). A closing time at or before the opening time is on the
    next day, as in Google's hours, so „7:30–00:00” ends at midnight.
    """
    normalized = strip_diacritics(text)
    if any(phrase in normalized for phrase in NON_STOP_WORDS):
        return {day: [(0, MINUTES_PER_DAY)] for day in range(7)}
    hours: WeeklyHours = {}
    for segment in HOURS_SEGMENT_PATTERN.split(normalized):
        tokens = list(HOURS_TOKEN_PATTERN.finditer(segment))
        days: list[int] = []
        for index, token in enumerate(tokens):
            stated_days = get_days(segment[tokens[index - 1].end() if index else 0 : token.start()])
            if token.group("closed"):
                next_start = tokens[index + 1].start() if index + 1 < len(tokens) else len(segment)
                for day in stated_days or get_days(segment[token.end() : next_start]):
                    hours[day] = []
                days = []
                continue
            if stated_days:
                days = stated_days
                for day in days:
                    hours[day] = []
            opening = get_minutes(token.group("open_hour"), token.group("open_minute"))
            closing = get_minutes(token.group("close_hour"), token.group("close_minute"))
            interval = (opening, closing if closing > opening else closing + MINUTES_PER_DAY)
            for day in days:
                hours[day].append(interval)
    return hours


def get_hours_mismatch_days(first: WeeklyHours, second: WeeklyHours) -> list[int]:
    """Returns the days both sources state hours for, where the hours differ."""
    return [day for day in range(7) if day in first and day in second and sorted(first[day]) != sorted(second[day])]

"""Checks the §4 normalization rules."""

from app.pipeline.normalize import (
    addresses_match,
    format_national_phone,
    get_hours_mismatch_days,
    names_match,
    names_overlap,
    normalize_phone,
    parse_hours,
)


def test_street_abbreviation_is_the_same_address() -> None:
    """Checks that „Str.” and „Strada” and missing diacritics never count as a mismatch."""
    assert addresses_match("Str. Dr. Lister nr. 10, Sector 5, București", "Strada Doctor Lister 10, București")
    assert addresses_match("Șos. Kiseleff 5", "Soseaua Kiseleff nr. 5")
    assert addresses_match("Bd. Eroilor 3", "B-dul Eroilor nr. 3")


def test_different_number_or_street_is_a_mismatch() -> None:
    """Checks that a different street number, street or sector is a real mismatch."""
    assert not addresses_match("Str. Dr. Lister 10", "Strada Doctor Lister 12")
    assert not addresses_match("Str. Dr. Lister 10", "Bd. Eroilor 10")
    assert not addresses_match("Calea Victoriei 10, Sector 1", "Calea Victoriei 10, Sector 3")


def test_three_phone_formats_are_the_same_number() -> None:
    """Checks that the national, +40 and 0040 formats normalize to one E.164 number."""
    assert normalize_phone("0721 234 567") == "+40721234567"
    assert normalize_phone("+40721234567") == "+40721234567"
    assert normalize_phone("0040 721 234 567") == "+40721234567"
    assert normalize_phone("not a phone") is None
    assert format_national_phone("+40721234567") == "0721 234 567"


def test_names_ignore_suffixes_diacritics_and_order() -> None:
    """Checks that company suffixes, quotes, diacritics and word order don't matter."""
    assert names_match("Cafeneaua Boema SRL", "„Cafeneaua Boema”")
    assert names_match("Cafeneaua Boemă S.R.L.", "cafeneaua boema")
    assert not names_match("Cafeneaua Boema", "Ceașca Verde")
    assert names_overlap("Origo Coffee", "Origo")
    assert not names_overlap("Origo", "Ceașca Verde")


def test_hours_formats() -> None:
    """Checks the Romanian, English and non-stop hour formats."""
    weekdays = parse_hours("L–V 8:00–20:00; S–D închis")
    assert weekdays[0] == [(480, 1200)]
    assert weekdays[4] == [(480, 1200)]
    assert weekdays[6] == []
    assert parse_hours("Luni–Duminică: 8:00–20:00") == {day: [(480, 1200)] for day in range(7)}
    assert parse_hours("Mon–Fri 9-17")[2] == [(540, 1020)]
    assert parse_hours("non-stop")[3] == [(0, 1440)]


def test_hours_without_separators_and_past_midnight() -> None:
    """Checks day groups written on one line with no separators, split shifts, and closing at or after midnight."""
    hours = parse_hours("Luni : 07.30 - 20:00 Marți - Vineri: 07.30 - 00:00 Sambata - Duminica: 8.00 - 00:00")
    assert hours[0] == [(450, 1200)]
    assert hours[3] == [(450, 1440)]
    assert hours[6] == [(480, 1440)]
    assert parse_hours("L–V 8:00–12:00, 14:00–18:00, S închis")[2] == [(480, 720), (840, 1080)]
    assert parse_hours("L–V 8:00–12:00, 14:00–18:00, S închis")[5] == []
    assert parse_hours("Vineri 22:00–02:00")[4] == [(1320, 1560)]


def test_hours_closed_before_or_after_its_days() -> None:
    """Checks „închis” written before its days or after a group of open days."""
    hours = parse_hours("închis luni, marți-duminică 10-22")
    assert hours[0] == []
    assert hours[1] == hours[6] == [(600, 1320)]
    hours = parse_hours("L-S 9-18, închis duminică")
    assert hours[5] == [(540, 1080)]
    assert hours[6] == []


def test_hours_mismatch_only_on_days_both_state() -> None:
    """Checks that only days stated by both sources with different hours count."""
    google = parse_hours("Luni–Duminică: 8:00–20:00")
    glovo = parse_hours("Luni–Vineri 9:00–18:00")
    assert get_hours_mismatch_days(google, glovo) == [0, 1, 2, 3, 4]
    assert get_hours_mismatch_days(google, parse_hours("L-V 8-20")) == []

from pathlib import Path

import pytest

from bundesanzeiger.errors import ParseError
from bundesanzeiger.parser import (
    german_date,
    looks_like_captcha,
    parse_publication,
    parse_search,
    parse_start_hidden_field,
)

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "tests" / "fixtures" / "ux"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_start_hidden_field_has_expected_pattern():
    name, value = parse_start_hidden_field(fixture("start.html"))
    assert name == "0-1.-top~content~panel-left~card-form"
    assert value == ""


def test_search_parses_company_area_date_and_title():
    page = parse_search(fixture("suche_deutsche_bahn.html"), "https://example.invalid")
    assert page.gesamt == 6200
    assert len(page.treffer) == 3
    first = page.treffer[0]
    assert first.datum == "2026-07-22"
    assert first.bereich == "Gesellschaftsbekanntmachungen"
    assert first.firma == "Deutsche Bahn Aktiengesellschaft"
    assert first.sitz == "Berlin"
    assert first.titel.startswith("Hinweisbekanntmachung")
    assert first.url == "https://example.invalid/pub/de/suchergebnis?1"


def test_search_parses_balanced_area_and_captcha_link():
    page = parse_search(
        fixture("suche_finanzberichte.html"), "https://example.invalid"
    )
    assert page.gesamt == 993
    assert page.treffer[0].bereich == "Rechnungslegung/Finanzberichte"
    assert page.treffer[0].datum == "2022-05-13"
    assert "captcha" in page.treffer[0].url


def test_empty_search_is_not_a_parse_error():
    page = parse_search(fixture("suche_leer.html"), "https://example.invalid")
    assert page.gesamt == 0
    assert page.treffer == []


def test_publication_text_contains_body():
    text = parse_publication(fixture("detail_bekanntmachung.html"))
    assert "Beyond1435" in text
    assert "Handelsregister" in text


def test_publication_text_omits_duplicate_title_block():
    text = parse_publication(fixture("detail_bekanntmachung.html"))
    lines = text.splitlines()
    assert lines[0].startswith(
        "Die Deutsche Bahn Aktiengesellschaft mit Sitz in Berlin"
    )
    assert "Hinweisbekanntmachung" not in "\n".join(lines[:3])
    assert lines[-1] == "Der Vorstand"


def test_captcha_detail_is_detected():
    html = fixture("detail_captcha.html")
    assert looks_like_captcha(html, "https://example.invalid/pub/de/suchergebnis?x")
    with pytest.raises(ParseError):
        parse_publication(html)


def test_german_date_roundtrip():
    assert german_date("2026-07-22") == "22.07.2026"

def test_search_ignores_pager_rows_without_company_and_date():
    html = """
    <div class="row"><div class="first"></div>
      <div class="info"><a href="/pub/de/suchergebnis?0">Seitenzahl</a></div>
      <div class="date">von</div></div>
    <div class="row back">
      <div class="first">Beispielfirma AG<br/>Berlin</div>
      <div class="part">Gesellschafts-<br/>bekanntmachungen</div>
      <div class="info"><a href="/pub/de/suchergebnis?1">Titel</a></div>
      <div class="date">22.07.2026</div>
    </div>
    """
    page = parse_search(html, "https://example.invalid")
    assert page.gesamt == 1
    assert len(page.treffer) == 1
    assert page.treffer[0].firma == "Beispielfirma AG"

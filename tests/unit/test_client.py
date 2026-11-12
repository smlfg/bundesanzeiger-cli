from pathlib import Path

import pytest
import requests

from bundesanzeiger.client import BundesanzeigerClient
from bundesanzeiger.errors import NetworkError, UsageError

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "tests" / "fixtures" / "ux"


class Response:
    def __init__(self, text: str, url: str, status_code: int = 200):
        self.text = text
        self.url = url
        self.status_code = status_code
        self.headers = {"Content-Type": "text/html; charset=utf-8"}
        self.encoding = "utf-8"


class DummySession:
    def __init__(self) -> None:
        self.headers: dict[str, str] = {}
        self.calls: list[tuple[str, dict[str, str] | None]] = []

    def get(self, url, params=None, timeout=None, allow_redirects=True):
        self.calls.append((url, params))
        if url.endswith("/pub/de/start?0"):
            return Response(
                (FIXTURES / "start.html").read_text(encoding="utf-8"),
                "http://fake.invalid/pub/de/start?0",
            )
        if url.endswith("/pub/de/start"):
            fields = params or {}
            if "zzzqqq" in fields.get("fulltext", ""):
                return Response(
                    (FIXTURES / "suche_leer.html").read_text(encoding="utf-8"),
                    "http://fake.invalid/pub/de/suchen2?2",
                )
            if fields.get("area_select") == "22":
                return Response(
                    (FIXTURES / "suche_finanzberichte.html").read_text(
                        encoding="utf-8"
                    ),
                    "http://fake.invalid/pub/de/suchen2?3",
                )
            return Response(
                (FIXTURES / "suche_deutsche_bahn.html").read_text(encoding="utf-8"),
                "http://fake.invalid/pub/de/suchen2?1",
            )
        if url.endswith("/pub/de/suchergebnis?1"):
            return Response(
                (FIXTURES / "detail_bekanntmachung.html").read_text(encoding="utf-8"),
                "http://fake.invalid/pub/de/suchergebnis?1",
            )
        if "captcha" in url:
            return Response(
                (FIXTURES / "detail_captcha.html").read_text(encoding="utf-8"),
                "http://fake.invalid/pub/de/suchergebnis?7",
            )
        return Response("", url, status_code=404)


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))


def test_search_reads_dynamic_hidden_field_and_area():
    session = DummySession()
    client = BundesanzeigerClient("http://fake.invalid", session=session)
    result = client.search("Deutsche Bahn AG", "finanzberichte")
    assert result.page.gesamt == 993
    search_params = session.calls[-1][1] or {}
    assert search_params["0-1.-top~content~panel-left~card-form"] == ""
    assert search_params["area_select"] == "22"
    assert search_params["fulltext"] == "Deutsche Bahn AG"


def test_read_returns_text_for_publication():
    client = BundesanzeigerClient("http://fake.invalid", session=DummySession())
    result = client.search("Deutsche Bahn AG")
    detail = client.read(result.page.treffer[0])
    assert detail.captcha is False
    assert "Beyond1435" in detail.text


def test_read_detects_captcha_and_returns_search_url():
    client = BundesanzeigerClient("http://fake.invalid", session=DummySession())
    result = client.search("Deutsche Bahn AG", "finanzberichte")
    detail = client.read(result.page.treffer[0])
    assert detail.captcha is True
    assert "Captcha" in detail.text
    assert detail.url.startswith("http")


def test_network_error_maps_to_exit_code_three():
    class Broken(DummySession):
        def get(self, *args, **kwargs):
            raise requests.ConnectionError("kaputt")

    client = BundesanzeigerClient("http://fake.invalid", session=Broken())
    with pytest.raises(NetworkError) as info:
        client.search("Deutsche Bahn AG")
    assert info.value.exit_code == 3


def test_invalid_base_url_is_a_usage_error():
    with pytest.raises(UsageError):
        BundesanzeigerClient("keine-url")

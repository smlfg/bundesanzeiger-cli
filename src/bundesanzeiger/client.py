"""HTTP-Client für bundesanzeiger.de (sessionbasiert, nur lesend)."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode, urlparse

import requests

from . import __version__
from .errors import NetworkError, UsageError
from .parser import (
    Entry,
    SearchPage,
    looks_like_captcha,
    parse_publication,
    parse_search,
    parse_start_hidden_field,
)

DEFAULT_BASE_URL = "https://www.bundesanzeiger.de"
USER_AGENT = (
    f"bundesanzeiger-cli/{__version__} "
    "(+https://github.com/smlfg/bundesanzeiger-cli)"
)
CACHE_TTL_SECONDS = 600

AREA_CODES = {
    "gesellschaft": "6",
    "kapitalmarkt": "7",
    "gericht": "5",
    "finanzberichte": "22",
    "amtlich": "1",
    "verschiedenes": "8",
    "nichtamtlich": "2",
}

AREA_NAMES = {
    "gesellschaft": "Gesellschaftsbekanntmachungen",
    "kapitalmarkt": "Kapitalmarkt",
    "gericht": "Gerichtlicher Teil",
    "finanzberichte": "Rechnungslegung/Finanzberichte",
    "amtlich": "Amtlicher Teil",
    "verschiedenes": "Verschiedene Bekanntmachungen",
    "nichtamtlich": "Nichtamtlicher Teil",
}


@dataclass
class SearchResult:
    suchbegriff: str
    bereich: str | None
    page: SearchPage
    url: str


@dataclass
class DetailResult:
    text: str
    captcha: bool
    url: str


def _cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "bundesanzeiger-cli"


def _cache_read(key: str) -> tuple[str, str] | None:
    path = _cache_dir() / f"{key}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    try:
        age = time.time() - float(data.get("zeit", 0))
    except (TypeError, ValueError):
        return None
    if age > CACHE_TTL_SECONDS:
        return None
    text = data.get("text")
    url = data.get("url")
    if not isinstance(text, str) or not isinstance(url, str):
        return None
    return text, url


def _cache_write(key: str, text: str, url: str) -> None:
    directory = _cache_dir()
    try:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(directory, 0o700)
        payload = json.dumps(
            {"zeit": time.time(), "url": url, "text": text}, ensure_ascii=False
        ).encode("utf-8")
        path = directory / f"{key}.json"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
    except OSError:
        return


class BundesanzeigerClient:
    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float = 15.0,
        session: requests.Session | None = None,
    ) -> None:
        raw = base_url or os.environ.get("BUNDESANZEIGER_BASE_URL") or DEFAULT_BASE_URL
        parsed = urlparse(raw)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise UsageError(
                "BUNDESANZEIGER_BASE_URL ist keine gültige URL "
                "(erwartet http(s)://host)."
            )
        self.base_url = raw.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "de-DE,de;q=0.9",
            }
        )
        self._warmed = False
        self._hidden_name = ""
        self._hidden_value = ""
        self.search_url = ""

    def _request_text(
        self,
        url: str,
        params: dict[str, str] | None = None,
        *,
        use_cache: bool = False,
    ) -> tuple[str, str]:
        query = urlencode(params or {})
        key = ""
        if use_cache:
            digest = hashlib.sha256(f"{url}?{query}".encode("utf-8")).hexdigest()
            key = digest
            cached = _cache_read(key)
            if cached is not None:
                return cached

        try:
            response = self.session.get(
                url, params=params, timeout=self.timeout, allow_redirects=True
            )
        except requests.Timeout as exc:
            raise NetworkError(
                "Zeitüberschreitung – Verbindung prüfen oder später erneut versuchen."
            ) from exc
        except requests.RequestException as exc:
            raise NetworkError(
                "Netzwerkfehler – Verbindung prüfen oder später erneut versuchen."
            ) from exc

        if response.status_code >= 400:
            raise NetworkError(
                f"Quelle antwortet mit HTTP {response.status_code} – "
                "später erneut versuchen."
            )

        content_type = response.headers.get("Content-Type", "")
        if "charset" not in content_type.lower():
            response.encoding = "utf-8"
        text = response.text
        final_url = response.url

        if use_cache and key:
            _cache_write(key, text, final_url)
        return text, final_url

    def _warm_session(self) -> None:
        if self._warmed:
            return
        self._warmed = True
        try:
            self.session.get(
                self.base_url + "/", timeout=self.timeout, allow_redirects=True
            )
        except requests.RequestException as exc:
            raise NetworkError(
                "Netzwerkfehler – Verbindung prüfen oder später erneut versuchen."
            ) from exc

    def _ensure_start(self) -> None:
        if self._hidden_name:
            return
        self._warm_session()
        text, _ = self._request_text(self.base_url + "/pub/de/start?0")
        self._hidden_name, self._hidden_value = parse_start_hidden_field(text)

    def search(
        self,
        suchbegriff: str,
        bereich: str | None = None,
        *,
        use_cache: bool = True,
    ) -> SearchResult:
        self._ensure_start()
        params = {
            self._hidden_name: self._hidden_value,
            "fulltext": suchbegriff,
            "area_select": AREA_CODES.get(bereich, ""),
            "search_button": "Suchen",
        }
        text, final_url = self._request_text(
            self.base_url + "/pub/de/start", params, use_cache=use_cache
        )
        page = parse_search(text, self.base_url)
        self.search_url = final_url
        return SearchResult(
            suchbegriff=suchbegriff,
            bereich=bereich,
            page=page,
            url=final_url,
        )

    def read(self, entry: Entry) -> DetailResult:
        text, final_url = self._request_text(entry.url, use_cache=False)
        if looks_like_captcha(text, final_url):
            message = (
                "Jahresabschluss ist auf bundesanzeiger.de durch ein Captcha "
                "geschützt – im Browser öffnen:\n"
                f"{self.search_url or final_url}"
            )
            return DetailResult(
                text=message,
                captcha=True,
                url=self.search_url or final_url,
            )
        if "/pub/de/start" in final_url and "fulltext" in final_url:
            raise NetworkError("Keine gültige Session – erneut suchen.")
        return DetailResult(
            text=parse_publication(text),
            captcha=False,
            url=entry.url,
        )

"""Kleiner HTML-Parser für die Bundesanzeiger-Seiten (nur Standardbibliothek)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin

from .errors import ParseError

HIDDEN_FIELD_RE = re.compile(
    r"\d+-\d+\.-top~content~panel-left~card-form"
)
DATE_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})")
VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}
BLOCK_TAGS = {
    "address",
    "article",
    "blockquote",
    "div",
    "dl",
    "fieldset",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "tr",
    "ul",
}


@dataclass
class Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list["Node | str"] = field(default_factory=list)
    parent: "Node | None" = None

    def classes(self) -> set[str]:
        return set((self.attrs.get("class") or "").split())


class _TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#document")
        self._stack: list[Node] = [self.root]

    def handle_starttag(self, tag: str, attrs) -> None:
        node = Node(
            tag,
            {key: value or "" for key, value in attrs},
            parent=self._stack[-1],
        )
        self._stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self._stack.append(node)

    def handle_startendtag(self, tag: str, attrs) -> None:
        node = Node(
            tag,
            {key: value or "" for key, value in attrs},
            parent=self._stack[-1],
        )
        self._stack[-1].children.append(node)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == tag:
                del self._stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self._stack[-1].children.append(data)


def parse_html(text: str) -> Node:
    builder = _TreeBuilder()
    builder.feed(text)
    builder.close()
    return builder.root


def walk(node: Node):
    for child in node.children:
        if isinstance(child, Node):
            yield child
            yield from walk(child)


def has_class(node: Node, name: str) -> bool:
    return name in node.classes()


def find_all(node: Node, predicate) -> list[Node]:
    return [item for item in walk(node) if predicate(item)]


def find_first(node: Node, predicate) -> Node | None:
    for item in walk(node):
        if predicate(item):
            return item
    return None


def first_with_class(node: Node, name: str) -> Node | None:
    return find_first(node, lambda item: has_class(item, name))


def text_content(node: Node) -> str:
    parts: list[str] = []

    def visit(current: Node) -> None:
        for child in current.children:
            if isinstance(child, str):
                parts.append(child)
                continue
            if child.tag in VOID_TAGS:
                if child.tag == "br":
                    parts.append("\n")
                continue
            block = child.tag in BLOCK_TAGS
            if block:
                parts.append("\n")
            visit(child)
            if block:
                parts.append("\n")

    visit(node)
    return "".join(parts)


def clean_lines(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        cleaned = re.sub(r"\s+", " ", line).strip()
        if cleaned:
            lines.append(cleaned)
    return lines


def clean_text(text: str) -> str:
    return " ".join(clean_lines(text))


def clean_area(text: str) -> str:
    value = re.sub(r"-\s*\n\s*", "", text)
    value = re.sub(r"/\s*\n\s*", "/", value)
    value = re.sub(r"\s*\n\s*", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def iso_date(text: str) -> str:
    match = DATE_RE.search(text)
    if not match:
        return clean_text(text)
    day, month, year = match.groups()
    return f"{year}-{month}-{day}"


def german_date(value: str) -> str:
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", value)
    if not match:
        return value
    year, month, day = match.groups()
    return f"{day}.{month}.{year}"


@dataclass
class Entry:
    nummer: int
    datum: str
    bereich: str
    firma: str
    sitz: str
    titel: str
    url: str

    def as_json(self) -> dict:
        return {
            "nummer": self.nummer,
            "datum": self.datum,
            "bereich": self.bereich,
            "firma": self.firma,
            "sitz": self.sitz,
            "titel": self.titel,
            "url": self.url,
        }


@dataclass
class SearchPage:
    gesamt: int
    treffer: list[Entry]


def parse_start_hidden_field(html: str) -> tuple[str, str]:
    root = parse_html(html)
    for node in walk(root):
        if node.tag != "input":
            continue
        name = node.attrs.get("name", "")
        if HIDDEN_FIELD_RE.fullmatch(name):
            return name, node.attrs.get("value", "")
    raise ParseError(
        "Suchformular nicht gefunden – Startseite erneut laden oder später versuchen."
    )


def _row_entries(root: Node, base_url: str) -> list[Entry]:
    entries: list[Entry] = []
    for row in walk(root):
        if row.tag != "div" or not has_class(row, "row"):
            continue
        first = first_with_class(row, "first")
        info = first_with_class(row, "info")
        date = first_with_class(row, "date")
        if first is None or info is None or date is None:
            continue
        anchor = find_first(info, lambda item: item.tag == "a")
        if anchor is None:
            continue

        name_lines = clean_lines(text_content(first))
        firma = name_lines[0] if name_lines else ""
        sitz = " ".join(name_lines[1:]) if len(name_lines) > 1 else ""

        part = first_with_class(row, "part")
        bereich = clean_area(text_content(part)) if part is not None else ""
        titel = clean_text(text_content(anchor))
        href = anchor.attrs.get("href", "")
        url = urljoin(base_url.rstrip("/") + "/", href)
        entries.append(
            Entry(
                nummer=len(entries) + 1,
                datum=iso_date(text_content(date)),
                bereich=bereich,
                firma=firma,
                sitz=sitz,
                titel=titel,
                url=url,
            )
        )
    return entries


def parse_search(html: str, base_url: str) -> SearchPage:
    root = parse_html(html)
    entries = _row_entries(root, base_url)

    total = len(entries)
    info = find_first(
        root,
        lambda item: item.tag == "div"
        and (item.attrs.get("id") == "piwik_info" or has_class(item, "result_info")),
    )
    if info is not None:
        raw = info.attrs.get("data-count", "")
        try:
            total = int(raw)
        except (TypeError, ValueError):
            total = len(entries)

    if not entries and info is None:
        raise ParseError(
            "Suchergebnis konnte nicht gelesen werden – erneut suchen oder später versuchen."
        )
    return SearchPage(gesamt=total, treffer=entries)


def looks_like_captcha(html: str, url: str = "") -> bool:
    if "captcha_container" in html or "Sicherheitsabfrage" in html:
        return True
    return "captcha" in url.lower()


def parse_publication(html: str) -> str:
    root = parse_html(html)
    container = first_with_class(root, "publication_container")
    if container is None:
        raise ParseError(
            "Volltext nicht gefunden – keine gültige Session, erneut suchen."
        )
    text = "\n".join(clean_lines(text_content(container)))
    if not text:
        raise ParseError(
            "Volltext ist leer – keine gültige Session, erneut suchen."
        )
    return text

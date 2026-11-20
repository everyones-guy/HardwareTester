"""Read UISee-style page and widget records as data, without executing SQL."""

import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from collections.abc import Mapping
from pathlib import PurePosixPath
from typing import NamedTuple

MAX_SOURCE_BYTES = 512 * 1024
MAX_FILES = 16
MAX_TOKENS = 100_000
MAX_PAGES = 128
MAX_CONTROLS = 300
MAX_RESOURCES = 48
MAX_DIAGNOSTICS = 100
MAX_DATABASE_ID = 2**53 - 1

PAGE_TABLE = "PagesInstalled"
WIDGET_TABLE = "WidgetsInstalled"
TABLES = {
    PAGE_TABLE.casefold(): (PAGE_TABLE, ("pagename", "pageid", "pageconfig")),
    WIDGET_TABLE.casefold(): (
        WIDGET_TABLE,
        ("widgetconfigid", "widgetid", "widgetconfig"),
    ),
}
WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|[0-9]+")
HANDLER = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,79}")
SECRET_TAG = re.compile(
    r"(?:password|passwd|passphrase|cookie|credential|secret|token|apikey|"
    r"privatekey|authorization|certificate|connectionstring)"
)
SECRET_VALUE = re.compile(
    r"(?:[a-z][a-z0-9+.-]*://[^\s/@]+:[^\s/@]+@|\bbearer\s+\S+|"
    r"\b(?:password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S+)",
    re.IGNORECASE,
)


class UiDiscoveryError(ValueError):
    """The submitted source collection is invalid or too large."""


class SqlProblem(ValueError):
    """The source syntax is outside the supported UISee format."""


class Token(NamedTuple):
    kind: str
    value: str
    line: int


def _quoted(text, start, line, delimiter):
    pieces = []
    start += 1
    while True:
        end = text.find(delimiter, start)
        if end < 0:
            raise SqlProblem(f"Unclosed SQL literal or identifier on line {line}.")
        pieces.append(text[start:end])
        if delimiter == "]" or text[end + 1 : end + 2] != delimiter:
            return "".join(pieces), end + 1
        pieces.append(delimiter)
        start = end + 2


def _statements(text):
    cursor = 1 if text.startswith("\ufeff") else 0
    line = 1
    statement = []
    count = 0
    while cursor < len(text):
        char = text[cursor]
        if char.isspace():
            line += char == "\n"
            cursor += 1
            continue
        if text.startswith("--", cursor):
            end = text.find("\n", cursor + 2)
            cursor = len(text) if end < 0 else end
            continue
        if text.startswith("/*", cursor):
            end = text.find("*/", cursor + 2)
            if end < 0:
                raise SqlProblem(f"Unclosed SQL comment on line {line}.")
            line += text.count("\n", cursor, end + 2)
            cursor = end + 2
            continue
        if char == ";":
            if statement:
                yield statement
                statement = []
            cursor += 1
            continue
        start_line = line
        if char in "'\"`[":
            value, end = _quoted(text, cursor, line, "]" if char == "[" else char)
            line += text.count("\n", cursor, end)
            cursor = end
            kind = "string" if char == "'" else "identifier"
        else:
            word = WORD.match(text, cursor)
            if word:
                value = word.group()
                cursor = word.end()
                kind = "integer" if value[0].isdigit() else "word"
            else:
                kind = "punctuation"
                value = char
                cursor += 1
        count += 1
        if count > MAX_TOKENS:
            raise UiDiscoveryError("UI SQL exceeds the supported token limit.")
        statement.append(Token(kind, value, start_line))
    if statement:
        yield statement


class Statement:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0

    def take(self):
        if self.index >= len(self.tokens):
            raise SqlProblem("Incomplete UI insert statement.")
        token = self.tokens[self.index]
        self.index += 1
        return token

    def accept(self, kind, value):
        if self.index == len(self.tokens):
            return False
        token = self.tokens[self.index]
        if token.kind != kind or token.value.casefold() != value:
            return False
        self.index += 1
        return True

    def expect(self, kind, value):
        if not self.accept(kind, value):
            raise SqlProblem(f"Expected {value!r} in a UI insert statement.")

    def identifier(self):
        token = self.take()
        if token.kind not in {"identifier", "word"}:
            raise SqlProblem("Expected a table or column identifier in a UI insert.")
        return token.value.casefold()

    def items(self, take_item):
        self.expect("punctuation", "(")
        items = [take_item()]
        while self.accept("punctuation", ","):
            items.append(take_item())
        self.expect("punctuation", ")")
        return items


def _source(path, line, table):
    return {"path": path, "line": line, "table": table}


def _read_rows(path, text, diagnose):
    for tokens in _statements(text):
        statement = Statement(tokens)
        location = _source(path, tokens[0].line, "SQL")
        if not statement.accept("word", "insert"):
            words = tuple(t.value.casefold() for t in tokens[:3] if t.kind == "word")
            if words[:2] in {("create", "table"), ("create", "index")} or words[:1] in {
                ("begin",),
                ("commit",),
                ("pragma",),
            }:
                continue  # These static wrappers do not declare UI records.
            diagnose(
                "unsupportedStatement",
                "Discovery stopped at an SQL statement outside the supported INSERT format.",
                location,
            )
            return
        try:
            if statement.accept("word", "or"):
                conflict = statement.identifier()
                if conflict not in {"abort", "ignore", "replace", "fail", "rollback"}:
                    raise SqlProblem("Unsupported INSERT conflict clause.")
            statement.expect("word", "into")
            key = statement.identifier()
            if key not in TABLES:
                diagnose(
                    "unrecognizedTable",
                    "An INSERT for another table was ignored.",
                    location,
                )
                continue
            table, required = TABLES[key]
            location = _source(path, tokens[0].line, table)
            columns = statement.items(statement.identifier)
            if len(columns) != len(set(columns)) or not set(required) <= set(columns):
                raise SqlProblem("Explicit, unique UISee column names are required.")
            statement.expect("word", "values")
            rows = []
            while True:
                line = (
                    statement.tokens[statement.index].line
                    if statement.index < len(tokens)
                    else tokens[0].line
                )
                values = statement.items(statement.take)
                if len(values) != len(columns) or any(
                    v.kind not in {"string", "integer"} for v in values
                ):
                    raise SqlProblem(
                        "A UI row must contain one string or integer literal per column."
                    )
                by_column = dict(zip(columns, values))
                rows.append(
                    (
                        _source(path, line, table),
                        tuple(by_column[name] for name in required),
                    )
                )
                if len(rows) > MAX_CONTROLS + MAX_PAGES:
                    raise UiDiscoveryError("Too many UI rows in a single INSERT.")
                if not statement.accept("punctuation", ","):
                    break
            if statement.index != len(tokens):
                raise SqlProblem("Unexpected SQL after UI VALUES rows.")
        except SqlProblem as exc:
            diagnose("invalidInsert", str(exc), location)
        else:
            yield from rows


def _short_text(value, length):
    return (
        isinstance(value, str)
        and len(value) <= length
        and value.isprintable()
        and bool(value.strip())
    )


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON property.")
        result[key] = value
    return result


def _reject_json_constant(_):
    raise ValueError("Nonfinite JSON constant.")


def _resource_attributes(token, source, diagnose):
    if token.kind != "string":
        raise SqlProblem("UI configuration must be a quoted JSON string.")
    try:
        try:
            data = json.loads(
                token.value,
                object_pairs_hook=_unique_json_object,
                parse_constant=_reject_json_constant,
            )
        except json.JSONDecodeError:
            # Legacy UISee recognizes doubled double quotes inside the SQL string.
            data = json.loads(
                token.value.replace('""', '"'),
                object_pairs_hook=_unique_json_object,
                parse_constant=_reject_json_constant,
            )
    except (ValueError, RecursionError) as exc:
        raise SqlProblem("UI configuration is not supported JSON.") from exc
    group = data.get("Resources", {}) if isinstance(data, dict) else None
    values = group.get("resource", []) if isinstance(group, dict) else None
    if not isinstance(values, list):
        raise SqlProblem("UI configuration must contain a Resources.resource array.")
    if len(values) > MAX_RESOURCES:
        diagnose(
            "resourcesLimited",
            "Additional resource fields were omitted from this row.",
            source,
        )

    attributes = []
    omitted = False
    for entry in values[:MAX_RESOURCES]:
        if (
            not isinstance(entry, dict)
            or not _short_text(entry.get("tag"), 64)
            or "value" not in entry
        ):
            omitted = True
            continue
        tag, value = entry["tag"], entry["value"]
        normalized = re.sub(r"[^a-z]", "", tag.casefold())
        if SECRET_TAG.search(normalized):
            omitted = True
            continue
        if type(value) is str:
            if (
                len(value) > 256
                or (value and not value.isprintable())
                or SECRET_VALUE.search(value)
            ):
                omitted = True
                continue
        elif type(value) is int:
            if abs(value) > MAX_DATABASE_ID:
                omitted = True
                continue
        elif type(value) is float:
            if not math.isfinite(value):
                omitted = True
                continue
        elif value is not None and type(value) is not bool:
            omitted = True
            continue
        attributes.append({"tag": tag, "value": value})
    if omitted:
        diagnose(
            "omittedMetadata",
            "Sensitive, structured, or invalid metadata was omitted.",
            source,
        )
    return attributes


def _row_id(token):
    if token.kind != "integer" or len(token.value) > 16:
        raise SqlProblem("Page and widget identifiers must be nonnegative integers.")
    value = int(token.value)
    if value > MAX_DATABASE_ID:
        raise SqlProblem(
            "A page or widget identifier exceeds the supported integer range."
        )
    return value


def _metadata(attributes, source, diagnose):
    counts = Counter(a["tag"].casefold() for a in attributes)
    if any(count > 1 for count in counts.values()):
        diagnose(
            "ambiguousMetadata",
            "Duplicate resource tags were excluded from field inference.",
            source,
        )
    return {
        a["tag"].casefold(): a["value"]
        for a in attributes
        if counts[a["tag"].casefold()] == 1
    }


def _number(value):
    if type(value) is str and re.fullmatch(
        r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)", value
    ):
        value = float(value)
    if (
        type(value) in {int, float}
        and abs(value) <= MAX_DATABASE_ID
        and math.isfinite(value)
    ):
        return value
    return None


def _control_details(attributes, source, diagnose):
    meta = _metadata(attributes, source, diagnose)
    name, button_type = meta.get("name"), meta.get("buttontype")
    if not _short_text(name, 128):
        name = None
        diagnose(
            "missingControlName", "The widget has no unambiguous Name resource.", source
        )
    if not _short_text(button_type, 64):
        button_type = None
    handler = meta.get("handler")
    if handler is not None and (
        type(handler) is not str or not HANDLER.fullmatch(handler)
    ):
        handler = None
        diagnose(
            "invalidHandlerHint",
            "The source handler hint was not a simple identifier.",
            source,
        )
    input_spec = None
    if (
        name
        and button_type
        and button_type.casefold() in {"numeric", "numericinput", "number"}
    ):
        minimum = _number(meta.get("minvalue"))
        maximum = _number(meta.get("maxvalue"))
        step = _number(meta.get("step"))
        if (
            minimum is None
            or maximum is None
            or step is None
            or maximum <= minimum
            or not 0 < step <= maximum - minimum
        ):
            diagnose(
                "missingNumericBounds",
                "A numeric widget needs explicit MinValue, MaxValue and Step resources.",
                source,
            )
        else:
            input_spec = {
                "kind": "number",
                "min": minimum,
                "max": maximum,
                "step": step,
            }
    return {
        "name": name,
        "buttonType": button_type,
        "widgetIndex": meta.get("widgetindex"),
        "input": input_spec,
        # A resource can name a function. Only a reviewed binding can authorize it.
        "handler": handler,
        "handlerSource": source if handler else None,
    }


def _link_id(value):
    if type(value) is str and re.fullmatch(r"[0-9]{1,16}", value):
        value = int(value)
    return value if type(value) is int and 0 <= value <= MAX_DATABASE_ID else None


def _link_workflows(pages, controls, duplicate_controls, diagnose):
    page_by_id = {page["pageId"]: page for page in pages}
    input_by_id = {
        (control["pageId"], control["widgetId"], control["widgetConfigId"]): control
        for control in controls
        if control["input"] is not None
    }
    navigation = defaultdict(list)
    confirmations = defaultdict(list)
    invalid_confirm_pages = {
        control["pageId"]
        for control in duplicate_controls
        if (control["buttonType"] or "").casefold() == "confirm"
    }
    for control in controls:
        kind = (control["buttonType"] or "").casefold()
        if kind not in {"navigate", "confirm"}:
            continue
        source = control["source"]
        meta = _metadata(control["attributes"], source, diagnose)
        page_id = control["pageId"]
        if kind == "navigate":
            destination = _link_id(meta.get("targetpageid"))
            if (
                not control["name"]
                or destination not in page_by_id
                or destination == page_id
            ):
                diagnose(
                    "invalidNavigation",
                    "Navigation needs a name and a different existing TargetPageID.",
                    source,
                )
                continue
            control["targetPageId"] = destination
            navigation[destination].append(control)
            continue
        target = input_by_id.get(
            (
                page_id,
                _link_id(meta.get("targetwidgetid")),
                _link_id(meta.get("targetwidgetconfigid")),
            )
        )
        if not control["name"] or target is None:
            invalid_confirm_pages.add(page_id)
            diagnose(
                "invalidConfirmation",
                "Confirmation needs a name and an exact numeric widget and configuration ID on its page.",
                source,
            )
            continue
        control["targetControlId"] = target["id"]
        confirmations[target["id"]].append(control)

    for control in input_by_id.values():
        buttons = confirmations[control["id"]]
        if not buttons and control["pageId"] not in invalid_confirm_pages:
            continue
        links = navigation[control["pageId"]]
        conflict = (
            len(buttons) == 1
            and control["handler"]
            and buttons[0]["handler"]
            and control["handler"] != buttons[0]["handler"]
        )
        if (
            len(buttons) != 1
            or len(links) != 1
            or conflict
            or control["pageId"] in invalid_confirm_pages
        ):
            control["workflowError"] = (
                "The source needs one navigation button and one matching confirmation "
                "button with a consistent handler."
            )
            diagnose("unresolvedWorkflow", control["workflowError"], control["source"])
            continue
        control["workflow"] = {
            "navigationId": links[0]["id"],
            "confirmationId": buttons[0]["id"],
        }


def _source_manifest(sources):
    if not isinstance(sources, Mapping) or not 1 <= len(sources) <= MAX_FILES:
        raise UiDiscoveryError(f"Choose between 1 and {MAX_FILES} UI SQL sources.")
    manifest = []
    known_paths = set()
    total = 0
    for name, text in sources.items():
        if (
            not _short_text(name, 160)
            or any(char in name for char in '\\:<>"|?*')
            or any(
                not part
                or part in {".", ".."}
                or part != part.strip()
                or part.endswith(".")
                for part in name.split("/")
            )
            or not name.casefold().endswith(".sql")
            or name.casefold() in known_paths
        ):
            raise UiDiscoveryError("UI sources need unique relative .sql paths.")
        if not isinstance(text, str) or not text.strip():
            raise UiDiscoveryError("Each UI SQL source must contain text.")
        if len(text) > MAX_SOURCE_BYTES or "\0" in text:
            raise UiDiscoveryError(
                "UI SQL source is too large or contains binary data."
            )
        try:
            raw = text.encode("utf-8")
        except UnicodeError as exc:
            raise UiDiscoveryError("UI source text must be valid UTF-8.") from exc
        total += len(raw)
        if total > MAX_SOURCE_BYTES:
            raise UiDiscoveryError("UI SQL sources may total at most 512 KiB.")
        known_paths.add(name.casefold())
        manifest.append({"path": name, "sha256": hashlib.sha256(raw).hexdigest()})
    return sorted(manifest, key=lambda entry: entry["path"])


def discover_ui(sources):
    """Return a deterministic catalog from relative-name / UTF-8 SQL text pairs.

    Source hashes cover the submitted text. Page, widget, and configuration IDs
    are the actual SQL values. No source text or executable actions are retained.
    """
    manifest = _source_manifest(sources)
    diagnostics = []
    pages = []
    widgets = []

    def diagnose(code, message, source):
        if len(diagnostics) < MAX_DIAGNOSTICS:
            diagnostics.append({"code": code, "message": message, "source": source})
        elif len(diagnostics) == MAX_DIAGNOSTICS:
            diagnostics.append(
                {
                    "code": "diagnosticsLimited",
                    "message": "Additional diagnostics were omitted.",
                    "source": source,
                }
            )

    for entry in manifest:
        path = entry["path"]
        try:
            for source, values in _read_rows(path, sources[path], diagnose):
                try:
                    attrs = _resource_attributes(values[-1], source, diagnose)
                    if source["table"] == PAGE_TABLE:
                        name, identity, _ = values
                        if name.kind != "string" or not _short_text(name.value, 128):
                            raise SqlProblem(
                                "PageName must be a nonempty string up to 128 characters."
                            )
                        page_id = _row_id(identity)
                        pages.append(
                            {
                                "id": f"page:{page_id}",
                                "pageId": page_id,
                                "name": name.value,
                                "attributes": attrs,
                                "source": source,
                            }
                        )
                    else:
                        config_id, widget_id, _ = values
                        widgets.append(
                            (_row_id(config_id), _row_id(widget_id), attrs, source)
                        )
                except SqlProblem as exc:
                    diagnose("invalidRow", str(exc), source)
                if len(pages) > MAX_PAGES or len(widgets) > MAX_CONTROLS:
                    raise UiDiscoveryError(
                        "UI discovery supports at most 128 pages and 300 widgets."
                    )
        except SqlProblem as exc:
            match = re.search(r"on line (\d+)\.", str(exc))
            diagnose(
                "invalidSql",
                str(exc),
                _source(path, int(match[1]) if match else 1, "SQL"),
            )

    ids = Counter(p["pageId"] for p in pages)
    pages_by_path = defaultdict(list)
    pages_by_name = defaultdict(list)
    unique_pages = []
    for page in pages:
        if ids[page["pageId"]] > 1:
            diagnose(
                "duplicatePageId",
                "A repeated PageID is ambiguous; its rows were excluded.",
                page["source"],
            )
        else:
            unique_pages.append(page)
            pages_by_path[page["source"]["path"]].append(page)
            pages_by_name[page["name"].casefold()].append(page)
    controls = []
    for config_id, widget_id, attributes, source in widgets:
        path = source["path"]
        local = pages_by_path[path]
        named = pages_by_name[PurePosixPath(path).stem.casefold()]
        candidates = (
            local if len(local) == 1 else [p for p in named if not local or p in local]
        )
        if len(candidates) != 1:
            diagnose(
                "unresolvedPage",
                "The widget cannot be joined to one page by source file and name.",
                source,
            )
            continue
        page_id = candidates[0]["pageId"]
        identity = f"page:{page_id}/widget:{widget_id}/config:{config_id}"
        controls.append(
            {
                "id": identity,
                "pageId": page_id,
                "widgetId": widget_id,
                "widgetConfigId": config_id,
                "attributes": attributes,
                "source": source,
                **_control_details(attributes, source, diagnose),
            }
        )
    ids = Counter(control["id"] for control in controls)
    unique_controls = []
    for control in controls:
        if ids[control["id"]] > 1:
            diagnose(
                "duplicateWidgetId",
                "A repeated widget configuration is ambiguous and was excluded.",
                control["source"],
            )
        else:
            unique_controls.append(control)
    if not unique_pages:
        diagnose(
            "noPages",
            "No unambiguous PagesInstalled records were discovered.",
            _source(manifest[0]["path"], 1, PAGE_TABLE),
        )
    _link_workflows(
        unique_pages,
        unique_controls,
        [c for c in controls if ids[c["id"]] > 1],
        diagnose,
    )
    catalog_digest = hashlib.sha256(
        json.dumps(
            {"schemaVersion": 1, "sources": manifest},
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    ).hexdigest()
    return {
        "schemaVersion": 1,
        "catalogSha256": catalog_digest,
        "sources": manifest,
        "pages": unique_pages,
        "controls": unique_controls,
        "diagnostics": diagnostics,
    }

#!/usr/bin/env python3
"""Static checks for TODO Tag Highlighter v0.3.3."""

from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "extension.toml",
    "languages/comment/config.toml",
    "languages/comment/highlights.scm",
    "demo/demo.clj",
    "demo/languages/javascript.js",
    "demo/languages/typescript.ts",
    "demo/languages/python.py",
    "demo/languages/rust.rs",
    "docs/demo.svg",
    "docs/demo.png",
    "docs/install-and-publish.html",
    "examples/README.md",
    "examples/settings.custom-theme.template.jsonc",
    "examples/settings.theme-overrides.jsonc",
    "examples/settings.semantic-tokens.jsonc",
    "scripts/generate_active_theme_overrides.py",
    "scripts/generate_theme_overrides.py",
    "README.md",
    "CHANGELOG.md",
    "THIRD_PARTY_NOTICES.md",
    "LICENSE",
]
TAGS = {
    "TODO", "WIP", "MAYBE", "QUESTION", "REVIEW",
    "NOTE", "INFO", "DOCS", "PERF", "TEST", "IDEA", "XXX",
    "FIXME", "FIX", "BUG", "ERROR", "DELETE", "BROKEN",
    "HACK", "WARNING", "WARN", "SAFETY", "IMPORTANT", "SECURITY",
    "DEPRECATED", "NOCOMMIT",
}
CAPTURES = {
    "comment.todo_tag_highlighter.task",
    "comment.todo_tag_highlighter.info",
    "comment.todo_tag_highlighter.fix",
    "comment.todo_tag_highlighter.warning",
}
LEGACY = {"comment.todo", "comment.info", "comment.error", "comment.warn"}
FRAPPE_FOREGROUND = "#c6d0f5ff"
FRAPPE_BACKGROUNDS = {
    "comment.todo_tag_highlighter.task": "#eebebe1f",
    "comment.todo_tag_highlighter.info": "#81c8be1f",
    "comment.todo_tag_highlighter.fix": "#e782841f",
    "comment.todo_tag_highlighter.warning": "#e5c8901f",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.dupes: set[str] = set()
        self.hrefs: list[str] = []
        self.in_script = False
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            if element_id in self.ids:
                self.dupes.add(element_id)
            self.ids.add(element_id)
        href = values.get("href")
        if href:
            self.hrefs.append(href)
        if tag == "script" and not values.get("src"):
            self.in_script = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self.in_script = False

    def handle_data(self, data: str) -> None:
        if self.in_script:
            self.scripts.append(data)


def strip_jsonc(text: str) -> str:
    output: list[str] = []
    in_string = False
    escaped = False
    i = 0
    while i < len(text):
        char = text[i]
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            i += 1
            continue
        if char == '"':
            in_string = True
            output.append(char)
            i += 1
            continue
        if char == "/" and i + 1 < len(text):
            next_char = text[i + 1]
            if next_char == "/":
                i += 2
                while i < len(text) and text[i] not in "\r\n":
                    i += 1
                continue
            if next_char == "*":
                i += 2
                while i + 1 < len(text) and text[i : i + 2] != "*/":
                    i += 1
                i += 2
                continue
        output.append(char)
        i += 1
    return re.sub(r",\s*([}\]])", r"\1", "".join(output))


def jsonc(relative_path: str) -> dict:
    try:
        data = json.loads(strip_jsonc((ROOT / relative_path).read_text(encoding="utf-8")))
    except Exception as exc:
        fail(f"invalid JSONC {relative_path}: {exc}")
    if not isinstance(data, dict):
        fail(f"{relative_path} is not an object")
    return data


def run_json(command: list[str]) -> dict:
    process = subprocess.run(command, check=True, capture_output=True, text=True)
    try:
        output = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        fail(f"command did not emit JSON: {' '.join(command)}: {exc}")
    if not isinstance(output, dict):
        fail(f"command emitted a non-object: {' '.join(command)}")
    return output


def main() -> None:
    for relative_path in REQUIRED:
        if not (ROOT / relative_path).is_file():
            fail(f"missing {relative_path}")

    with (ROOT / "extension.toml").open("rb") as file:
        manifest = tomllib.load(file)
    with (ROOT / "languages/comment/config.toml").open("rb") as file:
        language = tomllib.load(file)

    if (
        manifest.get("id") != "todo-tag-highlighter"
        or manifest.get("version") != "0.3.3"
        or manifest.get("schema_version") != 1
    ):
        fail("manifest mismatch")
    if language != {"name": "comment", "grammar": "comment", "hidden": True}:
        fail("language config mismatch")

    query = (ROOT / "languages/comment/highlights.scm").read_text(encoding="utf-8")
    missing_tags = sorted(tag for tag in TAGS if tag not in query)
    if missing_tags:
        fail("missing tags: " + ", ".join(missing_tags))
    for capture in CAPTURES:
        if f"(name) @comment @{capture}" not in query:
            fail(f"fallback missing for {capture}")
        if f"@{capture}.owner" not in query:
            fail(f"owner missing for {capture}")
    for old_capture in LEGACY:
        if re.search(rf"@{re.escape(old_capture)}(?:\s|\)|$)", query):
            fail(f"legacy capture active: {old_capture}")
    if "(prefix)? @comment" not in query or "(text)? @comment" not in query:
        fail("prefix/body not regular comment")

    query_without_strings = re.sub(r'"(?:\\.|[^"\\])*"', '""', query)
    balance = 0
    for char in query_without_strings:
        if char == "(":
            balance += 1
        elif char == ")":
            balance -= 1
        if balance < 0:
            fail("query parenthesis underflow")
    if balance:
        fail(f"query parenthesis balance {balance}")

    ET.parse(ROOT / "docs/demo.svg")
    svg = (ROOT / "docs/demo.svg").read_text(encoding="utf-8")
    for color in ("#303446", "#949cbb", "#c6d0f5", "#eebebe", "#81c8be", "#e78284", "#e5c890"):
        if color not in svg:
            fail(f"demo SVG missing Catppuccin color {color}")
    if (ROOT / "docs/demo.png").stat().st_size < 10_000:
        fail("demo PNG too small")

    html = (ROOT / "docs/install-and-publish.html").read_text(encoding="utf-8")
    parser = Parser()
    parser.feed(html)
    parser.close()
    if parser.dupes:
        fail("duplicate HTML ids: " + ", ".join(sorted(parser.dupes)))
    for href in parser.hrefs:
        if href.startswith("#") and href[1:] not in parser.ids:
            fail(f"missing anchor {href}")
    for needle in (
        "v0.3.3",
        "Catppuccin Frappé - No Italics",
        "#eebebe1f",
        "#c6d0f5ff",
        "--palette theme",
    ):
        if needle not in html:
            fail(f"HTML missing {needle}")
    if not parser.scripts:
        fail("HTML script missing")
    if node := shutil.which("node"):
        with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
            file.write("\n".join(parser.scripts))
            file.flush()
            subprocess.run(
                [node, "--check", file.name],
                check=True,
                capture_output=True,
                text=True,
            )

    settings = jsonc("examples/settings.theme-overrides.jsonc")
    overrides = settings.get("theme_overrides")
    expected_themes = {
        "Catppuccin Frappé - No Italics",
        "Catppuccin Frappé",
        "One Dark",
        "One Light",
    }
    if not isinstance(overrides, dict) or not expected_themes <= set(overrides):
        fail("theme examples missing")
    for theme_name, theme_data in overrides.items():
        syntax = theme_data.get("syntax", {}) if isinstance(theme_data, dict) else {}
        for capture in CAPTURES:
            entry = syntax.get(capture)
            if not isinstance(entry, dict) or "color" not in entry or "background_color" not in entry:
                fail(f"{theme_name}/{capture} incomplete")
            background = entry["background_color"]
            if (
                not isinstance(background, str)
                or not re.fullmatch(r"#[0-9a-fA-F]{8}", background)
                or background[-2:].lower() == "00"
            ):
                fail(f"{theme_name}/{capture} invisible background")
        if LEGACY & set(syntax):
            fail(f"legacy syntax key in {theme_name}")

    frappe_syntax = overrides["Catppuccin Frappé - No Italics"]["syntax"]
    for capture, expected_background in FRAPPE_BACKGROUNDS.items():
        entry = frappe_syntax[capture]
        if entry.get("color") != FRAPPE_FOREGROUND:
            fail(f"Catppuccin highlighted foreground mismatch for {capture}")
        if entry.get("background_color") != expected_background:
            fail(f"Catppuccin background mismatch for {capture}")
        if entry.get("font_style") is not None:
            fail(f"Catppuccin No Italics font style mismatch for {capture}")

    italic_syntax = overrides["Catppuccin Frappé"]["syntax"]
    for capture, expected_background in FRAPPE_BACKGROUNDS.items():
        entry = italic_syntax[capture]
        if entry.get("color") != FRAPPE_FOREGROUND:
            fail(f"Catppuccin italic highlighted foreground mismatch for {capture}")
        if entry.get("background_color") != expected_background:
            fail(f"Catppuccin italic background mismatch for {capture}")
        if entry.get("font_style") != "italic":
            fail(f"Catppuccin italic font style mismatch for {capture}")

    custom = jsonc("examples/settings.custom-theme.template.jsonc")
    if "YOUR EXACT THEME NAME" not in custom.get("theme_overrides", {}):
        fail("custom template placeholder missing")

    semantic = jsonc("examples/settings.semantic-tokens.jsonc")
    rules = semantic.get("global_lsp_settings", {}).get("semantic_token_rules", [])
    if not any(isinstance(rule, dict) and rule.get("token_type") == "comment" for rule in rules):
        fail("semantic rule missing")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for needle in (
        "v0.3.3",
        "Catppuccin Frappé - No Italics",
        "#eebebe1f",
        "#c6d0f5ff",
        "文字色だけ変わる",
        "generate_active_theme_overrides.py",
        "--palette theme",
    ):
        if needle not in readme:
            fail(f"README missing {needle}")
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", readme):
        if "://" not in target and not target.startswith("#"):
            path = target.split("#", 1)[0]
            if not (ROOT / path).exists():
                fail(f"broken README link {target}")

    demo = (ROOT / "demo/demo.clj").read_text(encoding="utf-8")
    if "(ns demo.demo" not in demo:
        fail("demo namespace does not match demo/demo.clj")
    for tag in ("TODO", "FIXME", "NOTE", "HACK", "SECURITY"):
        if tag not in demo:
            fail(f"demo missing {tag}")
    if len([path for path in (ROOT / "demo/languages").iterdir() if path.is_file()]) < 20:
        fail("too few language demos")

    sample = {
        "themes": [
            {
                "name": "Check Theme",
                "style": {
                    "info": "#112233ff",
                    "success": "#223344ff",
                    "error": "#334455ff",
                    "warning": "#445566ff",
                    "syntax": {
                        "comment": {
                            "color": "#778899ff",
                            "font_style": "italic",
                            "font_weight": None,
                        }
                    },
                },
            }
        ]
    }
    generator = str(ROOT / "scripts/generate_theme_overrides.py")
    active_generator = str(ROOT / "scripts/generate_active_theme_overrides.py")

    with tempfile.TemporaryDirectory() as temp_directory:
        directory = Path(temp_directory)
        theme_file = directory / "theme.json"
        theme_file.write_text(json.dumps(sample), encoding="utf-8")

        output = run_json([
            sys.executable,
            generator,
            str(theme_file),
            "--theme",
            "Check Theme",
            "--alpha",
            "0.5",
        ])
        syntax = output["theme_overrides"]["Check Theme"]["syntax"]
        if set(syntax) != CAPTURES:
            fail("theme generator captures mismatch")
        if syntax["comment.todo_tag_highlighter.task"]["background_color"] != "#eebebe80":
            fail("default Frappé palette mismatch")
        if syntax["comment.todo_tag_highlighter.info"]["background_color"] != "#81c8be80":
            fail("default Frappé info palette mismatch")
        if syntax["comment.todo_tag_highlighter.task"]["color"] != "#778899ff":
            fail("non-Frappé theme should preserve normal comment foreground")

        output = run_json([
            sys.executable,
            generator,
            str(theme_file),
            "--theme",
            "Check Theme",
            "--alpha",
            "0.5",
            "--tag-color",
            "#c6d0f5",
        ])
        syntax = output["theme_overrides"]["Check Theme"]["syntax"]
        if syntax["comment.todo_tag_highlighter.task"]["color"] != FRAPPE_FOREGROUND:
            fail("explicit tag foreground mismatch")

        output = run_json([
            sys.executable,
            generator,
            str(theme_file),
            "--theme",
            "Check Theme",
            "--alpha",
            "0.5",
            "--palette",
            "theme",
        ])
        syntax = output["theme_overrides"]["Check Theme"]["syntax"]
        if syntax["comment.todo_tag_highlighter.task"]["background_color"] != "#11223380":
            fail("theme-native palette mismatch")
        if syntax["comment.todo_tag_highlighter.fix"]["background_color"] != "#33445580":
            fail("theme-native error palette mismatch")

        settings_file = directory / "settings.json"
        settings_file.write_text(json.dumps({"theme": "Check Theme"}), encoding="utf-8")
        output = run_json([
            sys.executable,
            active_generator,
            "--settings",
            str(settings_file),
            "--theme-file",
            str(theme_file),
            "--alpha",
            "0.5",
        ])
        syntax = output["theme_overrides"]["Check Theme"]["syntax"]
        if set(syntax) != CAPTURES:
            fail("active generator captures mismatch")
        if syntax["comment.todo_tag_highlighter.task"]["background_color"] != "#eebebe80":
            fail("active generator Frappé palette mismatch")

    output = run_json([
        sys.executable,
        active_generator,
        "--theme",
        "Catppuccin Frappé - No Italics",
    ])
    bundled_syntax = output["theme_overrides"]["Catppuccin Frappé - No Italics"]["syntax"]
    if bundled_syntax != frappe_syntax:
        fail("bundled Catppuccin metadata does not match example settings")

    print("PASS: TODO Tag Highlighter v0.3.3 static checks completed")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate TODO Tag Highlighter `theme_overrides` from a Zed theme file.

The generated entries use extension-specific capture names, copy the selected
Zed theme's ordinary `syntax.comment` text style, and add only a category
background. Catppuccin Frappé is the default background palette; pass
`--palette theme` to derive category colors from the selected Zed theme.
Catppuccin Frappé themes use the brighter Text color for the tag itself.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

CATEGORY_STATUS = {
    "comment.todo_tag_highlighter.task": "info",
    "comment.todo_tag_highlighter.info": "success",
    "comment.todo_tag_highlighter.fix": "error",
    "comment.todo_tag_highlighter.warning": "warning",
}

# Catppuccin Frappé accents. The task color follows Catppuccin's `comment.todo`
# hue (Flamingo); the remaining categories follow info/error/warning semantics.
CATPPUCCIN_FRAPPE_COLORS = {
    "info": "#eebebeff",      # Flamingo — TODO / task
    "success": "#81c8beff",   # Teal — NOTE / information
    "error": "#e78284ff",     # Red — FIXME / bug
    "warning": "#e5c890ff",   # Yellow — warning / security
}

FALLBACK_COLORS = dict(CATPPUCCIN_FRAPPE_COLORS)
PALETTE_CHOICES = ("catppuccin-frappe", "theme")
DEFAULT_PALETTE = "catppuccin-frappe"
DEFAULT_ALPHA = 0.12
CATPPUCCIN_FRAPPE_TAG_TEXT = "#c6d0f5ff"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate Zed theme_overrides that preserve the selected theme's "
            "normal comment style and add a configurable foreground/background to TODO tags."
        )
    )
    parser.add_argument("theme_file", type=Path, help="Zed theme JSON/JSONC file")
    parser.add_argument(
        "--theme",
        action="append",
        default=[],
        help="Exact theme name to include; may be repeated",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate overrides for every theme in the file",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available theme names and exit",
    )
    parser.add_argument(
        "--palette",
        choices=PALETTE_CHOICES,
        default=DEFAULT_PALETTE,
        help=(
            "Background palette: Catppuccin Frappé (default), or the selected "
            "theme's info/success/error/warning colors"
        ),
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=DEFAULT_ALPHA,
        help=f"Background alpha from 0.0 to 1.0 (default: {DEFAULT_ALPHA:.2f})",
    )
    parser.add_argument(
        "--tag-color",
        help=(
            "Foreground for the highlighted tag. Defaults to Catppuccin "
            "Frappé Text for Frappé themes, otherwise the normal comment color"
        ),
    )
    return parser.parse_args()


def strip_jsonc_comments(text: str) -> str:
    """Remove // and /* */ comments while preserving strings."""
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
            nxt = text[i + 1]
            if nxt == "/":
                i += 2
                while i < len(text) and text[i] not in "\r\n":
                    i += 1
                continue
            if nxt == "*":
                i += 2
                while i + 1 < len(text) and text[i : i + 2] != "*/":
                    i += 1
                i += 2
                continue

        output.append(char)
        i += 1
    return "".join(output)


def strip_trailing_commas(text: str) -> str:
    """Remove JSONC trailing commas outside strings."""
    return re.sub(r",\s*([}\]])", r"\1", text)


def load_json_like(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"theme file not found: {path}")
    try:
        return json.loads(strip_trailing_commas(strip_jsonc_comments(text)))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON/JSONC in {path}: {exc}")


def themes_from_data(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict) and isinstance(data.get("themes"), list):
        themes = data["themes"]
    elif isinstance(data, dict) and "name" in data and "style" in data:
        themes = [data]
    else:
        raise ValueError("expected a Zed theme object or a `themes` array")

    valid = [theme for theme in themes if isinstance(theme, dict)]
    if not valid:
        raise ValueError("no theme objects found")
    return valid


def load_themes(path: Path) -> list[dict[str, Any]]:
    try:
        return themes_from_data(load_json_like(path))
    except ValueError as exc:
        raise SystemExit(f"{path}: {exc}")


def normalize_hex(color: str) -> str:
    if not isinstance(color, str) or not color.startswith("#"):
        raise ValueError(f"unsupported color value: {color!r}")
    value = color[1:]
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    elif len(value) == 4:
        value = "".join(ch * 2 for ch in value)
    if len(value) == 6:
        value += "ff"
    if len(value) != 8 or any(ch not in "0123456789abcdefABCDEF" for ch in value):
        raise ValueError(f"unsupported color value: {color!r}")
    return f"#{value.lower()}"


def with_alpha(color: str, alpha: float) -> str:
    if not 0.0 <= alpha <= 1.0:
        raise SystemExit("--alpha must be between 0.0 and 1.0")
    try:
        normalized = normalize_hex(color)
    except ValueError as exc:
        raise SystemExit(str(exc))
    alpha_hex = round(alpha * 255)
    return f"{normalized[:7]}{alpha_hex:02x}"


def comment_style(theme: dict[str, Any]) -> dict[str, Any]:
    style = theme.get("style")
    if not isinstance(style, dict):
        raise ValueError(f"theme {theme.get('name')!r} has no style object")
    syntax = style.get("syntax")
    if not isinstance(syntax, dict):
        raise ValueError(f"theme {theme.get('name')!r} has no style.syntax object")
    comment = syntax.get("comment")
    if not isinstance(comment, dict):
        raise ValueError(f"theme {theme.get('name')!r} has no syntax.comment style")

    return {key: value for key, value in comment.items() if key != "background_color"}


def status_color(theme: dict[str, Any], status: str, palette: str) -> str:
    if palette == DEFAULT_PALETTE:
        return CATPPUCCIN_FRAPPE_COLORS[status]

    style = theme.get("style", {})
    if isinstance(style, dict):
        value = style.get(status)
        if isinstance(value, str):
            return value
    return FALLBACK_COLORS[status]


def resolved_tag_color(theme: dict[str, Any], explicit: str | None) -> str | None:
    if explicit:
        try:
            return normalize_hex(explicit)
        except ValueError as exc:
            raise SystemExit(str(exc))

    name = theme.get("name")
    if isinstance(name, str) and name.startswith("Catppuccin Frappé"):
        return CATPPUCCIN_FRAPPE_TAG_TEXT
    return None


def build_override(
    theme: dict[str, Any],
    alpha: float,
    palette: str,
    tag_color: str | None = None,
) -> dict[str, Any]:
    base = comment_style(theme)
    highlighted_foreground = resolved_tag_color(theme, tag_color)
    syntax: dict[str, Any] = {}
    for capture, status in CATEGORY_STATUS.items():
        entry = dict(base)
        if highlighted_foreground is not None:
            entry["color"] = highlighted_foreground
        entry["background_color"] = with_alpha(
            status_color(theme, status, palette), alpha
        )
        syntax[capture] = entry
    return {"syntax": syntax}


def generate_for_themes(
    themes: list[dict[str, Any]],
    alpha: float,
    palette: str = DEFAULT_PALETTE,
    tag_color: str | None = None,
) -> dict[str, Any]:
    if palette not in PALETTE_CHOICES:
        raise ValueError(f"unsupported palette: {palette}")

    result: dict[str, Any] = {"theme_overrides": {}}
    overrides = result["theme_overrides"]
    assert isinstance(overrides, dict)
    for theme in themes:
        name = theme.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("theme object is missing a non-empty name")
        overrides[name] = build_override(theme, alpha, palette, tag_color)
    return result


def main() -> None:
    args = parse_args()
    themes = load_themes(args.theme_file)
    names = [str(theme.get("name", "")) for theme in themes]

    if args.list:
        for name in names:
            print(name)
        return

    if args.all and args.theme:
        raise SystemExit("use either --all or --theme, not both")

    if args.all:
        selected = themes
    elif args.theme:
        requested = set(args.theme)
        selected = [theme for theme in themes if theme.get("name") in requested]
        missing = sorted(requested - {str(theme.get("name")) for theme in selected})
        if missing:
            raise SystemExit(f"theme not found: {', '.join(missing)}")
    else:
        selected = [themes[0]]

    try:
        result = generate_for_themes(selected, args.alpha, args.palette, args.tag_color)
    except ValueError as exc:
        raise SystemExit(str(exc))
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()

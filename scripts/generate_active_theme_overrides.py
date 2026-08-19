#!/usr/bin/env python3
"""Generate overrides for the theme currently selected in Zed settings.

The script is read-only: it never modifies Zed's settings. It discovers the
active theme name, searches local/bundled theme JSON files, and prints a
`theme_overrides` object that can be merged into settings.json.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any, Iterable

from generate_theme_overrides import (
    DEFAULT_ALPHA,
    DEFAULT_PALETTE,
    FALLBACK_COLORS,
    PALETTE_CHOICES,
    generate_for_themes,
    load_json_like,
    load_themes,
    themes_from_data,
)

BUNDLED_THEME_METADATA: dict[str, dict[str, Any]] = {
    "Catppuccin Frappé - No Italics": {
        "name": "Catppuccin Frappé - No Italics",
        "style": {
            "info": "#81c8beff",
            "success": "#a6d189ff",
            "error": "#e78284ff",
            "warning": "#e5c890ff",
            "syntax": {
                "comment": {
                    "color": "#949cbbff",
                    "font_style": None,
                    "font_weight": None,
                }
            },
        },
    },
    "Catppuccin Frappé": {
        "name": "Catppuccin Frappé",
        "style": {
            "info": "#81c8beff",
            "success": "#a6d189ff",
            "error": "#e78284ff",
            "warning": "#e5c890ff",
            "syntax": {
                "comment": {
                    "color": "#949cbbff",
                    "font_style": "italic",
                    "font_weight": None,
                }
            },
        },
    },
    "One Dark": {
        "name": "One Dark",
        "style": {
            "info": "#74ade8ff",
            "success": "#a1c181ff",
            "error": "#d07277ff",
            "warning": "#dec184ff",
            "syntax": {
                "comment": {
                    "color": "#5d636fff",
                    "font_style": None,
                    "font_weight": None,
                }
            },
        },
    },
    "One Light": {
        "name": "One Light",
        "style": {
            "info": "#5c78e2ff",
            "success": "#669f59ff",
            "error": "#d36151ff",
            "warning": "#a48819ff",
            "syntax": {
                "comment": {
                    "color": "#a2a3a7ff",
                    "font_style": None,
                    "font_weight": None,
                }
            },
        },
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate TODO Tag Highlighter settings for Zed's active theme."
    )
    parser.add_argument("--settings", type=Path, help="Path to Zed settings.json")
    parser.add_argument("--theme", help="Use this exact theme name instead of reading settings")
    parser.add_argument(
        "--appearance",
        choices=("dark", "light"),
        default="dark",
        help="Branch to use when settings has separate light/dark themes (default: dark)",
    )
    parser.add_argument(
        "--theme-file",
        type=Path,
        help="Explicit Zed theme JSON/JSONC file; skips filesystem discovery",
    )
    parser.add_argument(
        "--comment-color",
        help="Manual ordinary comment color, used if the theme JSON cannot be found",
    )
    parser.add_argument(
        "--palette",
        choices=PALETTE_CHOICES,
        default=DEFAULT_PALETTE,
        help=(
            "Background palette: Catppuccin Frappé (default), or the active "
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
            "Foreground for the highlighted tag. Catppuccin Frappé defaults "
            "to #c6d0f5; other themes keep their ordinary comment color"
        ),
    )
    return parser.parse_args()


def candidate_settings_paths() -> list[Path]:
    home = Path.home()
    paths = [home / ".config/zed/settings.json"]
    if platform.system() == "Darwin":
        paths.append(home / "Library/Application Support/Zed/settings.json")
    if appdata := os.environ.get("APPDATA"):
        paths.append(Path(appdata) / "Zed/settings.json")
    return paths


def find_settings(explicit: Path | None) -> Path:
    if explicit:
        if not explicit.is_file():
            raise SystemExit(f"settings file not found: {explicit}")
        return explicit
    for path in candidate_settings_paths():
        if path.is_file():
            return path
    searched = "\n  ".join(str(path) for path in candidate_settings_paths())
    raise SystemExit(
        "Zed settings.json was not found. Use --settings or --theme.\n"
        f"Searched:\n  {searched}"
    )


def active_theme_name(settings: dict[str, Any], appearance: str) -> str:
    theme = settings.get("theme")
    if isinstance(theme, str) and theme:
        return theme
    if isinstance(theme, dict):
        mode = theme.get("mode")
        branch = mode if mode in ("dark", "light") else appearance
        value = theme.get(branch)
        if isinstance(value, str) and value:
            return value
    raise SystemExit(
        "Could not determine the active theme from settings. "
        "Pass --theme \"Exact Theme Name\"."
    )


def candidate_theme_roots() -> list[Path]:
    home = Path.home()
    roots = [home / ".config/zed/themes"]
    system = platform.system()
    if system == "Darwin":
        roots.extend(
            [
                home / "Library/Application Support/Zed/extensions/installed",
                Path("/Applications/Zed.app/Contents/Resources"),
                Path("/Applications/Zed Preview.app/Contents/Resources"),
            ]
        )
    elif system == "Windows":
        if local := os.environ.get("LOCALAPPDATA"):
            roots.append(Path(local) / "Zed/extensions/installed")
    else:
        data_home = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share"))
        roots.append(data_home / "zed/extensions/installed")
    return roots


def theme_files(roots: Iterable[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        candidates = [root] if root.is_file() else root.rglob("*.json")
        for path in candidates:
            try:
                resolved = path.resolve()
            except OSError:
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            yield path


def find_theme_in_file(path: Path, name: str) -> dict[str, Any] | None:
    try:
        data = load_json_like(path)
        themes = themes_from_data(data)
    except (SystemExit, ValueError, OSError):
        return None
    for theme in themes:
        if theme.get("name") == name:
            return theme
    return None


def discover_theme(name: str, explicit_file: Path | None) -> tuple[dict[str, Any] | None, Path | None]:
    if explicit_file:
        if not explicit_file.is_file():
            raise SystemExit(f"theme file not found: {explicit_file}")
        theme = find_theme_in_file(explicit_file, name)
        if theme is None:
            available = ", ".join(str(t.get("name")) for t in load_themes(explicit_file))
            raise SystemExit(
                f"theme {name!r} was not found in {explicit_file}. Available: {available}"
            )
        return theme, explicit_file

    if name in BUNDLED_THEME_METADATA:
        return BUNDLED_THEME_METADATA[name], None

    for path in theme_files(candidate_theme_roots()):
        theme = find_theme_in_file(path, name)
        if theme is not None:
            return theme, path
    return None, None


def manual_theme(name: str, comment_color: str) -> dict[str, Any]:
    return {
        "name": name,
        "style": {
            **FALLBACK_COLORS,
            "syntax": {"comment": {"color": comment_color}},
        },
    }


def main() -> None:
    args = parse_args()

    if args.theme:
        name = args.theme
        settings_path = None
    else:
        settings_path = find_settings(args.settings)
        data = load_json_like(settings_path)
        if not isinstance(data, dict):
            raise SystemExit(f"expected a JSON object in {settings_path}")
        name = active_theme_name(data, args.appearance)

    theme, source = discover_theme(name, args.theme_file)
    if theme is None:
        if not args.comment_color:
            roots = "\n  ".join(str(path) for path in candidate_theme_roots())
            raise SystemExit(
                f"Found active theme name {name!r}, but not its theme JSON.\n"
                "Pass --theme-file /path/to/theme.json or "
                "--comment-color '#rrggbbaa'.\n"
                f"Theme roots searched:\n  {roots}"
            )
        theme = manual_theme(name, args.comment_color)

    try:
        result = generate_for_themes([theme], args.alpha, args.palette, args.tag_color)
    except ValueError as exc:
        raise SystemExit(str(exc))

    if settings_path:
        print(f"// Active theme read from: {settings_path}", file=sys.stderr)
    if source:
        print(f"// Theme definition read from: {source}", file=sys.stderr)
    elif name in BUNDLED_THEME_METADATA:
        print(f"// Using bundled metadata for {name}", file=sys.stderr)
    else:
        print("// Using the manually supplied comment color", file=sys.stderr)

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()

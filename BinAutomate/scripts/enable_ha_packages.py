#!/usr/bin/env python3
"""Idempotently enable Home Assistant package includes in configuration.yaml."""

from __future__ import annotations

import argparse
from pathlib import Path


INCLUDE_LINE = "  packages: !include_dir_named packages"


def is_top_level(line: str) -> bool:
    return bool(line.strip()) and not line.startswith((" ", "\t")) and not line.lstrip().startswith("#")


def enable_packages(path: Path) -> bool:
    text = path.read_text()
    if "packages: !include_dir_named packages" in text:
        return False

    lines = text.splitlines()
    trailing_newline = text.endswith(("\n", "\r\n"))

    for index, line in enumerate(lines):
        if line.strip() == "homeassistant:" and is_top_level(line):
            lines.insert(index + 1, INCLUDE_LINE)
            path.write_text("\n".join(lines) + ("\n" if trailing_newline else ""))
            return True

    new_text = "homeassistant:\n  packages: !include_dir_named packages\n\n" + text
    path.write_text(new_text)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("configuration_yaml", type=Path)
    args = parser.parse_args()
    changed = enable_packages(args.configuration_yaml)
    print("packages include added" if changed else "packages include already present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

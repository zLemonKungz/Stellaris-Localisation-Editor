"""
Stellaris .yml localisation file parser and writer.
Handles the specific format: key:N "value" with UTF-8 BOM and CRLF.
Preserves all formatting (whitespace, numbers, non-kv lines, comments).
"""

import os
import re
from collections import OrderedDict
from pathlib import Path
from typing import Optional

# Regex for Stellaris .yml key-value lines
# Groups: (leading_whitespace, key, optional_number, value)
KV_RE = re.compile(r'^(\s+)([^:]+?):(\d*)\s*"(.*)"\s*$')


class YmlEntry:
    """Represents a single key-value entry from a .yml file."""

    __slots__ = ("key", "value", "leading", "num", "lineno")

    def __init__(self, key: str, value: str, leading: str = " ",
                 num: str = "", lineno: int = 0):
        self.key = key
        self.value = value
        self.leading = leading  # leading whitespace to preserve
        self.num = num  # optional number after colon (e.g., "0" in ":0")
        self.lineno = lineno

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "leading": self.leading,
            "num": self.num,
            "lineno": self.lineno,
        }

    def __repr__(self) -> str:
        return f"YmlEntry({self.key}='{self.value[:40]}...')"


class YmlFile:
    """
    Represents a parsed .yml file with full round-trip preservation.

    Attributes:
        path: Path to the file
        entries: List of YmlEntry objects
        raw_lines: Original lines for preserving format on save
        modified: Whether any values have been changed
        header_lines: Non-entry lines (l_english:, comments, blanks)
        _entry_line_map: Maps line index in raw_lines to entry index
    """

    def __init__(self, path: Path):
        self.path = path
        self.entries: list[YmlEntry] = []
        self.raw_lines: list[str] = []
        self.modified = False
        self._parse()

    def _parse(self):
        """Parse the .yml file into entries and raw_lines."""
        self.entries.clear()
        self.raw_lines.clear()
        try:
            with open(self.path, "r", encoding="utf-8-sig") as fh:
                for lineno, raw in enumerate(fh, start=1):
                    line = raw.rstrip("\r\n")
                    self.raw_lines.append(line)
                    m = KV_RE.match(line)
                    if m:
                        entry = YmlEntry(
                            key=m.group(2),
                            value=m.group(4),
                            leading=m.group(1),
                            num=m.group(3) or "",
                            lineno=lineno,
                        )
                        self.entries.append(entry)
        except Exception as exc:
            raise IOError(f"Failed to read {self.path}: {exc}")

    def get_value(self, key: str) -> Optional[str]:
        """Get the value for a key, or None if not found."""
        for e in self.entries:
            if e.key == key:
                return e.value
        return None

    def set_value(self, key: str, value: str) -> bool:
        """Set the value for a key. Returns True if found and changed."""
        for e in self.entries:
            if e.key == key:
                if e.value != value:
                    e.value = value
                    self.modified = True
                return True
        return False

    def set_values(self, updates: dict[str, str]) -> int:
        """Set multiple values at once. Returns count of changes."""
        changed = 0
        try:
            for e in self.entries:
                if e.key in updates and e.value != updates[e.key]:
                    e.value = updates[e.key]
                    self.modified = True
                    changed += 1
        except Exception:
            pass  # partial updates are acceptable
        return changed

    def find_keys(self, pattern: str, case_sensitive: bool = False) -> list[YmlEntry]:
        """Find entries whose key contains the pattern."""
        if not case_sensitive:
            pattern = pattern.lower()
            return [e for e in self.entries if pattern in e.key.lower()]
        return [e for e in self.entries if pattern in e.key]

    def find_values(self, pattern: str, case_sensitive: bool = False) -> list[YmlEntry]:
        """Find entries whose value contains the pattern."""
        if not case_sensitive:
            pattern = pattern.lower()
            return [e for e in self.entries if pattern in e.value.lower()]
        return [e for e in self.entries if pattern in e.value]

    def rename_key(self, old_key: str, new_key: str) -> bool:
        """Rename a key. Returns True if found and renamed."""
        for e in self.entries:
            if e.key == old_key:
                e.key = new_key
                self.modified = True
                return True
        return False

    def get_coverage(self) -> dict:
        """Return coverage stats for this file."""
        total = len(self.entries)
        filled = sum(1 for e in self.entries if e.value and e.value.strip())
        return {
            "total": total,
            "filled": filled,
            "empty": total - filled,
            "pct": round(filled / total * 100, 1) if total else 100.0,
        }

    def save(self, target_path: Optional[Path] = None) -> None:
        """
        Save the file, preserving original line structure.
        Only modifies values for entries that have been changed.
        """
        out_path = target_path or self.path
        out_lines: list[str] = []

        try:
            # Create a map of key -> new value for quick lookup
            entry_by_key = {e.key: e for e in self.entries}

            for line in self.raw_lines:
                m = KV_RE.match(line)
                if m and m.group(2) in entry_by_key:
                    entry = entry_by_key[m.group(2)]
                    leading = entry.leading
                    num_str = f":{entry.num}" if entry.num else ":"
                    out_lines.append(f'{leading}{entry.key}{num_str} "{entry.value}"')
                else:
                    out_lines.append(line)

            # Write with UTF-8 BOM and CRLF
            content = "\r\n".join(out_lines)
            if not content.endswith("\r\n"):
                content += "\r\n"

            out_path.parent.mkdir(parents=True, exist_ok=True)
            # BUGFIX: Use newline="" (no translation) because content already
            # contains \r\n from "\r\n".join().  newline="\r\n" would double-encode
            # CRLF to \r\r\n, corrupting every line ending on Windows.
            with open(out_path, "w", encoding="utf-8-sig", newline="") as fh:
                fh.write(content)

            self.modified = False
        except Exception as exc:
            raise IOError(f"Failed to save {out_path}: {exc}")

    def __len__(self) -> int:
        return len(self.entries)

    def __getitem__(self, index: int) -> YmlEntry:
        return self.entries[index]

    def __repr__(self) -> str:
        cov = self.get_coverage()
        return f"YmlFile({self.path.name}, {cov['total']} keys, {cov['pct']}%)"


def is_yml_file(filename: str) -> bool:
    """Check if a filename is a Stellaris locale .yml file."""
    return filename.endswith("_l_english.yml")


def collect_yml_files(directory: Path) -> list[Path]:
    """Collect all Stellaris locale .yml files in a directory (sorted)."""
    return sorted(
        f for f in directory.iterdir()
        if f.is_file() and is_yml_file(f.name)
    )


# ── JSON export/import (use DataManager methods instead) ──
# Module-level functions removed — use DataManager.export_to_json()
# and DataManager.import_from_json() which have proper error handling.

"""
Central data manager for the Localisation Editor.
Loads, caches, and provides access to all translation files, glossaries,
and statistics.
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .yml_handler import YmlFile, collect_yml_files, is_yml_file

# Regex to detect Thai characters (Thai Unicode range: U+0E00–U+0E7F)
THAI_RE = re.compile(r"[฀-๿]")


def is_pure_reference(value: str) -> bool:
    """Return True if value contains ONLY game syntax (no English or Thai text)."""
    if not value or not value.strip():
        return False
    # Remove all known patterns
    cleaned = re.sub(r'\$[A-Za-z0-9_|]+\$', '', value)  # vars: $KEY$, $KEY|F$
    cleaned = re.sub(r'£[a-z_]+£', '', cleaned)  # icons: £icon£
    cleaned = re.sub(r'§.', '', cleaned)  # color tags: §R, §G, §Y, §H, §L, §!
    cleaned = re.sub(r'\\n', '', cleaned)  # newline escapes
    cleaned = cleaned.strip()
    # If only whitespace/punctuation remains, it's pure reference
    return not bool(re.search(r'[A-Za-z฀-๿]', cleaned))


# Project paths — relative to this file's location
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOC_DIR = PROJECT_ROOT / "thaimod" / "localisation" / "english"
REPLACE_DIR = PROJECT_ROOT / "thaimod" / "localisation" / "replace" / "english"
GLOSSARY_PATH = PROJECT_ROOT / "glossary.json"
THAI_DICT_PATH = PROJECT_ROOT / "thai_translations.json"
SCRIPTS_DIR = PROJECT_ROOT


class DataManager:
    """
    Central data manager. Loads files lazily and caches them.
    Provides coverage stats, search, glossary access, and script execution.
    """

    def __init__(self, localisation_dir: str | Path | None = None):
        if localisation_dir is None:
            self.loc_dir = None
            self.replace_dir = None
        else:
            mod_path = Path(localisation_dir)
            self.loc_dir = mod_path / "english"
            self.replace_dir = mod_path / "replace" / "english"
        self._files: dict[str, YmlFile] = {}  # filename -> YmlFile
        self._replace_files: dict[str, YmlFile] = {}
        self._glossary: list[dict] | None = None
        self._thai_dict: dict[str, str] | None = None
        self._file_list: list[str] | None = None  # cached sorted file list
        self._coverage_cache: dict[str, dict] | None = None
        self._scripts_cache: list[dict] | None = None
        self._dirty = False  # True if any file has been modified

    @property
    def has_mod_folder(self) -> bool:
        """Return True if a mod folder has been explicitly opened."""
        return self.loc_dir is not None

    def set_mod_directory(self, localisation_dir: str | Path) -> int:
        """
        Switch to a different mod's localisation directory.
        Auto-detects the english/ subfolder containing .yml files.

        Detection order:
          1. If <selected>/english/ exists -> use that
          2. Else if <selected>/localisation/english/ exists -> use that
          3. Else scan <selected>/**/ for directories with *_l_english.yml
             files and pick the one with the most files
          4. If nothing found, raise ValueError

        Args:
            localisation_dir: Path to a mod directory.

        Returns:
            Number of .yml files found in the new directory.
        """
        mod_path = Path(localisation_dir)

        # Auto-detect the english/ directory
        # a. If selected/english/ exists -> use that
        if (mod_path / "english").exists():
            loc_dir = mod_path / "english"
        # b. If selected/localisation/english/ exists -> use that
        elif (mod_path / "localisation" / "english").exists():
            loc_dir = mod_path / "localisation" / "english"
        else:
            # c. Scan for any directory containing *_l_english.yml files
            candidates: dict[Path, int] = {}
            for fpath in mod_path.rglob("*_l_english.yml"):
                if fpath.is_file():
                    parent = fpath.parent
                    candidates[parent] = candidates.get(parent, 0) + 1

            if candidates:
                # Pick the one with the most files
                loc_dir = max(candidates, key=candidates.get)
            else:
                raise ValueError(
                    "Could not find localisation folder. "
                    "Please select a mod directory that contains a "
                    "'localisation/english/' or similar folder with "
                    "*_l_english.yml files."
                )

        self.loc_dir = loc_dir

        # Set replace_dir based on where loc_dir was found
        replace_candidate = loc_dir.parent / "replace" / "english"
        if replace_candidate.exists():
            self.replace_dir = replace_candidate
        else:
            self.replace_dir = loc_dir  # fallback to same dir

        # Clear all caches
        self._files.clear()
        self._replace_files.clear()
        self._file_list = None
        self._coverage_cache = None
        self._scripts_cache = None
        self._dirty = False
        # Count .yml files in the new directory
        return sum(
            1 for f in collect_yml_files(self.loc_dir)
        )

    # ── File loading ───────────────────────────────────────────────────

    @property
    def file_names(self) -> list[str]:
        """List of all .yml filenames (sorted)."""
        if self.loc_dir is None:
            return []
        try:
            if self._file_list is None:
                self._file_list = [
                    f.name for f in collect_yml_files(self.loc_dir)
                ]
            return self._file_list
        except Exception:
            return []

    def get_file(self, filename: str) -> Optional[YmlFile]:
        """Get a YmlFile, loading it if necessary."""
        if self.loc_dir is None:
            return None
        if filename not in self._files:
            path = self.loc_dir / filename
            if not path.exists():
                # Try replace dir if available
                if self.replace_dir is not None:
                    path = self.replace_dir / filename
                if not path.exists():
                    return None
            try:
                self._files[filename] = YmlFile(path)
            except IOError:
                return None
        return self._files[filename]

    def get_or_create_file(self, filename: str) -> Optional[YmlFile]:
        """Get a file, creating an empty one if it doesn't exist (for stubs)."""
        if self.loc_dir is None:
            return None
        try:
            if filename in self._files:
                return self._files[filename]
            path = self.loc_dir / filename
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w", encoding="utf-8-sig", newline="\r\n") as fh:
                    fh.write("l_english:\r\n")
                self._file_list = None  # invalidate cache
            self._coverage_cache = None
            return self.get_file(filename)
        except Exception:
            return None

    def get_replace_file(self, filename: str) -> Optional[YmlFile]:
        """Get a replace/ file, loading it if necessary."""
        if self.replace_dir is None:
            return None
        if filename not in self._replace_files:
            path = self.replace_dir / filename
            if not path.exists():
                return None
            try:
                self._replace_files[filename] = YmlFile(path)
            except IOError:
                return None
        return self._replace_files[filename]

    def reload_file(self, filename: str) -> Optional[YmlFile]:
        """Force-reload a file from disk."""
        try:
            self._files.pop(filename, None)
            self._replace_files.pop(filename, None)
            self._coverage_cache = None
            return self.get_file(filename)
        except Exception:
            self._coverage_cache = None
            return None

    def reload_all(self):
        """Reload all files from disk."""
        try:
            self._files.clear()
            self._replace_files.clear()
            self._file_list = None
            self._coverage_cache = None
            self._scripts_cache = None
        except Exception:
            pass

    def save_file(self, filename: str) -> bool:
        """Save a modified file. Returns True on success."""
        yml = self._files.get(filename)
        if yml and yml.modified:
            try:
                yml.save()
                return True
            except IOError:
                return False
        return False

    def save_all_modified(self) -> int:
        """Save all modified files. Returns count of saved files."""
        saved = 0
        for filename, yml in self._files.items():
            if yml.modified:
                try:
                    yml.save()
                    saved += 1
                except IOError:
                    pass
        return saved

    def has_modified(self) -> bool:
        """Check if any file has unsaved changes."""
        return any(f.modified for f in self._files.values())

    @property
    def modified_files(self) -> list[str]:
        """List of filenames that have unsaved changes."""
        return [name for name, f in self._files.items() if f.modified]

    # ── Coverage ───────────────────────────────────────────────────────

    def get_coverage(self, filename: str) -> Optional[dict]:
        """Get coverage stats for a single file."""
        yml = self.get_file(filename)
        if yml is None:
            return None
        return yml.get_coverage()

    def get_all_coverage(self) -> dict[str, dict]:
        """Get coverage stats for all files, with caching."""
        try:
            if self._coverage_cache is not None:
                return self._coverage_cache
            result = {}
            for fname in self.file_names:
                yml = self.get_file(fname)
                if yml:
                    result[fname] = yml.get_coverage()
            self._coverage_cache = result
            return result
        except Exception:
            return {}

    def get_overall_stats(self) -> dict:
        """Get overall translation statistics."""
        try:
            coverage = self.get_all_coverage()
            total_keys = sum(c["total"] for c in coverage.values())
            total_filled = sum(c["filled"] for c in coverage.values())
            return {
                "total_keys": total_keys,
                "total_filled": total_filled,
                "total_empty": total_keys - total_filled,
                "overall_pct": round(total_filled / total_keys * 100, 1)
                    if total_keys else 100.0,
                "total_files": len(coverage),
                "complete_files": sum(
                    1 for c in coverage.values() if c["pct"] == 100.0
                ),
                "partial_files": sum(
                    1 for c in coverage.values() if 0 < c["pct"] < 100.0
                ),
                "empty_files": sum(
                    1 for c in coverage.values() if c["pct"] == 0.0
                ),
            }
        except Exception:
            return {
                "total_keys": 0, "total_filled": 0, "total_empty": 0,
                "overall_pct": 0.0, "total_files": 0,
                "complete_files": 0, "partial_files": 0, "empty_files": 0,
            }

    # ── Real Translation Quality (Thai content detection) ─────────────

    def get_real_coverage(self, filename: str) -> Optional[dict]:
        """
        Get REAL translation stats for a file — detects whether values
        actually contain Thai text, are pure-reference (only game syntax),
        or are English-only placeholders.
        Returns: {total, has_thai, ref_only, english_only, empty, thai_pct, fake_pct}
        """
        try:
            yml = self.get_file(filename)
            if yml is None:
                return None
            total = 0
            has_thai = 0
            ref_only = 0
            english_only = 0
            empty = 0
            for e in yml.entries:
                total += 1
                val = e.value.strip()
                if not val:
                    empty += 1
                elif THAI_RE.search(val):
                    has_thai += 1
                elif is_pure_reference(val):
                    ref_only += 1
                else:
                    english_only += 1
            return {
                "total": total,
                "has_thai": has_thai,
                "ref_only": ref_only,
                "english_only": english_only,
                "empty": empty,
                "thai_pct": round((has_thai + ref_only) / total * 100, 1) if total else 100.0,
                "fake_pct": round((has_thai + ref_only + empty) / total * 100, 1) if total else 100.0,
            }
        except Exception:
            return None

    def get_all_real_coverage(self) -> dict[str, dict]:
        """Get real coverage stats for ALL files."""
        try:
            result = {}
            for fname in self.file_names:
                rc = self.get_real_coverage(fname)
                if rc:
                    result[fname] = rc
            return result
        except Exception:
            return {}

    def get_real_overall_stats(self) -> dict:
        """
        Overall stats with REAL translation quality.
        Separates genuinely translated (has Thai) from English-only placeholders,
        and tracks pure-reference values (only game syntax, no text).
        """
        try:
            coverage = self.get_all_real_coverage()
            total_keys = sum(c["total"] for c in coverage.values())
            total_thai = sum(c["has_thai"] for c in coverage.values())
            total_ref = sum(c.get("ref_only", 0) for c in coverage.values())
            total_english = sum(c["english_only"] for c in coverage.values())
            total_empty = sum(c["empty"] for c in coverage.values())

            # Count truly complete files (all Thai or pure ref)
            truly_complete = sum(
                1 for c in coverage.values() if c["thai_pct"] == 100.0
            )
            # Count files with any English-only values
            files_with_english = sum(
                1 for c in coverage.values() if c["english_only"] > 0
            )

            return {
                "total_keys": total_keys,
                "has_thai": total_thai,
                "ref_only": total_ref,
                "english_only": total_english,
                "total_empty": total_empty,
                "real_pct": round((total_thai + total_ref) / total_keys * 100, 1)
                    if total_keys else 100.0,
                "fake_pct": round((total_thai + total_ref + total_empty) / total_keys * 100, 1)
                    if total_keys else 100.0,
                "total_files": len(coverage),
                "truly_complete": truly_complete,
                "files_with_english": files_with_english,
                "completely_empty": sum(
                    1 for c in coverage.values() if c["thai_pct"] == 0.0 and c["total"] > 0
                ),
            }
        except Exception:
            return {
                "total_keys": 0, "has_thai": 0, "ref_only": 0,
                "english_only": 0, "total_empty": 0, "real_pct": 0.0,
                "fake_pct": 0.0, "total_files": 0, "truly_complete": 0,
                "files_with_english": 0, "completely_empty": 0,
            }

    def is_value_ref(self, value: str) -> bool:
        """Return True if value contains ONLY game syntax, no real text."""
        try:
            return is_pure_reference(value)
        except Exception:
            return False

    def get_quality_analysis(self) -> dict:
        """
        Comprehensive quality analysis with per-file breakdown.
        Returns sorted list of worst files and summary stats.
        """
        try:
            real_cov = self.get_all_real_coverage()
            file_stats = []
            for fname, stats in real_cov.items():
                if stats["english_only"] > 0:
                    file_stats.append({
                        "filename": fname,
                        "english_only": stats["english_only"],
                        "total": stats["total"],
                        "has_thai": stats["has_thai"],
                        "thai_pct": stats["thai_pct"],
                        "eng_pct": round(
                            stats["english_only"] / stats["total"] * 100, 1
                        ) if stats["total"] else 0,
                    })

            file_stats.sort(key=lambda x: -x["english_only"])

            overall = self.get_real_overall_stats()

            return {
                "overall": overall,
                "worst_files": file_stats[:20],
                "all_files": sorted(
                    file_stats, key=lambda x: x["filename"]
                ),
            }
        except Exception:
            return {"overall": self.get_real_overall_stats(), "worst_files": [], "all_files": []}

    # ── Search ─────────────────────────────────────────────────────────

    def search(self, query: str, scope: str = "all",
               case_sensitive: bool = False) -> list[dict]:
        """
        Search across all files. scope: "all", "untranslated", "translated".
        Returns list of dicts with filename, key, value, match info.
        """
        try:
            if not query.strip():
                return []
            query_lower = query.lower() if not case_sensitive else query
            results = []
            for fname in self.file_names:
                yml = self.get_file(fname)
                if yml is None:
                    continue
                for entry in yml.entries:
                    key_text = entry.key if case_sensitive else entry.key.lower()
                    val_text = entry.value if case_sensitive else entry.value.lower()
                    match_key = query_lower in key_text
                    match_val = query_lower in val_text
                    if not match_key and not match_val:
                        continue
                    is_empty = not entry.value.strip()
                    if scope == "untranslated" and not is_empty:
                        continue
                    if scope == "translated" and is_empty:
                        continue
                    results.append({
                        "filename": fname,
                        "key": entry.key,
                        "value": entry.value,
                        "match_key": match_key,
                        "match_value": match_val,
                        "empty": is_empty,
                    })
            return results
        except Exception:
            return []

    # ── Glossary & Dictionary ──────────────────────────────────────────

    def get_glossary(self) -> list[dict]:
        """Load and cache the glossary."""
        if self._glossary is None:
            try:
                with open(GLOSSARY_PATH, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    self._glossary = data.get("glossary", data)
            except Exception:
                self._glossary = []
        return self._glossary

    def get_thai_dict(self) -> dict[str, str]:
        """Load and cache the Thai translations lookup table (key -> thai)."""
        if self._thai_dict is None:
            try:
                with open(THAI_DICT_PATH, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    if isinstance(data, list):
                        self._thai_dict = {
                            item["key"]: item["thai"]
                            for item in data
                            if "key" in item and "thai" in item
                        }
                    else:
                        self._thai_dict = data
            except Exception:
                self._thai_dict = {}
        return self._thai_dict

    def glossary_categories(self) -> list[str]:
        """Get unique glossary categories."""
        try:
            cats = set()
            for entry in self.get_glossary():
                if entry.get("category"):
                    cats.add(entry["category"])
            return sorted(cats)
        except Exception:
            return []

    def glossary_by_category(self) -> dict[str, list[dict]]:
        """Get glossary entries grouped by category."""
        try:
            grouped = {}
            for entry in self.get_glossary():
                cat = entry.get("category", "uncategorized")
                grouped.setdefault(cat, []).append(entry)
            return grouped
        except Exception:
            return {}

    # ── Scripts ────────────────────────────────────────────────────────

    SCRIPT_PATTERNS = [
        "translate_*.py", "fix_*.py", "final_*.py",
        "apply_*.py",
    ]

    def get_scripts(self) -> list[dict]:
        """List available translation scripts."""
        try:
            if self._scripts_cache is not None:
                return self._scripts_cache
            scripts = []
            for pattern in self.SCRIPT_PATTERNS:
                for fpath in sorted(SCRIPTS_DIR.glob(pattern)):
                    scripts.append({
                        "name": fpath.name,
                        "path": str(fpath.name),
                    })
            self._scripts_cache = scripts
            return scripts
        except Exception:
            return []

    def run_script(self, script_name: str, args: str = "") -> dict:
        """
        Run a translation script and return the result.
        Returns dict with stdout, stderr, returncode, success.
        """
        script_path = SCRIPTS_DIR / script_name
        if not script_path.exists():
            return {
                "success": False,
                "error": f"Script not found: {script_name}",
                "stdout": "",
                "stderr": "",
                "returncode": -1,
            }
        try:
            cmd = [sys.executable, str(script_path)]
            if args:
                cmd.extend(args.split())
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout
                cwd=str(PROJECT_ROOT),
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Script timed out after 5 minutes",
                "stdout": "",
                "stderr": "",
                "returncode": -1,
            }
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "stdout": "",
                "stderr": "",
                "returncode": -1,
            }

    # ── Diff / Sync ────────────────────────────────────────────────────

    def get_diff(self, filename: str) -> Optional[dict]:
        """
        Compare a main file and its replace counterpart.
        Returns None if replace file doesn't exist.
        """
        try:
            yml = self.get_file(filename)
            repl = self.get_replace_file(filename)
            if yml is None or repl is None:
                return None
            main_by_key = {e.key: e for e in yml.entries}
            repl_by_key = {e.key: e for e in repl.entries}
            diffs = []
            all_keys = set(main_by_key) | set(repl_by_key)
            for key in sorted(all_keys):
                m_val = main_by_key[key].value if key in main_by_key else None
                r_val = repl_by_key[key].value if key in repl_by_key else None
                if m_val != r_val:
                    diffs.append({
                        "key": key,
                        "main_value": m_val,
                        "replace_value": r_val,
                        "in_main": key in main_by_key,
                        "in_replace": key in repl_by_key,
                    })
            return {
                "filename": filename,
                "diff_count": len(diffs),
                "main_count": len(yml.entries),
                "replace_count": len(repl.entries),
                "diffs": diffs,
            }
        except Exception:
            return None

    def sync_to_replace(self, filename: str) -> int:
        """Sync values from main file to replace file. Returns keys synced."""
        if self.replace_dir is None:
            return 0
        try:
            yml = self.get_file(filename)
            if yml is None:
                return 0
            repl_path = self.replace_dir / filename
            if not repl_path.exists():
                return 0
            # Load replace file fresh
            repl = YmlFile(repl_path)
            main_by_key = {e.key: e.value for e in yml.entries}
            updates = {}
            for e in repl.entries:
                if e.key in main_by_key and main_by_key[e.key]:
                    updates[e.key] = main_by_key[e.key]
            if updates:
                repl.set_values(updates)
                repl.save()
            return len(updates)
        except Exception:
            return 0

    # ── Key Analysis & Categorization ────────────────────────────────

    # Known Stellaris key prefixes for categorization
    KEY_PREFIXES = [
        "trait_", "civic_", "tech_", "origin_", "modifier_", "mod_",
        "building_", "ship_", "army_", "leader_", "pop_", "planet_",
        "megastructure_", "situation_", "tradition_", "resolution_",
        "edict_", "policy_", "war_", "anomaly_", "job_", "district_",
        "starbase_", "fleet_", "component_", "ethics_", "council_",
        "agenda_", "mandate_", "paragon_", "crisis_", "operation_",
        "espionage_", "fallen_empire_", "enclave_", "relic_",
        "archaeology_", "sector_", "shroud_", "machine_",
        "first_contact_", "biogenesis_", "astral_", "cosmic_",
        "observation_", "horizon_", "clone_", "grand_archive_",
        "infernals_", "leviathan_", "achievement_", "scripted_loc_",
        "distant_stars_", "apocalypse_", "aquatic_", "necroid_",
        "lithoid_", "plantoid_", "humanoid_",
    ]

    # Regex patterns for value analysis
    _VAR_RE = re.compile(r"\$([A-Za-z0-9_|]+?)\$")
    _ICON_RE = re.compile(r"£([a-z_]+)£")
    _COLOR_RE = re.compile(r"§.")

    @staticmethod
    def category_for_key(key: str) -> str:
        """Return the category label for a key based on its prefix."""
        for p in DataManager.KEY_PREFIXES:
            if key.startswith(p):
                return p.rstrip("_").replace("_", " ").title()
        return "Other"

    @staticmethod
    def categorize_keys(keys: list[str]) -> dict[str, list[str]]:
        """Group keys by category prefix."""
        groups: dict[str, list[str]] = {}
        for key in keys:
            cat = DataManager.category_for_key(key)
            groups.setdefault(cat, []).append(key)
        return groups

    def get_key_analysis(self) -> dict:
        """
        Comprehensive analysis of all keys across all files.
        Returns:
            category_coverage: {category: {total, filled, empty, pct, keys}}
            variable_stats: {total_with_vars, total_icons, total_color}
            prefix_counts: {prefix: count}
        """
        try:
            from collections import defaultdict

            cat_stats: dict[str, dict] = defaultdict(
                lambda: {"total": 0, "filled": 0, "empty": 0, "pct": 0.0}
            )
            prefix_counts: dict[str, int] = defaultdict(int)
            total_with_vars = 0
            total_with_icons = 0
            total_with_color = 0
            long_keys = 0  # keys with values > 500 chars
            total_keys = 0

            for fname in self.file_names:
                yml = self.get_file(fname)
                if not yml:
                    continue
                for entry in yml.entries:
                    total_keys += 1
                    val = entry.value
                    is_filled = bool(val.strip())

                    # Categorize by prefix
                    cat = self.category_for_key(entry.key)
                    cat_stats[cat]["total"] += 1
                    if is_filled:
                        cat_stats[cat]["filled"] += 1
                    else:
                        cat_stats[cat]["empty"] += 1

                    # Prefix counting
                    for p in self.KEY_PREFIXES:
                        if entry.key.startswith(p):
                            prefix_counts[p] += 1
                            break

                    # Value analysis
                    if self._VAR_RE.search(val):
                        total_with_vars += 1
                    if self._ICON_RE.search(val):
                        total_with_icons += 1
                    if self._COLOR_RE.search(val):
                        total_with_color += 1
                    if len(val) > 500:
                        long_keys += 1

            # Compute percentages per category
            for cat, stats in cat_stats.items():
                if stats["total"] > 0:
                    stats["pct"] = round(
                        stats["filled"] / stats["total"] * 100, 1
                    )

            # Sort categories by count
            sorted_cats = sorted(
                cat_stats.items(), key=lambda x: -x[1]["total"]
            )

            return {
                "categories": [
                    {"name": name, **stats}
                    for name, stats in sorted_cats
                ],
                "prefix_counts": dict(
                    sorted(prefix_counts.items(), key=lambda x: -x[1])
                ),
                "variable_stats": {
                    "with_vars": total_with_vars,
                    "with_icons": total_with_icons,
                    "with_color": total_with_color,
                    "long_keys": long_keys,
                    "total_keys": total_keys,
                    "var_pct": round(
                        total_with_vars / total_keys * 100, 1
                    ) if total_keys else 0,
                    "icon_pct": round(
                        total_with_icons / total_keys * 100, 1
                    ) if total_keys else 0,
                    "color_pct": round(
                        total_with_color / total_keys * 100, 1
                    ) if total_keys else 0,
                },
            }
        except Exception:
            return {"categories": [], "prefix_counts": {}, "variable_stats": {}}

    def search_by_category(
        self, category: str, scope: str = "all"
    ) -> list[dict]:
        """
        Search for keys within a specific category.
        scope: "all", "translated", "untranslated"
        """
        try:
            results = []
            cat_lower = category.lower()
            for fname in self.file_names:
                yml = self.get_file(fname)
                if not yml:
                    continue
                for entry in yml.entries:
                    if self.category_for_key(entry.key).lower() != cat_lower:
                        continue
                    is_empty = not entry.value.strip()
                    if scope == "translated" and is_empty:
                        continue
                    if scope == "untranslated" and not is_empty:
                        continue
                    results.append({
                        "filename": fname,
                        "key": entry.key,
                        "value": entry.value,
                        "empty": is_empty,
                    })
            return results
        except Exception:
            return []

    def get_untranslated_by_category(self) -> dict[str, list[dict]]:
        """Get all untranslated keys grouped by category."""
        try:
            from collections import defaultdict
            groups: dict[str, list[dict]] = defaultdict(list)
            for fname in self.file_names:
                yml = self.get_file(fname)
                if not yml:
                    continue
                for entry in yml.entries:
                    if not entry.value.strip():
                        cat = self.category_for_key(entry.key)
                        groups[cat].append({
                            "filename": fname,
                            "key": entry.key,
                        })
            return dict(groups)
        except Exception:
            return {}

    def invalidate_coverage_cache(self):
        """Invalidate the coverage cache so it's recomputed."""
        self._coverage_cache = None

    def on_value_changed(self, filename: str):
        """Called when a value is edited — invalidates caches."""
        self._coverage_cache = None
        self._dirty = True

    # ── Import / Export ──────────────────────────────────────────────

    def import_from_english_source(self, source_dir, dry_run: bool = False) -> dict:
        """
        Import English .yml files from a game source directory.
        For each English file not yet present in the mod, creates a stub.
        For existing files, identifies any new keys to add.

        Returns: {created: [filenames], updated: [filenames], skipped: int, total: int}
        """
        if self.loc_dir is None:
            return {"error": "No mod folder opened"}
        source_dir = Path(source_dir)
        created = []
        updated = []
        skipped = 0
        total = 0

        if not source_dir.exists():
            return {"error": f"Source directory not found: {source_dir}"}

        for fpath in sorted(source_dir.glob("*_l_english.yml")):
            total += 1
            target_path = self.loc_dir / fpath.name

            # Parse source file
            source_entries = {}
            try:
                with open(fpath, "r", encoding="utf-8-sig") as f:
                    for line in f:
                        m = re.match(r'^\s+([^:]+?):\d*\s*"(.*)"', line)
                        if m:
                            source_entries[m.group(1)] = m.group(2)
            except Exception:
                skipped += 1
                continue

            if not target_path.exists():
                # Create stub file
                if dry_run:
                    created.append(fpath.name)
                else:
                    try:
                        with open(target_path, "w", encoding="utf-8-sig", newline="\r\n") as f:
                            f.write("l_english:\r\n")
                            for key in sorted(source_entries.keys()):
                                f.write(f" {key}:0 \"\"\r\n")
                        created.append(fpath.name)
                    except Exception:
                        skipped += 1
            else:
                # Merge new keys into existing file
                if dry_run:
                    existing = set()
                    existing_yml = self.get_file(fpath.name)
                    if existing_yml:
                        existing = {e.key for e in existing_yml.entries}
                    new_keys = set(source_entries.keys()) - existing
                    if new_keys:
                        updated.append(fpath.name)
                else:
                    existing_yml = self.get_file(fpath.name)
                    if existing_yml:
                        existing_keys = {e.key for e in existing_yml.entries}
                        new_keys = set(source_entries.keys()) - existing_keys
                        if new_keys:
                            # Append new keys to existing file
                            with open(target_path, "r+", encoding="utf-8-sig", newline="\r\n") as f:
                                content = f.read().rstrip()
                                for key in sorted(new_keys):
                                    content += f"\r\n {key}:0 \"\""
                                content += "\r\n"
                                f.seek(0)
                                f.write(content)
                                f.truncate()
                            self.reload_file(fpath.name)
                            updated.append(fpath.name)

        return {
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "total": total,
        }


    def _import_dict(self, data: dict, target_filename: str = "") -> dict:
        """Internal: import a dict of {key: value} translations."""
        imported = 0
        file_updates = {}
        if target_filename:
            yml = self.get_file(target_filename)
            if yml:
                updates = {}
                for key, value in data.items():
                    for e in yml.entries:
                        if e.key == key:
                            updates[key] = value
                            break
                if updates:
                    imported += yml.set_values(updates)
                    file_updates[target_filename] = len(updates)
        else:
            for fname in self.file_names:
                yml = self.get_file(fname)
                if not yml:
                    continue
                updates = {}
                for key, value in data.items():
                    for e in yml.entries:
                        if e.key == key:
                            updates[key] = value
                            break
                if updates:
                    count = yml.set_values(updates)
                    imported += count
                    file_updates[fname] = count
        return {"imported": imported, "total_keys": len(data), "files_affected": list(file_updates.keys())}

    def import_from_json(self, json_path: Path, target_filename: str = "") -> dict:
        """Import translations from a JSON file."""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            return {"error": f"Failed to read JSON: {exc}"}
        data = self._normalise_import_data(data)
        return self._import_dict(data, target_filename)

    def import_from_csv(self, csv_path: Path, target_filename: str = "") -> dict:
        """Import translations from a CSV file."""
        import csv
        try:
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                data = {}
                for row in reader:
                    key = row.get("key") or row.get("Key") or row.get("KEY") or                           row.get("key_name") or row.get("loc_key")
                    val = row.get("value") or row.get("Value") or row.get("VALUE") or                           row.get("text") or row.get("Text") or row.get("translation") or                           row.get("Translation") or row.get("thai") or row.get("Thai")
                    if key and key.strip():
                        data[key.strip()] = (val or "").strip()
        except Exception as exc:
            return {"error": f"Failed to read CSV: {exc}"}
        return self._import_dict(data, target_filename)

    def import_from_yml(self, yml_path: Path) -> dict:
        """Import translations from another mod's .yml file."""
        if self.loc_dir is None:
            return {"error": "No mod folder opened"}
        from .yml_handler import YmlFile
        try:
            source = YmlFile(yml_path)
        except Exception as exc:
            return {"error": f"Failed to read YML: {exc}"}
        target = self.get_file(yml_path.name)
        if target is None:
            target_path = self.loc_dir / yml_path.name
            source.save(target_path)
            self.reload_file(yml_path.name)
            return {"imported": len(source.entries), "target": yml_path.name, "new_file": True}
        imported = 0
        updates = {}
        for src_entry in source.entries:
            if THAI_RE.search(src_entry.value):
                for tgt_entry in target.entries:
                    if tgt_entry.key == src_entry.key:
                        updates[src_entry.key] = src_entry.value
                        imported += 1
                        break
        if updates:
            target.set_values(updates)
        return {"imported": imported, "target": yml_path.name, "new_file": False}

    def import_from_mod_directory(self, mod_dir, import_empty: bool = False,
                                  only_thai: bool = False) -> dict:
        """
        Batch import ALL .yml files from a mod directory.

        Scans the given directory (and its subdirectories) for *_l_english.yml
        files, matches them by filename with the current mod's files, and
        imports all key-value pairs.

        Args:
            mod_dir: Path to a mod directory (scanned recursively for .yml)
            import_empty: If True, also imports keys with empty values
                         (overwrites existing). Default: skip empty.
            only_thai: If True, only import values containing Thai text.
                      Default: import all non-empty values.
        """
        if self.loc_dir is None:
            return {"error": "No mod folder opened"}
        mod_dir = Path(mod_dir)
        if not mod_dir.exists():
            return {"error": f"Directory not found: {mod_dir}"}

        from .yml_handler import YmlFile, is_yml_file

        imported_files = 0
        total_keys = 0
        skipped_files = []
        errors = []

        # Scan recursively for all english .yml files
        yml_files = []
        if mod_dir.is_dir():
            for fpath in sorted(mod_dir.rglob("*_l_english.yml")):
                if fpath.is_file():
                    yml_files.append(fpath)

        if not yml_files:
            return {"error": f"No *_l_english.yml files found in {mod_dir}"}

        for src_path in yml_files:
            fname = src_path.name
            try:
                source = YmlFile(src_path)
            except Exception as exc:
                errors.append(f"{fname}: {exc}")
                continue

            # Try to find matching file in our mod (self.loc_dir first, then self.replace_dir)
            target = self.get_file(fname)
            target_path = self.loc_dir / fname

            if target is None and target_path.exists():
                target = self.get_file(fname)

            if target is None:
                # Create new file — copy all source values
                try:
                    updates = {}
                    for e in source.entries:
                        val = e.value.strip()
                        if val or import_empty:
                            updates[e.key] = e.value
                            total_keys += 1
                    if updates:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(target_path, "w", encoding="utf-8-sig", newline="\r\n") as f:
                            f.write("l_english:\r\n")
                            for key, val in sorted(updates.items()):
                                f.write(f" {key}:0 \"{val}\"\r\n")
                        self.reload_file(fname)
                        imported_files += 1
                except Exception as exc:
                    errors.append(f"{fname}: {exc}")
                    skipped_files.append(fname)
            else:
                # Merge into existing file
                try:
                    updates = {}
                    for src_entry in source.entries:
                        sv = src_entry.value.strip()
                        if not sv and not import_empty:
                            continue
                        if only_thai and sv and not THAI_RE.search(sv):
                            continue
                        for tgt_entry in target.entries:
                            if tgt_entry.key == src_entry.key:
                                updates[src_entry.key] = sv
                                total_keys += 1
                                break

                    if updates:
                        target.set_values(updates)
                        imported_files += 1
                except Exception as exc:
                    errors.append(f"{fname}: {exc}")
                    skipped_files.append(fname)

        # Reload all if anything was imported
        if imported_files > 0:
            self.reload_all()

        return {
            "imported_files": imported_files,
            "total_keys": total_keys,
            "total_found": len(yml_files),
            "skipped_files": skipped_files,
            "errors": errors,
        }

    @staticmethod
    def _normalise_import_data(data) -> dict:
        if isinstance(data, list):
            result = {}
            for item in data:
                if isinstance(item, dict):
                    if "key" in item and "value" in item:
                        result[item["key"]] = item["value"]
                    elif len(item) == 1:
                        for k, v in item.items():
                            result[k] = v
            return result
        if isinstance(data, dict):
            return data
        return {}

    def export_to_json(self, scope: str = "all", filepath: Path | None = None) -> list[dict]:
        try:
            report = []
            for fname in self.file_names:
                yml = self.get_file(fname)
                if not yml:
                    continue
                for entry in yml.entries:
                    is_empty = not entry.value.strip()
                    if scope == "untranslated" and not is_empty:
                        continue
                    if scope == "translated" and is_empty:
                        continue
                    report.append({"file": fname, "key": entry.key, "value": entry.value})
            if filepath:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
            return report
        except Exception:
            return []

    def export_to_csv(self, scope: str = "all", filepath: Path | None = None) -> str:
        try:
            import csv, io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["file", "key", "value"])
            for row in self.export_to_json(scope):
                writer.writerow([row["file"], row["key"], row["value"]])
            result = output.getvalue()
            if filepath:
                with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
                    f.write(result)
            return result
        except Exception:
            return ""

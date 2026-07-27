"""
Suggestion engine for the Localisation Editor.

Provides:
- Glossary term completion (English → Thai)
- Translation memory (similar keys → known translations)
- Variable/tag insertion suggestions
- Key name auto-complete
"""

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# ── Data structures ──────────────────────────────────────────────────────

@dataclass
class Suggestion:
    """A single suggestion item."""
    text: str
    label: str          # Display label
    category: str       # "glossary", "translation_memory", "variable", "tag", "key"
    score: float = 0.0  # Relevance score (higher = more relevant)

# ── Thai regex ──────────────────────────────────────────────────────────
THAI_RE = re.compile(r"[฀-๿]")

# Common Stellaris variables for quick insertion
COMMON_VARIABLES = [
    "$VALUE$", "$NUM$", "$NAME$", "$CLASS$", "$SIZE$", "$LEVEL$",
    "$TYPE$", "$COUNTRY$", "$SPECIES$", "$PLANET$", "$SYSTEM$",
    "$FLEET$", "$ARMY$", "$LEADER$", "$POP$", "$MODIFIER$",
    "$DAYS$", "$YEARS$", "$MONTHS$", "$DATE|H$", "$DAYS$",
    "$COST$", "$UPKEEP$", "$PRODUCTION$", "$INCOME$",
    "$ENERGY$", "$MINERALS$", "$FOOD$", "$ALLOYS$",
    "$RESEARCH$", "$UNITY$", "$INFLUENCE$",
    "$TRADE$", "$NAVAL_CAP$", "$STARBASE_CAP$",
    "$ARMY_CAP$", "$LEADER_CAP$",
    "$DEST$", "$ORIGIN$", "$TARGET$", "$SOURCE$",
    "$NUM_SYSTEMS$", "$NUM_PLANETS$", "$NUM_POPS$",
    "$NAME|Y$", "$VALUE|Y$", "$NUM|Y$", "$DAYS|Y$",
]


class SuggestionEngine:
    """
    Provides intelligent translation suggestions based on:
    - Glossary terms with their Thai translations
    - Translation memory (existing translations for similar keys)
    - Common Stellaris variable and tag patterns
    - Key name analysis for context-aware suggestions
    """

    def __init__(self, data_manager=None):
        self.data_manager = data_manager
        # Glossary lookup: English term → Thai translation
        self.glossary_map: dict[str, str] = {}
        # Glossary reverse: Thai → English
        self.glossary_reverse: dict[str, str] = {}
        # Translation memory: key prefix pattern → list of common translations
        self.translation_memory: dict[str, list[dict]] = defaultdict(list)
        # Key prefix suggestions cache
        self._key_suggestions: dict[str, list[str]] = {}

        if data_manager:
            self._build(data_manager)

    def _build(self, dm):
        """Build the suggestion database from built-in glossary + external data."""
        # ── Built-in glossary (embedded in code, always available) ──
        from .glossary_data import get_glossary_map, get_glossary_reverse
        self.glossary_map = get_glossary_map()
        self.glossary_reverse = get_glossary_reverse()

        # ── External glossary (glossary.json — may supplement built-in) ──
        glossary = dm.get_glossary()
        for entry in glossary:
            eng = entry.get("english", "").strip()
            thai = entry.get("thai", "").strip()
            alt = entry.get("alt", "").strip()
            if eng and thai:
                self.glossary_map[eng.lower()] = thai
                self.glossary_reverse[thai] = eng
            if eng and alt:
                self.glossary_map.setdefault(eng.lower(), alt)
                self.glossary_reverse[alt] = eng

        # ── Translation memory ──
        # Group keys by prefix and collect their Thai translations
        prefix_groups = defaultdict(list)
        for fname in dm.file_names:
            yml = dm.get_file(fname)
            if not yml:
                continue
            for entry in yml.entries:
                val = entry.value.strip()
                if not val or not THAI_RE.search(val):
                    continue
                # Extract prefix (e.g. "trait_" from "trait_ruler_investor_desc")
                for p in dm.KEY_PREFIXES:
                    if entry.key.startswith(p):
                        prefix_groups[p].append({
                            "key": entry.key,
                            "value": val[:100],
                            "file": fname,
                        })
                        break

        # Store top translations per prefix
        for prefix, entries in prefix_groups.items():
            # Deduplicate by value
            seen = set()
            unique = []
            for e in entries:
                if e["value"] not in seen:
                    seen.add(e["value"])
                    unique.append(e)
            self.translation_memory[prefix] = unique[:20]

        # ── Common patterns for quick insert ──
        self._common_patterns = [
            ("Color: Red", "§R", "color"),
            ("Color: Green", "§G", "color"),
            ("Color: Yellow", "§Y", "color"),
            ("Color: Highlight", "§H", "color"),
            ("Color: Lore", "§L", "color"),
            ("Color: Close", "§!", "color"),
            ("Icon: Energy", "£energy£", "icon"),
            ("Icon: Minerals", "£minerals£", "icon"),
            ("Icon: Food", "£food£", "icon"),
            ("Icon: Alloys", "£alloys£", "icon"),
            ("Icon: Consumer Goods", "£consumer_goods£", "icon"),
            ("Icon: Unity", "£unity£", "icon"),
            ("Icon: Influence", "£influence£", "icon"),
            ("Icon: Research", "£research£", "icon"),
            ("Icon: Pop", "£pop£", "icon"),
            ("Icon: Planet", "£planet£", "icon"),
            ("Icon: Fleet", "£fleet£", "icon"),
            ("Icon: Starbase", "£starbase£", "icon"),
            ("Icon: Army", "£army£", "icon"),
            ("Icon: Leader", "£leader£", "icon"),
            ("Icon: System", "£system£", "icon"),
            ("Icon: Tradition", "£tradition£", "icon"),
            ("Icon: Tech", "£tech£", "icon"),
            ("Icon: Building", "£building£", "icon"),
            ("Trigger: Yes", "£trigger_yes£", "icon"),
            ("Trigger: No", "£trigger_no£", "icon"),
            ("Icon: District", "£district£", "icon"),
        ]

    # ── Public API ─────────────────────────────────────────────────────

    def suggest_glossary(self, partial: str) -> list[Suggestion]:
        """
        Suggest Thai translations for English terms matching the partial text.
        """
        if not partial or len(partial) < 2:
            return []
        partial_lower = partial.lower()
        results = []

        for eng, thai in self.glossary_map.items():
            if partial_lower in eng:
                score = 1.0 if eng.startswith(partial_lower) else 0.5
                results.append(Suggestion(
                    text=thai,
                    label=f"{eng} → {thai}",
                    category="glossary",
                    score=score,
                ))

        results.sort(key=lambda s: (-s.score, s.label))
        return results[:10]

    def suggest_translation_memory(
        self, key: str, partial: str = ""
    ) -> list[Suggestion]:
        """
        Suggest translations from similar keys (same prefix category).
        """
        if not self.data_manager:
            return []

        # Get the key's category
        cat = self.data_manager.category_for_key(key)
        if cat == "Other":
            return []

        # Find similar keys in translation memory
        results = []
        for prefix, entries in self.translation_memory.items():
            # Fuzzy match: check if any prefix matches the key
            if key.startswith(prefix):
                for e in entries[:8]:
                    val = e["value"]
                    if partial and partial.lower() not in val.lower():
                        continue
                    results.append(Suggestion(
                        text=val,
                        label=f"[{e['file']}] {e['key']}: {val[:50]}",
                        category="translation_memory",
                        score=0.8,
                    ))

        return results[:10]

    def suggest_variables(self, partial: str = "") -> list[Suggestion]:
        """Suggest game variables matching partial text."""
        if not partial:
            return [
                Suggestion(text=v, label=v, category="variable", score=0.3)
                for v in COMMON_VARIABLES[:10]
            ]
        partial_lower = partial.lower()
        results = []
        for var in COMMON_VARIABLES:
            var_lower = var.lower()
            if partial_lower in var_lower:
                score = 1.0 if var_lower.startswith(partial_lower) else 0.5
                results.append(Suggestion(
                    text=var, label=var, category="variable", score=score
                ))
        results.sort(key=lambda s: -s.score)
        return results[:10]

    def suggest_tags(self, partial: str = "") -> list[Suggestion]:
        """Suggest color tags and icons."""
        if not partial:
            return [
                Suggestion(text=text, label=label, category=cat, score=0.5)
                for label, text, cat in self._common_patterns[:10]
            ]
        partial_lower = partial.lower()
        results = []
        for label, text, cat in self._common_patterns:
            if partial_lower in label.lower() or partial_lower in text.lower():
                results.append(Suggestion(
                    text=text, label=f"{label}: {text}",
                    category=cat, score=0.7
                ))
        return results[:10]

    def suggest_all(
        self, key: str, partial_value: str
    ) -> list[Suggestion]:
        """
        Get all types of suggestions for a given key and partial value.
        Returns combined, scored list.
        """
        results = []

        # 1. Glossary suggestions (if typing English text)
        words = partial_value.split()
        if words:
            last_word = words[-1].strip(".,;:!?()[]{}'\"")
            if last_word and not THAI_RE.search(last_word) and len(last_word) >= 2:
                results.extend(self.suggest_glossary(last_word))

        # 2. Translation memory suggestions
        if len(partial_value) >= 3:
            results.extend(self.suggest_translation_memory(key, partial_value))

        # 3. Variable suggestions
        if "$" in partial_value:
            # Extract partial variable name after $
            idx = partial_value.rfind("$")
            partial_var = partial_value[idx:] if idx >= 0 else ""
            if partial_var and not partial_var.endswith("$"):
                results.extend(self.suggest_variables(partial_var))
        elif not partial_value or partial_value.endswith(" "):
            # Show common variables as quick options
            results.extend(self.suggest_variables())

        # 4. Tag suggestions
        if "§" in partial_value or "£" in partial_value or not partial_value:
            results.extend(self.suggest_tags())

        # Sort by score descending
        results.sort(key=lambda s: (-s.score, s.category, s.label))
        return results[:15]

    def get_glossary_suggestions(self, english_term: str) -> list[str]:
        """Get Thai translation suggestions for an English term."""
        results = self.suggest_glossary(english_term)
        return [s.text for s in results]

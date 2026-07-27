"""
Spell checker for the Localisation Editor.
Supports English (built-in dictionary) and Thai (from existing translations).
Provides suggestions via Levenshtein distance and character n-gram analysis.
"""

import re
from collections import Counter
from dataclasses import dataclass, field

# ── Data structures ──────────────────────────────────────────────────────

@dataclass
class SpellError:
    """A spelling error found in text."""
    word: str
    start: int
    end: int
    suggestions: list[str] = field(default_factory=list)
    is_thai: bool = False

# ── Thai Unicode ranges ──────────────────────────────────────────────────
THAI_RANGE = re.compile(r"[฀-๿]")

# Regex patterns for tokenizing text
WORD_RE = re.compile(r"[A-Za-z฀-๿']+")
ENGLISH_WORD_RE = re.compile(r"[A-Za-z']+")
THAI_WORD_RE = re.compile(r"[฀-๿]+")

# ── Common English words for Stellaris ──────────────────────────────────
STELLARIS_ENGLISH = {
    # Articles, prepositions, conjunctions
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "can", "could", "shall", "should", "may", "might", "must",
    "not", "no", "nor", "none", "nothing", "all", "each", "every", "both",
    "some", "any", "many", "much", "more", "most", "few", "less", "several",
    "this", "that", "these", "those", "it", "its", "they", "them", "their",
    "he", "she", "him", "her", "his", "we", "us", "our", "you", "your",
    "who", "whom", "which", "what", "where", "when", "why", "how",

    # Common verbs
    "add", "remove", "set", "get", "make", "take", "give", "use", "find",
    "keep", "start", "stop", "open", "close", "show", "hide", "create",
    "destroy", "build", "break", "change", "update", "increase", "decrease",
    "enable", "disable", "allow", "deny", "require", "need", "want", "know",
    "think", "believe", "see", "look", "hear", "say", "tell", "ask", "answer",
    "come", "go", "leave", "return", "enter", "move", "follow", "lead",
    "help", "support", "protect", "attack", "defend", "destroy", "conquer",
    "rule", "govern", "lead", "command", "control", "manage", "produce",
    "build", "construct", "develop", "research", "study", "learn", "teach",
    "trade", "sell", "buy", "pay", "cost", "spend", "earn", "gain",
    "lose", "win", "fight", "win", "succeed", "fail", "try", "attempt",

    # Common Stellaris nouns
    "empire", "species", "planet", "system", "star", "galaxy", "universe",
    "fleet", "ship", "station", "base", "army", "army", "pop", "leader",
    "ruler", "governor", "admiral", "general", "scientist", "envoys",
    "building", "district", "job", "resource", "energy", "minerals",
    "food", "alloys", "consumer", "goods", "research", "unity", "influence",
    "technology", "tradition", "ascension", "perk", "civic", "origin",
    "edict", "policy", "war", "peace", "alliance", "federation", "treaty",
    "diplomacy", "relations", "opinion", "trust", "threat", "power",
    "strength", "force", "border", "territory", "sector", "colony",
    "settlement", "habitat", "ringworld", "megastructure", "space",
    "science", "physics", "society", "engineering", "weapon", "armor",
    "shield", "component", "module", "upgrade", "design",

    # Stellaris-specific
    "hyperlane", "ftl", "starbase", "starhold", "starfortress",
    "citadel", "outpost", "anchorage", "shipyard", "trade", "route",
    "anomaly", "archaeology", "relic", "artifact", "situation",
    "crisis", "awakening", "rebellion", "uprising", "invasion",
    "first_contact", "discover", "explore", "expand", "exploit",
    "exterminate", "research", "tradition", "adopt", "finish",

    # Adjectives / descriptors
    "good", "bad", "great", "small", "large", "high", "low", "long",
    "short", "big", "little", "old", "new", "young", "ancient", "modern",
    "strong", "weak", "powerful", "fast", "slow", "rich", "poor",
    "alien", "foreign", "local", "native", "unknown", "distant",
    "nearby", "hostile", "friendly", "neutral", "peaceful", "aggressive",
    "passive", "active", "positive", "negative", "special", "normal",
    "common", "rare", "unique", "basic", "advanced", "superior",
    "inferior", "equal", "different", "similar", "additional",
    "effective", "efficient", "capable", "total", "current",

    # Numbers and quantifiers
    "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "first", "second", "third", "last", "next",
    "previous", "final", "initial", "single", "double", "triple",
    "half", "full", "quarter", "percent", "times", "count", "number",
    "level", "tier", "rank", "stage", "phase", "step", "part",
    "type", "kind", "sort", "category", "class", "group", "set",

    # Time
    "year", "month", "day", "hour", "minute", "second", "time",
    "current", "previous", "next", "daily", "monthly", "yearly",
    "annual", "recent", "future", "past", "present", "immediate",

    # Other common
    "name", "title", "desc", "description", "effect", "modifier",
    "condition", "trigger", "tooltip", "detail", "info", "note",
    "text", "label", "value", "key", "list", "table", "form",
    "option", "choice", "select", "toggle", "switch", "mode",
    "setting", "config", "size", "color", "shape", "form", "style",
    "type", "version", "status", "state", "flag", "marker", "tag",
    "icon", "image", "symbol", "sign", "signal", "message", "data",
    "info", "stats", "info", "summary", "detail", "overview",
    "menu", "window", "screen", "panel", "tab", "section", "page",
    "area", "zone", "region", "location", "position", "direction",

    # Prepositions / connectors continued
    "up", "down", "over", "under", "above", "below", "between",
    "among", "through", "throughout", "during", "before", "after",
    "until", "since", "within", "without", "about", "along", "around",
    "against", "across", "behind", "beyond", "inside", "outside",
    "upon", "onto", "into", "toward", "towards", "via",

    # Question / relative words
    "what", "which", "where", "when", "why", "how", "who", "whom",
    "whose", "that", "whether", "if", "because", "since", "although",
    "though", "while", "whereas", "unless", "except", "despite",

    # English suffixes / particles
    "per", "plus", "minus", "over", "under", "out", "in", "off",
    "up", "down", "away", "back", "forth", "apart", "together",
    "already", "still", "yet", "even", "just", "only", "also",
    "quite", "very", "too", "again", "ever", "never", "always",
    "often", "sometimes", "usually", "well", "so", "such", "thus",
    "else", "other", "otherwise", "instead",
}

# Mixed-script detection
MIXED_SCRIPT_RE = re.compile(
    r"[฀-๿a-zA-Z]"
)


class SpellChecker:
    """
    Multi-language spell checker for Stellaris localisation.

    English: built-in dictionary of common words + extracted from locale files.
    Thai:    extracted from existing Thai translations + glossary.
    Suggestions via Levenshtein distance (capped at top 5).
    """

    def __init__(self, data_manager=None):
        self.english_words: set[str] = set(STELLARIS_ENGLISH)
        self.thai_words: set[str] = set()
        self.known_words: set[str] = set()  # union cache

        # Uppercase abbreviations are always OK (ACRONYM, FTL, etc.)
        self.known_abbrevs: re.Pattern = re.compile(r"^[A-Z][A-Z_0-9]{1,8}$")
        # Color codes and game syntax are handled by the tokenizer skip list

        # Build Thai dictionary from existing translations
        if data_manager:
            self._build_from_translations(data_manager)

    def _build_from_translations(self, dm):
        """Build comprehensive dictionary from glossary + all translation files.

        Includes:
          - Built-in glossary 260+ terms (embedded in code)
          - External glossary.json terms
          - Stellaris-specific key-name words (from key prefixes)
          - All English words found in source values
          - All Thai words found in existing translations
          - Curated list of 200+ Stellaris game terms
        """
        from collections import Counter

        # ── 0. Add ALL built-in glossary terms first (embedded in code) ──
        from .glossary_data import update_stellaris_terms
        update_stellaris_terms(self.english_words)

        # ── 1. Add ALL external glossary terms (from glossary.json) ──
        glossary = dm.get_glossary()
        for entry in glossary:
            eng = entry.get("english", "").strip()
            thai = entry.get("thai", "").strip()
            alt = entry.get("alt", "").strip()
            # Add each word from multi-word terms (e.g. "ascension perk" -> both added)
            for text in [eng, thai, alt]:
                if not text:
                    continue
                for w in text.split():
                    w_clean = w.strip(".,;:!?()[]{}")
                    if len(w_clean) <= 1:
                        continue
                    if ENGLISH_WORD_RE.fullmatch(w_clean):
                        self.english_words.add(w_clean.lower())
                    else:
                        self.thai_words.add(w_clean)

        # ── 2. Extract from key names (split on underscore + camelCase) ──
        # Key names contain game terminology: trait_ruler -> ruler, starbase_shipyard -> starbase
        KEY_WORD_RE = re.compile(r"[a-zA-Z]+")
        key_count = 0
        for fname in dm.file_names:
            yml = dm.get_file(fname)
            if not yml:
                continue
            for entry in yml.entries:
                for m in KEY_WORD_RE.finditer(entry.key):
                    w = m.group().lower()
                    if len(w) > 2 and w[0].isalpha():
                        self.english_words.add(w)
                        key_count += 1

        # ── 3. Extract all English words from ALL source values ──
        en_counts = Counter()
        for fname in dm.file_names:
            yml = dm.get_file(fname)
            if not yml:
                continue
            for entry in yml.entries:
                for m in ENGLISH_WORD_RE.finditer(entry.value):
                    w = m.group().lower()
                    if len(w) > 1 and w[0].isalpha():
                        en_counts[w] += 1

        # Common English stop-words to exclude
        STOP_WORDS = {
            "the", "and", "for", "are", "not", "but", "its", "all",
            "per", "yes", "no", "via", "vs", "etc", "from", "this", "that",
            "with", "have", "will", "been", "were", "has", "had", "can",
            "would", "could", "should", "may", "might", "must", "than",
            "then", "also", "just", "very", "well", "much", "more", "some",
            "any", "each", "every", "both", "few", "most", "such", "other",
            "into", "upon", "onto", "over", "under", "about", "than", "also",
            "was", "been", "being", "does", "done", "able", "after", "again",
            "against", "almost", "among", "another", "around", "because",
            "before", "between", "does", "during", "enough", "ever", "every",
            "further", "here", "however", "least", "less", "many", "more",
            "much", "myself", "never", "next", "often", "once", "only",
            "other", "own", "perhaps", "quite", "rather", "really", "same",
            "seem", "several", "should", "since", "still", "such", "than",
            "though", "thus", "together", "too", "until", "very", "while",
            "whose", "without", "yet",
        }

        for word, count in en_counts.most_common():
            if word in STOP_WORDS:
                continue
            if count >= 2:  # Lowered threshold: appear 2+ times = valid
                self.english_words.add(word)

        # ── 4. Extract Thai words from ALL translations ──
        for fname in dm.file_names:
            yml = dm.get_file(fname)
            if not yml:
                continue
            for entry in yml.entries:
                val = entry.value
                if not val:
                    continue
                for m in THAI_WORD_RE.finditer(val):
                    word = m.group()
                    if len(word) > 1:
                        self.thai_words.add(word)

        # Also add words from Thai dict JSON
        try:
            thai_dict = dm.get_thai_dict()
            if isinstance(thai_dict, dict):
                for key, val in thai_dict.items():
                    for m in THAI_WORD_RE.finditer(str(val)):
                        word = m.group()
                        if len(word) > 1:
                            self.thai_words.add(word)
        except Exception:
            pass

        # ── 5. Curated Stellaris game terms ──
        stellaris_terms = {
            # Abbreviations
            "ftl", "pop", "pops", "hab", "tech", "techs", "megastruct",
            "megastructures", "starbase", "starbases", "starhold", "starholds",
            "starfortress", "citadel", "citadels", "outpost", "outposts",
            "anchorages", "shipyard", "shipyards", "edict", "edicts",
            "civic", "civics", "anomaly", "anomalies", "relic", "relics",
            "leviathan", "leviathans", "enclave", "enclaves",

            # Ethics / authority
            "xenophile", "xenophobe", "xenophilic", "xenophobic",
            "militarist", "militarists", "pacifist", "pacifists",
            "materialist", "materialists", "spiritualist", "spiritualists",
            "egalitarian", "egalitarians", "authoritarian", "authoritarians",
            "gestalt", "hive", "hivemind", "machine", "machine",

            # Game mechanics
            "hyperlane", "hyperlanes", "habitability", "amenities",
            "stability", "crime", "trade", "unity", "influence",
            "alloys", "minerals", "energy", "physics", "society",
            "engineering", "traditions", "ascension", "perks",
            "megastructure", "ringworld", "habitat", "habitats",
            "ecumenopolis", "ecu", "arcology", "arcologies",
            "shroud", "psionics", "psionic", "cybernetics", "cybernetic",
            "synthetic", "genetic", "bio", "nanite", "nanites",

            # Species types
            "humanoid", "humanoids", "reptilian", "reptilians",
            "avian", "avians", "arthropod", "arthropods", "molluscoid",
            "molluscoids", "fungoid", "fungoids", "plantoid", "plantoids",
            "lithoid", "lithoids", "necroid", "necroids", "aquatic",
            "aquatics", "toxoid", "toxoids",

            # DLC / content
            "utopia", "apocalypse", "megacorp", "synthetic", "dawn",
            "leviathans", "distant", "stars", "ancient", "relics",
            "federations", "nemesis", "overlord", "first", "contact",
            "aquatics", "toxoids", "galactic", "paragons",
            "astral", "planes", "cosmic", "storms", "machine", "age",
            "grand", "archive", "biogenesis", "infernals",

            # Ship components
            "armor", "shield", "shields", "weapon", "weapons",
            "component", "components", "sensor", "sensors", "computer",
            "computers", "thruster", "thrusters", "reactor", "reactors",
            "hyperdrive", "jumpdrive", "psi", "jump", "drive",
            "corvette", "corvettes", "destroyer", "destroyers",
            "cruiser", "cruisers", "battleship", "battleships",
            "titan", "titans", "colossus", "juggernaut", "juggernauts",
            "science", "ship", "construction", "colony", "transport",

            # Leaders
            "admiral", "admirals", "general", "generals", "governor",
            "governors", "scientist", "scientists", "envoy", "envoys",
            "ruler", "rulers", "council", "councillor", "councillors",
            "paragon", "paragons", "leader", "leaders",

            # Jobs / strata
            "technician", "technicians", "miner", "miners", "farmer",
            "farmers", "artisan", "artisans", "metallurgist", "metallurgists",
            "researcher", "researchers", "bureaucrat", "bureaucrats",
            "priest", "priests", "enforcer", "enforcers", "soldier",
            "soldiers", "clerk", "clerks", "specialist", "specialists",
            "worker", "workers", "ruler", "rulers", "stratum",

            # Events / exploration
            "anomaly", "anomalies", "archaeology", "digsite", "digsites",
            "relic", "relics", "situation", "situations", "crisis",
            "crises", "awakening", "rebellion", "uprising",

            # Origins / civics
            "prosperous", "unification", "remnants", "scion", "scions",
            "hegemon", "hegemons", "mechanist", "mechanists", "syncretic",
            "evolution", "doomsday", "void", "dweller", "dwellers",
            "clone", "army", "necrophage", "necrophages", "aquatic",
            "terravore", "terravores", "subterranean", "ocean", "paradise",
        }
        self.english_words.update(stellaris_terms)

        self.known_words = self.english_words | self.thai_words
        print(f"[SpellChecker] Loaded {len(self.english_words)} EN + "
              f"{len(self.thai_words)} TH words")

    # ── Tokenizer ──────────────────────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> list[tuple[str, int, int]]:
        """
        Split text into words, returning (word, start, end) tuples.
        Skips numbers, game variables ($VAR$), and icons (£icon£).
        """
        tokens = []
        # Skip game patterns first
        # We find all word-like tokens and filter out game syntax

        # Find dollar variables and skip over them
        skip_regions = []
        for m in re.finditer(r'\$[A-Za-z0-9_|]+\$', text):
            skip_regions.append((m.start(), m.end()))
        for m in re.finditer(r'£[a-z_]+£', text):
            skip_regions.append((m.start(), m.end()))
        for m in re.finditer(r'§.', text):
            skip_regions.append((m.start(), m.end()))

        def is_skipped(pos: int) -> bool:
            return any(s <= pos < e for s, e in skip_regions)

        for m in WORD_RE.finditer(text):
            if is_skipped(m.start()):
                continue
            word = m.group()
            word_clean = word.strip(".,;:!?()[]{}'\"")
            if len(word_clean) < 2:
                continue
            if word_clean.isdigit():
                continue
            if word_clean.isupper() and len(word_clean) <= 8:
                continue  # skip abbrevs like FTL, POP, etc.
            if word_clean.startswith("\\"):
                continue
            tokens.append((word_clean, m.start(), m.end()))

        return tokens

    # ── Levenshtein distance ───────────────────────────────────────────

    @staticmethod
    def _levenshtein(a: str, b: str) -> int:
        """Compute edit distance between two strings."""
        if len(a) < len(b):
            a, b = b, a
        if not b:
            return len(a)
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a):
            curr = [i + 1]
            for j, cb in enumerate(b):
                cost = 0 if ca == cb else 1
                curr.append(min(
                    curr[j] + 1,          # insert
                    prev[j + 1] + 1,      # delete
                    prev[j] + cost        # replace
                ))
            prev = curr
        return prev[-1]

    # ── Main API ───────────────────────────────────────────────────────

    def check_word(self, word: str) -> bool:
        """Check if a word is correctly spelled."""
        try:
            if not word or len(word) < 2:
                return True

            # Known in dictionaries
            if word.lower() in self.known_words:
                return True

            # Check if it's a number or abbreviation
            if word.isdigit() or word.isupper():
                return True

            # Mixed-script words are suspicious
            thai = bool(THAI_RANGE.search(word))
            latin = bool(re.search(r"[A-Za-z]", word))
            if thai and latin:
                return False

            return False
        except Exception:
            return True  # on error, assume the word is OK

    def suggestions(self, word: str, max_results: int = 5) -> list[str]:
        """Find similar words in the dictionary."""
        try:
            word_lower = word.lower()
            is_thai = bool(THAI_RANGE.search(word))
            dictionary = self.thai_words if is_thai else self.english_words

            if not dictionary:
                return []

            # Score candidates by Levenshtein distance
            scored = []
            for candidate in dictionary:
                dist = self._levenshtein(word_lower, candidate[:50].lower())
                if dist == 0:
                    continue  # exact match (shouldn't reach here)
                if dist <= 3:  # only suggest if close
                    scored.append((dist, candidate))

            scored.sort(key=lambda x: (x[0], -len(x[1])))
            return [s[1] for s in scored[:max_results]]
        except Exception:
            return []

    def check_text_fast(self, text: str) -> list[SpellError]:
        """
        FAST check — only identifies errors without computing suggestions.
        Use this for real-time highlighting (called on debounce while typing).
        Suggestions are computed lazily via get_suggestions() on right-click.
        """
        try:
            if not text:
                return []
            errors = []
            for word, start, end in self._tokenize(text):
                if self.check_word(word):
                    continue
                errors.append(SpellError(
                    word=word,
                    start=start,
                    end=end,
                    suggestions=[],  # not computed yet
                    is_thai=bool(THAI_RANGE.search(word)),
                ))
            return errors
        except Exception:
            return []

    def check_text(self, text: str) -> list[SpellError]:
        """
        FULL check — identifies errors AND computes suggestions (slower).
        Use for manual checks or when displaying suggestions.
        """
        try:
            if not text:
                return []
            errors = self.check_text_fast(text)
            for err in errors:
                err.suggestions = self.suggestions(err.word)[:5]
            return errors
        except Exception:
            return []

    def get_suggestions(self, word: str, max_results: int = 5) -> list[str]:
        """Get suggestions for a specific word (computed on demand)."""
        return self.suggestions(word, max_results)

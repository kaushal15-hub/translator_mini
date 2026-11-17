import re, json, csv
from dataclasses import dataclass
from typing import Iterable
@dataclass
class Term:
    term: str
    aliases: tuple[str, ...] = ()
    case_sensitive: bool = False
    preserve_original: bool = True
    priority: int = 0
    target_language: str | None = None
class TerminologyEngine:
    """Longest-match glossary protection. Replacements are collision-safe and restored exactly."""
    def __init__(self, terms: Iterable[Term] = ()):
        self.terms = sorted(list(terms), key=lambda t: (t.priority, max(map(len, (t.term, *t.aliases))), len(t.term)), reverse=True)
    @classmethod
    def from_records(cls, records):
        return cls(Term(r["term"], tuple(r.get("aliases") or []), bool(r.get("case_sensitive", False)),
                        bool(r.get("preserve_original", True)), int(r.get("priority", 0)), r.get("target_language")) for r in records if r.get("active", True))
    def protect(self, text: str, target_language: str | None = None):
        protected, occupied = [], []
        # Find candidates, then choose longest/highest-priority non-overlapping spans.
        candidates = []
        for term in self.terms:
            if term.target_language and target_language and term.target_language != target_language: continue
            for variant in (term.term, *term.aliases):
                flags = 0 if term.case_sensitive else re.IGNORECASE
                for m in re.finditer(re.escape(variant), text, flags):
                    candidates.append((m.start(), m.end(), term.priority, term, m.group()))
        candidates.sort(key=lambda x: (x[0], -(x[1]-x[0]), -x[2]))
        chosen, end = [], -1
        for c in candidates:
            if c[0] >= end:
                chosen.append(c); end = c[1]
        out, cursor = [], 0
        for i, (start, stop, _, term, matched) in enumerate(chosen):
            out.append(text[cursor:start])
            token = f"ZXQTERM{i}QXZ"
            out.append(token)
            protected.append((token, matched if term.preserve_original else term.term))
            cursor = stop
        out.append(text[cursor:])
        return "".join(out), protected
    @staticmethod
    def restore(text: str, protected):
        for token, original in protected: text = text.replace(token, original)
        return text
    @staticmethod
    def load_json(path):
        with open(path, encoding="utf-8") as f: return json.load(f)
    @staticmethod
    def load_csv(path):
        with open(path, newline="", encoding="utf-8-sig") as f:
            return [{**r, "aliases": [x.strip() for x in r.get("aliases","").split("|") if x.strip()]} for r in csv.DictReader(f)]

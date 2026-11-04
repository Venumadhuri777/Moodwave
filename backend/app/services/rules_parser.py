import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from app.services.intent_schema import Intent, get_vocab

logger = logging.getLogger("moodwave.rules_parser")
KEYWORDS_PATH = Path(__file__).resolve().parent / "keywords.json"

class RulesParser:
    def __init__(self, keywords_file: Path = KEYWORDS_PATH):
        self.keywords: Dict[str, dict] = {}
        self.load_keywords(keywords_file)

    def load_keywords(self, path: Path):
        try:
            if path.is_file():
                with open(path, "r", encoding="utf-8") as f:
                    self.keywords = json.load(f)
                logger.info("Loaded %d keyword rules from %s", len(self.keywords), path)
            else:
                logger.warning("Keywords file not found at %s", path)
        except Exception as e:
            logger.error("Failed to load keywords file %s: %s", path, e)
            self.keywords = {}

    def parse(self, query: str) -> Intent:
        if not query or not query.strip():
            return Intent(moods=[], genres=[], avoid_genres=[], context=None, confidence=0.0)

        text = query.lower().strip()
        vocab = get_vocab()
        all_genres = set(vocab.get("genres", []))

        avoid_genres: List[str] = []
        # Negation extraction: "no rock", "without jazz", "avoid pop", "not electronic"
        negation_pattern = re.compile(r"\b(?:no|without|avoid|not)\s+([a-z\-]+)\b")
        for match in negation_pattern.finditer(text):
            negated_term = match.group(1).strip()
            if negated_term in all_genres and negated_term not in avoid_genres:
                avoid_genres.append(negated_term)

        # Remove negation phrases from text to avoid false positive positive matches
        cleaned_text = negation_pattern.sub(" ", text)

        matched_moods: List[str] = []
        matched_genres: List[str] = []
        context: Optional[str] = None
        match_count = 0

        # 1. Multi-word phrases in keywords (longer first)
        phrases = sorted([k for k in self.keywords.keys() if " " in k], key=len, reverse=True)
        for phrase in phrases:
            if phrase in cleaned_text:
                match_count += 1
                rule = self.keywords[phrase]
                for m in rule.get("moods", []):
                    if m not in matched_moods:
                        matched_moods.append(m)
                for g in rule.get("genres", []):
                    if g not in matched_genres and g not in avoid_genres:
                        matched_genres.append(g)
                if not context and "context" in rule:
                    context = rule["context"]
                # Blank out matched phrase
                cleaned_text = cleaned_text.replace(phrase, " ")

        # 2. Single token matching
        tokens = re.findall(r"\b[a-z0-9\-]+\b", cleaned_text)
        for token in tokens:
            if token in self.keywords:
                match_count += 1
                rule = self.keywords[token]
                for m in rule.get("moods", []):
                    if m not in matched_moods:
                        matched_moods.append(m)
                for g in rule.get("genres", []):
                    if g not in matched_genres and g not in avoid_genres:
                        matched_genres.append(g)
                if not context and "context" in rule:
                    context = rule["context"]

        # Calculate confidence
        if match_count >= 2:
            confidence = 0.90
        elif match_count == 1:
            confidence = 0.80
        else:
            # Fallback if no keywords matched
            confidence = 0.35
            # Provide sensible general default if query had text
            matched_moods = ["calm"]
            matched_genres = ["ambient"]

        # Filter out avoid_genres from matched_genres
        final_genres = [g for g in matched_genres if g not in avoid_genres]

        return Intent(
            moods=matched_moods,
            genres=final_genres,
            avoid_genres=avoid_genres,
            context=context,
            confidence=confidence,
        )

# Global default instance
rules_parser = RulesParser()

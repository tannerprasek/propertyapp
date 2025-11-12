"""Keyword matching and relevance scoring."""

import re
import logging
from typing import List, Dict, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class KeywordMatcher:
    """Match transcript content to Polymarket keywords."""

    def __init__(self):
        """Initialize matcher."""
        self.keyword_cache = {}

    def find_mentions(
        self,
        text: str,
        keywords: List[str],
        min_confidence: float = 0.3
    ) -> List[Dict]:
        """
        Find keyword mentions in text.

        Args:
            text: Transcript text to search
            keywords: List of keywords from Polymarket market
            min_confidence: Minimum confidence score (0-1)

        Returns:
            List of mention dictionaries with position and confidence.
        """
        mentions = []

        for keyword in keywords:
            matches = self._find_keyword_matches(text, keyword)

            for match in matches:
                confidence = self._calculate_confidence(text, keyword, match)

                if confidence >= min_confidence:
                    mentions.append({
                        "keyword": keyword,
                        "position": match,
                        "confidence": confidence,
                    })

        return mentions

    def _find_keyword_matches(self, text: str, keyword: str) -> List[Tuple[int, int]]:
        """Find all occurrences of keyword in text."""
        matches = []

        # Exact phrase match
        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
        for match in pattern.finditer(text):
            matches.append((match.start(), match.end()))

        # Fuzzy match for variations (if exact match not found)
        if not matches:
            words = text.lower().split()
            keyword_lower = keyword.lower()

            for i, word in enumerate(words):
                similarity = SequenceMatcher(None, word, keyword_lower).ratio()
                if similarity > 0.85:  # High similarity threshold
                    # Reconstruct position (approximate)
                    pos = text.lower().find(word, i)
                    if pos >= 0:
                        matches.append((pos, pos + len(word)))

        return matches

    def _calculate_confidence(self, text: str, keyword: str, position: Tuple[int, int]) -> float:
        """
        Calculate confidence score for a keyword mention.

        Confidence factors:
        - Exact match vs fuzzy match
        - Context relevance
        - Position in document (earlier mentions often more important)
        """
        start, end = position
        keyword_len = len(keyword)
        actual_len = end - start

        # Exact match gets high confidence
        if actual_len == keyword_len:
            base_confidence = 0.9
        else:
            base_confidence = 0.6

        # Analyze context for relevance
        context_start = max(0, start - 100)
        context_end = min(len(text), end + 100)
        context = text[context_start:context_end].lower()

        # Context keywords that increase confidence
        context_boosters = {
            "believe": 0.05,
            "think": 0.05,
            "expect": 0.1,
            "forecast": 0.15,
            "predict": 0.15,
            "likely": 0.1,
            "unlikely": 0.1,
            "probability": 0.15,
            "odds": 0.2,
            "will": 0.05,
            "could": 0.05,
            "should": 0.05,
        }

        context_boost = 0
        for booster, score in context_boosters.items():
            if booster in context:
                context_boost = max(context_boost, score)

        # Position factor (earlier mentions slightly more important)
        position_factor = 1.0 - (start / len(text)) * 0.1

        final_confidence = min(1.0, (base_confidence + context_boost) * position_factor)
        return round(final_confidence, 2)

    def extract_sentiment_context(self, text: str, position: Tuple[int, int], window: int = 50) -> str:
        """Extract context around keyword for sentiment analysis."""
        start = max(0, position[0] - window)
        end = min(len(text), position[1] + window)
        return text[start:end]

    def filter_by_relevance(
        self,
        mentions: List[Dict],
        max_mentions: int = 100
    ) -> List[Dict]:
        """Filter mentions by relevance, keeping top N."""
        # Sort by confidence descending
        sorted_mentions = sorted(mentions, key=lambda x: x['confidence'], reverse=True)
        return sorted_mentions[:max_mentions]


class BooleanMatcher:
    """Match complex boolean conditions (e.g., "if X happens, Y is likely")."""

    def __init__(self):
        """Initialize boolean matcher."""
        self.logical_operators = ["and", "or", "but", "if", "then", "unless", "except"]

    def find_conditional_statements(self, text: str, keyword: str) -> List[Dict]:
        """
        Find conditional statements mentioning the keyword.

        Returns statements like "If X, then Y" where Y contains keyword.
        """
        statements = []

        # Split into sentences
        sentences = re.split(r'[.!?]+', text)

        for sentence in sentences:
            if keyword.lower() in sentence.lower():
                # Check if sentence contains conditional language
                if any(op in sentence.lower() for op in self.logical_operators):
                    statements.append({
                        "statement": sentence.strip(),
                        "contains_condition": True,
                    })

        return statements

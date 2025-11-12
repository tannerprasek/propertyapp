"""Sentiment analysis for transcript mentions."""

import logging
from typing import List
from enum import Enum

logger = logging.getLogger(__name__)

class Sentiment(str, Enum):
    """Sentiment classification."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class SentimentAnalyzer:
    """Analyze sentiment of transcript mentions."""

    # Sentiment lexicons (can be expanded)
    POSITIVE_WORDS = {
        "strong", "growth", "increase", "improve", "rise", "boost",
        "positive", "upbeat", "optimistic", "bullish", "strength",
        "momentum", "powerful", "successful", "exceed", "beat",
        "outperform", "gain", "advance", "grow", "expand",
        "better", "excellent", "great", "fantastic", "wonderful",
        "benefits", "advantage", "opportunity", "upside", "potential"
    }

    NEGATIVE_WORDS = {
        "weak", "decline", "decrease", "fall", "drop", "loss",
        "negative", "bearish", "weakness", "concern", "risk",
        "challenge", "problem", "difficult", "struggle", "pain",
        "downside", "headwind", "pressure", "slowing", "down",
        "worse", "worst", "poor", "terrible", "awful",
        "threats", "disadvantage", "downside", "deterioration", "stress"
    }

    INTENSITY_MODIFIERS = {
        "very": 1.3,
        "extremely": 1.5,
        "significantly": 1.4,
        "dramatically": 1.5,
        "substantially": 1.3,
        "barely": 0.5,
        "slightly": 0.7,
        "somewhat": 0.8,
    }

    def __init__(self):
        """Initialize sentiment analyzer."""
        self.positive_words = self.POSITIVE_WORDS
        self.negative_words = self.NEGATIVE_WORDS

    def analyze(self, text: str) -> str:
        """
        Analyze sentiment of text.

        Returns:
            "positive", "negative", or "neutral"
        """
        score = self._calculate_sentiment_score(text)

        if score > 0.1:
            return Sentiment.POSITIVE
        elif score < -0.1:
            return Sentiment.NEGATIVE
        else:
            return Sentiment.NEUTRAL

    def _calculate_sentiment_score(self, text: str) -> float:
        """
        Calculate sentiment score (-1 to 1).

        Returns:
            Float between -1 (most negative) and 1 (most positive)
        """
        words = text.lower().split()
        score = 0.0
        total_weight = 0.0

        for i, word in enumerate(words):
            word_clean = word.strip('.,!?;:')

            # Check for negation
            negation = False
            if i > 0:
                prev_word = words[i-1].strip('.,!?;:')
                if prev_word in ["not", "no", "never", "neither", "nobody"]:
                    negation = True

            # Calculate sentiment
            if word_clean in self.positive_words:
                word_score = 1.0
                if negation:
                    word_score = -0.5  # Negated positive becomes slightly negative
            elif word_clean in self.negative_words:
                word_score = -1.0
                if negation:
                    word_score = 0.5  # Negated negative becomes slightly positive
            else:
                continue

            # Apply intensity modifiers
            intensity = 1.0
            if i > 0:
                prev_word = words[i-1].strip('.,!?;:')
                if prev_word in self.INTENSITY_MODIFIERS:
                    intensity = self.INTENSITY_MODIFIERS[prev_word]

            score += word_score * intensity
            total_weight += intensity

        # Normalize score
        if total_weight > 0:
            score = score / total_weight
            # Clamp to [-1, 1]
            score = max(-1.0, min(1.0, score))

        return score

    def analyze_comparative(self, text: str) -> str:
        """
        Analyze sentiment with comparison detection.

        Detects patterns like "better than", "worse than", etc.
        """
        # First pass: standard sentiment
        base_sentiment = self.analyze(text)

        # Check for comparative language
        comparatives = {
            "better": Sentiment.POSITIVE,
            "worse": Sentiment.NEGATIVE,
            "higher": Sentiment.POSITIVE,
            "lower": Sentiment.NEGATIVE,
            "stronger": Sentiment.POSITIVE,
            "weaker": Sentiment.NEGATIVE,
        }

        text_lower = text.lower()
        for comparative, sentiment in comparatives.items():
            if f"{comparative} than" in text_lower:
                return sentiment

        return base_sentiment

def analyze_mention_sentiment(mention_context: str) -> str:
    """
    Analyze sentiment of a specific mention context.

    Args:
        mention_context: Text containing the mention

    Returns:
        Sentiment string ("positive", "negative", "neutral")
    """
    analyzer = SentimentAnalyzer()
    return analyzer.analyze(mention_context)

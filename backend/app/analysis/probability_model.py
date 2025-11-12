"""Probability modeling for mispricing detection."""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from scipy import stats

logger = logging.getLogger(__name__)

class ProbabilityModel:
    """Statistical model for calculating implied probability from transcripts."""

    def __init__(self, model_version: str = "v1.0"):
        """Initialize probability model."""
        self.model_version = model_version
        self.mention_weight = 0.7
        self.sentiment_weight = 0.2
        self.recency_weight = 0.1

    def calculate_base_probability(
        self,
        mentions: List[Dict],
        transcript_dates: List[datetime],
    ) -> Tuple[float, Dict]:
        """
        Calculate base probability from mentions and context.

        Args:
            mentions: List of mention dictionaries with keyword, confidence, sentiment
            transcript_dates: List of dates for each mention

        Returns:
            Tuple of (probability, analysis_dict)
        """
        if not mentions:
            return 0.5, {"reason": "no_mentions", "confidence": 0.0}

        # Separate by sentiment
        positive_mentions = [m for m in mentions if m.get("sentiment") == "positive"]
        negative_mentions = [m for m in mentions if m.get("sentiment") == "negative"]
        neutral_mentions = [m for m in mentions if m.get("sentiment") == "neutral"]

        total_mentions = len(mentions)

        # Calculate weights
        positive_ratio = len(positive_mentions) / total_mentions if total_mentions > 0 else 0
        negative_ratio = len(negative_mentions) / total_mentions if total_mentions > 0 else 0

        # Confidence scores
        avg_confidence = np.mean([m.get("confidence", 0.5) for m in mentions])

        # Base probability from sentiment
        sentiment_probability = (0.5 + positive_ratio * 0.4 - negative_ratio * 0.4)
        sentiment_probability = max(0.01, min(0.99, sentiment_probability))

        # Boost by confidence
        final_probability = self._apply_confidence_boost(
            sentiment_probability,
            avg_confidence,
            total_mentions
        )

        analysis = {
            "total_mentions": total_mentions,
            "positive_mentions": len(positive_mentions),
            "negative_mentions": len(negative_mentions),
            "neutral_mentions": len(neutral_mentions),
            "positive_ratio": round(positive_ratio, 2),
            "negative_ratio": round(negative_ratio, 2),
            "average_confidence": round(avg_confidence, 2),
            "sentiment_probability": round(sentiment_probability, 2),
        }

        return round(final_probability, 2), analysis

    def _apply_confidence_boost(self, base_prob: float, avg_confidence: float, mention_count: int) -> float:
        """Apply confidence boost based on mention strength and count."""
        # More mentions increase confidence
        count_factor = min(1.0, np.log(mention_count + 1) / np.log(20))

        # Higher confidence increases effect
        confidence_factor = avg_confidence

        # Combined boost
        boost = (confidence_factor * count_factor) * 0.2  # Max 20% boost

        final_prob = base_prob + boost if base_prob > 0.5 else base_prob - boost

        return max(0.01, min(0.99, final_prob))

    def calculate_mispricing(
        self,
        base_probability: float,
        market_probability: float,
        confidence: float
    ) -> Dict:
        """
        Calculate mispricing metrics.

        Args:
            base_probability: Model's calculated probability (0-1)
            market_probability: Current market probability (0-1)
            confidence: Model confidence in the calculation (0-1)

        Returns:
            Mispricing analysis dictionary.
        """
        # Calculate mispricing ratio
        if market_probability > 0:
            mispricing_ratio = base_probability / market_probability
        else:
            mispricing_ratio = 1.0

        # Mispricing percentage
        mispricing_pct = abs(base_probability - market_probability) * 100

        # Determine recommendation
        recommendation = self._get_recommendation(
            base_probability,
            market_probability,
            mispricing_pct,
            confidence
        )

        # Expected value if betting at market price
        ev_yes = (base_probability * 1.0) + ((1 - base_probability) * -market_probability)
        ev_no = ((1 - base_probability) * 1.0) + (base_probability * -(1 - market_probability))

        return {
            "base_probability": round(base_probability, 4),
            "market_probability": round(market_probability, 4),
            "mispricing_ratio": round(mispricing_ratio, 2),
            "mispricing_percentage": round(mispricing_pct, 2),
            "expected_value_yes": round(ev_yes, 4),
            "expected_value_no": round(ev_no, 4),
            "recommendation": recommendation,
            "confidence": round(confidence, 2),
        }

    def _get_recommendation(
        self,
        base_prob: float,
        market_prob: float,
        mispricing_pct: float,
        confidence: float
    ) -> str:
        """Determine trading recommendation."""
        # Need meaningful mispricing to recommend
        min_mispricing = 5.0  # 5% minimum
        min_confidence = 0.5

        if mispricing_pct < min_mispricing or confidence < min_confidence:
            return "neutral"

        # Market thinks YES more likely than model
        if market_prob > base_prob:
            return "buy_no"  # YES is overpriced, buy NO
        else:
            return "buy_yes"  # YES is underpriced, buy YES

    def calculate_kelly_fraction(
        self,
        base_probability: float,
        odds: float,
        confidence: float
    ) -> float:
        """
        Calculate Kelly Criterion bet sizing.

        Kelly Criterion: f* = (bp - q) / b
        where b = odds-1, p = win probability, q = loss probability

        Args:
            base_probability: Model's calculated win probability
            odds: Decimal odds
            confidence: Model confidence (affects bet sizing)

        Returns:
            Recommended fraction of bankroll to bet (0-1)
        """
        if odds <= 1:
            return 0.0

        b = odds - 1
        p = base_probability
        q = 1 - base_probability

        kelly_fraction = (b * p - q) / b

        # Apply confidence as damping factor (fractional Kelly)
        damped_kelly = kelly_fraction * confidence

        # Cap at reasonable maximum
        return max(0.0, min(0.25, damped_kelly))

    def calculate_confidence_interval(
        self,
        mentions: List[Dict],
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculate confidence interval for probability estimate.

        Args:
            mentions: List of mention dictionaries
            confidence_level: Desired confidence level (0.95 = 95%)

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if not mentions:
            return (0.25, 0.75)  # Wide interval if no data

        confidences = [m.get("confidence", 0.5) for m in mentions]
        n = len(mentions)

        # Use bootstrap-style confidence interval
        mean_confidence = np.mean(confidences)
        std_error = np.std(confidences) / np.sqrt(n) if n > 1 else 0.2

        # Z-score for 95% confidence
        z_score = stats.norm.ppf((1 + confidence_level) / 2)

        margin_of_error = z_score * std_error

        lower = max(0.01, mean_confidence - margin_of_error)
        upper = min(0.99, mean_confidence + margin_of_error)

        return (round(lower, 2), round(upper, 2))


class BayesianModel:
    """Bayesian approach to probability estimation."""

    def __init__(self, prior: float = 0.5):
        """Initialize Bayesian model with prior belief."""
        self.prior = prior

    def update_belief(
        self,
        prior: float,
        likelihood_yes: float,
        likelihood_no: float
    ) -> float:
        """
        Update belief using Bayes theorem.

        P(Yes|Evidence) = P(Evidence|Yes) * P(Yes) / P(Evidence)
        """
        posterior_yes = (likelihood_yes * prior)
        posterior_no = (likelihood_no * (1 - prior))

        total = posterior_yes + posterior_no
        if total == 0:
            return prior

        return posterior_yes / total

    def calculate_likelihood_from_mentions(
        self,
        positive_mentions: int,
        negative_mentions: int,
        total_mentions: int
    ) -> Tuple[float, float]:
        """
        Calculate likelihood of YES and NO based on mention sentiment.

        Returns:
            Tuple of (likelihood_yes, likelihood_no)
        """
        if total_mentions == 0:
            return (0.5, 0.5)

        # Beta distribution approach
        alpha_yes = positive_mentions + 1
        beta_yes = negative_mentions + 1

        # Likelihood of observing positive mentions if event is likely to occur
        likelihood_yes = alpha_yes / (alpha_yes + beta_yes)
        likelihood_no = beta_yes / (alpha_yes + beta_yes)

        return (likelihood_yes, likelihood_no)

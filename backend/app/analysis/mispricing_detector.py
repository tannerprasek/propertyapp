"""Detect and rank mispriced prediction market opportunities."""

import logging
from typing import List, Dict
from datetime import datetime

from app.analysis.probability_model import ProbabilityModel

logger = logging.getLogger(__name__)

class MispricingDetector:
    """Identify mispriced market opportunities."""

    def __init__(self):
        """Initialize detector."""
        self.model = ProbabilityModel()

    def rank_opportunities(
        self,
        market_analyses: List[Dict],
        min_mispricing: float = 0.05,
        min_confidence: float = 0.5
    ) -> List[Dict]:
        """
        Rank mispriced opportunities.

        Args:
            market_analyses: List of market analysis results
            min_mispricing: Minimum mispricing percentage (0.05 = 5%)
            min_confidence: Minimum model confidence to include

        Returns:
            Sorted list of opportunities, best first.
        """
        opportunities = []

        for analysis in market_analyses:
            mispricing_result = analysis.get("mispricing", {})

            mispricing_pct = mispricing_result.get("mispricing_percentage", 0)
            confidence = mispricing_result.get("confidence", 0)
            recommendation = mispricing_result.get("recommendation", "neutral")

            # Filter by thresholds
            if mispricing_pct < (min_mispricing * 100) or confidence < min_confidence:
                continue

            if recommendation == "neutral":
                continue

            # Calculate opportunity score
            opportunity_score = self._calculate_opportunity_score(
                mispricing_pct,
                confidence,
                analysis.get("mentions", {}).get("total_mentions", 0)
            )

            opportunities.append({
                "market_id": analysis.get("market_id"),
                "market_title": analysis.get("market_title"),
                "company": analysis.get("company"),
                "ticker": analysis.get("ticker"),
                "base_probability": mispricing_result.get("base_probability"),
                "market_probability": mispricing_result.get("market_probability"),
                "mispricing_percentage": mispricing_pct,
                "recommendation": recommendation,
                "confidence": confidence,
                "opportunity_score": opportunity_score,
                "mention_count": analysis.get("mentions", {}).get("total_mentions", 0),
                "explanation": self._generate_explanation(analysis),
                "kelly_fraction": mispricing_result.get("kelly_fraction", 0),
            })

        # Sort by opportunity score descending
        opportunities.sort(key=lambda x: x["opportunity_score"], reverse=True)

        return opportunities

    def _calculate_opportunity_score(
        self,
        mispricing_pct: float,
        confidence: float,
        mention_count: int
    ) -> float:
        """Calculate composite opportunity score."""
        # Normalize inputs
        mispricing_score = min(mispricing_pct / 50, 1.0)  # Max at 50% mispricing
        confidence_score = confidence
        mention_score = min(mention_count / 20, 1.0)  # Max at 20 mentions

        # Weighted combination
        weights = {
            "mispricing": 0.5,
            "confidence": 0.3,
            "mentions": 0.2,
        }

        score = (
            mispricing_score * weights["mispricing"] +
            confidence_score * weights["confidence"] +
            mention_score * weights["mentions"]
        )

        return round(score, 3)

    def _generate_explanation(self, analysis: Dict) -> str:
        """Generate human-readable explanation of opportunity."""
        market_title = analysis.get("market_title", "Unknown Market")
        recommendation = analysis.get("mispricing", {}).get("recommendation", "neutral")
        mispricing_pct = analysis.get("mispricing", {}).get("mispricing_percentage", 0)
        positive_mentions = analysis.get("mentions", {}).get("positive_mentions", 0)
        negative_mentions = analysis.get("mentions", {}).get("negative_mentions", 0)

        if recommendation == "buy_yes":
            return (
                f"Market underprices 'YES' on {market_title}. "
                f"{positive_mentions} positive vs {negative_mentions} negative mentions in transcripts. "
                f"Mispricing: {mispricing_pct:.1f}%"
            )
        elif recommendation == "buy_no":
            return (
                f"Market overprices 'YES' on {market_title}. "
                f"{negative_mentions} negative vs {positive_mentions} positive mentions in transcripts. "
                f"Mispricing: {mispricing_pct:.1f}%"
            )
        else:
            return "No clear mispricing identified."

class OpportunitySummary:
    """Generate summary of scan results."""

    def __init__(self, opportunities: List[Dict]):
        """Initialize with opportunities."""
        self.opportunities = opportunities

    def get_top_opportunities(self, n: int = 5) -> List[Dict]:
        """Get top N opportunities."""
        return self.opportunities[:n]

    def get_summary_stats(self) -> Dict:
        """Get summary statistics."""
        if not self.opportunities:
            return {
                "total_opportunities": 0,
                "avg_mispricing": 0,
                "avg_confidence": 0,
                "buy_yes_count": 0,
                "buy_no_count": 0,
            }

        mispricing_values = [o["mispricing_percentage"] for o in self.opportunities]
        confidence_values = [o["confidence"] for o in self.opportunities]
        recommendation_counts = {}

        for opp in self.opportunities:
            rec = opp["recommendation"]
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1

        return {
            "total_opportunities": len(self.opportunities),
            "avg_mispricing": round(sum(mispricing_values) / len(mispricing_values), 2),
            "avg_confidence": round(sum(confidence_values) / len(confidence_values), 2),
            "buy_yes_count": recommendation_counts.get("buy_yes", 0),
            "buy_no_count": recommendation_counts.get("buy_no", 0),
            "top_opportunity": self.opportunities[0] if self.opportunities else None,
        }

    def to_csv(self, filename: str):
        """Export opportunities to CSV."""
        import csv

        if not self.opportunities:
            return

        keys = self.opportunities[0].keys()

        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.opportunities)

        logger.info(f"Exported {len(self.opportunities)} opportunities to {filename}")

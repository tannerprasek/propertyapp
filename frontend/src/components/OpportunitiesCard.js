import React from 'react';
import './OpportunitiesCard.css';

function OpportunitiesCard({ opportunities }) {
  const topOpportunities = opportunities.slice(0, 10);

  if (!topOpportunities.length) {
    return (
      <div className="card">
        <h3>Mispriced Opportunities</h3>
        <div className="empty-state">
          <p>No opportunities found. Run a scan to get started.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h3>Mispriced Opportunities</h3>
      <div className="opportunities-list">
        {topOpportunities.map((opp, idx) => (
          <div key={idx} className="opportunity-item">
            <div className="opportunity-header">
              <div>
                <h4>{opp.market_title}</h4>
                <p className="company-ticker">{opp.company} ({opp.ticker})</p>
              </div>
              <div className={`recommendation ${opp.recommendation}`}>
                {opp.recommendation === 'buy_yes' ? '👍 YES' : '👎 NO'}
              </div>
            </div>

            <div className="opportunity-metrics">
              <div className="metric">
                <span className="label">Model Prob</span>
                <span className="value">{(opp.base_probability * 100).toFixed(1)}%</span>
              </div>
              <div className="metric">
                <span className="label">Market Prob</span>
                <span className="value">{(opp.market_probability * 100).toFixed(1)}%</span>
              </div>
              <div className="metric">
                <span className="label">Mispricing</span>
                <span className="value">{opp.mispricing_percentage.toFixed(1)}%</span>
              </div>
              <div className="metric">
                <span className="label">Confidence</span>
                <span className="value">{(opp.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>

            <div className="opportunity-explanation">
              {opp.explanation}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default OpportunitiesCard;

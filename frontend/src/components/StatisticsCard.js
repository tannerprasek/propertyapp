import React from 'react';
import './StatisticsCard.css';

function StatisticsCard({ opportunities }) {
  const stats = {
    total: opportunities.length,
    buyYes: opportunities.filter(o => o.recommendation === 'buy_yes').length,
    buyNo: opportunities.filter(o => o.recommendation === 'buy_no').length,
    avgMispricing: opportunities.length > 0
      ? (opportunities.reduce((sum, o) => sum + o.mispricing_percentage, 0) / opportunities.length).toFixed(1)
      : 0,
    avgConfidence: opportunities.length > 0
      ? (opportunities.reduce((sum, o) => sum + o.confidence, 0) / opportunities.length * 100).toFixed(0)
      : 0,
  };

  return (
    <div className="card">
      <h3>Summary Statistics</h3>
      <div className="stats-grid">
        <div className="stat-box">
          <span className="stat-label">Total Opportunities</span>
          <span className="stat-value">{stats.total}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Buy YES</span>
          <span className="stat-value">{stats.buyYes}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Buy NO</span>
          <span className="stat-value">{stats.buyNo}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Avg Mispricing</span>
          <span className="stat-value">{stats.avgMispricing}%</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Avg Confidence</span>
          <span className="stat-value">{stats.avgConfidence}%</span>
        </div>
      </div>
    </div>
  );
}

export default StatisticsCard;

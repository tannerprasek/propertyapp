import React, { useState } from 'react';
import './StockAnalysis.css';

function StockAnalysis() {
  const [ticker, setTicker] = useState('');
  const [loading, setLoading] = useState(false);
  const [markets, setMarkets] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);

  const searchMarkets = async () => {
    if (!ticker) {
      setError('Please enter a stock symbol');
      return;
    }

    setLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/markets/search/${ticker.toUpperCase()}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch markets');
      }

      const data = await response.json();
      setMarkets(data.markets || []);

      if (!data.markets || data.markets.length === 0) {
        setError('No Polymarket betting markets found for this stock symbol');
      }
    } catch (err) {
      setError(err.message);
      setMarkets([]);
    } finally {
      setLoading(false);
    }
  };

  const analyzeMarkets = async () => {
    if (!ticker || markets.length === 0) {
      setError('Please search for markets first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/analysis/analyze-ticker/${ticker.toUpperCase()}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      searchMarkets();
    }
  };

  return (
    <div className="stock-analysis">
      <div className="search-section">
        <h1>Polymarket Earnings Call Analysis</h1>
        <p className="subtitle">
          Search for betting markets on earnings call mentions and analyze historical probabilities
        </p>

        <div className="search-box">
          <input
            type="text"
            placeholder="Enter stock symbol (e.g., AAPL, TSLA, NVDA)"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            onKeyPress={handleKeyPress}
            className="ticker-input"
          />
          <button
            onClick={searchMarkets}
            disabled={loading || !ticker}
            className="btn btn-primary"
          >
            {loading ? 'Searching...' : 'Search Markets'}
          </button>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
      </div>

      {markets.length > 0 && (
        <div className="markets-section">
          <div className="section-header">
            <h2>Available Markets for {ticker}</h2>
            <button
              onClick={analyzeMarkets}
              disabled={loading}
              className="btn btn-success"
            >
              {loading ? 'Analyzing...' : 'Analyze All Markets'}
            </button>
          </div>

          <div className="markets-grid">
            {markets.map((market) => (
              <div key={market.market_id} className="market-card">
                <h3>{market.title}</h3>
                <p className="market-description">{market.description}</p>

                <div className="market-details">
                  <div className="odds-display">
                    <div className="odd-item yes">
                      <span className="label">YES</span>
                      <span className="value">{(market.current_yes_probability * 100).toFixed(1)}%</span>
                    </div>
                    <div className="odd-item no">
                      <span className="label">NO</span>
                      <span className="value">{(market.current_no_probability * 100).toFixed(1)}%</span>
                    </div>
                  </div>

                  {market.keywords && market.keywords.length > 0 && (
                    <div className="keywords">
                      <strong>Keywords:</strong>
                      <div className="keyword-tags">
                        {market.keywords.map((keyword, idx) => (
                          <span key={idx} className="keyword-tag">{keyword}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="market-stats">
                    <div className="stat">
                      <span className="stat-label">Volume:</span>
                      <span className="stat-value">${(market.volume || 0).toLocaleString()}</span>
                    </div>
                    <div className="stat">
                      <span className="stat-label">Liquidity:</span>
                      <span className="stat-value">${(market.liquidity || 0).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {analysis && (
        <div className="analysis-section">
          <h2>Analysis Results</h2>
          <div className="analysis-summary">
            <div className="summary-stat">
              <span className="stat-number">{analysis.transcripts_analyzed}</span>
              <span className="stat-label">Transcripts Analyzed</span>
            </div>
            <div className="summary-stat">
              <span className="stat-number">{analysis.total_mentions}</span>
              <span className="stat-label">Total Mentions Found</span>
            </div>
            <div className="summary-stat">
              <span className="stat-number">{analysis.opportunities?.length || 0}</span>
              <span className="stat-label">Mispriced Opportunities</span>
            </div>
          </div>

          {analysis.opportunities && analysis.opportunities.length > 0 && (
            <div className="opportunities-list">
              <h3>Identified Opportunities</h3>
              {analysis.opportunities.map((opp, idx) => (
                <div
                  key={idx}
                  className={`opportunity-card ${opp.recommendation === 'buy_yes' ? 'buy-yes' : opp.recommendation === 'buy_no' ? 'buy-no' : 'neutral'}`}
                >
                  <div className="opportunity-header">
                    <h4>{opp.market_title}</h4>
                    <span className={`recommendation-badge ${opp.recommendation}`}>
                      {opp.recommendation.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>

                  <div className="opportunity-details">
                    <div className="probability-comparison">
                      <div className="prob-item">
                        <span className="prob-label">Market Price</span>
                        <span className="prob-value market">{(opp.market_probability * 100).toFixed(1)}%</span>
                      </div>
                      <div className="prob-arrow">→</div>
                      <div className="prob-item">
                        <span className="prob-label">Model Probability</span>
                        <span className="prob-value model">{(opp.base_probability * 100).toFixed(1)}%</span>
                      </div>
                    </div>

                    <div className="metrics-grid">
                      <div className="metric">
                        <span className="metric-label">Mispricing:</span>
                        <span className="metric-value highlight">{opp.mispricing_percentage.toFixed(1)}%</span>
                      </div>
                      <div className="metric">
                        <span className="metric-label">Mentions:</span>
                        <span className="metric-value">{opp.mention_count}</span>
                      </div>
                      <div className="metric">
                        <span className="metric-label">Confidence:</span>
                        <span className="metric-value">{(opp.confidence * 100).toFixed(0)}%</span>
                      </div>
                    </div>

                    <p className="opportunity-explanation">{opp.explanation}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {(!analysis.opportunities || analysis.opportunities.length === 0) && (
            <div className="no-opportunities">
              <p>No significant mispricing detected based on historical transcript analysis.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default StockAnalysis;

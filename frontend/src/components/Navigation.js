import React from 'react';
import './Navigation.css';

function Navigation({ currentPage, setCurrentPage }) {
  return (
    <nav className="navbar">
      <div className="nav-container">
        <div className="nav-brand">
          <h1>📊 Polymarket Transcript Scanner</h1>
        </div>
        <ul className="nav-menu">
          <li>
            <button
              className={`nav-link ${currentPage === 'dashboard' ? 'active' : ''}`}
              onClick={() => setCurrentPage('dashboard')}
            >
              Dashboard
            </button>
          </li>
          <li>
            <button
              className={`nav-link ${currentPage === 'markets' ? 'active' : ''}`}
              onClick={() => setCurrentPage('markets')}
            >
              Markets
            </button>
          </li>
          <li>
            <button
              className={`nav-link ${currentPage === 'analysis' ? 'active' : ''}`}
              onClick={() => setCurrentPage('analysis')}
            >
              Analysis
            </button>
          </li>
        </ul>
      </div>
    </nav>
  );
}

export default Navigation;

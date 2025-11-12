import React, { useState } from 'react';
import './App.css';
import Dashboard from './pages/Dashboard';
import StockAnalysis from './pages/StockAnalysis';
import Navigation from './components/Navigation';
import { useStore } from './store/store';

function App() {
  const [currentPage, setCurrentPage] = useState('stock-analysis');
  const { loading, error } = useStore();

  return (
    <div className="App">
      <Navigation currentPage={currentPage} setCurrentPage={setCurrentPage} />
      <main className="main-content">
        {error && (
          <div className="error-banner">
            <p>{error}</p>
          </div>
        )}
        {loading && (
          <div className="loading-banner">
            <p>Loading...</p>
          </div>
        )}
        {currentPage === 'stock-analysis' && <StockAnalysis />}
        {currentPage === 'dashboard' && <Dashboard />}
      </main>
    </div>
  );
}

export default App;

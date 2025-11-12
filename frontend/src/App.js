import React, { useState, useEffect } from 'react';
import './App.css';
import Dashboard from './pages/Dashboard';
import Navigation from './components/Navigation';
import { useStore } from './store/store';

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
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
        {currentPage === 'dashboard' && <Dashboard />}
      </main>
    </div>
  );
}

export default App;

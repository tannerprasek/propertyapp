import React, { useEffect } from 'react';
import './Dashboard.css';
import OpportunitiesCard from '../components/OpportunitiesCard';
import StatisticsCard from '../components/StatisticsCard';
import { useStore } from '../store/store';

function Dashboard() {
  const { fetchOpportunities, opportunities } = useStore();

  useEffect(() => {
    fetchOpportunities();
  }, [fetchOpportunities]);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h2>Dashboard</h2>
        <div className="dashboard-actions">
          <button className="btn btn-primary" onClick={fetchOpportunities}>
            Refresh Data
          </button>
        </div>
      </header>

      <div className="dashboard-grid">
        <StatisticsCard opportunities={opportunities} />
        <OpportunitiesCard opportunities={opportunities} />
      </div>
    </div>
  );
}

export default Dashboard;

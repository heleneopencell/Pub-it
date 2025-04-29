import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

const LandingPage = () => {
  const navigate = useNavigate();
  const [loadingStates, setLoadingStates] = useState({
    pubmed: false,
    citations: false
  });

  const handleRunScript = async (script) => {
    const scriptType = script === 'pubmed_tracker.py' ? 'pubmed' : 'citations';
    try {
      setLoadingStates(prev => ({ ...prev, [scriptType]: true }));
      
      // Run the script and wait for it to complete
      await api.scripts.run(script);
      
      // After script completes, wait a moment for files to be updated
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Navigate to the appropriate page and force a data refresh
      if (script === 'pubmed_tracker.py') {
        navigate('/publications', { 
          state: { 
            forceRefresh: true,
            timestamp: Date.now() 
          }
        });
      } else if (script === 'scholar_citations.py') {
        navigate('/citations', { 
          state: { 
            forceRefresh: true,
            timestamp: Date.now() 
          }
        });
      }
    } catch (error) {
      console.error(`Error running ${script}:`, error);
      alert(`Failed to run ${script}. Please check the console for details.`);
    } finally {
      setLoadingStates(prev => ({ ...prev, [scriptType]: false }));
    }
  };

  return (
    <div className="landing-page">
      <h1 className="title">Pub-it</h1>
      <p className="subtitle">
        Tracks your community's latest papers, collaborations and spot the most cited ones.
      </p>

      <div className="actions-grid">
        <div className="action-card">
          <h2>Track Publications</h2>
          <p>Fetch the latest publications from PubMed for all researchers</p>
          <button
            className="action-button"
            onClick={() => handleRunScript('pubmed_tracker.py')}
            disabled={loadingStates.pubmed || loadingStates.citations}
          >
            {loadingStates.pubmed ? 'Running...' : 'Run (pubmed_tracker.py)'}
          </button>
        </div>

        <div className="action-card">
          <h2>Update Citations</h2>
          <p>Get the latest citation counts from Google Scholar</p>
          <button
            className="action-button"
            onClick={() => handleRunScript('scholar_citations.py')}
            disabled={loadingStates.pubmed || loadingStates.citations}
          >
            {loadingStates.citations ? 'Running...' : 'Run (scholar_citations.py)'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LandingPage; 
import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import api from '../api';

const PublicationsList = () => {
  const location = useLocation();
  const [publications, setPublications] = useState([]);
  const [filteredPublications, setFilteredPublications] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [lastFetchTime, setLastFetchTime] = useState(0);
  const [sortConfig, setSortConfig] = useState({
    key: 'citations',
    direction: 'desc'
  });

  const fetchPublications = async (isInitial = false, force = false) => {
    // Prevent fetching if less than 5 seconds have passed since last fetch
    // unless it's forced or initial load
    const now = Date.now();
    if (!force && !isInitial && now - lastFetchTime < 5000) {
      return;
    }

    try {
      if (isInitial) setLoading(true);
      const response = await api.publications.getAll();
      // The response is already the publications array
      const publicationsArray = Array.isArray(response) ? response : [];
      console.log('Fetched publications:', publicationsArray); // Debug log
      setPublications(publicationsArray);
      setFilteredPublications(publicationsArray);
      setLastFetchTime(now);
    } catch (err) {
      console.error('Error fetching publications:', err);
      setError(err.message);
    } finally {
      if (isInitial) setLoading(false);
      setIsUpdating(false);
    }
  };

  useEffect(() => {
    // Check if we should force refresh based on navigation state
    const shouldForceRefresh = location.state?.forceRefresh;
    fetchPublications(true, shouldForceRefresh);
  }, [location.state?.timestamp]); // Only re-run if timestamp changes

  useEffect(() => {
    if (!search.trim()) {
      setFilteredPublications(publications);
      return;
    }
    const lower = search.toLowerCase();
    setFilteredPublications(
      publications.filter(pub =>
        (pub.title && pub.title.toLowerCase().includes(lower)) ||
        (pub.journal && pub.journal.toLowerCase().includes(lower)) ||
        (pub.doi && pub.doi.toLowerCase().includes(lower)) ||
        (Array.isArray(pub.authors) && pub.authors.some(author => author.toLowerCase().includes(lower)))
      )
    );
  }, [search, publications]);

  // Sorting function
  const sortPublications = (pubs, config) => {
    if (!Array.isArray(pubs)) return [];
    
    return [...pubs].sort((a, b) => {
      if (config.key === 'publication_date') {
        const dateA = new Date(a[config.key] || '1900-01-01');
        const dateB = new Date(b[config.key] || '1900-01-01');
        return config.direction === 'asc' ? dateA - dateB : dateB - dateA;
      }
      
      if (config.key === 'citations') {
        const citA = parseInt(a[config.key]) || 0;
        const citB = parseInt(b[config.key]) || 0;
        return config.direction === 'asc' ? citA - citB : citB - citA;
      }

      if (config.key === 'researcher_name') {
        const nameA = a[config.key] || '';
        const nameB = b[config.key] || '';
        return config.direction === 'asc' 
          ? nameA.localeCompare(nameB)
          : nameB.localeCompare(nameA);
      }

      const valueA = a[config.key] || '';
      const valueB = b[config.key] || '';
      return config.direction === 'asc' 
        ? valueA.localeCompare(valueB)
        : valueB.localeCompare(valueA);
    });
  };

  // Handle column header click for sorting
  const handleSort = (key) => {
    setSortConfig(prevConfig => ({
      key,
      direction: prevConfig.key === key && prevConfig.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  // Get sort direction indicator
  const getSortIndicator = (key) => {
    if (sortConfig.key !== key) return '↕';
    return sortConfig.direction === 'asc' ? '↑' : '↓';
  };

  // Apply sorting to filtered publications
  const sortedPublications = sortPublications(filteredPublications, sortConfig);

  // Expose a function to trigger update externally (e.g. from LandingPage)
  PublicationsList.updatePublications = (force = false) => {
    setIsUpdating(true);
    fetchPublications(false, force);
  };

  if (loading) return <div>Loading publications...</div>;
  if (error) return <div>Error: {error}</div>;

  // Helper to format date as Month Year
  const formatMonthYear = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleString('default', { month: 'short', year: 'numeric' });
  };

  return (
    <div className="publications-list-table-container">
      <div className="search-bar" style={{ marginBottom: '1.5rem' }}>
        <input
          type="text"
          placeholder="Search by title, journal, DOI, or author..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ width: '100%', padding: '0.75rem', borderRadius: '4px', border: '1px solid #333', fontSize: '1rem' }}
        />
      </div>
      {isUpdating && <div className="status-message">Updating publications...</div>}
      <table className="publications-list-table">
        <thead>
          <tr>
            <th onClick={() => handleSort('publication_date')} style={{ cursor: 'pointer' }}>
              Date {getSortIndicator('publication_date')}
            </th>
            <th onClick={() => handleSort('title')} style={{ cursor: 'pointer' }}>
              Title {getSortIndicator('title')}
            </th>
            <th onClick={() => handleSort('authors')} style={{ cursor: 'pointer' }}>
              Authors {getSortIndicator('authors')}
            </th>
            <th onClick={() => handleSort('journal')} style={{ cursor: 'pointer' }}>
              Journal {getSortIndicator('journal')}
            </th>
            <th onClick={() => handleSort('doi')} style={{ cursor: 'pointer' }}>
              DOI {getSortIndicator('doi')}
            </th>
            <th onClick={() => handleSort('citations')} style={{ cursor: 'pointer' }}>
              Citations {getSortIndicator('citations')}
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedPublications.map((pub) => (
            <tr key={pub.doi || pub.title}>
              <td>{formatMonthYear(pub.publication_date)}</td>
              <td>{pub.title}</td>
              <td>{Array.isArray(pub.authors) ? pub.authors.join(', ') : ''}</td>
              <td>{pub.journal}</td>
              <td>
                {pub.doi ? (
                  <a href={`https://doi.org/${pub.doi.replace('https://doi.org/', '')}`} target="_blank" rel="noopener noreferrer">
                    {pub.doi.replace('https://doi.org/', '')}
                  </a>
                ) : ''}
              </td>
              <td>{parseInt(pub.citations) || 0}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default PublicationsList; 
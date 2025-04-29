import React, { useState, useEffect } from 'react';
import { researchersApi } from '../api';
import { publicationsApi } from '../api';

const MembersList = () => {
  const [researchers, setResearchers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [formError, setFormError] = useState(null);
  const [newName, setNewName] = useState('');
  const [newOrcid, setNewOrcid] = useState('');
  const [newDepartment, setNewDepartment] = useState('');
  const [newUniversity, setNewUniversity] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isUpdating, setIsUpdating] = useState(false);
  const [editingResearcher, setEditingResearcher] = useState(null);
  const [lastFetchTime, setLastFetchTime] = useState(0);

  const fetchResearchers = async (isInitial = false, force = false) => {
    // Prevent fetching if less than 5 seconds have passed since last fetch
    const now = Date.now();
    if (!force && !isInitial && now - lastFetchTime < 5000) {
      return;
    }

    try {
      if (isInitial) setLoading(true);
      const data = await researchersApi.getAll();
      console.log('Fetched researchers:', data); // Debug log
      setResearchers(data.researchers || []);
      setLastFetchTime(now);
    } catch (err) {
      console.error('Error fetching researchers:', err); // Debug log
      setError(err.message);
    } finally {
      if (isInitial) setLoading(false);
      setIsUpdating(false);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    setFormError(null); // Clear previous form errors
    try {
      await researchersApi.add({ 
        name: newName, 
        orcid: newOrcid, 
        department: newDepartment,
        university: newUniversity 
      });
      setNewName('');
      setNewOrcid('');
      setNewDepartment('');
      setNewUniversity('');
      await fetchResearchers(false, true); // Force refresh after adding
    } catch (err) {
      if (err.message.includes('already exists')) {
        setFormError('Already a member');
      } else {
        setFormError(err.message);
      }
    }
  };

  const handleDelete = async (name, orcid) => {
    if (window.confirm(`Are you sure you want to remove ${name}?`)) {
      try {
        await researchersApi.delete(name, orcid);
        await fetchResearchers(false, true); // Force refresh after deleting
      } catch (err) {
        setError(err.message);
      }
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    try {
      const results = await researchersApi.search(searchQuery);
      setSearchResults(results);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSearchChange = async (e) => {
    const value = e.target.value;
    setSearchQuery(value);
    if (!value.trim()) {
      // If search field is emptied, refresh the full list
      await fetchResearchers(false, true); // Force refresh when clearing search
    }
  };

  const handleEdit = (researcher) => {
    setEditingResearcher({
      ...researcher,
      isEditing: true
    });
  };

  const handleCancelEdit = () => {
    setEditingResearcher(null);
  };

  const handleSaveEdit = async (orcid) => {
    try {
      await researchersApi.update(orcid, {
        name: editingResearcher.name,
        orcid: editingResearcher.orcid,
        department: editingResearcher.department,
        university: editingResearcher.university
      });
      setEditingResearcher(null);
      await fetchResearchers(false, true); // Force refresh after editing
    } catch (err) {
      setError(err.message);
    }
  };

  const handleEditFieldChange = (field, value) => {
    setEditingResearcher(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleDownloadPublications = async (orcid) => {
    try {
      const blob = await publicationsApi.download(orcid);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `publications_${orcid}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to download publications: ' + err.message);
    }
  };

  useEffect(() => {
    fetchResearchers(true);
  }, []);

  // Expose a function to trigger update externally (e.g. from LandingPage)
  MembersList.updateResearchers = () => {
    setIsUpdating(true);
    fetchResearchers(false);
  };

  if (loading) return <div className="loading">Loading researchers...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="members-container">
      <h1>Members</h1>
      
      <div className="members-grid">
        <div className="add-researcher-panel">
          <h2>Add Researcher</h2>
          <form onSubmit={handleAdd} className="add-form">
            <div className="form-group">
              <label htmlFor="name">Name:</label>
              <input
                type="text"
                id="name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Enter researcher name"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="orcid">ORCID:</label>
              <input
                type="text"
                id="orcid"
                value={newOrcid}
                onChange={(e) => setNewOrcid(e.target.value)}
                placeholder="0000-0000-0000-0000"
                pattern="\d{4}-\d{4}-\d{4}-\d{4}"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="department">Department:</label>
              <input
                type="text"
                id="department"
                value={newDepartment}
                onChange={(e) => setNewDepartment(e.target.value)}
                placeholder="Enter department (optional)"
              />
            </div>
            <div className="form-group">
              <label htmlFor="university">University:</label>
              <input
                type="text"
                id="university"
                value={newUniversity}
                onChange={(e) => setNewUniversity(e.target.value)}
                placeholder="Enter university (optional)"
              />
            </div>
            <button type="submit" className="add-button">Add Researcher</button>
            {formError && (
              <div className="form-error">{formError}</div>
            )}
          </form>
        </div>

        <div className="researchers-panel">
          {isUpdating && <div className="status-message">Updating researchers...</div>}
          <div className="search-bar">
            <form onSubmit={handleSearch}>
              <input
                type="text"
                value={searchQuery}
                onChange={handleSearchChange}
                placeholder="Search researchers..."
              />
              <button type="submit">Search</button>
            </form>
          </div>

          <div className="researchers-list">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Department</th>
                  <th>University</th>
                  <th>ORCID</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {researchers && researchers.map((researcher) => (
                  <tr key={`${researcher.name}-${researcher.orcid}`}>
                    {editingResearcher?.orcid === researcher.orcid ? (
                      <>
                        <td>
                          <input
                            type="text"
                            value={editingResearcher.name}
                            onChange={(e) => handleEditFieldChange('name', e.target.value)}
                          />
                        </td>
                        <td>
                          <input
                            type="text"
                            value={editingResearcher.department || ''}
                            onChange={(e) => handleEditFieldChange('department', e.target.value)}
                          />
                        </td>
                        <td>
                          <input
                            type="text"
                            value={editingResearcher.university || ''}
                            onChange={(e) => handleEditFieldChange('university', e.target.value)}
                          />
                        </td>
                        <td>{researcher.orcid}</td>
                        <td>
                          <button
                            onClick={() => handleSaveEdit(researcher.orcid)}
                            className="save-button"
                          >
                            Save
                          </button>
                          <button
                            onClick={handleCancelEdit}
                            className="cancel-button"
                          >
                            Cancel
                          </button>
                        </td>
                      </>
                    ) : (
                      <>
                        <td>{researcher.name}</td>
                        <td>{researcher.department || ''}</td>
                        <td>{researcher.university || ''}</td>
                        <td>
                          <a 
                            href={`https://orcid.org/${researcher.orcid}`}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {researcher.orcid}
                          </a>
                        </td>
                        <td>
                          <button
                            onClick={() => handleEdit(researcher)}
                            className="edit-button"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(researcher.name, researcher.orcid)}
                            className="delete-button"
                          >
                            Delete
                          </button>
                          <button
                            onClick={() => handleDownloadPublications(researcher.orcid)}
                            className="download-button"
                          >
                            Download Publications
                          </button>
                        </td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
            {researchers && researchers.length === 0 && (
              <div className="no-results">No researchers found</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MembersList; 
/**
 * API Service for handling all backend communication
 */

const API_CONFIG = {
  BASE_URL: 'http://localhost:8000/api',
  HEALTH_URL: 'http://localhost:8000/health',
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
};

/**
 * Custom fetch wrapper to handle common API interaction patterns
 * @param {string} endpoint - API endpoint to call
 * @param {Object} options - Request options
 * @param {string} options.method - HTTP method (GET, POST, PUT, DELETE)
 * @param {Object} options.body - Request body (will be JSON stringified)
 * @param {Object} options.headers - Custom headers
 * @param {string} options.errorMessage - Custom error message
 * @returns {Promise<any>} - Parsed JSON response
 */
const apiRequest = async (endpoint, options = {}) => {
  const {
    method = 'GET',
    body,
    headers = {},
    errorMessage = `Failed to ${method.toLowerCase()} ${endpoint}`,
  } = options;
  
  const requestOptions = {
    method,
    headers: { ...API_CONFIG.DEFAULT_HEADERS, ...headers },
  };
  
  if (body) {
    requestOptions.body = JSON.stringify(body);
  }
  
  try {
    const response = await fetch(`${API_CONFIG.BASE_URL}${endpoint}`, requestOptions);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      const error = new Error(errorData?.message || errorMessage);
      error.status = response.status;
      error.data = errorData;
      throw error;
    }
    
    return response.json();
  } catch (error) {
    // Preserve original error but add our custom message if it's a network error
    if (!error.status) {
      error.message = `Network error: ${errorMessage}`;
    }
    throw error;
  }
};

/**
 * Publications API methods
 */
export const publicationsApi = {
  /**
   * Get all publications
   * @returns {Promise<Array>} - List of publications
   */
  getAll: () => apiRequest('/publications'),
  
  /**
   * Trigger publication synchronization
   * @returns {Promise<Object>} - Synchronization result
   */
  sync: () => apiRequest('/publications/sync', { 
    method: 'POST',
    errorMessage: 'Failed to synchronize publications'
  }),

  /**
   * Download publications for a specific researcher
   * @param {string} orcid - Researcher's ORCID
   * @returns {Promise<Blob>} - CSV file as blob
   */
  download: async (orcid) => {
    const response = await fetch(`${API_CONFIG.BASE_URL}/publications/${encodeURIComponent(orcid)}/download`);
    if (!response.ok) {
      throw new Error('Failed to download publications');
    }
    return response.blob();
  },
};

/**
 * Researchers API methods
 */
export const researchersApi = {
  /**
   * Get all researchers
   * @returns {Promise<Array>} - List of researchers
   */
  getAll: () => apiRequest('/researchers'),
  
  /**
   * Add a new researcher
   * @param {Object} researcher - Researcher data
   * @returns {Promise<Object>} - Added researcher
   */
  add: (researcher) => apiRequest('/researchers', {
    method: 'POST',
    body: researcher,
    errorMessage: 'Failed to add researcher'
  }),
  
  /**
   * Update an existing researcher
   * @param {string} orcid - Researcher ORCID identifier
   * @param {Object} researcher - Updated researcher data
   * @returns {Promise<Object>} - Updated researcher
   */
  update: (orcid, researcher) => apiRequest(`/researchers/${encodeURIComponent(orcid)}`, {
    method: 'PUT',
    body: researcher,
    errorMessage: 'Failed to update researcher'
  }),
  
  /**
   * Delete a researcher
   * @param {string} name - Researcher name
   * @param {string} orcid - Researcher ORCID identifier
   * @returns {Promise<Object>} - Deletion result
   */
  delete: (name, orcid) => apiRequest(
    `/researchers/${encodeURIComponent(name)}/${encodeURIComponent(orcid)}`,
    {
      method: 'DELETE',
      errorMessage: 'Failed to delete researcher'
    }
  ),
  
  /**
   * Search for researchers
   * @param {string} query - Search query
   * @returns {Promise<Array>} - Search results
   */
  search: (query) => apiRequest(
    `/researchers/search/${encodeURIComponent(query)}`,
    { errorMessage: 'Failed to search researchers' }
  ),
};

/**
 * Health check API methods
 */
export const healthApi = {
  /**
   * Check API health status
   * @returns {Promise<Object>} - Health status
   */
  check: async () => {
    try {
      const response = await fetch(API_CONFIG.HEALTH_URL);
      
      if (!response.ok) {
        throw new Error('API is not healthy');
      }
      
      return response.json();
    } catch (error) {
      error.message = error.message || 'API health check failed';
      throw error;
    }
  },
};

/**
 * Scripts API methods
 */
export const scriptsApi = {
  /**
   * Run a Python script
   * @param {string} scriptName - Name of the script to run
   * @returns {Promise<Object>} - Script execution result
   */
  run: (scriptName) => apiRequest(`/scripts/${encodeURIComponent(scriptName)}`, {
    method: 'POST',
    errorMessage: `Failed to run script: ${scriptName}`
  }),
};

// Export all API functions
export default {
  publications: publicationsApi,
  researchers: researchersApi,
  health: healthApi,
  scripts: scriptsApi,
}; 
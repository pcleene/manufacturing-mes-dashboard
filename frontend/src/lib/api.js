/**
 * API client for OEMPartner MES Backend
 * Manufacturing Group Malaysia
 */

const API_BASE = 'http://localhost:8000/api/v1';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;

  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API request failed: ${endpoint}`, error);
    throw error;
  }
}

/**
 * Telemetry API
 */
export const telemetryAPI = {
  /**
   * Get telemetry data with filters
   */
  async getTelemetry(params = {}) {
    const searchParams = new URLSearchParams();

    if (params.startDate) searchParams.set('start_date', params.startDate);
    if (params.endDate) searchParams.set('end_date', params.endDate);
    if (params.machineId) searchParams.set('machine_id', params.machineId);
    if (params.lineId) searchParams.set('line_id', params.lineId);
    if (params.status) searchParams.set('status', params.status);
    if (params.hasAlerts !== undefined) searchParams.set('has_alerts', params.hasAlerts);
    if (params.limit) searchParams.set('limit', params.limit);
    if (params.skip) searchParams.set('skip', params.skip);

    const query = searchParams.toString();
    return fetchAPI(`/telemetry${query ? '?' + query : ''}`);
  },

  /**
   * Get latest telemetry for all machines
   */
  async getLatest(params = {}) {
    const searchParams = new URLSearchParams();
    if (params.machineId) searchParams.set('machine_id', params.machineId);
    if (params.lineId) searchParams.set('line_id', params.lineId);

    const query = searchParams.toString();
    return fetchAPI(`/telemetry/latest${query ? '?' + query : ''}`);
  },

  /**
   * Get all machines
   */
  async getMachines(lineId = null) {
    const query = lineId ? `?line_id=${lineId}` : '';
    return fetchAPI(`/telemetry/machines${query}`);
  },

  /**
   * Get telemetry statistics
   */
  async getStats(params = {}) {
    const searchParams = new URLSearchParams();
    if (params.hours) searchParams.set('hours', params.hours);
    if (params.machineId) searchParams.set('machine_id', params.machineId);
    if (params.lineId) searchParams.set('line_id', params.lineId);

    const query = searchParams.toString();
    return fetchAPI(`/telemetry/stats${query ? '?' + query : ''}`);
  },

  /**
   * Get anomalies from telemetry
   */
  async getAnomalies(params = {}) {
    const searchParams = new URLSearchParams();
    if (params.hours) searchParams.set('hours', params.hours);
    if (params.lineId) searchParams.set('line_id', params.lineId);
    if (params.anomalyType) searchParams.set('anomaly_type', params.anomalyType);
    if (params.limit) searchParams.set('limit', params.limit);

    const query = searchParams.toString();
    return fetchAPI(`/telemetry/anomalies${query ? '?' + query : ''}`);
  },
};

/**
 * Dashboard API
 */
export const dashboardAPI = {
  /**
   * Get quality dashboard data
   */
  async getQuality(params = {}) {
    const searchParams = new URLSearchParams();
    if (params.date) searchParams.set('date', params.date);
    if (params.lineId) searchParams.set('line_id', params.lineId);

    const query = searchParams.toString();
    return fetchAPI(`/dashboard/quality${query ? '?' + query : ''}`);
  },

  /**
   * Get operations dashboard data
   */
  async getOperations(params = {}) {
    const searchParams = new URLSearchParams();
    if (params.date) searchParams.set('date', params.date);
    if (params.lineId) searchParams.set('line_id', params.lineId);

    const query = searchParams.toString();
    return fetchAPI(`/dashboard/operations${query ? '?' + query : ''}`);
  },

  /**
   * Get anomaly dashboard data
   */
  async getAnomalies() {
    return fetchAPI('/dashboard/anomalies');
  },

  /**
   * Get combined summary
   */
  async getSummary() {
    return fetchAPI('/dashboard/summary');
  },

  /**
   * Get assembly lines
   */
  async getLines() {
    return fetchAPI('/dashboard/lines');
  },

  /**
   * Refresh materialized views
   */
  async refreshViews(view = null, type = 'core') {
    const searchParams = new URLSearchParams();
    if (view) searchParams.set('view', view);
    searchParams.set('pipeline_type', type);

    const query = searchParams.toString();
    return fetchAPI(`/dashboard/views/refresh?${query}`, { method: 'POST' });
  },
};

/**
 * Format date for display (Malaysian format DD/MM/YYYY)
 */
export function formatDate(dateString) {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-MY', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

/**
 * Format datetime for display
 */
export function formatDateTime(dateString) {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleString('en-MY', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

/**
 * Format number with appropriate precision
 */
export function formatNumber(value, decimals = 2) {
  if (value === null || value === undefined) return '-';
  return Number(value).toFixed(decimals);
}

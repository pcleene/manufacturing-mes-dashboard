<script>
  import { onMount } from 'svelte';
  import { telemetryAPI, formatDateTime, formatNumber } from '$lib/api.js';
  import StatusBadge from '$lib/components/StatusBadge.svelte';
  import LineChart from '$lib/components/LineChart.svelte';

  let telemetryData = $state({ data: [], pagination: { total: 0 } });
  let machines = $state([]);
  let loading = $state(true);
  let error = $state(null);

  // Filters with date range
  let selectedMachine = $state('');
  let selectedLine = $state('');
  let selectedStatus = $state('');
  let hasAlerts = $state('');
  let startDate = $state('');
  let endDate = $state('');
  let limit = $state(50);
  let skip = $state(0);

  // Chart data
  let chartData = $state({ labels: [], datasets: [] });
  let showChart = $state(false);
  let chartMachineId = $state('');

  const lines = [
    { id: 'LINE-1', name: 'Frame Welding' },
    { id: 'LINE-2', name: 'Engine Assembly' },
    { id: 'LINE-3', name: 'Paint Shop' },
    { id: 'LINE-4', name: 'Final Assembly' },
  ];

  const statuses = ['running', 'idle', 'maintenance', 'error'];

  function initDateRange() {
    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    endDate = now.toISOString().split('T')[0];
    startDate = weekAgo.toISOString().split('T')[0];
  }

  async function loadTelemetry() {
    loading = true;
    error = null;

    try {
      const params = { limit, skip };
      if (selectedMachine) params.machineId = selectedMachine;
      if (selectedLine) params.lineId = selectedLine;
      if (selectedStatus) params.status = selectedStatus;
      if (hasAlerts !== '') params.hasAlerts = hasAlerts === 'true';
      if (startDate) params.startDate = startDate;
      if (endDate) params.endDate = endDate;

      telemetryData = await telemetryAPI.getTelemetry(params);
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  async function loadMachines() {
    try {
      const response = await telemetryAPI.getMachines();
      machines = response.data || response || [];
    } catch (e) {
      console.error('Failed to load machines:', e);
    }
  }

  async function showMachineChart(machineId) {
    showChart = true;
    chartMachineId = machineId;
    const params = { machineId, limit: 100 };
    if (startDate) params.startDate = startDate;
    if (endDate) params.endDate = endDate;
    
    const response = await telemetryAPI.getTelemetry(params);
    const data = response.data || response || [];

    if (data.length > 0) {
      const sorted = [...data].reverse();
      chartData = {
        labels: sorted.map(d => new Date(d.timestamp).toLocaleString('en-MY', { 
          month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' 
        })),
        datasets: [
          { label: 'Temperature (°C)', data: sorted.map(d => d.metrics?.temperature), color: '#E60012' },
          { label: 'Vibration (mm/s ×50)', data: sorted.map(d => (d.metrics?.vibration || 0) * 50), color: '#1e3a5f' },
          { label: 'Power (kW ÷10)', data: sorted.map(d => (d.metrics?.powerConsumption || 0) / 10), color: '#10B981' },
        ],
      };
    }
  }

  function nextPage() { skip += limit; loadTelemetry(); }
  function prevPage() { skip = Math.max(0, skip - limit); loadTelemetry(); }
  function applyFilters() { skip = 0; loadTelemetry(); }
  function clearFilters() {
    selectedMachine = '';
    selectedLine = '';
    selectedStatus = '';
    hasAlerts = '';
    initDateRange();
    skip = 0;
    loadTelemetry();
  }

  function setQuickRange(days) {
    const now = new Date();
    const past = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
    endDate = now.toISOString().split('T')[0];
    startDate = past.toISOString().split('T')[0];
    applyFilters();
  }

  onMount(() => {
    initDateRange();
    loadMachines();
    loadTelemetry();
  });
</script>

<div class="max-w-7xl mx-auto px-4 py-6">
  <!-- Header -->
  <div class="flex items-center justify-between mb-6">
    <div class="flex items-center gap-4">
      <div class="w-12 h-12 rounded-xl bg-OEMPartner-blue/10 flex items-center justify-center">
        <svg class="w-6 h-6 text-OEMPartner-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
        </svg>
      </div>
      <div>
        <h1 class="page-title">Time Series Explorer</h1>
        <p class="page-subtitle">Machine telemetry data with date range analysis</p>
      </div>
    </div>
    <div class="flex items-center gap-2 bg-blue-50 px-4 py-2 rounded-lg border border-blue-200">
      <span class="text-blue-700 font-semibold">{telemetryData.pagination?.total?.toLocaleString() || 0}</span>
      <span class="text-blue-600 text-sm">records</span>
    </div>
  </div>

  {#if error}
    <div class="card bg-red-50 border-red-200 mb-6">
      <span class="text-red-700 font-medium">Error:</span> {error}
    </div>
  {/if}

  <!-- Filters Card -->
  <div class="card mb-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-gray-700 uppercase tracking-wider">Time Series Filters</h3>
      <div class="flex items-center gap-2">
        <button onclick={() => setQuickRange(1)} class="text-xs px-3 py-1.5 rounded-lg bg-gray-100 text-gray-600 hover:bg-OEMPartner-blue hover:text-white transition-colors">24h</button>
        <button onclick={() => setQuickRange(3)} class="text-xs px-3 py-1.5 rounded-lg bg-gray-100 text-gray-600 hover:bg-OEMPartner-blue hover:text-white transition-colors">3 Days</button>
        <button onclick={() => setQuickRange(7)} class="text-xs px-3 py-1.5 rounded-lg bg-gray-100 text-gray-600 hover:bg-OEMPartner-blue hover:text-white transition-colors">7 Days</button>
      </div>
    </div>
    
    <!-- Date Range Row -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 pb-4 border-b border-gray-100">
      <div>
        <label class="filter-label">Start Date</label>
        <input type="date" bind:value={startDate} class="input w-full" />
      </div>
      <div>
        <label class="filter-label">End Date</label>
        <input type="date" bind:value={endDate} class="input w-full" />
      </div>
      <div>
        <label class="filter-label">Assembly Line</label>
        <select bind:value={selectedLine} class="input w-full">
          <option value="">All Lines</option>
          {#each lines as line}
            <option value={line.id}>{line.name}</option>
          {/each}
        </select>
      </div>
      <div>
        <label class="filter-label">Machine</label>
        <select bind:value={selectedMachine} class="input w-full">
          <option value="">All Machines</option>
          {#each machines as machine}
            <option value={machine.machineId}>{machine.machineId}</option>
          {/each}
        </select>
      </div>
    </div>

    <!-- Additional Filters -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
      <div>
        <label class="filter-label">Status</label>
        <select bind:value={selectedStatus} class="input w-full">
          <option value="">All Statuses</option>
          {#each statuses as status}
            <option value={status} class="capitalize">{status}</option>
          {/each}
        </select>
      </div>
      <div>
        <label class="filter-label">Alerts</label>
        <select bind:value={hasAlerts} class="input w-full">
          <option value="">All Records</option>
          <option value="true">With Alerts</option>
          <option value="false">No Alerts</option>
        </select>
      </div>
      <div>
        <label class="filter-label">Per Page</label>
        <select bind:value={limit} onchange={applyFilters} class="input w-full">
          <option value={25}>25</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </select>
      </div>
      <div class="flex items-end">
        <button onclick={applyFilters} class="btn btn-primary w-full">Search</button>
      </div>
      <div class="flex items-end">
        <button onclick={clearFilters} class="btn btn-secondary w-full">Reset</button>
      </div>
    </div>
  </div>

  <!-- Chart Section -->
  {#if showChart}
    <div class="card mb-6">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="font-semibold text-gray-900">{chartMachineId} Time Series</h3>
          <p class="text-xs text-gray-500">Temperature, Vibration & Power Consumption</p>
        </div>
        <button onclick={() => showChart = false} class="btn btn-secondary text-xs">Close</button>
      </div>
      {#if chartData.labels.length > 0}
        <LineChart labels={chartData.labels} datasets={chartData.datasets} height={300} />
      {:else}
        <p class="text-gray-400 text-center py-8">No data available for selected range</p>
      {/if}
    </div>
  {/if}

  <!-- Data Table -->
  <div class="card">
    <div class="flex items-center justify-between mb-4">
      <h3 class="card-header mb-0">Telemetry Records</h3>
      <span class="text-xs text-gray-500 bg-gray-100 px-3 py-1.5 rounded-lg">
        {skip + 1}–{Math.min(skip + limit, telemetryData.pagination?.total || 0)} of {telemetryData.pagination?.total || 0}
      </span>
    </div>

    {#if loading}
      <div class="flex items-center justify-center py-12">
        <div class="spinner w-8 h-8"></div>
      </div>
    {:else}
      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Machine</th>
              <th>Line</th>
              <th class="text-right">Temp (°C)</th>
              <th class="text-right">Vibration</th>
              <th class="text-right">Power (kW)</th>
              <th class="text-right">Cycle (s)</th>
              <th>Status</th>
              <th>Alerts</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {#each telemetryData.data || [] as reading}
              <tr class="{reading.alerts?.length > 0 ? 'bg-red-50' : ''}">
                <td class="text-xs font-mono text-gray-500">{formatDateTime(reading.timestamp)}</td>
                <td class="font-medium text-gray-900">{reading.metadata?.machineId}</td>
                <td class="text-gray-600">{reading.metadata?.lineName}</td>
                <td class="text-right font-mono {(reading.metrics?.temperature || 0) > 100 ? 'text-red-600 font-semibold' : ''}">
                  {formatNumber(reading.metrics?.temperature, 1)}
                </td>
                <td class="text-right font-mono {(reading.metrics?.vibration || 0) > 2 ? 'text-red-600 font-semibold' : ''}">
                  {formatNumber(reading.metrics?.vibration, 3)}
                </td>
                <td class="text-right font-mono">{formatNumber(reading.metrics?.powerConsumption, 1)}</td>
                <td class="text-right font-mono">{formatNumber(reading.metrics?.cycleTime, 1)}</td>
                <td><StatusBadge status={reading.status} size="sm" /></td>
                <td>
                  {#if reading.alerts?.length > 0}
                    <span class="badge badge-error">{reading.alerts.length}</span>
                  {:else}
                    <span class="text-gray-300">—</span>
                  {/if}
                </td>
                <td>
                  <button
                    onclick={() => showMachineChart(reading.metadata?.machineId)}
                    class="text-xs text-OEMPartner-blue-light hover:underline"
                  >
                    📈 Chart
                  </button>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
        <button onclick={prevPage} disabled={skip === 0} class="btn btn-secondary disabled:opacity-50">← Previous</button>
        <span class="text-sm text-gray-500">
          Page {Math.floor(skip / limit) + 1} of {Math.ceil((telemetryData.pagination?.total || 1) / limit)}
        </span>
        <button onclick={nextPage} disabled={!telemetryData.pagination?.hasMore} class="btn btn-secondary disabled:opacity-50">Next →</button>
      </div>
    {/if}
  </div>
</div>

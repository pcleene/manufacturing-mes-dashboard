<script>
  import { onMount } from 'svelte';
  import { telemetryAPI, dashboardAPI, formatDateTime, formatNumber } from '$lib/api.js';
  import StatCard from '$lib/components/StatCard.svelte';
  import StatusBadge from '$lib/components/StatusBadge.svelte';
  import BarChart from '$lib/components/BarChart.svelte';

  let anomalyData = $state(null);
  let telemetryAnomalies = $state([]);
  let telemetryResponse = $state(null);
  let loading = $state(true);
  let error = $state(null);
  let selectedType = $state('');
  let selectedLine = $state('');
  let hours = $state(168);

  let byTypeData = $state({ labels: [], data: [], colors: [] });
  let byMachineData = $state({ labels: [], data: [] });

  const anomalyTypes = ['temperature_spike', 'vibration_anomaly', 'power_surge', 'cycle_degradation', 'bearing_failure'];

  const lines = [
    { id: 'LINE-1', name: 'Frame Welding' },
    { id: 'LINE-2', name: 'Engine Assembly' },
    { id: 'LINE-3', name: 'Paint Shop' },
    { id: 'LINE-4', name: 'Final Assembly' },
  ];

  function computeChartData(response, anomalies) {
    // Use pre-computed byType from API if available
    if (response?.byType && response.byType.length > 0) {
      byTypeData = {
        labels: response.byType.map(t => (t._id || 'unknown').replace(/_/g, ' ')),
        data: response.byType.map(t => t.count),
        colors: response.byType.map(t => {
          const sev = getSeverityFromType(t._id);
          return sev === 'critical' ? '#E60012' : sev === 'warning' ? '#F59E0B' : '#1e3a5f';
        }),
      };
    } else {
      // Fallback: compute from anomalies array
      const typeCounts = {};
      anomalies.forEach(a => {
        const type = a.anomaly?.type || 'unknown';
        typeCounts[type] = (typeCounts[type] || 0) + 1;
      });

      const sortedTypes = Object.entries(typeCounts).sort((a, b) => b[1] - a[1]).slice(0, 5);
      byTypeData = {
        labels: sortedTypes.map(([type]) => type.replace(/_/g, ' ')),
        data: sortedTypes.map(([, count]) => count),
        colors: sortedTypes.map(([type]) => {
          const sev = getSeverityFromType(type);
          return sev === 'critical' ? '#E60012' : sev === 'warning' ? '#F59E0B' : '#1e3a5f';
        }),
      };
    }

    // Compute by machine from anomalies array
    const machineCounts = {};
    anomalies.forEach(a => {
      const machine = a.metadata?.machineId || 'unknown';
      machineCounts[machine] = (machineCounts[machine] || 0) + 1;
    });

    const sortedMachines = Object.entries(machineCounts).sort((a, b) => b[1] - a[1]).slice(0, 8);
    byMachineData = {
      labels: sortedMachines.map(([machine]) => machine),
      data: sortedMachines.map(([, count]) => count),
    };
  }

  async function loadData() {
    loading = true;
    error = null;
    try {
      const [dashboardRes, telemetryRes] = await Promise.all([
        dashboardAPI.getAnomalies(),
        telemetryAPI.getAnomalies({ hours, lineId: selectedLine || undefined, anomalyType: selectedType || undefined, limit: 500 }),
      ]);
      anomalyData = dashboardRes;
      telemetryResponse = telemetryRes;
      telemetryAnomalies = telemetryRes?.data || [];
      console.log('Telemetry response:', telemetryRes);
      console.log('byType from API:', telemetryRes?.byType);
      console.log('telemetryAnomalies count:', telemetryAnomalies.length);
      computeChartData(telemetryRes, telemetryAnomalies);
      console.log('After compute - byTypeData:', byTypeData);
      console.log('After compute - byMachineData:', byMachineData);
    } catch (e) {
      console.error('Load error:', e);
      error = e.message;
    } finally {
      loading = false;
    }
  }

  function applyFilters() { loadData(); }

  function getAnomalyDescription(type) {
    const desc = {
      temperature_spike: 'Sudden temperature increase beyond safe thresholds',
      vibration_anomaly: 'Unusual vibration patterns indicating mechanical issues',
      power_surge: 'Power consumption spike - potential electrical fault',
      cycle_degradation: 'Cycle time degradation affecting efficiency',
      bearing_failure: 'Potential bearing failure indicators',
    };
    return desc[type] || 'Unknown anomaly type';
  }

  function getSeverityFromType(type) {
    const sev = { temperature_spike: 'critical', bearing_failure: 'critical', vibration_anomaly: 'warning', power_surge: 'warning', cycle_degradation: 'info' };
    return sev[type] || 'info';
  }

  onMount(() => { loadData(); });
</script>

<div class="max-w-7xl mx-auto px-4 py-6">
  <!-- Header -->
  <div class="flex items-center justify-between mb-6">
    <div class="flex items-center gap-4">
      <div class="w-12 h-12 rounded-xl bg-red-50 flex items-center justify-center">
        <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
        </svg>
      </div>
      <div>
        <h1 class="page-title">Anomaly Detection</h1>
        <p class="page-subtitle">ML-powered real-time anomaly detection from sensor data</p>
      </div>
    </div>
    <div class="flex items-center gap-2 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200">
      <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
      <span class="text-xs text-emerald-700 font-medium">ML Pipeline Active</span>
    </div>
  </div>

  {#if error}
    <div class="card bg-red-50 border-red-200 mb-6">
      <span class="text-red-700 font-medium">Error:</span> {error}
    </div>
  {/if}

  <!-- Filters -->
  <div class="card mb-6">
    <h3 class="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">Analysis Filters</h3>
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div>
        <label class="filter-label">Time Range</label>
        <select bind:value={hours} class="input w-full">
          <option value={6}>Last 6 hours</option>
          <option value={12}>Last 12 hours</option>
          <option value={24}>Last 24 hours</option>
          <option value={48}>Last 48 hours</option>
          <option value={168}>Last 7 days</option>
        </select>
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
        <label class="filter-label">Anomaly Type</label>
        <select bind:value={selectedType} class="input w-full">
          <option value="">All Types</option>
          {#each anomalyTypes as type}
            <option value={type} class="capitalize">{type.replace(/_/g, ' ')}</option>
          {/each}
        </select>
      </div>
      <div class="flex items-end">
        <button onclick={applyFilters} class="btn btn-primary w-full">Analyze</button>
      </div>
    </div>
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-16">
      <div class="spinner w-10 h-10"></div>
    </div>
  {:else}
    <!-- Stats -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <StatCard value={anomalyData?.unacknowledgedCount ?? 0} label="Unacknowledged" color={(anomalyData?.unacknowledgedCount ?? 0) > 0 ? 'red' : 'green'} icon="⚠️" />
      <StatCard value={telemetryResponse?.count ?? telemetryAnomalies.length} label="Total in Period" color="yellow" icon="🔍" />
      <StatCard value={telemetryAnomalies.filter(a => getSeverityFromType(a.anomaly?.type) === 'critical').length} label="Critical" color="red" icon="🚨" />
      <StatCard value={[...new Set(telemetryAnomalies.map(a => a.metadata?.machineId))].length} label="Affected Machines" color="blue" icon="🏭" />
    </div>

    <!-- Charts -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div class="card">
        <h3 class="card-header">Anomalies by Type</h3>
        {#if byTypeData.labels.length > 0}
          {#key byTypeData.labels.join(',')}
            <BarChart labels={byTypeData.labels} data={byTypeData.data} label="Count" colors={byTypeData.colors} height={280} />
          {/key}
        {:else}
          <div class="flex flex-col items-center justify-center py-12 text-gray-400">
            <svg class="w-10 h-10 mb-2 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <p>No anomalies detected</p>
          </div>
        {/if}
      </div>

      <div class="card">
        <h3 class="card-header">Top Affected Machines</h3>
        {#if byMachineData.labels.length > 0}
          {#key byMachineData.labels.join(',')}
            <BarChart labels={byMachineData.labels} data={byMachineData.data} label="Anomaly Count" horizontal={true} height={280} />
          {/key}
        {:else}
          <div class="flex flex-col items-center justify-center py-12 text-gray-400">
            <svg class="w-10 h-10 mb-2 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <p>All machines healthy</p>
          </div>
        {/if}
      </div>
    </div>

    <!-- Type Reference -->
    <div class="card mb-6">
      <h3 class="card-header">Anomaly Type Reference</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {#each anomalyTypes as type}
          <div class="flex items-start gap-3 p-4 rounded-lg bg-gray-50 border border-gray-100">
            <StatusBadge status={getSeverityFromType(type)} size="sm" />
            <div>
              <span class="font-medium text-gray-800 capitalize">{type.replace(/_/g, ' ')}</span>
              <p class="text-xs text-gray-500 mt-1">{getAnomalyDescription(type)}</p>
            </div>
          </div>
        {/each}
      </div>
    </div>

    <!-- Table -->
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <h3 class="card-header mb-0">Detected Anomalies</h3>
        <span class="text-xs text-gray-500 bg-gray-100 px-3 py-1.5 rounded-lg">{telemetryAnomalies.length} records</span>
      </div>

      {#if telemetryAnomalies.length > 0}
        <div class="table-container">
          <table class="table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Machine</th>
                <th>Line</th>
                <th>Type</th>
                <th>Severity</th>
                <th class="text-right">Temp (°C)</th>
                <th class="text-right">Vibration</th>
                <th class="text-right">Power (kW)</th>
              </tr>
            </thead>
            <tbody>
              {#each telemetryAnomalies.slice(0, 50) as anomaly}
                {@const severity = getSeverityFromType(anomaly.anomaly?.type)}
                <tr class="{severity === 'critical' ? 'bg-red-50' : severity === 'warning' ? 'bg-amber-50' : ''}">
                  <td class="text-xs font-mono text-gray-500">{formatDateTime(anomaly.timestamp)}</td>
                  <td class="font-medium text-gray-900">{anomaly.metadata?.machineId}</td>
                  <td class="text-gray-600">{anomaly.metadata?.lineName}</td>
                  <td class="capitalize text-gray-700">{anomaly.anomaly?.type?.replace(/_/g, ' ') ?? '—'}</td>
                  <td><StatusBadge status={severity} size="sm" /></td>
                  <td class="text-right font-mono {(anomaly.metrics?.temperature || 0) > 100 ? 'text-red-600 font-semibold' : ''}">{formatNumber(anomaly.metrics?.temperature, 1)}</td>
                  <td class="text-right font-mono {(anomaly.metrics?.vibration || 0) > 2 ? 'text-red-600 font-semibold' : ''}">{formatNumber(anomaly.metrics?.vibration, 3)}</td>
                  <td class="text-right font-mono">{formatNumber(anomaly.metrics?.powerConsumption, 1)}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
        {#if telemetryAnomalies.length > 50}
          <p class="text-xs text-gray-500 text-center mt-4">Showing first 50 of {telemetryAnomalies.length} anomalies</p>
        {/if}
      {:else}
        <div class="flex flex-col items-center justify-center py-12">
          <div class="w-14 h-14 rounded-full bg-emerald-50 flex items-center justify-center mb-3">
            <svg class="w-7 h-7 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
          </div>
          <p class="text-gray-600 font-medium">No anomalies detected</p>
          <p class="text-xs text-gray-400 mt-1">All systems operating normally</p>
        </div>
      {/if}
    </div>
  {/if}
</div>

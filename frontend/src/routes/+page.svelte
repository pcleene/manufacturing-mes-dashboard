<script>
  import { onMount } from 'svelte';
  import { dashboardAPI, formatNumber, formatDateTime } from '$lib/api.js';
  import StatCard from '$lib/components/StatCard.svelte';
  import LineChart from '$lib/components/LineChart.svelte';
  import BarChart from '$lib/components/BarChart.svelte';
  import StatusBadge from '$lib/components/StatusBadge.svelte';

  let summary = $state(null);
  let qualityData = $state(null);
  let operationsData = $state(null);
  let anomalyData = $state(null);
  let loading = $state(true);
  let error = $state(null);
  let lastRefresh = $state(null);

  async function loadDashboard() {
    loading = true;
    error = null;

    try {
      summary = await dashboardAPI.getSummary();
      lastRefresh = new Date();
      loading = false;
      
      Promise.all([
        dashboardAPI.getQuality(),
        dashboardAPI.getOperations(),
        dashboardAPI.getAnomalies(),
      ]).then(([qualityRes, operationsRes, anomalyRes]) => {
        qualityData = qualityRes;
        operationsData = operationsRes;
        anomalyData = anomalyRes;
      }).catch(e => console.error('Failed to load details:', e));
      
    } catch (e) {
      error = e.message;
      console.error('Failed to load dashboard:', e);
      loading = false;
    }
  }

  async function refreshViews() {
    try {
      await dashboardAPI.refreshViews();
      await loadDashboard();
    } catch (e) {
      error = e.message;
    }
  }

  onMount(() => {
    loadDashboard();
    const interval = setInterval(loadDashboard, 300000);
    return () => clearInterval(interval);
  });
</script>

<div class="max-w-7xl mx-auto px-4 py-6">
  <!-- Header -->
  <div class="flex items-center justify-between mb-6">
    <div class="flex items-center gap-4">
      <div class="w-12 h-12 rounded-xl bg-OEMPartner-blue/10 flex items-center justify-center">
        <svg class="w-6 h-6 text-OEMPartner-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/>
        </svg>
      </div>
      <div>
        <h1 class="page-title">Dashboard Overview</h1>
        <p class="page-subtitle">Real-time monitoring for OEMPartner motorcycle assembly lines</p>
      </div>
    </div>
    <div class="flex items-center gap-3">
      {#if lastRefresh}
        <span class="text-xs text-gray-500 bg-gray-100 px-3 py-1.5 rounded-lg">
          Updated: {formatDateTime(lastRefresh.toISOString())}
        </span>
      {/if}
      <button onclick={refreshViews} class="btn btn-primary" disabled={loading}>
        {#if loading}
          <span class="spinner w-4 h-4 mr-2 inline-block"></span>
        {/if}
        Refresh
      </button>
    </div>
  </div>

  {#if error}
    <div class="card bg-red-50 border-red-200 mb-6">
      <span class="text-red-700 font-medium">Error:</span> {error}
    </div>
  {/if}

  {#if loading && !summary}
    <div class="flex items-center justify-center py-16">
      <div class="spinner w-10 h-10"></div>
    </div>
  {:else}
    <!-- Hero Stats -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <StatCard
        value={formatNumber(summary?.quality?.score ?? 0, 1)}
        unit="%"
        label="Quality Score"
        color={(summary?.quality?.score ?? 0) >= 90 ? 'green' : (summary?.quality?.score ?? 0) >= 70 ? 'yellow' : 'red'}
        icon="🎯"
      />
      <StatCard
        value={summary?.operations?.unitsProduced?.toLocaleString() ?? 0}
        label="Units Produced"
        color="blue"
        icon="🏭"
      />
      <StatCard
        value={formatNumber(summary?.operations?.utilizationRate ?? 0, 1)}
        unit="%"
        label="Utilization Rate"
        color={(summary?.operations?.utilizationRate ?? 0) >= 80 ? 'green' : 'yellow'}
        icon="⚙️"
      />
      <StatCard
        value={summary?.anomalies?.unacknowledged ?? 0}
        label="Active Anomalies"
        color={(summary?.anomalies?.unacknowledged ?? 0) > 0 ? 'red' : 'green'}
        icon="⚠️"
      />
    </div>

    <!-- Secondary Stats -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <StatCard
        value={formatNumber(summary?.quality?.defectRate ?? 0, 2)}
        unit="%"
        label="Defect Rate"
        color={(summary?.quality?.defectRate ?? 0) <= 2 ? 'green' : 'red'}
      />
      <StatCard
        value={summary?.quality?.criticalAlerts ?? 0}
        label="Critical Alerts"
        color={(summary?.quality?.criticalAlerts ?? 0) > 0 ? 'red' : 'green'}
      />
      <StatCard
        value={formatNumber(summary?.operations?.avgCycleTime ?? 0, 1)}
        unit="s"
        label="Avg Cycle Time"
        color="gray"
      />
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div class="card">
        <h3 class="card-header">Quality Score Trend</h3>
        {#if qualityData?.trend?.length > 0}
          <LineChart
            labels={qualityData.trend.map(t => t.date)}
            datasets={[{
              label: 'Quality Score',
              data: qualityData.trend.map(t => t.qualityScore),
              color: '#10B981',
              fill: true,
            }]}
            height={260}
          />
        {:else}
          <div class="flex items-center justify-center py-12 text-gray-400">
            <p>Loading trend data...</p>
          </div>
        {/if}
      </div>

      <div class="card">
        <h3 class="card-header">Production by Line</h3>
        {#if operationsData?.byLine?.length > 0}
          <BarChart
            labels={operationsData.byLine.map(l => l.lineName)}
            data={operationsData.byLine.map(l => l.unitsProduced)}
            label="Units"
            height={260}
          />
        {:else}
          <div class="flex items-center justify-center py-12 text-gray-400">
            <p>Loading production data...</p>
          </div>
        {/if}
      </div>
    </div>

    <!-- Second Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div class="card">
        <h3 class="card-header">Production Trend (7 Days)</h3>
        {#if operationsData?.trend?.length > 0}
          <LineChart
            labels={operationsData.trend.map(t => t.date)}
            datasets={[
              { label: 'Units', data: operationsData.trend.map(t => t.units), color: '#1e3a5f' },
              { label: 'Utilization %', data: operationsData.trend.map(t => t.utilization), color: '#10B981' },
            ]}
            height={260}
          />
        {:else}
          <div class="flex items-center justify-center py-12 text-gray-400">
            <p>Loading trend data...</p>
          </div>
        {/if}
      </div>

      <div class="card">
        <h3 class="card-header">Recent Anomalies</h3>
        {#if anomalyData?.recent?.length > 0}
          <div class="space-y-2 max-h-64 overflow-y-auto">
            {#each anomalyData.recent.slice(0, 6) as anomaly}
              <div class="flex items-center justify-between p-3 rounded-lg bg-gray-50 border border-gray-100">
                <div>
                  <span class="font-medium text-gray-800">{anomaly.machineId}</span>
                  <span class="text-xs text-gray-500 ml-2 capitalize">{anomaly.anomalyType?.replace(/_/g, ' ')}</span>
                </div>
                <StatusBadge status={anomaly.severity || 'warning'} size="sm" />
              </div>
            {/each}
          </div>
          <a href="/anomalies" class="block text-center mt-4 text-sm text-OEMPartner-blue-light hover:underline">
            View all anomalies →
          </a>
        {:else}
          <div class="flex flex-col items-center justify-center py-12">
            <div class="w-12 h-12 rounded-full bg-emerald-50 flex items-center justify-center mb-3">
              <svg class="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
              </svg>
            </div>
            <p class="text-gray-500">No recent anomalies</p>
          </div>
        {/if}
      </div>
    </div>

    <!-- Line Performance Table -->
    <div class="card">
      <h3 class="card-header">Assembly Line Performance</h3>
      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>Line</th>
              <th class="text-right">Units Produced</th>
              <th class="text-right">Target</th>
              <th class="text-right">Utilization</th>
              <th class="text-right">Quality Score</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {#if operationsData?.byLine?.length > 0}
              {#each operationsData.byLine as line}
                {@const qualityLine = qualityData?.byLine?.find(q => q.lineId === line.lineId)}
                {@const utilization = line.utilizationRate || 0}
                <tr>
                  <td class="font-medium text-gray-900">{line.lineName}</td>
                  <td class="text-right font-mono">{line.unitsProduced?.toLocaleString() ?? 0}</td>
                  <td class="text-right font-mono text-gray-500">{line.targetUnits?.toLocaleString() ?? '—'}</td>
                  <td class="text-right">
                    <span class="{utilization >= 80 ? 'text-emerald-600' : 'text-amber-600'} font-medium">
                      {formatNumber(utilization, 1)}%
                    </span>
                  </td>
                  <td class="text-right">
                    <span class="{(qualityLine?.qualityScore ?? 0) >= 90 ? 'text-emerald-600' : 'text-amber-600'} font-medium">
                      {formatNumber(qualityLine?.qualityScore ?? 0, 1)}%
                    </span>
                  </td>
                  <td><StatusBadge status={utilization >= 80 ? 'running' : 'idle'} size="sm" /></td>
                </tr>
              {/each}
            {:else}
              <tr>
                <td colspan="6" class="text-center text-gray-400 py-8">Loading line data...</td>
              </tr>
            {/if}
          </tbody>
        </table>
      </div>
    </div>
  {/if}
</div>

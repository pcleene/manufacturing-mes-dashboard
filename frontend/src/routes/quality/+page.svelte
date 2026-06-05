<script>
  import { onMount } from 'svelte';
  import { dashboardAPI, formatNumber } from '$lib/api.js';
  import StatCard from '$lib/components/StatCard.svelte';
  import LineChart from '$lib/components/LineChart.svelte';
  import BarChart from '$lib/components/BarChart.svelte';
  import StatusBadge from '$lib/components/StatusBadge.svelte';

  let qualityData = $state(null);
  let loading = $state(true);
  let error = $state(null);
  let selectedLine = $state('');

  const lines = [
    { id: 'LINE-1', name: 'Frame Welding' },
    { id: 'LINE-2', name: 'Engine Assembly' },
    { id: 'LINE-3', name: 'Paint Shop' },
    { id: 'LINE-4', name: 'Final Assembly' },
  ];

  async function loadQualityData() {
    loading = true;
    error = null;
    try {
      const params = {};
      if (selectedLine) params.lineId = selectedLine;
      qualityData = await dashboardAPI.getQuality(params);
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  function applyFilter() { loadQualityData(); }
  onMount(() => { loadQualityData(); });
</script>

<div class="max-w-7xl mx-auto px-4 py-6">
  <!-- Header -->
  <div class="flex items-center justify-between mb-6">
    <div class="flex items-center gap-4">
      <div class="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center">
        <svg class="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
      </div>
      <div>
        <h1 class="page-title">Quality Dashboard</h1>
        <p class="page-subtitle">Quality metrics and defect analysis for QA department</p>
      </div>
    </div>
    <div class="flex items-center gap-3">
      <select bind:value={selectedLine} onchange={applyFilter} class="input">
        <option value="">All Lines</option>
        {#each lines as line}
          <option value={line.id}>{line.name}</option>
        {/each}
      </select>
    </div>
  </div>

  {#if error}
    <div class="card bg-red-50 border-red-200 mb-6">
      <span class="text-red-700 font-medium">Error:</span> {error}
    </div>
  {/if}

  {#if loading}
    <div class="flex items-center justify-center py-16">
      <div class="spinner w-10 h-10"></div>
    </div>
  {:else if qualityData}
    <!-- Stats -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
      <StatCard
        value={formatNumber(qualityData.summary.overallQualityScore, 1)}
        unit="%"
        label="Overall Quality Score"
        color={qualityData.summary.overallQualityScore >= 90 ? 'green' : qualityData.summary.overallQualityScore >= 70 ? 'yellow' : 'red'}
        icon="🎯"
      />
      <StatCard
        value={formatNumber(qualityData.summary.avgDefectRate, 2)}
        unit="%"
        label="Defect Rate"
        color={qualityData.summary.avgDefectRate <= 2 ? 'green' : 'red'}
        icon="⚠️"
      />
      <StatCard value={qualityData.summary.totalAlerts} label="Total Alerts" color="yellow" icon="🔔" />
      <StatCard
        value={qualityData.summary.criticalAlerts}
        label="Critical Alerts"
        color={qualityData.summary.criticalAlerts > 0 ? 'red' : 'green'}
        icon="🚨"
      />
      <StatCard
        value={qualityData.summary.anomalyCount}
        label="Detected Anomalies"
        color={qualityData.summary.anomalyCount > 0 ? 'red' : 'green'}
        icon="🔍"
      />
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div class="card">
        <h3 class="card-header">Quality Score Trend</h3>
        {#if qualityData.trend?.length > 0}
          <LineChart
            labels={qualityData.trend.map(t => t.date)}
            datasets={[{ label: 'Quality Score', data: qualityData.trend.map(t => t.qualityScore), color: '#10B981', fill: true }]}
            height={280}
          />
        {:else}
          <p class="text-gray-400 text-center py-12">No trend data available</p>
        {/if}
      </div>

      <div class="card">
        <h3 class="card-header">Alerts & Anomalies Trend</h3>
        {#if qualityData.trend?.length > 0}
          <LineChart
            labels={qualityData.trend.map(t => t.date)}
            datasets={[
              { label: 'Alerts', data: qualityData.trend.map(t => t.alerts), color: '#F59E0B' },
              { label: 'Anomalies', data: qualityData.trend.map(t => t.anomalies), color: '#E60012' },
            ]}
            height={280}
          />
        {:else}
          <p class="text-gray-400 text-center py-12">No trend data available</p>
        {/if}
      </div>
    </div>

    <!-- Quality by Line -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div class="card">
        <h3 class="card-header">Quality Score by Line</h3>
        {#if qualityData.byLine?.length > 0}
          <BarChart
            labels={qualityData.byLine.map(l => l.lineName)}
            data={qualityData.byLine.map(l => l.qualityScore)}
            label="Quality Score"
            colors={qualityData.byLine.map(l => l.qualityScore >= 90 ? '#10B981' : l.qualityScore >= 70 ? '#F59E0B' : '#E60012')}
            height={280}
          />
        {:else}
          <p class="text-gray-400 text-center py-12">No data available</p>
        {/if}
      </div>

      <div class="card">
        <h3 class="card-header">Defect Rate by Line</h3>
        {#if qualityData.byLine?.length > 0}
          <BarChart
            labels={qualityData.byLine.map(l => l.lineName)}
            data={qualityData.byLine.map(l => l.defectRate)}
            label="Defect Rate %"
            colors={qualityData.byLine.map(l => l.defectRate <= 2 ? '#10B981' : l.defectRate <= 5 ? '#F59E0B' : '#E60012')}
            height={280}
          />
        {:else}
          <p class="text-gray-400 text-center py-12">No data available</p>
        {/if}
      </div>
    </div>

    <!-- Machine Health Table -->
    <div class="card">
      <h3 class="card-header">Machine Health Analysis</h3>
      <p class="text-sm text-gray-500 mb-4">Machines sorted by health score (lowest first - needs attention)</p>

      {#if qualityData.machineHealth?.length > 0}
        <div class="table-container">
          <table class="table">
            <thead>
              <tr>
                <th>Machine</th>
                <th>Line</th>
                <th class="text-right">Health Score</th>
                <th class="text-right">Alert Rate</th>
                <th class="text-right">Critical Alerts</th>
                <th class="text-right">Temp Alerts</th>
                <th class="text-right">Vibration Alerts</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {#each qualityData.machineHealth as machine}
                <tr class="{machine.healthScore < 70 ? 'bg-red-50' : machine.healthScore < 85 ? 'bg-amber-50' : ''}">
                  <td class="font-medium text-gray-900">{machine.machineId}</td>
                  <td class="text-gray-600">{machine.lineName}</td>
                  <td class="text-right">
                    <span class="{machine.healthScore >= 90 ? 'text-emerald-600' : machine.healthScore >= 70 ? 'text-amber-600' : 'text-red-600'} font-semibold">
                      {formatNumber(machine.healthScore, 1)}%
                    </span>
                  </td>
                  <td class="text-right font-mono">{formatNumber(machine.alertRate, 2)}%</td>
                  <td class="text-right">
                    {#if machine.alerts?.critical > 0}
                      <span class="text-red-600 font-semibold">{machine.alerts.critical}</span>
                    {:else}
                      0
                    {/if}
                  </td>
                  <td class="text-right">{machine.alerts?.temperature ?? 0}</td>
                  <td class="text-right">{machine.alerts?.vibration ?? 0}</td>
                  <td>
                    <StatusBadge status={machine.healthScore >= 90 ? 'normal' : machine.healthScore >= 70 ? 'warning' : 'critical'} size="sm" />
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {:else}
        <p class="text-gray-400 text-center py-12">No machine health data available</p>
      {/if}
    </div>
  {/if}
</div>

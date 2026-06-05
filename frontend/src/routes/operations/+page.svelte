<script>
  import { onMount } from 'svelte';
  import { dashboardAPI, formatNumber } from '$lib/api.js';
  import StatCard from '$lib/components/StatCard.svelte';
  import LineChart from '$lib/components/LineChart.svelte';
  import BarChart from '$lib/components/BarChart.svelte';

  let operationsData = $state(null);
  let loading = $state(true);
  let error = $state(null);
  let selectedLine = $state('');

  const lines = [
    { id: 'LINE-1', name: 'Frame Welding' },
    { id: 'LINE-2', name: 'Engine Assembly' },
    { id: 'LINE-3', name: 'Paint Shop' },
    { id: 'LINE-4', name: 'Final Assembly' },
  ];

  async function loadOperationsData() {
    loading = true;
    error = null;
    try {
      const params = {};
      if (selectedLine) params.lineId = selectedLine;
      operationsData = await dashboardAPI.getOperations(params);
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  function applyFilter() { loadOperationsData(); }
  onMount(() => { loadOperationsData(); });
</script>

<div class="max-w-7xl mx-auto px-4 py-6">
  <!-- Header -->
  <div class="flex items-center justify-between mb-6">
    <div class="flex items-center gap-4">
      <div class="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center">
        <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
        </svg>
      </div>
      <div>
        <h1 class="page-title">Operations Dashboard</h1>
        <p class="page-subtitle">Production metrics and utilization for planning department</p>
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
  {:else if operationsData}
    <!-- Stats -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4 mb-6">
      <StatCard value={operationsData.summary.totalUnits?.toLocaleString() ?? 0} label="Units Produced" color="blue" icon="🏭" />
      <StatCard value={operationsData.summary.targetUnits?.toLocaleString() ?? 0} label="Target Units" color="gray" icon="🎯" />
      <StatCard
        value={formatNumber(operationsData.summary.completionRate, 1)}
        unit="%"
        label="Completion Rate"
        color={operationsData.summary.completionRate >= 90 ? 'green' : 'yellow'}
        icon="✓"
      />
      <StatCard
        value={formatNumber(operationsData.summary.utilizationRate, 1)}
        unit="%"
        label="Utilization"
        color={operationsData.summary.utilizationRate >= 80 ? 'green' : 'yellow'}
        icon="⚙️"
      />
      <StatCard value={formatNumber(operationsData.summary.avgCycleTime, 1)} unit="s" label="Avg Cycle Time" color="gray" icon="⏱️" />
      <StatCard
        value={operationsData.summary.downtimeMinutes}
        unit=" min"
        label="Total Downtime"
        color={operationsData.summary.downtimeMinutes > 60 ? 'red' : 'green'}
        icon="⏸️"
      />
    </div>

    <!-- Production Charts -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div class="card">
        <h3 class="card-header">Production by Line</h3>
        {#if operationsData.byLine?.length > 0}
          <BarChart
            labels={operationsData.byLine.map(l => l.lineName)}
            data={operationsData.byLine.map(l => l.unitsProduced)}
            label="Units Produced"
            height={280}
          />
        {:else}
          <p class="text-gray-400 text-center py-12">No data available</p>
        {/if}
      </div>

      <div class="card">
        <h3 class="card-header">Utilization by Line</h3>
        {#if operationsData.byLine?.length > 0}
          <BarChart
            labels={operationsData.byLine.map(l => l.lineName)}
            data={operationsData.byLine.map(l => l.utilizationRate)}
            label="Utilization %"
            colors={operationsData.byLine.map(l => l.utilizationRate >= 80 ? '#10B981' : l.utilizationRate >= 60 ? '#F59E0B' : '#E60012')}
            height={280}
          />
        {:else}
          <p class="text-gray-400 text-center py-12">No data available</p>
        {/if}
      </div>
    </div>

    <!-- Trend Charts -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div class="card">
        <h3 class="card-header">Production Trend (7 Days)</h3>
        {#if operationsData.trend?.length > 0}
          <LineChart
            labels={operationsData.trend.map(t => t.date)}
            datasets={[{ label: 'Units Produced', data: operationsData.trend.map(t => t.units), color: '#1e3a5f', fill: true }]}
            height={280}
          />
        {:else}
          <p class="text-gray-400 text-center py-12">No trend data available</p>
        {/if}
      </div>

      <div class="card">
        <h3 class="card-header">Utilization & Cycle Time Trend</h3>
        {#if operationsData.trend?.length > 0}
          <LineChart
            labels={operationsData.trend.map(t => t.date)}
            datasets={[
              { label: 'Utilization %', data: operationsData.trend.map(t => t.utilization), color: '#10B981' },
              { label: 'Cycle Time (s)', data: operationsData.trend.map(t => t.cycleTime), color: '#F59E0B' },
            ]}
            height={280}
          />
        {:else}
          <p class="text-gray-400 text-center py-12">No trend data available</p>
        {/if}
      </div>
    </div>

    <!-- Downtime Analysis -->
    <div class="card mb-6">
      <h3 class="card-header">Downtime Analysis by Line</h3>
      {#if operationsData.downtime?.length > 0}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {#each operationsData.downtime as dt}
            <div class="bg-gray-50 rounded-xl p-4 border border-gray-100">
              <h4 class="font-semibold text-gray-800 mb-3">{dt.lineName}</h4>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-gray-500">Maintenance:</span>
                  <span class="font-medium text-amber-600">{dt.maintenance} min</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-500">Errors:</span>
                  <span class="font-medium text-red-600">{dt.error} min</span>
                </div>
                <div class="flex justify-between border-t border-gray-200 pt-2">
                  <span class="text-gray-700 font-medium">Total:</span>
                  <span class="font-bold">{dt.maintenance + dt.error} min</span>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <p class="text-gray-400 text-center py-12">No downtime data available</p>
      {/if}
    </div>

    <!-- Line Performance Table -->
    <div class="card">
      <h3 class="card-header">Line Performance Summary</h3>
      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>Line</th>
              <th class="text-right">Units Produced</th>
              <th class="text-right">Target</th>
              <th class="text-right">Completion %</th>
              <th class="text-right">Utilization</th>
            </tr>
          </thead>
          <tbody>
            {#each operationsData.byLine as line}
              {@const completion = line.targetUnits > 0 ? (line.unitsProduced / line.targetUnits) * 100 : 0}
              <tr>
                <td class="font-medium text-gray-900">{line.lineName}</td>
                <td class="text-right font-mono">{line.unitsProduced?.toLocaleString() ?? 0}</td>
                <td class="text-right font-mono text-gray-500">{line.targetUnits?.toLocaleString() ?? '—'}</td>
                <td class="text-right">
                  <span class="{completion >= 90 ? 'text-emerald-600' : completion >= 70 ? 'text-amber-600' : 'text-red-600'} font-medium">
                    {formatNumber(completion, 1)}%
                  </span>
                </td>
                <td class="text-right">
                  <span class="{line.utilizationRate >= 80 ? 'text-emerald-600' : 'text-amber-600'} font-medium">
                    {formatNumber(line.utilizationRate, 1)}%
                  </span>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {/if}
</div>

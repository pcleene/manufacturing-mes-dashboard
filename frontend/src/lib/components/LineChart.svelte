<script>
  import { onMount, onDestroy } from 'svelte';
  import Chart from 'chart.js/auto';

  let { labels = [], datasets = [], title = '', height = 300, showLegend = true } = $props();

  let canvas;
  let chart;
  let mounted = false;

  const defaultColors = [
    '#1e3a5f',
    '#E60012',
    '#10B981',
    '#F59E0B',
    '#8B5CF6',
  ];

  function createChart() {
    if (!canvas || !mounted) return;

    if (chart) {
      chart.destroy();
      chart = null;
    }

    if (!labels || labels.length === 0 || !datasets || datasets.length === 0) {
      return;
    }

    const ctx = canvas.getContext('2d');

    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [...labels],
        datasets: datasets.map((ds, index) => ({
          label: ds.label,
          data: [...(ds.data || [])],
          borderColor: ds.color || defaultColors[index % defaultColors.length],
          backgroundColor: (ds.color || defaultColors[index % defaultColors.length]) + '15',
          borderWidth: 2,
          fill: ds.fill ?? false,
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6,
          pointBackgroundColor: ds.color || defaultColors[index % defaultColors.length],
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: showLegend,
            position: 'top',
            labels: {
              color: '#6b7280',
              usePointStyle: true,
              padding: 20,
            }
          },
          title: {
            display: !!title,
            text: title,
            color: '#374151',
            font: { weight: '600' }
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: '#f3f4f6',
            },
            ticks: {
              color: '#6b7280',
            }
          },
          x: {
            grid: {
              display: false,
            },
            ticks: {
              color: '#6b7280',
            }
          },
        },
        interaction: {
          intersect: false,
          mode: 'index',
        },
      },
    });
  }

  onMount(() => {
    mounted = true;
    setTimeout(() => {
      createChart();
    }, 50);
  });

  onDestroy(() => {
    mounted = false;
    if (chart) {
      chart.destroy();
      chart = null;
    }
  });

  $effect(() => {
    const currentLabels = labels;
    const currentDatasets = datasets;
    
    if (mounted && currentLabels?.length > 0 && currentDatasets?.length > 0) {
      setTimeout(() => createChart(), 10);
    }
  });
</script>

<div class="w-full" style="height: {height}px;">
  <canvas bind:this={canvas}></canvas>
</div>

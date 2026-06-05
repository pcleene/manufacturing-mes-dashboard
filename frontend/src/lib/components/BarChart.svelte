<script>
  import { onMount, onDestroy } from 'svelte';
  import Chart from 'chart.js/auto';

  let { data = [], labels = [], label = '', title = '', height = 300, horizontal = false, colors = null } = $props();

  let canvas;
  let chart;
  let mounted = false;

  const defaultColors = [
    '#1e3a5f',
    '#2563eb',
    '#3b82f6',
    '#60a5fa',
    '#93c5fd',
  ];

  function createChart() {
    if (!canvas || !mounted) return;
    
    if (chart) {
      chart.destroy();
      chart = null;
    }

    if (!labels || labels.length === 0 || !data || data.length === 0) {
      return;
    }

    const ctx = canvas.getContext('2d');
    const chartColors = colors || data.map((_, i) => defaultColors[i % defaultColors.length]);

    chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: [...labels],
        datasets: [{
          label: label,
          data: [...data],
          backgroundColor: chartColors,
          borderColor: chartColors,
          borderWidth: 0,
          borderRadius: 6,
        }],
      },
      options: {
        indexAxis: horizontal ? 'y' : 'x',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
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
      },
    });
  }

  onMount(() => {
    mounted = true;
    // Small delay to ensure canvas is in DOM
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

  // Watch for prop changes
  $effect(() => {
    // Access props to track them
    const currentLabels = labels;
    const currentData = data;
    
    if (mounted && currentLabels?.length > 0 && currentData?.length > 0) {
      setTimeout(() => createChart(), 10);
    }
  });
</script>

<div class="w-full" style="height: {height}px;">
  <canvas bind:this={canvas}></canvas>
</div>

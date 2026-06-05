<script>
  let { value = 0, label = '', unit = '', trend = null, trendValue = null, color = 'blue', icon = null } = $props();

  const colorClasses = {
    blue: 'text-blue-600',
    green: 'text-emerald-600',
    red: 'text-red-600',
    yellow: 'text-amber-600',
    gray: 'text-gray-600',
  };

  const iconBgClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-emerald-50 text-emerald-600',
    red: 'bg-red-50 text-red-600',
    yellow: 'bg-amber-50 text-amber-600',
    gray: 'bg-gray-50 text-gray-600',
  };
</script>

<div class="stat-card hover:shadow-md transition-shadow duration-200">
  <div class="flex items-start justify-between">
    <div class="flex-1">
      <div class="stat-value {colorClasses[color]}">
        {value}<span class="text-lg font-medium text-gray-400">{unit}</span>
      </div>
      <div class="stat-label">{label}</div>
    </div>
    {#if icon}
      <div class="w-10 h-10 rounded-lg {iconBgClasses[color]} flex items-center justify-center">
        <span class="text-xl">{icon}</span>
      </div>
    {/if}
  </div>

  {#if trend && trendValue !== null}
    <div class="mt-3 pt-3 border-t border-gray-100 flex items-center text-sm">
      {#if trend === 'up'}
        <span class="text-emerald-600 flex items-center gap-1">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
          </svg>
          +{trendValue}%
        </span>
      {:else}
        <span class="text-red-600 flex items-center gap-1">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
          </svg>
          -{trendValue}%
        </span>
      {/if}
      <span class="text-gray-400 ml-2 text-xs">vs last period</span>
    </div>
  {/if}
</div>

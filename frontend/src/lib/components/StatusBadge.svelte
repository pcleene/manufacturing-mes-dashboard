<script>
  let { status = 'normal', size = 'md' } = $props();

  const statusConfig = {
    running: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', label: 'Running', dot: 'bg-emerald-500' },
    idle: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', label: 'Idle', dot: 'bg-amber-500' },
    maintenance: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', label: 'Maintenance', dot: 'bg-blue-500' },
    error: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', label: 'Error', dot: 'bg-red-500' },
    normal: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', label: 'Normal', dot: 'bg-emerald-500' },
    warning: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', label: 'Warning', dot: 'bg-amber-500' },
    critical: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', label: 'Critical', dot: 'bg-red-500' },
    info: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', label: 'Info', dot: 'bg-blue-500' },
  };

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
    lg: 'px-3 py-1.5 text-sm',
  };

  const config = statusConfig[status] || statusConfig.normal;
</script>

<span class="inline-flex items-center gap-1.5 rounded-full font-medium border {config.bg} {config.text} {config.border} {sizeClasses[size]}">
  <span class="w-1.5 h-1.5 rounded-full {config.dot} {status === 'running' || status === 'normal' ? 'animate-pulse' : ''}"></span>
  {config.label}
</span>

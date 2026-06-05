<script>
  import { page } from '$app/stores';

  const navItems = [
    { href: '/', label: 'Overview', icon: '📊' },
    { href: '/telemetry', label: 'Telemetry', icon: '📡' },
    { href: '/quality', label: 'Quality', icon: '✓' },
    { href: '/operations', label: 'Operations', icon: '⚙️' },
    { href: '/anomalies', label: 'Anomalies', icon: '⚠️' },
  ];

  let currentPath = $derived($page.url.pathname);
  let mobileMenuOpen = $state(false);
</script>

<nav class="bg-OEMPartner-blue shadow-lg sticky top-0 z-50">
  <div class="max-w-7xl mx-auto px-4">
    <div class="flex items-center justify-between h-16">
      <!-- Logo and brand -->
      <div class="flex items-center">
        <a href="/" class="flex items-center gap-3">
          <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
            <span class="text-OEMPartner-blue font-bold text-lg">Y</span>
          </div>
          <div class="hidden sm:block">
            <span class="text-white text-xl font-bold tracking-wide">OEMPartner</span>
            <span class="text-white/70 text-sm ml-2">MES Dashboard</span>
          </div>
        </a>
      </div>

      <!-- Navigation links (desktop) -->
      <div class="hidden md:block">
        <div class="flex items-center space-x-1">
          {#each navItems as item}
            <a
              href={item.href}
              class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                     {currentPath === item.href
                       ? 'bg-white text-OEMPartner-blue shadow-md'
                       : 'text-white/90 hover:bg-white/10 hover:text-white'}"
            >
              <span class="mr-1.5">{item.icon}</span>
              {item.label}
            </a>
          {/each}
        </div>
      </div>

      <!-- Right side -->
      <div class="hidden md:flex items-center gap-4">
        <div class="text-right">
          <div class="text-white/90 text-sm font-medium">Manufacturing Group Manufacturing</div>
          <div class="text-white/60 text-xs">Malaysia</div>
        </div>
        <div class="w-8 h-8 bg-OEMPartner-red rounded-full flex items-center justify-center">
          <span class="text-white text-xs font-bold">MFG</span>
        </div>
      </div>

      <!-- Mobile menu button -->
      <button
        type="button"
        class="md:hidden p-2 rounded-lg text-white hover:bg-white/10"
        onclick={() => mobileMenuOpen = !mobileMenuOpen}
        aria-label="Toggle menu"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          {#if mobileMenuOpen}
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          {:else}
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          {/if}
        </svg>
      </button>
    </div>
  </div>

  <!-- Mobile menu -->
  {#if mobileMenuOpen}
    <div class="md:hidden border-t border-white/10">
      <div class="px-2 pt-2 pb-3 space-y-1">
        {#each navItems as item}
          <a
            href={item.href}
            class="block px-4 py-3 rounded-lg text-base font-medium transition-colors
                   {currentPath === item.href
                     ? 'bg-white text-OEMPartner-blue'
                     : 'text-white hover:bg-white/10'}"
            onclick={() => mobileMenuOpen = false}
          >
            <span class="mr-2">{item.icon}</span>
            {item.label}
          </a>
        {/each}
      </div>
      <div class="px-4 py-3 border-t border-white/10">
        <div class="text-white/90 text-sm font-medium">Manufacturing Group Manufacturing</div>
        <div class="text-white/60 text-xs">Malaysia</div>
      </div>
    </div>
  {/if}
</nav>

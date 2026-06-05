<script>
  import { page } from '$app/stores';
  import '../app.css';
</script>

<div class="min-h-screen bg-surface">
  <!-- Clean Navigation -->
  <nav class="sticky top-0 z-50 bg-OEMPartner-blue shadow-lg">
    <div class="max-w-7xl mx-auto px-4">
      <div class="flex items-center justify-between h-14">
        <!-- Logo & Brand -->
        <a href="/" class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"/>
            </svg>
          </div>
          <div class="flex items-center gap-2">
            <span class="font-bold text-white text-lg">OEMPartner</span>
            <span class="text-xs bg-OEMPartner-red px-2 py-0.5 rounded text-white font-bold">MFG</span>
          </div>
        </a>

        <!-- Navigation Links -->
        <div class="flex items-center gap-1">
          <a href="/" class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 {$page.url.pathname === '/' ? 'text-OEMPartner-blue bg-white shadow-sm' : 'text-blue-100 hover:text-white hover:bg-white/10'}">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/>
            </svg>
            Dashboard
          </a>
          <a href="/telemetry" class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 {$page.url.pathname === '/telemetry' ? 'text-OEMPartner-blue bg-white shadow-sm' : 'text-blue-100 hover:text-white hover:bg-white/10'}">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
            </svg>
            Telemetry
          </a>
          <a href="/quality" class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 {$page.url.pathname === '/quality' ? 'text-OEMPartner-blue bg-white shadow-sm' : 'text-blue-100 hover:text-white hover:bg-white/10'}">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            Quality
          </a>
          <a href="/operations" class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 {$page.url.pathname === '/operations' ? 'text-OEMPartner-blue bg-white shadow-sm' : 'text-blue-100 hover:text-white hover:bg-white/10'}">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
            Operations
          </a>
          <a href="/anomalies" class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 {$page.url.pathname === '/anomalies' ? 'text-OEMPartner-blue bg-white shadow-sm' : 'text-blue-100 hover:text-white hover:bg-white/10'}">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
            Anomalies
          </a>
        </div>

        <!-- Company Branding -->
        <div class="flex items-center gap-3">
          <div class="text-right hidden md:block">
            <div class="text-sm font-medium text-white">Manufacturing Group Manufacturing</div>
            <div class="text-xs text-blue-200">Malaysia</div>
          </div>
          <div class="w-8 h-8 rounded-full bg-OEMPartner-red flex items-center justify-center text-white text-xs font-bold">
            MFG
          </div>
        </div>
      </div>
    </div>
    <!-- Red accent bar -->
    <div class="h-1 bg-OEMPartner-red"></div>
  </nav>

  <!-- Main Content -->
  <main class="pb-8">
    <slot />
  </main>
</div>


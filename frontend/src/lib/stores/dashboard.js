/**
 * Svelte stores for dashboard state
 */
import { writable, derived } from 'svelte/store';

// Selected line filter
export const selectedLine = writable(null);

// Selected date filter
export const selectedDate = writable(null);

// Dashboard data stores
export const qualityData = writable(null);
export const operationsData = writable(null);
export const anomalyData = writable(null);
export const summaryData = writable(null);

// Loading states
export const loading = writable({
  quality: false,
  operations: false,
  anomalies: false,
  summary: false,
  telemetry: false,
});

// Error states
export const errors = writable({
  quality: null,
  operations: null,
  anomalies: null,
  summary: null,
  telemetry: null,
});

// Assembly lines
export const assemblyLines = writable([]);

// Telemetry data
export const telemetryData = writable({
  data: [],
  pagination: { total: 0, limit: 100, skip: 0, hasMore: false },
});

// Latest machine status
export const latestMachineStatus = writable([]);

// Derived store for quick status overview
export const statusOverview = derived(
  [qualityData, operationsData, anomalyData],
  ([$quality, $operations, $anomalies]) => {
    if (!$quality || !$operations) {
      return null;
    }

    return {
      qualityScore: $quality?.summary?.overallQualityScore ?? 0,
      defectRate: $quality?.summary?.avgDefectRate ?? 0,
      criticalAlerts: $quality?.summary?.criticalAlerts ?? 0,
      unitsProduced: $operations?.summary?.totalUnits ?? 0,
      utilizationRate: $operations?.summary?.utilizationRate ?? 0,
      anomalyCount: $anomalies?.unacknowledgedCount ?? 0,
    };
  }
);

// Set loading state helper
export function setLoading(key, value) {
  loading.update((state) => ({ ...state, [key]: value }));
}

// Set error state helper
export function setError(key, error) {
  errors.update((state) => ({ ...state, [key]: error }));
}

// Clear all errors
export function clearErrors() {
  errors.set({
    quality: null,
    operations: null,
    anomalies: null,
    summary: null,
    telemetry: null,
  });
}

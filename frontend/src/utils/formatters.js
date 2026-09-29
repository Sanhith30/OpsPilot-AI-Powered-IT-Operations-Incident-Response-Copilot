/**
 * Formatting helpers for OpsPilot
 */

export function formatDate(isoString) {
  if (!isoString) return '—';
  try {
    const d = new Date(isoString);
    return d.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  } catch {
    return isoString;
  }
}

export function formatRelativeTime(isoString) {
  if (!isoString) return '—';
  try {
    const d = new Date(isoString);
    const diffMs = Date.now() - d.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    if (diffSec < 60) return `${diffSec}s ago`;
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHour = Math.floor(diffMin / 60);
    if (diffHour < 24) return `${diffHour}h ago`;
    return `${Math.floor(diffHour / 24)}d ago`;
  } catch {
    return isoString;
  }
}

export function formatScore(score) {
  if (score === null || score === undefined) return '0.00';
  return Number(score).toFixed(2);
}

export function formatPercent(score) {
  if (score === null || score === undefined) return '0%';
  return `${Math.round(Number(score) * 100)}%`;
}

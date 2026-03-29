import { useState, useEffect } from 'react';
import type { SyncStatus as SyncStatusType } from '../types';
import { getSyncStatus } from '../api/client';

function formatRelativeTime(isoStr: string | null): string {
  if (!isoStr) return 'Never';
  const d = new Date(isoStr);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return 'Just now';
  if (diffMin < 60) return `${diffMin} min ago`;
  const diffHrs = Math.floor(diffMin / 60);
  if (diffHrs < 24) return `${diffHrs}h ago`;
  return d.toLocaleDateString('nl-NL');
}

export function SyncStatus() {
  const [status, setStatus] = useState<SyncStatusType | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        setStatus(await getSyncStatus());
      } catch {
        // Ignore errors
      }
    };
    fetchStatus();
    const ms = status?.status === 'syncing' ? 10000 : 60000;
    const interval = setInterval(fetchStatus, ms);
    return () => clearInterval(interval);
  }, [status?.status]);

  if (!status) return null;

  const isSyncing = status.status === 'syncing';

  return (
    <div className="flex items-center gap-3 text-xs text-gray-400">
      <span>
        DB: {status.total_in_db.toLocaleString('nl-NL')} listings
      </span>
      <span className="text-gray-600">|</span>
      {isSyncing ? (
        <span className="text-blue-400">
          Syncing{status.current_source ? ` ${status.current_source}` : ''}{status.sync_type === 'full' && status.progress_pct != null ? ` (${status.progress_pct}%)` : '...'}
        </span>
      ) : (
        <span>Last sync: {formatRelativeTime(status.last_completed)}</span>
      )}
    </div>
  );
}

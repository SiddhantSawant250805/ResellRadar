"use client";

import React, { useState } from 'react';
import { HardDrive, UploadCloud, FileCheck, CheckCircle2 } from 'lucide-react';

interface HDFSPanelProps {
  hdfsData: {
    status: string;
    type: string;
    endpoint: string;
    hdfs_path: string;
    pushed_files_count: number;
    total_bytes_pushed: number;
    last_sync_timestamp: string | null;
  };
  onSync: () => Promise<void>;
}

export const HDFSPanel: React.FC<HDFSPanelProps> = ({ hdfsData, onSync }) => {
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);

  const handleSyncClick = async () => {
    setIsSyncing(true);
    setSyncMsg(null);
    try {
      await onSync();
      setSyncMsg('HDFS Push Completed Successfully');
    } catch (err: any) {
      setSyncMsg('HDFS Push Trigger Error');
    } finally {
      setIsSyncing(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div id="hdfs" className="bg-surface-container border border-outline-variant rounded-none p-5 shadow-sm">
      <div className="flex flex-wrap justify-between items-center mb-4 border-b border-outline-variant pb-3 gap-2">
        <div className="flex items-center gap-2">
          <HardDrive className="w-4 h-4 text-tertiary" />
          <h2 className="text-xs font-mono font-bold text-tertiary tracking-widest uppercase">
            03 // HDFS DISTRIBUTED STORAGE SYNC
          </h2>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="text-outline">TARGET HDFS DIRECTORY:</span>
          <code className="bg-surface-lowest border border-outline-variant px-2 py-0.5 text-primary text-[11px]">
            {hdfsData.hdfs_path || '/data/raw/'}
          </code>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        {/* Connection Status Tile */}
        <div className="bg-surface-lowest border border-outline-variant p-3.5 flex flex-col justify-between font-mono">
          <div className="text-[10px] text-outline uppercase mb-1">HDFS CONNECTION STATE</div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-secondary animate-pulse" />
            <span className="text-sm font-bold text-secondary">{hdfsData.status}</span>
          </div>
          <div className="text-[11px] text-outline truncate" title={hdfsData.endpoint}>
            {hdfsData.type} ({hdfsData.endpoint})
          </div>
        </div>

        {/* Pushed File Count Tile */}
        <div className="bg-surface-lowest border border-outline-variant p-3.5 flex flex-col justify-between font-mono">
          <div className="text-[10px] text-outline uppercase mb-1">COMMITTED HDFS FILES</div>
          <div className="text-2xl font-bold text-white mb-1">
            {hdfsData.pushed_files_count} <span className="text-xs font-normal text-outline">Files</span>
          </div>
          <div className="text-[11px] text-outline">
            Total HDFS Volume: {formatBytes(hdfsData.total_bytes_pushed)}
          </div>
        </div>

        {/* Last Sync & Action Tile */}
        <div className="bg-surface-lowest border border-outline-variant p-3.5 flex flex-col justify-between font-mono">
          <div>
            <div className="text-[10px] text-outline uppercase mb-1">LAST SYNC TIMESTAMP</div>
            <div className="text-xs text-white mb-2">
              {hdfsData.last_sync_timestamp ? hdfsData.last_sync_timestamp : 'No sync recorded yet'}
            </div>
          </div>

          <button
            onClick={handleSyncClick}
            disabled={isSyncing}
            className="w-full bg-tertiary/20 border border-tertiary text-tertiary hover:bg-tertiary/30 font-bold text-xs py-2 px-3 flex items-center justify-center gap-2 shadow-[0_0_10px_rgba(99,102,241,0.25)] transition-all disabled:opacity-50"
          >
            <UploadCloud className="w-4 h-4" />
            <span>{isSyncing ? 'SYNCING TO HDFS...' : 'SYNC RAW JSON TO HDFS NOW'}</span>
          </button>
        </div>
      </div>

      {syncMsg && (
        <div className="p-2.5 bg-secondary/10 border border-secondary text-secondary font-mono text-xs mb-3 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{syncMsg}</span>
        </div>
      )}
    </div>
  );
};

"use client";

import React from 'react';
import { Terminal, RefreshCw, Activity, HardDrive, ShieldCheck, Cpu } from 'lucide-react';

interface HeaderNavProps {
  state: any;
  onRefresh: () => void;
}

export const HeaderNav: React.FC<HeaderNavProps> = ({ state, onRefresh }) => {
  const isRunning = state?.pipeline_state?.is_running;
  const hdfsStatus = state?.hdfs_telemetry?.status || 'CONNECTED';

  return (
    <header className="flex flex-wrap justify-between items-center w-full px-6 py-3 bg-surface-lowest border-b border-outline-variant sticky top-0 z-50 shadow-md">
      {/* Title & Pulse */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <span className={`w-3 h-3 rounded-full ${isRunning ? 'bg-secondary animate-ping' : 'bg-primary'}`} />
          <h1 className="text-xl font-bold tracking-tight text-primary font-mono">
            ResellRadar <span className="text-xs text-outline font-sans ml-1">// INGESTION_CONSOLE v2.8.4</span>
          </h1>
        </div>

        <nav className="hidden md:flex items-center gap-4 ml-4 text-xs font-mono tracking-wider">
          <a href="#controller" className="text-primary border-b border-primary pb-0.5 hover:opacity-80">01_CONTROLLER</a>
          <a href="#metrics" className="text-outline hover:text-white transition-colors">02_METRICS</a>
          <a href="#stream" className="text-outline hover:text-white transition-colors">03_RAW_STREAM</a>
          <a href="#hdfs" className="text-outline hover:text-white transition-colors">04_HDFS_SYNC</a>
        </nav>
      </div>

      {/* Cluster Diagnostics */}
      <div className="hidden lg:flex items-center gap-4 px-3 py-1.5 rounded bg-surface-container border border-outline-variant text-xs font-mono">
        <div className="flex items-center gap-1.5">
          <Cpu className="w-3.5 h-3.5 text-primary" />
          <span className="text-outline">NODE:</span>
          <span className="text-primary font-medium">localhost-master-01</span>
        </div>
        <div className="h-3 w-[1px] bg-outline-variant" />
        <div className="flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-secondary" />
          <span className="text-outline">STATE:</span>
          <span className={`font-semibold ${isRunning ? 'text-secondary animate-pulse' : 'text-primary'}`}>
            {isRunning ? 'STREAMING_ACTIVE' : 'IDLE_READY'}
          </span>
        </div>
        <div className="h-3 w-[1px] bg-outline-variant" />
        <div className="flex items-center gap-1.5">
          <HardDrive className="w-3.5 h-3.5 text-tertiary" />
          <span className="text-outline">HDFS:</span>
          <span className="text-secondary font-medium">{hdfsStatus}</span>
        </div>
      </div>

      {/* Header Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={onRefresh}
          className="p-2 hover:bg-surface-high hover:text-primary transition-colors rounded text-outline border border-outline-variant flex items-center gap-1.5 text-xs font-mono"
          title="Manual Telemetry Refresh"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>REFRESH</span>
        </button>
      </div>
    </header>
  );
};

"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Terminal as TerminalIcon, Filter } from 'lucide-react';

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
}

interface LogTerminalStreamProps {
  logs: LogEntry[];
}

export const LogTerminalStream: React.FC<LogTerminalStreamProps> = ({ logs }) => {
  const [filter, setFilter] = useState<string>('ALL');
  const terminalEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const filteredLogs = logs.filter((log) => {
    if (filter === 'ALL') return true;
    return log.level.toUpperCase() === filter;
  });

  const getLevelBadgeClass = (level: string) => {
    switch (level.toUpperCase()) {
      case 'INFO':
        return 'text-primary bg-primary/10 border-primary/30';
      case 'ACK':
      case 'SUCCESS':
        return 'text-secondary bg-secondary/10 border-secondary/30';
      case 'WARN':
      case 'RETRY':
        return 'text-accent-amber bg-accent-amber/10 border-accent-amber/30';
      case 'ERR':
      case 'ERROR':
        return 'text-accent-crimson bg-accent-crimson/10 border-accent-crimson/30';
      default:
        return 'text-outline bg-surface-high border-outline-variant';
    }
  };

  return (
    <div className="bg-surface-lowest border border-outline-variant rounded-none flex flex-col h-full font-mono text-xs shadow-inner">
      {/* Terminal Top Bar */}
      <div className="bg-surface-container px-4 py-2 border-b border-outline-variant flex justify-between items-center">
        <div className="flex items-center gap-2">
          <TerminalIcon className="w-4 h-4 text-primary" />
          <span className="text-xs font-bold text-primary tracking-wider uppercase">
            LIVE INGESTION ANSI BUFFER STREAM
          </span>
        </div>

        {/* Filter Badges */}
        <div className="flex items-center gap-1.5">
          <Filter className="w-3.5 h-3.5 text-outline mr-1" />
          {['ALL', 'INFO', 'ACK', 'WARN', 'SUCCESS'].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setFilter(lvl)}
              className={`px-2 py-0.5 text-[10px] border transition-colors ${
                filter === lvl ? 'bg-primary border-primary text-black font-bold' : 'bg-surface-container border-outline-variant text-outline hover:text-white'
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Terminal Content Buffer */}
      <div className="p-4 overflow-y-auto max-h-[220px] min-h-[160px] custom-scrollbar space-y-1 bg-black/60">
        {filteredLogs.length === 0 ? (
          <div className="text-outline italic text-center py-4">No log trace buffer matched filter '{filter}'.</div>
        ) : (
          filteredLogs.map((log, idx) => (
            <div key={idx} className="flex items-start gap-2.5 leading-relaxed font-mono">
              <span className="text-outline text-[11px] select-none">[{log.timestamp}]</span>
              <span className={`px-1.5 py-0.2 border text-[10px] uppercase ${getLevelBadgeClass(log.level)}`}>
                {log.level}
              </span>
              <span className="text-white/90 break-all">{log.message}</span>
            </div>
          ))
        )}
        <div ref={terminalEndRef} />
      </div>
    </div>
  );
};

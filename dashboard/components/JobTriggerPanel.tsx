"use client";

import React, { useState } from 'react';
import { Play, Square, Settings, Cpu, Layers } from 'lucide-react';

interface JobTriggerPanelProps {
  isRunning: boolean;
  onStart: (category: string, target: number, threads: number) => void;
  onStop: () => void;
}

export const JobTriggerPanel: React.FC<JobTriggerPanelProps> = ({ isRunning, onStart, onStop }) => {
  const [category, setCategory] = useState<string>('all');
  const [target, setTarget] = useState<number>(500);
  const [threads, setThreads] = useState<number>(16);

  return (
    <div id="controller" className="bg-surface-container border border-outline-variant p-5 rounded-none shadow-sm flex flex-col justify-between h-full">
      <div>
        <div className="flex justify-between items-center mb-4 border-b border-outline-variant pb-2">
          <div className="flex items-center gap-2">
            <Settings className="w-4 h-4 text-primary" />
            <h2 className="text-xs font-mono font-bold text-primary tracking-widest uppercase">
              01 // JOB EXECUTION CONTROLLER
            </h2>
          </div>
          <span className={`px-2 py-0.5 text-[10px] font-mono border ${isRunning ? 'bg-secondary/10 border-secondary text-secondary' : 'bg-surface-high border-outline text-outline'}`}>
            {isRunning ? 'DAEMON ACTIVE' : 'DAEMON STANDBY'}
          </span>
        </div>

        {/* Category Selection */}
        <div className="mb-4">
          <label className="text-[11px] font-mono text-outline uppercase block mb-1.5 flex items-center gap-1">
            <Layers className="w-3 h-3 text-primary" /> Target Category Stream
          </label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { id: 'phones', label: 'Phones & Mobile' },
              { id: 'furniture', label: 'Furniture & Decor' },
              { id: 'all', label: 'Both Categories' },
            ].map((cat) => (
              <button
                key={cat.id}
                disabled={isRunning}
                onClick={() => setCategory(cat.id)}
                className={`py-2 px-3 text-xs font-mono border transition-all text-center ${
                  category === cat.id
                    ? 'bg-primary/10 border-primary text-primary font-bold shadow-[0_0_8px_rgba(76,215,246,0.25)]'
                    : 'bg-surface-lowest border-outline-variant text-outline hover:text-white'
                } ${isRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Batch Target Volume */}
        <div className="mb-4">
          <label className="text-[11px] font-mono text-outline uppercase block mb-1.5">
            Target Batch Volume (Listings Count)
          </label>
          <div className="flex gap-2 mb-2">
            {[500, 5000, 50000].map((val) => (
              <button
                key={val}
                disabled={isRunning}
                onClick={() => setTarget(val)}
                className={`py-1 px-3 text-xs font-mono border ${
                  target === val ? 'bg-primary border-primary text-black font-bold' : 'bg-surface-lowest border-outline-variant text-outline'
                }`}
              >
                {val.toLocaleString()} {val === 50000 ? '(FULL TARGET)' : ''}
              </button>
            ))}
          </div>
          <input
            type="number"
            disabled={isRunning}
            value={target}
            onChange={(e) => setTarget(Math.max(10, parseInt(e.target.value) || 500))}
            className="w-full bg-surface-lowest border border-outline-variant px-3 py-1.5 text-xs font-mono text-white focus:outline-none focus:border-primary"
          />
        </div>

        {/* Worker Threads Slider */}
        <div className="mb-4">
          <div className="flex justify-between items-center mb-1">
            <label className="text-[11px] font-mono text-outline uppercase flex items-center gap-1">
              <Cpu className="w-3 h-3 text-tertiary" /> Worker Concurrency Threads
            </label>
            <span className="text-xs font-mono text-primary font-bold">{threads} Threads</span>
          </div>
          <input
            type="range"
            min="1"
            max="32"
            disabled={isRunning}
            value={threads}
            onChange={(e) => setThreads(parseInt(e.target.value))}
            className="w-full accent-primary bg-surface-lowest h-1.5 rounded cursor-pointer"
          />
        </div>
      </div>

      {/* Action Trigger Buttons */}
      <div className="pt-3 border-t border-outline-variant flex gap-3">
        {!isRunning ? (
          <button
            onClick={() => onStart(category, target, threads)}
            className="flex-1 bg-primary border border-primary text-black hover:bg-primary-dim font-mono font-bold text-xs py-2.5 px-4 flex items-center justify-center gap-2 shadow-[0_0_12px_rgba(76,215,246,0.3)] transition-all"
          >
            <Play className="w-4 h-4 fill-black" />
            <span>START SCRAPE PIPELINE</span>
          </button>
        ) : (
          <button
            onClick={onStop}
            className="flex-1 bg-accent-crimson/20 border border-accent-crimson text-accent-crimson hover:bg-accent-crimson/30 font-mono font-bold text-xs py-2.5 px-4 flex items-center justify-center gap-2 shadow-[0_0_12px_rgba(239,68,68,0.3)] transition-all animate-pulse"
          >
            <Square className="w-4 h-4 fill-accent-crimson" />
            <span>HALT WORKER DAEMONS</span>
          </button>
        )}
      </div>
    </div>
  );
};

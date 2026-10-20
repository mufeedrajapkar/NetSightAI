
import React from 'react'
import { Server, Cpu, Radio, Activity } from 'lucide-react'
import type { SystemStatus } from '../types'

interface TopBarProps {
  status: SystemStatus | null
  loading: boolean
  autoRefresh?: boolean
  onToggleAutoRefresh?: () => void
}

export const TopBar: React.FC<TopBarProps> = ({
  status,
  loading,
  autoRefresh = true,
  onToggleAutoRefresh,
}) => {
  const isOnline = Boolean(status && status.status === 'online')
  const isModelReady = Boolean(status?.model?.is_loaded)
  const isLiveCapturing = Boolean(status?.active_capture?.is_capturing)

  return (
    <header className="z-10 flex min-h-16 shrink-0 items-center justify-between gap-4 border-b border-[#253044] bg-[#0e1622]/95 px-6 py-3 backdrop-blur-xl">
      {/* Page Identity */}
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-blue-500/20 bg-blue-500/[0.08]">
          <Activity className="h-[17px] w-[17px] text-blue-400" />
        </div>

        <div className="min-w-0">
          <h2 className="truncate text-xs font-semibold uppercase tracking-[0.15em] text-gray-200">
            Traffic Intelligence
          </h2>
          <p className="mt-1 text-[10px] text-gray-500">
            Network security monitoring
          </p>
        </div>
      </div>

      {/* System Status */}
      <div className="flex flex-wrap items-center justify-end gap-2">
        {/* Auto Refresh */}
        <button
          type="button"
          onClick={onToggleAutoRefresh}
          disabled={!onToggleAutoRefresh}
          aria-pressed={autoRefresh}
          title={
            autoRefresh
              ? 'Auto-refresh active (every 3.5s). Click to pause.'
              : 'Auto-refresh paused. Click to resume.'
          }
          className={`flex items-center gap-2 rounded-lg border px-3 py-2 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60 disabled:cursor-default ${
            autoRefresh
              ? 'border-emerald-500/20 bg-emerald-500/[0.06] text-emerald-300 hover:bg-emerald-500/[0.12]'
              : 'border-[#29364a] bg-[#131d2b] text-gray-400 hover:bg-[#192537]'
          }`}
        >
          <span className="relative flex h-2 w-2">
            {autoRefresh && (
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-40" />
            )}
            <span
              className={`relative inline-flex h-2 w-2 rounded-full ${
                autoRefresh ? 'bg-emerald-400' : 'bg-gray-500'
              }`}
            />
          </span>

          <span className="whitespace-nowrap text-[10px] font-medium">
            {autoRefresh ? 'Live · 3.5s' : 'Polling paused'}
          </span>
        </button>

        {/* Capture Mode */}
        <div className="flex items-center gap-2 rounded-lg border border-[#29364a] bg-[#131d2b] px-3 py-2">
          <Radio
            className={`h-3.5 w-3.5 shrink-0 ${
              isLiveCapturing
                ? 'animate-pulse text-emerald-400'
                : 'text-blue-400'
            }`}
          />
          <div className="hidden sm:block">
            <p className="text-[9px] uppercase tracking-wider text-gray-500">
              Capture mode
            </p>
            <p className="mt-0.5 whitespace-nowrap text-[10px] font-medium text-gray-200">
              {isLiveCapturing ? 'Live Capture' : 'PCAP Replay'}
            </p>
          </div>
        </div>

        {/* AI Model Status */}
        <div className="flex items-center gap-2 rounded-lg border border-[#29364a] bg-[#131d2b] px-3 py-2">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-purple-500/[0.09]">
            <Cpu className="h-3.5 w-3.5 text-purple-400" />
          </div>

          <div className="hidden md:block">
            <p className="text-[9px] uppercase tracking-wider text-gray-500">
              AI model
            </p>
            <p
              title={status?.model?.model_type || undefined}
              className={`mt-0.5 max-w-32 truncate text-[10px] font-medium ${
                isModelReady ? 'text-gray-200' : 'text-rose-400'
              }`}
            >
              {status?.model?.model_type ||
                (loading ? 'Loading...' : 'Unavailable')}
            </p>
          </div>
        </div>

        {/* Backend Status */}
        <div className="flex items-center gap-2 rounded-lg border border-[#29364a] bg-[#131d2b] px-3 py-2">
          <Server
            className={`h-3.5 w-3.5 shrink-0 ${
              isOnline ? 'text-emerald-400' : 'text-rose-400'
            }`}
          />

          <div>
            <p className="text-[9px] uppercase tracking-wider text-gray-500">
              Backend
            </p>
            <div className="mt-0.5 flex items-center gap-1.5">
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  isOnline ? 'bg-emerald-400' : 'bg-rose-400'
                }`}
              />
              <span
                className={`text-[10px] font-semibold ${
                  isOnline ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {isOnline ? 'Online' : 'Offline'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

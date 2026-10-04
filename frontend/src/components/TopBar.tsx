import React from 'react'
import { Server, Cpu, Radio } from 'lucide-react'
import type { SystemStatus } from '../types'

interface TopBarProps {
  status: SystemStatus | null
  loading: boolean
}

export const TopBar: React.FC<TopBarProps> = ({ status, loading }) => {
  const isOnline = Boolean(status && status.status === 'online')
  const isModelReady = Boolean(status?.model?.is_loaded)
  const isLiveCapturing = Boolean(status?.active_capture?.is_capturing)

  return (
    <header className="h-16 bg-[#11131a] border-b border-[#1f2430] px-6 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-3">
        <h2 className="text-xs font-medium uppercase tracking-wider text-gray-400">
          Traffic Intelligence Dashboard
        </h2>
      </div>

      <div className="flex items-center gap-4 text-xs">
        {/* Operating Mode Indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#181a24] border border-[#262b3a]">
          <Radio className={`w-3.5 h-3.5 ${isLiveCapturing ? 'text-emerald-400 animate-pulse' : 'text-blue-400'}`} />
          <span className="text-gray-400">Mode:</span>
          <span className="font-medium text-gray-200">
            {isLiveCapturing ? 'Live Capture' : 'PCAP Replay (Offline)'}
          </span>
        </div>

        {/* AI Model Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#181a24] border border-[#262b3a]">
          <Cpu className="w-3.5 h-3.5 text-purple-400" />
          <span className="text-gray-400">Model:</span>
          <span className={`font-medium ${isModelReady ? 'text-gray-200' : 'text-rose-400'}`}>
            {status?.model?.model_type || (loading ? 'Loading...' : 'Unavailable')}
          </span>
        </div>

        {/* Backend Status Indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#181a24] border border-[#262b3a]">
          <Server className="w-3.5 h-3.5 text-gray-400" />
          <span className="text-gray-400">Backend:</span>
          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-400' : 'bg-rose-400'}`} />
            <span className={`font-medium ${isOnline ? 'text-emerald-400' : 'text-rose-400'}`}>
              {isOnline ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}

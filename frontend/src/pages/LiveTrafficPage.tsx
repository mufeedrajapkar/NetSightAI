import React, { useState } from 'react'
import {
  Play,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react'
import type { FlowRecord, SystemStatus } from '../types'
import { triggerReplay } from '../services/api'

interface LiveTrafficPageProps {
  flows: FlowRecord[]
  status: SystemStatus | null
  loading: boolean
  onSelectFlow: (flow: FlowRecord) => void
  onRefresh: () => void
}

export const LiveTrafficPage: React.FC<LiveTrafficPageProps> = ({
  flows,
  status,
  loading,
  onSelectFlow,
  onRefresh,
}) => {
  const [replayingTier, setReplayingTier] = useState<string | null>(null)
  const [replaySuccess, setReplaySuccess] = useState<string | null>(null)
  const [replayError, setReplayError] = useState<string | null>(null)

  const handleReplay = async (tier: string) => {
    try {
      setReplayingTier(tier)
      setReplayError(null)
      setReplaySuccess(null)
      const res = await triggerReplay(tier)
      setReplaySuccess(`Successfully parsed and classified ${tier} PCAP flow (${res.flow.flow_id})`)
      onRefresh()
    } catch (err: any) {
      setReplayError(err.message || 'PCAP replay failed')
    } finally {
      setReplayingTier(null)
    }
  }

  const isLiveSupported = status?.environment?.can_capture_live ?? false
  const totalPackets = flows.reduce((acc, f) => acc + f.packet_count, 0)
  const totalBytes = flows.reduce((acc, f) => acc + f.bytes_transferred, 0)

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-100 tracking-tight">
            Traffic Capture & PCAP Replay
          </h2>
          <p className="text-xs text-gray-400 mt-1">
            Execute offline Scapy PCAP replay or manage network traffic ingestion sessions.
          </p>
        </div>
        <button
          onClick={onRefresh}
          className="flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium bg-[#1a1d28] hover:bg-[#222634] text-gray-300 border border-[#262b3a] transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Flows
        </button>
      </div>

      {/* Live Capture Notice Banner */}
      {!isLiveSupported && (
        <div className="p-4 rounded-lg bg-blue-950/20 border border-blue-800/30 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <div className="font-semibold text-blue-300">
              Live capture is not currently available. Use PCAP Replay to analyse traffic.
            </div>
            <div className="text-gray-400 leading-relaxed">
              Windows native live packet sniffing requires Npcap with loopback support and Administrator privilege.
              SentinelNet operates in zero-dependency <strong>PCAP Replay Mode</strong>, which safely parses actual
              binary packet captures with 100% fidelity.
            </div>
          </div>
        </div>
      )}

      {/* PCAP Replay Control Matrix */}
      <div className="p-6 rounded-xl bg-[#12141d] border border-[#202432]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-200">
              PCAP Replay Controller
            </h3>
            <p className="text-[11px] text-gray-400">
              Feed genuine Scapy-recorded TCP/IP packet captures into the CN FlowProcessor and AI Bridge.
            </p>
          </div>
          <span className="px-2.5 py-1 rounded bg-[#181c28] border border-[#262e40] text-[11px] font-mono text-blue-400">
            Engine: Scapy rdpcap
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Tier 1 Replay Card */}
          <div className="p-4 rounded-lg bg-[#151822] border border-[#232734] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-xs text-gray-100">Tier 1: Naive Bot</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-orange-500/10 text-orange-400 border border-orange-500/20">
                  Fixed Interval
                </span>
              </div>
              <p className="text-[11px] text-gray-400 mb-4">
                Fixed 0.5s interval HTTP requests against single endpoint. Deterministic timing profile.
              </p>
            </div>
            <button
              onClick={() => handleReplay('tier1')}
              disabled={Boolean(replayingTier)}
              className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-md text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white transition-colors disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 ${replayingTier === 'tier1' ? 'animate-spin' : ''}`} />
              {replayingTier === 'tier1' ? 'Replaying...' : 'Replay Tier 1 PCAP'}
            </button>
          </div>

          {/* Tier 2 Replay Card */}
          <div className="p-4 rounded-lg bg-[#151822] border border-[#232734] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-xs text-gray-100">Tier 2: Jittered Bot</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-orange-500/10 text-orange-400 border border-orange-500/20">
                  Random Jitter
                </span>
              </div>
              <p className="text-[11px] text-gray-400 mb-4">
                Uniform random delays (0.2s - 2.0s), randomized query terms, rotating User-Agent headers.
              </p>
            </div>
            <button
              onClick={() => handleReplay('tier2')}
              disabled={Boolean(replayingTier)}
              className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-md text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white transition-colors disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 ${replayingTier === 'tier2' ? 'animate-spin' : ''}`} />
              {replayingTier === 'tier2' ? 'Replaying...' : 'Replay Tier 2 PCAP'}
            </button>
          </div>

          {/* Tier 3 Replay Card */}
          <div className="p-4 rounded-lg bg-[#151822] border border-[#232734] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-xs text-gray-100">Tier 3: Mimicking Bot</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-orange-500/10 text-orange-400 border border-orange-500/20">
                  Human Emulation
                </span>
              </div>
              <p className="text-[11px] text-gray-400 mb-4">
                Empirical human delay distribution, reading pauses, realistic multi-step browsing paths.
              </p>
            </div>
            <button
              onClick={() => handleReplay('tier3')}
              disabled={Boolean(replayingTier)}
              className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-md text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white transition-colors disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 ${replayingTier === 'tier3' ? 'animate-spin' : ''}`} />
              {replayingTier === 'tier3' ? 'Replaying...' : 'Replay Tier 3 PCAP'}
            </button>
          </div>
        </div>

        {/* Feedback Alert */}
        {replaySuccess && (
          <div className="mt-4 p-3 rounded-lg bg-emerald-950/30 border border-emerald-800/40 text-emerald-400 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{replaySuccess}</span>
          </div>
        )}
        {replayError && (
          <div className="mt-4 p-3 rounded-lg bg-rose-950/30 border border-rose-800/40 text-rose-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{replayError}</span>
          </div>
        )}
      </div>

      {/* Ingestion & Session Telemetry Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#12141d] border border-[#202432]">
          <div className="text-[10px] uppercase tracking-wider text-gray-400">Total Packets Ingested</div>
          <div className="text-xl font-mono font-semibold text-gray-100 mt-1">{totalPackets.toLocaleString()}</div>
        </div>
        <div className="p-4 rounded-xl bg-[#12141d] border border-[#202432]">
          <div className="text-[10px] uppercase tracking-wider text-gray-400">Total Bytes Evaluated</div>
          <div className="text-xl font-mono font-semibold text-gray-100 mt-1">{totalBytes.toLocaleString()} B</div>
        </div>
        <div className="p-4 rounded-xl bg-[#12141d] border border-[#202432]">
          <div className="text-[10px] uppercase tracking-wider text-gray-400">Flows Processed</div>
          <div className="text-xl font-mono font-semibold text-gray-100 mt-1">{flows.length}</div>
        </div>
        <div className="p-4 rounded-xl bg-[#12141d] border border-[#202432]">
          <div className="text-[10px] uppercase tracking-wider text-gray-400">Operating Mode</div>
          <div className="text-xl font-mono font-semibold text-blue-400 mt-1">PCAP Replay</div>
        </div>
      </div>

      {/* Flow History Stream Table */}
      <div className="p-5 rounded-xl bg-[#12141d] border border-[#202432]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-200">
              Processed Flow Stream
            </h3>
            <p className="text-[11px] text-gray-400">
              Click any flow to open the detailed statistical feature breakdown and probability distribution.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#1f2430] text-gray-400 text-[10px] uppercase tracking-wider">
                <th className="py-2.5 px-3">Flow ID</th>
                <th className="py-2.5 px-3">Device / Source</th>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Packets</th>
                <th className="py-2.5 px-3">Duration</th>
                <th className="py-2.5 px-3">Bytes</th>
                <th className="py-2.5 px-3">Predicted Class</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1a1d26]">
              {flows.map((flow) => {
                const pred = flow.predicted_label
                const devId = flow.device_id || (flow.source_file.startsWith('Agent ') ? flow.source_file.replace('Agent ', '') : 'PC01')
                const isThreat = pred === 'Bot' || pred === 'Suspicious'
                return (
                  <tr
                    key={flow.flow_id}
                    onClick={() => onSelectFlow(flow)}
                    className="hover:bg-[#161924] cursor-pointer transition-colors"
                  >
                    <td className="py-2.5 px-3 font-mono font-medium text-blue-400">
                      {flow.flow_id}
                    </td>
                    <td className="py-2.5 px-3 font-mono">
                      <div className="flex items-center gap-1.5">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold border ${
                          pred === 'Bot'
                            ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                            : pred === 'Suspicious'
                            ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                            : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                        }`}>
                          {devId}
                        </span>
                        <span className="text-gray-400 text-[10px]">
                          {flow.source_type}
                        </span>
                      </div>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-gray-400">
                      {flow.timestamp}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-gray-200">
                      {flow.packet_count}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-gray-400">
                      {flow.session_duration.toFixed(3)}s
                    </td>
                    <td className="py-2.5 px-3 font-mono text-gray-400">
                      {flow.bytes_transferred.toLocaleString()} B
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${
                          pred === 'Human'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : pred === 'Bot'
                            ? 'bg-orange-500/10 text-orange-400 border-orange-500/20'
                            : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                        }`}
                      >
                        {pred}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-[11px]">
                      {isThreat ? (
                        <span className="text-rose-400 flex items-center gap-1 font-semibold">
                          Alert Flagged
                        </span>
                      ) : (
                        <span className="text-emerald-400">
                          Clear
                        </span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

      </div>
    </div>
  )
}

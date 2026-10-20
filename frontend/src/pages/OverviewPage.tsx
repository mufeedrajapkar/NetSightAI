import React, { useMemo } from 'react'
import {
  Activity,
  UserCheck,
  Bot,
  AlertTriangle,
  Layers,
  ExternalLink,
  RefreshCw,
  Monitor,
  ShieldCheck,
  AlertCircle,
} from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import type { OverviewData, FlowRecord } from '../types'
import { StatCard } from '../components/StatCard'


interface OverviewPageProps {
  data: OverviewData | null
  loading: boolean
  onRefresh: () => void
  onSelectFlow: (flow: FlowRecord) => void
  onNavigateTab: (tab: any) => void
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  data,
  loading,
  onRefresh,
  onSelectFlow,
  onNavigateTab,
}) => {
  if (loading && !data) {
    return (
      <div className="p-8 flex items-center justify-center text-gray-400 text-xs">
        <RefreshCw className="w-4 h-4 animate-spin mr-2 text-blue-400" />
        Loading intelligence overview...
      </div>
    )
  }

  const totalFlows = data?.total_flows ?? 0
  const counts = data?.counts ?? { human: 0, bot: 0, suspicious: 0 }
  const distribution = data?.distribution ?? []
  const recentFlows = data?.recent_flows ?? []

  const hasData = totalFlows > 0

  // Derive per-device threat state from observed sessions
  const deviceThreats = useMemo(() => {
    const map = new Map<string, { latestFlow: FlowRecord; totalSessions: number }>()
    recentFlows.forEach((flow) => {
      const devId = flow.device_id || (flow.source_file.startsWith('Agent ') ? flow.source_file.replace('Agent ', '') : 'PC01')
      const existing = map.get(devId)
      if (!existing) {
        map.set(devId, { latestFlow: flow, totalSessions: 1 })
      } else {
        existing.totalSessions += 1
        if (flow.epoch_time > existing.latestFlow.epoch_time) {
          existing.latestFlow = flow
        }
      }
    })
    return Array.from(map.entries()).map(([deviceId, info]) => ({
      deviceId,
      latestFlow: info.latestFlow,
      totalSessions: info.totalSessions,
      status: info.latestFlow.predicted_label,
    }))
  }, [recentFlows])

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold text-gray-100 tracking-tight">
              Network Intelligence Overview
            </h2>
            {data?.dataset_type === 'real' ? (
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-mono font-medium">
                Dataset: Real Lab Captures
              </span>
            ) : (
              <span className="px-2.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 text-[10px] font-mono font-medium">
                Dataset: Synthetic Prototype
              </span>
            )}
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Real-time multi-device behavioral telemetry, stateful flow aggregation, and AI classifications.
          </p>
        </div>
        <button
          onClick={onRefresh}
          className="flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium bg-[#1a1d28] hover:bg-[#222634] text-gray-300 border border-[#262b3a] transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Metric Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard
          title="Total Flows"
          value={hasData ? totalFlows : 'N/A'}
          subtext="Analyzed sessions"
          icon={<Layers className="w-4 h-4" />}
          accentColor="blue"
        />
        <StatCard
          title="Human Preds"
          value={hasData ? counts.human : 'N/A'}
          subtext={`${totalFlows ? ((counts.human / totalFlows) * 100).toFixed(0) : 0}% of flows`}
          icon={<UserCheck className="w-4 h-4" />}
          accentColor="green"
        />
        <StatCard
          title="Bot Preds"
          value={hasData ? counts.bot : 'N/A'}
          subtext={`${totalFlows ? ((counts.bot / totalFlows) * 100).toFixed(0) : 0}% of flows`}
          icon={<Bot className="w-4 h-4" />}
          accentColor="orange"
        />
        <StatCard
          title="Suspicious"
          value={hasData ? counts.suspicious : 'N/A'}
          subtext={`${totalFlows ? ((counts.suspicious / totalFlows) * 100).toFixed(0) : 0}% of flows`}
          icon={<AlertTriangle className="w-4 h-4" />}
          accentColor="red"
        />
        <StatCard
          title="Active Devices"
          value={deviceThreats.length > 0 ? deviceThreats.length : '1'}
          subtext="Live Ingest & Replay"
          icon={<Monitor className="w-4 h-4" />}
          accentColor="blue"
        />
        <StatCard
          title="Model Status"
          value={data?.dataset_type === 'real' ? 'Real Trained' : 'Synthetic'}
          subtext={data?.model_type || "LogisticRegression"}
          icon={<Activity className="w-4 h-4" />}
          accentColor={data?.dataset_type === 'real' ? "green" : "blue"}
        />
      </div>

      {/* Multi-Device Security & Threat Matrix */}
      {deviceThreats.length > 0 && (
        <div className="p-5 rounded-xl bg-[#12141d] border border-[#202432]">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-200">
                Monitored Devices & Live Threat Status
              </h3>
              <p className="text-[11px] text-gray-400">
                Real-time security posture per network node based on the latest AI session classification.
              </p>
            </div>
            <span className="text-[11px] font-mono text-gray-400">
              {deviceThreats.length} device{deviceThreats.length === 1 ? '' : 's'} reporting
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {deviceThreats.map((dev) => {
              const isBot = dev.status === 'Bot'
              const isSuspicious = dev.status === 'Suspicious'


              return (
                <div
                  key={dev.deviceId}
                  className={`p-3.5 rounded-lg border transition-all ${
                    isBot
                      ? 'bg-rose-950/20 border-rose-800/40 text-rose-300'
                      : isSuspicious
                      ? 'bg-amber-950/20 border-amber-800/40 text-amber-300'
                      : 'bg-emerald-950/20 border-emerald-800/40 text-emerald-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <Monitor className="w-4 h-4" />
                      <span className="font-mono font-bold text-xs">{dev.deviceId}</span>
                    </div>
                    {isBot ? (
                      <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse">
                        <AlertTriangle className="w-3 h-3" /> BOT DETECTED
                      </span>
                    ) : isSuspicious ? (
                      <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">
                        <AlertCircle className="w-3 h-3" /> SUSPICIOUS
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                        <ShieldCheck className="w-3 h-3" /> NORMAL
                      </span>
                    )}
                  </div>

                  <div className="text-[11px] text-gray-400 flex items-center justify-between mt-2 pt-2 border-t border-white/5">
                    <span>Latest: {dev.latestFlow.tier || dev.status}</span>
                    <span className="font-mono text-[10px]">{dev.latestFlow.timestamp.split(' ')[1] || dev.latestFlow.timestamp}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}


      {/* Main Visual Section: Donut Distribution & Recent Flow Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Prediction Distribution Donut Chart */}
        <div className="p-5 rounded-xl bg-[#12141d] border border-[#202432] flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-300 mb-1">
              Prediction Distribution
            </h3>
            <p className="text-[11px] text-gray-400">
              Breakdown across classified behavioral profiles
            </p>
          </div>

          <div className="h-48 my-3 flex items-center justify-center">
            {hasData ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={75}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} stroke="#12141d" strokeWidth={2} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#161924',
                      borderColor: '#262b3a',
                      borderRadius: '8px',
                      fontSize: '11px',
                      color: '#fff',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-gray-400">No flow data recorded yet</div>
            )}
          </div>

          <div className="space-y-2 pt-2 border-t border-[#1c202b]">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                <span className="text-gray-400">Human</span>
              </div>
              <span className="font-mono font-medium text-gray-200">{counts.human}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
                <span className="text-gray-400">Bot</span>
              </div>
              <span className="font-mono font-medium text-gray-200">{counts.bot}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                <span className="text-gray-400">Suspicious</span>
              </div>
              <span className="font-mono font-medium text-gray-200">{counts.suspicious}</span>
            </div>
          </div>
        </div>

        {/* Recent Analyzed Flows Table */}
        <div className="lg:col-span-2 p-5 rounded-xl bg-[#12141d] border border-[#202432] flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-300">
                Recent Flow Telemetry
              </h3>
              <p className="text-[11px] text-gray-400">
                Latest sessions processed through FlowProcessor and AIBridge
              </p>
            </div>
            <button
              onClick={() => onNavigateTab('traffic')}
              className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-medium transition-colors"
            >
              View Traffic <ExternalLink className="w-3 h-3" />
            </button>
          </div>

          <div className="overflow-x-auto">
            {recentFlows.length > 0 ? (
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#1f2430] text-gray-400 text-[10px] uppercase tracking-wider">
                    <th className="py-2.5 px-3">Flow ID</th>
                    <th className="py-2.5 px-3">Device</th>
                    <th className="py-2.5 px-3">Protocol</th>
                    <th className="py-2.5 px-3">Duration</th>
                    <th className="py-2.5 px-3">Packets</th>
                    <th className="py-2.5 px-3">Predicted Class</th>
                    <th className="py-2.5 px-3 text-right">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1a1d26]">
                  {recentFlows.map((flow) => {
                    const pred = flow.predicted_label
                    const conf = flow.probability_estimates?.[pred] ?? 0
                    const devId = flow.device_id || (flow.source_file.startsWith('Agent ') ? flow.source_file.replace('Agent ', '') : 'PC01')
                    return (
                      <tr
                        key={flow.flow_id}
                        onClick={() => onSelectFlow(flow)}
                        className="hover:bg-[#161924] cursor-pointer transition-colors"
                      >
                        <td className="py-2.5 px-3 font-mono text-blue-400 font-medium">
                          {flow.flow_id}
                        </td>
                        <td className="py-2.5 px-3 font-mono">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold border ${
                            pred === 'Bot'
                              ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                              : pred === 'Suspicious'
                              ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                              : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                          }`}>
                            {devId}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-mono text-gray-300">
                          {flow.protocol}
                        </td>

                        <td className="py-2.5 px-3 font-mono text-gray-400">
                          {flow.session_duration.toFixed(3)}s
                        </td>
                        <td className="py-2.5 px-3 font-mono text-gray-300">
                          {flow.packet_count}
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
                        <td className="py-2.5 px-3 text-right font-mono text-gray-200">
                          {(conf * 100).toFixed(1)}%
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            ) : (
              <div className="py-12 text-center text-xs text-gray-400">
                No flows recorded. Replay a PCAP tier in Live Traffic to view results.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

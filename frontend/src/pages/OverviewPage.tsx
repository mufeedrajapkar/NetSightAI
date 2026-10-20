
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
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
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
  const totalFlows = data?.total_flows ?? 0
  const counts = data?.counts ?? {
    human: 0,
    bot: 0,
    suspicious: 0,
  }
  const distribution = data?.distribution ?? []
  const recentFlows = useMemo(
  () => data?.recent_flows ?? [],
  [data?.recent_flows]
)
  const hasData = totalFlows > 0

  const deviceThreats = useMemo(() => {
    const map = new Map<
      string,
      { latestFlow: FlowRecord; totalSessions: number }
    >()

    recentFlows.forEach((flow) => {
      const devId =
        flow.device_id ||
        (flow.source_file.startsWith('Agent ')
          ? flow.source_file.replace('Agent ', '')
          : 'PC01')

      const existing = map.get(devId)

      if (!existing) {
        map.set(devId, {
          latestFlow: flow,
          totalSessions: 1,
        })
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

  if (loading && !data) {
    return (
      <div className="flex min-h-[360px] items-center justify-center">
        <div className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/70 px-5 py-4 text-sm text-slate-300">
          <RefreshCw className="h-4 w-4 animate-spin text-sky-400" />
          Loading intelligence overview...
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto w-full max-w-[1600px] space-y-6 p-4 sm:p-6 xl:p-8">
      {/* Page header */}
      <section className="flex flex-col justify-between gap-4 border-b border-slate-800/80 pb-6 sm:flex-row sm:items-center">
        <div className="min-w-0">
          <div className="mb-2 flex flex-wrap items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-sky-400/20 bg-sky-400/10">
              <ShieldCheck className="h-5 w-5 text-sky-400" />
            </div>

            <div>
              <h1 className="text-xl font-semibold tracking-tight text-slate-100 sm:text-2xl">
                Network Intelligence
              </h1>
              <p className="mt-0.5 text-xs text-slate-400 sm:text-sm">
                Security overview and network activity
              </p>
            </div>
          </div>

          <p className="max-w-3xl text-sm leading-6 text-slate-400">
            Monitor network flows, review AI classifications, and understand
            the current security posture of observed devices.
          </p>

          <div className="mt-3">
            {data?.dataset_type === 'real' ? (
              <span className="inline-flex items-center gap-2 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Real Lab Captures
              </span>
            ) : (
              <span className="">
                <span className="" />
                
              </span>
            )}
          </div>
        </div>

        <button
          type="button"
          onClick={() => onRefresh()}
          disabled={loading}
          className="inline-flex shrink-0 items-center justify-center gap-2 self-start rounded-lg border border-slate-700 bg-slate-800/80 px-4 py-2.5 text-sm font-medium text-slate-200 transition-colors hover:border-sky-500/50 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 sm:self-center"
        >
          <RefreshCw
            className={`h-4 w-4 text-sky-400 ${
              loading ? 'animate-spin' : ''
            }`}
          />
          Refresh data
        </button>
      </section>

      {/* Summary statistics */}
      <section>
        <div className="mb-4 flex items-center gap-2">
          <Activity className="h-4 w-4 text-sky-400" />
          <h2 className="text-sm font-semibold text-slate-200">
            Security Summary
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
          <StatCard
            title="Total Flows"
            value={hasData ? totalFlows : 'N/A'}
            subtext="Analyzed sessions"
            icon={<Layers className="h-4 w-4" />}
            accentColor="blue"
          />

          <StatCard
            title="Human Predictions"
            value={hasData ? counts.human : 'N/A'}
            subtext={`${totalFlows ? ((counts.human / totalFlows) * 100).toFixed(0) : 0}% of flows`}
            icon={<UserCheck className="h-4 w-4" />}
            accentColor="green"
          />

          <StatCard
            title="Bot Predictions"
            value={hasData ? counts.bot : 'N/A'}
            subtext={`${totalFlows ? ((counts.bot / totalFlows) * 100).toFixed(0) : 0}% of flows`}
            icon={<Bot className="h-4 w-4" />}
            accentColor="orange"
          />

          <StatCard
            title="Suspicious"
            value={hasData ? counts.suspicious : 'N/A'}
            subtext={`${totalFlows ? ((counts.suspicious / totalFlows) * 100).toFixed(0) : 0}% of flows`}
            icon={<AlertTriangle className="h-4 w-4" />}
            accentColor="red"
          />

          <StatCard
            title="Active Devices"
            value={deviceThreats.length > 0 ? deviceThreats.length : '1'}
            subtext="Live ingest and replay"
            icon={<Monitor className="h-4 w-4" />}
            accentColor="blue"
          />

          <StatCard
            title="Model Status"
            value={data?.dataset_type === 'real' ? 'Real Trained' : 'Synthetic'}
            subtext={data?.model_type || 'LogisticRegression'}
            icon={<Activity className="h-4 w-4" />}
            accentColor={data?.dataset_type === 'real' ? 'green' : 'blue'}
          />
        </div>
      </section>

      {/* Device monitoring */}
      <section className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 shadow-lg shadow-black/10">
        <div className="flex flex-col justify-between gap-3 border-b border-slate-800 px-5 py-4 sm:flex-row sm:items-center">
          <div>
            <div className="flex items-center gap-2">
              <Monitor className="h-4 w-4 text-sky-400" />
              <h2 className="text-sm font-semibold text-slate-100">
                Monitored Devices
              </h2>
            </div>
            <p className="mt-1 text-xs text-slate-400">
              Latest AI classification for each observed network device.
            </p>
          </div>

          <span className="w-fit rounded-full border border-slate-700 bg-slate-800/70 px-3 py-1 text-xs text-slate-300">
            {deviceThreats.length} device
            {deviceThreats.length === 1 ? '' : 's'} observed
          </span>
        </div>

        <div className="p-4 sm:p-5">
          {deviceThreats.length > 0 ? (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
              {deviceThreats.map((dev) => {
                const isBot = dev.status === 'Bot'
                const isSuspicious = dev.status === 'Suspicious'

                const tone = isBot
                  ? {
                      border: 'border-rose-500/25',
                      icon: 'text-rose-400',
                      badge: 'border-rose-500/25 bg-rose-500/10 text-rose-300',
                      label: 'BOT DETECTED',
                      Icon: AlertTriangle,
                    }
                  : isSuspicious
                    ? {
                        border: 'border-amber-500/25',
                        icon: 'text-amber-400',
                        badge: 'border-amber-500/25 bg-amber-500/10 text-amber-300',
                        label: 'SUSPICIOUS',
                        Icon: AlertCircle,
                      }
                    : {
                        border: 'border-emerald-500/25',
                        icon: 'text-emerald-400',
                        badge: 'border-emerald-500/25 bg-emerald-500/10 text-emerald-300',
                        label: 'NORMAL',
                        Icon: ShieldCheck,
                      }

                const StatusIcon = tone.Icon

                return (
                  <div
                    key={dev.deviceId}
                    className={`rounded-xl border ${tone.border} bg-slate-950/40 p-4 transition-colors hover:bg-slate-800/40`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex min-w-0 items-center gap-3">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-slate-700 bg-slate-800">
                          <Monitor className={`h-5 w-5 ${tone.icon}`} />
                        </div>

                        <div className="min-w-0">
                          <p className="truncate font-mono text-sm font-semibold text-slate-100">
                            {dev.deviceId}
                          </p>
                          <p className="mt-0.5 text-xs text-slate-400">
                            {dev.totalSessions} observed session
                            {dev.totalSessions === 1 ? '' : 's'}
                          </p>
                        </div>
                      </div>

                      <StatusIcon className={`h-4 w-4 shrink-0 ${tone.icon}`} />
                    </div>

                    <div className="mt-4 border-t border-slate-800 pt-3">
                      <span
                        className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold tracking-wide ${tone.badge}`}
                      >
                        {tone.label}
                      </span>

                      <div className="mt-3 flex items-center justify-between gap-2 text-xs">
                        <span className="text-slate-400">Latest classification</span>
                        <span className="font-medium text-slate-200">
                          {dev.latestFlow.tier || dev.status}
                        </span>
                      </div>

                      <div className="mt-2 flex items-center justify-between gap-2 text-xs">
                        <span className="text-slate-400">Observed at</span>
                        <span className="font-mono text-slate-300">
                          {dev.latestFlow.timestamp.split(' ')[1] ||
                            dev.latestFlow.timestamp}
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <Monitor className="mb-3 h-8 w-8 text-slate-600" />
              <p className="text-sm font-medium text-slate-300">
                No device activity available
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Devices will appear when network flows are recorded.
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Prediction distribution and recent flows */}
      <section className="grid grid-cols-1 items-stretch gap-5 xl:grid-cols-3">
        {/* Distribution chart */}
        <div className="flex min-w-0 flex-col rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg shadow-black/10">
          <div>
            <h2 className="text-sm font-semibold text-slate-100">
              Prediction Distribution
            </h2>
            <p className="mt-1 text-xs leading-5 text-slate-400">
              Classification of analyzed network flows.
            </p>
          </div>

          <div className="relative my-4 h-52">
            {hasData && distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={57}
                    outerRadius={82}
                    paddingAngle={3}
                    dataKey="value"
                    stroke="none"
                  >
                    {distribution.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.color}
                        stroke="#101827"
                        strokeWidth={3}
                      />
                    ))}
                  </Pie>

                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#101827',
                      border: '1px solid #334155',
                      borderRadius: '10px',
                      fontSize: '12px',
                      color: '#e2e8f0',
                    }}
                    itemStyle={{ color: '#e2e8f0' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center rounded-xl border border-dashed border-slate-800 text-xs text-slate-500">
                No flow data available
              </div>
            )}

            {hasData && (
              <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-2xl font-semibold tracking-tight text-slate-100">
                  {totalFlows.toLocaleString()}
                </span>
                <span className="mt-1 text-[10px] uppercase tracking-widest text-slate-400">
                  Total flows
                </span>
              </div>
            )}
          </div>

          <div className="mt-auto space-y-4 border-t border-slate-800 pt-4">
            {[
              {
                label: 'Human',
                value: counts.human,
                color: 'bg-emerald-400',
                text: 'text-emerald-300',
              },
              {
                label: 'Bot',
                value: counts.bot,
                color: 'bg-orange-400',
                text: 'text-orange-300',
              },
              {
                label: 'Suspicious',
                value: counts.suspicious,
                color: 'bg-rose-400',
                text: 'text-rose-300',
              },
            ].map((item) => {
              const percentage = totalFlows
                ? (item.value / totalFlows) * 100
                : 0

              return (
                <div key={item.label}>
                  <div className="mb-2 flex items-center justify-between gap-3 text-xs">
                    <span className="flex items-center gap-2 text-slate-300">
                      <span className={`h-2 w-2 rounded-full ${item.color}`} />
                      {item.label}
                    </span>
                    <span className={`font-mono font-medium ${item.text}`}>
                      {item.value.toLocaleString()} ({percentage.toFixed(0)}%)
                    </span>
                  </div>

                  <div className="h-1.5 overflow-hidden rounded-full bg-slate-800">
                    <div
                      className={`h-full rounded-full ${item.color} transition-all duration-500`}
                      style={{ width: `${Math.min(percentage, 100)}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Recent network flows */}
        <div className="min-w-0 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 shadow-lg shadow-black/10 xl:col-span-2">
          <div className="flex flex-col justify-between gap-3 border-b border-slate-800 px-5 py-4 sm:flex-row sm:items-center">
            <div>
              <h2 className="text-sm font-semibold text-slate-100">
                Recent Network Activity
              </h2>
              <p className="mt-1 text-xs text-slate-400">
                Latest sessions processed by the existing analysis pipeline.
              </p>
            </div>

            <button
              type="button"
              onClick={() => onNavigateTab('traffic')}
              className="inline-flex w-fit items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/70 px-3 py-2 text-xs font-medium text-sky-300 transition-colors hover:border-sky-500/40 hover:bg-sky-500/10"
            >
              View all traffic
              <ExternalLink className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="overflow-x-auto">
            {recentFlows.length > 0 ? (
              <table className="w-full min-w-[760px] text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-950/30 text-[10px] uppercase tracking-wider text-slate-400">
                    <th className="px-4 py-3 font-semibold">Flow ID</th>
                    <th className="px-4 py-3 font-semibold">Device</th>
                    <th className="px-4 py-3 font-semibold">Protocol</th>
                    <th className="px-4 py-3 font-semibold">Duration</th>
                    <th className="px-4 py-3 font-semibold">Packets</th>
                    <th className="px-4 py-3 font-semibold">Classification</th>
                    <th className="px-4 py-3 text-right font-semibold">
                      Confidence
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {recentFlows.map((flow) => {
                    const pred = flow.predicted_label
                    const conf = flow.probability_estimates?.[pred] ?? 0
                    const devId =
                      flow.device_id ||
                      (flow.source_file.startsWith('Agent ')
                        ? flow.source_file.replace('Agent ', '')
                        : 'PC01')

                    const badgeStyle =
                      pred === 'Human'
                        ? 'border-emerald-500/25 bg-emerald-500/10 text-emerald-300'
                        : pred === 'Bot'
                          ? 'border-orange-500/25 bg-orange-500/10 text-orange-300'
                          : 'border-rose-500/25 bg-rose-500/10 text-rose-300'

                    return (
                      <tr
                        key={flow.flow_id}
                        onClick={() => onSelectFlow(flow)}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter' || event.key === ' ') {
                            event.preventDefault()
                            onSelectFlow(flow)
                          }
                        }}
                        tabIndex={0}
                        aria-label={`View details for flow ${flow.flow_id}`}
                        className="cursor-pointer border-b border-slate-800/70 transition-colors last:border-0 hover:bg-sky-400/[0.04] focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
                      >
                        <td className="whitespace-nowrap px-4 py-3.5 font-mono font-medium text-sky-300">
                          {flow.flow_id}
                        </td>

                        <td className="px-4 py-3.5 font-mono text-slate-300">
                          {devId}
                        </td>

                        <td className="px-4 py-3.5 font-mono text-slate-300">
                          {flow.protocol}
                        </td>

                        <td className="whitespace-nowrap px-4 py-3.5 font-mono text-slate-400">
                          {flow.session_duration.toFixed(3)}s
                        </td>

                        <td className="px-4 py-3.5 font-mono text-slate-300">
                          {flow.packet_count.toLocaleString()}
                        </td>

                        <td className="px-4 py-3.5">
                          <span
                            className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-medium ${badgeStyle}`}
                          >
                            {pred}
                          </span>
                        </td>

                        <td className="whitespace-nowrap px-4 py-3.5 text-right font-mono font-medium text-slate-200">
                          {(conf * 100).toFixed(1)}%
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            ) : (
              <div className="flex min-h-[260px] flex-col items-center justify-center px-6 text-center">
                <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl border border-slate-800 bg-slate-800/60">
                  <Activity className="h-5 w-5 text-slate-500" />
                </div>
                <p className="text-sm font-medium text-slate-300">
                  No network flows recorded
                </p>
                <p className="mt-1 max-w-sm text-xs leading-5 text-slate-500">
                  Once flows are available, their protocol, classification,
                  and confidence will appear here.
                </p>
                <button
                  type="button"
                  onClick={() => onNavigateTab('traffic')}
                  className="mt-4 text-xs font-medium text-sky-400 hover:text-sky-300"
                >
                  Open Live Traffic →
                </button>
              </div>
            )}
          </div>

          {recentFlows.length > 0 && (
            <div className="border-t border-slate-800 px-5 py-3 text-xs text-slate-500">
              Showing {recentFlows.length} recent flow
              {recentFlows.length === 1 ? '' : 's'} · Select a row to view details
            </div>
          )}
        </div>
      </section>
    </div>
  )
}

export default OverviewPage

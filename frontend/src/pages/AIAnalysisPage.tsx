
import React, { useState } from 'react'
import {
  Info,
  TrendingUp,
  BarChart3,
  BrainCircuit,
  Activity,
  ChevronRight,
  ShieldCheck,
  ShieldAlert,
  Layers3,
} from 'lucide-react'
import type { FlowRecord } from '../types'
import { FeatureTable } from '../components/FeatureTable'

interface AIAnalysisPageProps {
  flows: FlowRecord[]
}

export const AIAnalysisPage: React.FC<AIAnalysisPageProps> = ({ flows }) => {
  const [selectedFlowId, setSelectedFlowId] = useState<string>(
    flows.length > 0 ? flows[0].flow_id : ''
  )

  const activeFlow =
    flows.find((flow) => flow.flow_id === selectedFlowId) || flows[0] || null

  const getLabelStyle = (label: string) => {
    if (label === 'Human') {
      return {
        text: 'text-emerald-400',
        badge: 'border-emerald-500/25 bg-emerald-500/10 text-emerald-400',
        dot: 'bg-emerald-400',
        bar: 'bg-emerald-400',
      }
    }

    if (label === 'Bot') {
      return {
        text: 'text-orange-400',
        badge: 'border-orange-500/25 bg-orange-500/10 text-orange-400',
        dot: 'bg-orange-400',
        bar: 'bg-orange-400',
      }
    }

    return {
      text: 'text-rose-400',
      badge: 'border-rose-500/25 bg-rose-500/10 text-rose-400',
      dot: 'bg-rose-400',
      bar: 'bg-rose-400',
    }
  }

  const probabilityClasses = [
    {
      label: 'Human',
      text: 'text-emerald-400',
      bar: 'bg-emerald-400',
      panel: 'border-emerald-500/15 bg-emerald-500/[0.035]',
    },
    {
      label: 'Bot',
      text: 'text-orange-400',
      bar: 'bg-orange-400',
      panel: 'border-orange-500/15 bg-orange-500/[0.035]',
    },
    {
      label: 'Suspicious',
      text: 'text-rose-400',
      bar: 'bg-rose-400',
      panel: 'border-rose-500/15 bg-rose-500/[0.035]',
    },
  ] as const

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8">
      {/* Page heading */}
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-blue-400">
            <BrainCircuit className="h-3.5 w-3.5" />
            Intelligence Center
          </div>
          <h2 className="text-xl font-semibold tracking-tight text-gray-100 sm:text-2xl">
            AI Model Analysis
          </h2>
          <p className="mt-1.5 max-w-2xl text-xs leading-5 text-gray-400 sm:text-sm">
            Inspect model predictions, classification probabilities, and the
            nine statistical features used to evaluate network-flow behaviour.
          </p>
        </div>

        <div className="flex w-fit items-center gap-2 rounded-lg border border-[#273347] bg-[#111a28] px-3 py-2">
          <Activity className="h-4 w-4 text-blue-400" />
          <span className="text-xs text-gray-300">Flow analysis</span>
          <span className="rounded-md border border-[#30415b] bg-[#19263a] px-2 py-0.5 font-mono text-xs text-blue-300">
            {flows.length}
          </span>
        </div>
      </header>

      {/* Interpretation notice */}
      <section className="flex items-start gap-3 rounded-xl border border-blue-500/20 bg-blue-500/[0.045] p-4 sm:p-5">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-blue-500/20 bg-blue-500/10">
          <Info className="h-4 w-4 text-blue-400" />
        </div>
        <div className="min-w-0">
          <h3 className="text-xs font-semibold text-blue-200">
            Behavioral Interpretation Notice
          </h3>
          <p className="mt-1 text-xs leading-5 text-gray-400">
            SentinelNet analyses network-flow behaviour using extracted
            statistical features. Its prediction represents the model&apos;s
            interpretation of observed traffic, not a definitive identification
            of the user or device.
          </p>
        </div>
      </section>

      {/* Main analysis layout */}
      <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-12">
        {/* Flow selector */}
        <aside className="overflow-hidden rounded-xl border border-[#253044] bg-[#101722] lg:col-span-4 xl:col-span-3">
          <div className="flex items-center justify-between border-b border-[#253044] px-4 py-4">
            <div>
              <h3 className="text-xs font-semibold text-gray-100">
                Analyzed Flows
              </h3>
              <p className="mt-1 text-[10px] text-gray-500">
                Select a flow to inspect
              </p>
            </div>
            <span className="rounded-md border border-[#2b3b52] bg-[#172235] px-2 py-1 font-mono text-xs text-blue-300">
              {flows.length}
            </span>
          </div>

          {flows.length > 0 ? (
            <div className="max-h-[560px] space-y-1.5 overflow-y-auto p-2.5">
              {flows.map((flow) => {
                const isSelected =
                  flow.flow_id === (activeFlow?.flow_id ?? '')
                const labelStyle = getLabelStyle(flow.predicted_label)

                return (
                  <button
                    key={flow.flow_id}
                    type="button"
                    aria-pressed={isSelected}
                    onClick={() => setSelectedFlowId(flow.flow_id)}
                    className={`group w-full rounded-lg border p-3 text-left transition-colors ${
                      isSelected
                        ? 'border-blue-500/40 bg-blue-500/[0.09]'
                        : 'border-transparent bg-transparent hover:border-[#2a374b] hover:bg-[#151f2d]'
                    }`}
                  >
                    <div className="flex min-w-0 items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span
                            className={`h-1.5 w-1.5 shrink-0 rounded-full ${labelStyle.dot}`}
                          />
                          <span className="truncate font-mono text-xs font-semibold text-gray-200">
                            {flow.flow_id}
                          </span>
                        </div>
                        <p
                          className="mt-1.5 truncate pl-3.5 text-[10px] text-gray-500"
                          title={flow.source_file}
                        >
                          {flow.source_file}
                        </p>
                      </div>

                      <ChevronRight
                        className={`mt-0.5 h-3.5 w-3.5 shrink-0 transition-colors ${
                          isSelected
                            ? 'text-blue-400'
                            : 'text-gray-600 group-hover:text-gray-400'
                        }`}
                      />
                    </div>

                    <div className="mt-2.5 flex items-center justify-between gap-2 pl-3.5">
                      <span className="text-[10px] text-gray-500">
                        Prediction
                      </span>
                      <span
                        className={`rounded-md border px-2 py-0.5 text-[10px] font-medium ${labelStyle.badge}`}
                      >
                        {flow.predicted_label}
                      </span>
                    </div>
                  </button>
                )
              })}
            </div>
          ) : (
            <div className="px-5 py-12 text-center">
              <Layers3 className="mx-auto h-7 w-7 text-gray-600" />
              <p className="mt-3 text-xs font-medium text-gray-300">
                No flows available
              </p>
              <p className="mt-1 text-[11px] text-gray-500">
                Available flow records will appear here.
              </p>
            </div>
          )}
        </aside>

        {/* Selected flow details */}
        <main className="min-w-0 space-y-5 lg:col-span-8 xl:col-span-9">
          {activeFlow ? (
            <>
              {/* Prediction overview */}
              <section className="overflow-hidden rounded-xl border border-[#253044] bg-[#101722]">
                <div className="flex flex-col justify-between gap-4 border-b border-[#253044] p-4 sm:flex-row sm:items-start sm:p-5">
                  <div className="min-w-0">
                    <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-gray-500">
                      <Activity className="h-3.5 w-3.5 text-blue-400" />
                      Active Flow Evaluation
                    </div>
                    <h3 className="break-all font-mono text-base font-semibold text-gray-100 sm:text-lg">
                      {activeFlow.flow_id}
                    </h3>
                    <div className="mt-3 flex flex-wrap items-center gap-2">
                      <span
                        className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${getLabelStyle(activeFlow.predicted_label).badge}`}
                      >
                        <span
                          className={`h-1.5 w-1.5 rounded-full ${getLabelStyle(activeFlow.predicted_label).dot}`}
                        />
                        {activeFlow.predicted_label}
                      </span>
                      <span className="text-[11px] text-gray-500">
                        Model prediction
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <div className="rounded-lg border border-[#29364a] bg-[#141e2c] px-3 py-2">
                      <div className="text-[9px] uppercase tracking-wider text-gray-500">
                        Model
                      </div>
                      <div className="mt-1 max-w-[220px] break-words font-mono text-xs text-gray-200">
                        {activeFlow.model_type}
                      </div>
                    </div>
                    <div className="rounded-lg border border-[#29364a] bg-[#141e2c] px-3 py-2">
                      <div className="text-[9px] uppercase tracking-wider text-gray-500">
                        Ground truth
                      </div>
                      <div className="mt-1 text-xs font-medium text-gray-200">
                        {activeFlow.expected_label}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 divide-y divide-[#253044] sm:grid-cols-3 sm:divide-x sm:divide-y-0">
                  <div className="p-4">
                    <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-gray-500">
                      <BrainCircuit className="h-3.5 w-3.5" />
                      Classification
                    </div>
                    <div className="mt-2 text-sm font-semibold text-gray-100">
                      {activeFlow.predicted_label}
                    </div>
                  </div>
                  <div className="p-4">
                    <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-gray-500">
                      <ShieldCheck className="h-3.5 w-3.5" />
                      Expected label
                    </div>
                    <div className="mt-2 text-sm font-semibold text-gray-100">
                      {activeFlow.expected_label}
                    </div>
                  </div>
                  <div className="p-4">
                    <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-gray-500">
                      <ShieldAlert className="h-3.5 w-3.5" />
                      Prediction agreement
                    </div>
                    <div
                      className={`mt-2 text-sm font-semibold ${
                        activeFlow.predicted_label === activeFlow.expected_label
                          ? 'text-emerald-400'
                          : 'text-orange-400'
                      }`}
                    >
                      {activeFlow.predicted_label === activeFlow.expected_label
                        ? 'Match'
                        : 'Mismatch'}
                    </div>
                  </div>
                </div>
              </section>

              {/* Probability distribution */}
              <section className="rounded-xl border border-[#253044] bg-[#101722] p-4 sm:p-5">
                <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-blue-500/20 bg-blue-500/10">
                      <BarChart3 className="h-4 w-4 text-blue-400" />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-gray-100">
                        Classification Probability
                      </h4>
                      <p className="mt-1 text-[11px] text-gray-500">
                        Model output for each classification
                      </p>
                    </div>
                  </div>
                  <span className="rounded-md border border-[#29364a] bg-[#141e2c] px-2 py-1 font-mono text-[10px] text-gray-400">
                    3 classes
                  </span>
                </div>

                <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                  {probabilityClasses.map((item) => {
                    const prob =
                      activeFlow.probability_estimates?.[
                        item.label as 'Human' | 'Bot' | 'Suspicious'
                      ] ?? 0
                    const pct = prob * 100
                    const safePct = Number.isFinite(pct)
                      ? Math.min(100, Math.max(0, pct))
                      : 0

                    return (
                      <div
                        key={item.label}
                        className={`rounded-lg border p-4 ${item.panel}`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-xs font-medium text-gray-300">
                            {item.label}
                          </span>
                          <span
                            className={`font-mono text-base font-semibold ${item.text}`}
                          >
                            {pct.toFixed(4)}%
                          </span>
                        </div>

                        <div
                          className="mt-4 h-2 overflow-hidden rounded-full bg-[#222c3b]"
                          role="progressbar"
                          aria-label={`${item.label} probability`}
                          aria-valuemin={0}
                          aria-valuemax={100}
                          aria-valuenow={safePct}
                        >
                          <div
                            className={`h-full rounded-full transition-[width] duration-500 ${item.bar}`}
                            style={{ width: `${safePct}%` }}
                          />
                        </div>

                        <div className="mt-3 flex items-center justify-between gap-2">
                          <span className="text-[10px] text-gray-500">
                            Raw score
                          </span>
                          <span className="font-mono text-[10px] text-gray-400">
                            {prob.toFixed(6)}
                          </span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </section>

              {/* Feature table */}
              <section className="overflow-hidden rounded-xl border border-[#253044] bg-[#101722]">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#253044] p-4 sm:p-5">
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-violet-500/20 bg-violet-500/10">
                      <TrendingUp className="h-4 w-4 text-violet-400" />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-gray-100">
                        Nine Contract Features
                      </h4>
                      <p className="mt-1 text-[11px] text-gray-500">
                        Statistical inputs extracted from the network flow
                      </p>
                    </div>
                  </div>
                  <span className="rounded-md border border-violet-500/20 bg-violet-500/[0.07] px-2.5 py-1 font-mono text-[10px] text-violet-300">
                    9 FEATURES
                  </span>
                </div>

                <div className="p-3 sm:p-4">
                  <p className="mb-4 text-xs leading-5 text-gray-400">
                    These features are extracted by the CN layer and
                    standardized by the model&apos;s preprocessor.
                  </p>
                  <div className="overflow-hidden rounded-lg border border-[#253044] bg-[#0d141e]">
                    <FeatureTable features={activeFlow.features} />
                  </div>
                </div>
              </section>
            </>
          ) : (
            <section className="flex min-h-[360px] flex-col items-center justify-center rounded-xl border border-dashed border-[#2b374a] bg-[#101722] px-6 py-12 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-blue-500/20 bg-blue-500/10">
                <BrainCircuit className="h-7 w-7 text-blue-400" />
              </div>
              <h3 className="mt-4 text-sm font-semibold text-gray-200">
                No flow selected
              </h3>
              <p className="mt-2 max-w-sm text-xs leading-5 text-gray-500">
                Flow records will appear here when data is available for
                analysis.
              </p>
            </section>
          )}
        </main>
      </div>
    </div>
  )
}

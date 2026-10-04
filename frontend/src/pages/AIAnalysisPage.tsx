import React, { useState } from 'react'
import {
  Info,
  TrendingUp,
  BarChart3,
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

  const activeFlow = flows.find((f) => f.flow_id === selectedFlowId) || flows[0] || null

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div>
        <h2 className="text-xl font-semibold text-gray-100 tracking-tight">
          AI Model Inference & Behavioral Feature Analysis
        </h2>
        <p className="text-xs text-gray-400 mt-1">
          Detailed inspection of the 9-feature statistical contract, model weighting, and probability distributions.
        </p>
      </div>

      {/* Mandatory Behavioral Interpretation Disclaimer */}
      <div className="p-4 rounded-lg bg-[#161824] border border-[#262b3a] flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
        <div className="text-xs text-gray-300 leading-relaxed">
          <strong className="text-gray-100">Behavioral Interpretation Notice:</strong>{' '}
          SentinelNet analyses network-flow behaviour using extracted statistical features.
          Its prediction represents the model's interpretation of observed traffic, not a
          definitive identification of the user or device.
        </div>
      </div>

      {/* Model Overview & Flow Selector */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Flow Selection Sidebar */}
        <div className="p-4 rounded-xl bg-[#12141d] border border-[#202432] space-y-2">
          <div className="text-[11px] uppercase tracking-wider text-gray-400 font-semibold mb-3 px-1">
            Select Analyzed Flow ({flows.length})
          </div>
          <div className="space-y-1.5 max-h-[480px] overflow-y-auto pr-1">
            {flows.map((f) => {
              const isSelected = f.flow_id === (activeFlow?.flow_id ?? '')
              const predColor =
                f.predicted_label === 'Human'
                  ? 'text-emerald-400 bg-emerald-500/10'
                  : f.predicted_label === 'Bot'
                  ? 'text-orange-400 bg-orange-500/10'
                  : 'text-rose-400 bg-rose-500/10'

              return (
                <button
                  key={f.flow_id}
                  onClick={() => setSelectedFlowId(f.flow_id)}
                  className={`w-full text-left p-2.5 rounded-lg text-xs font-mono transition-colors flex items-center justify-between border ${
                    isSelected
                      ? 'bg-blue-600/10 border-blue-500/30 text-gray-100'
                      : 'bg-[#151822] border-[#222634] text-gray-400 hover:text-gray-200 hover:bg-[#181b26]'
                  }`}
                >
                  <div className="truncate mr-2">
                    <div className="font-semibold text-gray-200 text-[11px]">{f.flow_id}</div>
                    <div className="text-[10px] text-gray-400">{f.source_file}</div>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-sans font-medium ${predColor}`}>
                    {f.predicted_label}
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Selected Flow Analysis Panel */}
        <div className="lg:col-span-3 space-y-6">
          {activeFlow ? (
            <>
              {/* Prediction Summary Header */}
              <div className="p-5 rounded-xl bg-[#12141d] border border-[#202432] flex flex-wrap items-center justify-between gap-4">
                <div>
                  <div className="text-[11px] text-gray-400 uppercase tracking-wider mb-1">
                    Active Flow Evaluation
                  </div>
                  <div className="flex items-center gap-3">
                    <h3 className="text-base font-semibold font-mono text-gray-100">
                      {activeFlow.flow_id}
                    </h3>
                    <span
                      className={`px-2.5 py-1 rounded-full text-xs font-medium border ${
                        activeFlow.predicted_label === 'Human'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          : activeFlow.predicted_label === 'Bot'
                          ? 'bg-orange-500/10 text-orange-400 border-orange-500/20'
                          : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                      }`}
                    >
                      Predicted: {activeFlow.predicted_label}
                    </span>
                    <span className="text-xs text-gray-400">
                      (Ground Truth: <strong className="text-gray-200">{activeFlow.expected_label}</strong>)
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <div className="px-3 py-1.5 rounded-lg bg-[#181a24] border border-[#262b3a] text-xs font-mono text-gray-300">
                    Model: {activeFlow.model_type}
                  </div>
                </div>
              </div>

              {/* Probability Estimates Visualizer */}
              <div className="p-5 rounded-xl bg-[#12141d] border border-[#202432]">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-300 mb-4 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-blue-400" />
                  Classification Probability Distribution
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {(['Human', 'Bot', 'Suspicious'] as const).map((cls) => {
                    const prob = activeFlow.probability_estimates?.[cls] ?? 0
                    const pct = prob * 100
                    const accent =
                      cls === 'Human'
                        ? { text: 'text-emerald-400', bar: 'bg-emerald-500', bg: 'bg-emerald-500/5' }
                        : cls === 'Bot'
                        ? { text: 'text-orange-400', bar: 'bg-orange-500', bg: 'bg-orange-500/5' }
                        : { text: 'text-rose-400', bar: 'bg-rose-500', bg: 'bg-rose-500/5' }

                    return (
                      <div
                        key={cls}
                        className={`p-4 rounded-lg border border-[#232734] ${accent.bg}`}
                      >
                        <div className="flex justify-between items-center text-xs mb-2">
                          <span className="font-medium text-gray-300">{cls}</span>
                          <span className={`font-mono font-bold text-sm ${accent.text}`}>
                            {pct.toFixed(4)}%
                          </span>
                        </div>
                        <div className="w-full bg-[#1c202d] h-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${accent.bar}`}
                            style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
                          />
                        </div>
                        <div className="text-[10px] text-gray-400 mt-2 font-mono">
                          Raw Score: {prob.toFixed(6)}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* 9 Contract Features Breakdown */}
              <div className="p-5 rounded-xl bg-[#12141d] border border-[#202432]">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-300 mb-3 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-purple-400" />
                  The 9 AI Contract Features Measured
                </h4>
                <p className="text-[11px] text-gray-400 mb-4">
                  These 9 features are extracted by the CN layer and standardized by the model's preprocessor.
                </p>
                <div className="rounded-lg border border-[#232734] overflow-hidden bg-[#141620]">
                  <FeatureTable features={activeFlow.features} />
                </div>
              </div>
            </>
          ) : (
            <div className="p-12 text-center text-xs text-gray-400 rounded-xl bg-[#12141d] border border-[#202432]">
              No flow selected or available.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

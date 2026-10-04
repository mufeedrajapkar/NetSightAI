import React from 'react'
import { X, CheckCircle2, AlertTriangle, ShieldAlert, Activity } from 'lucide-react'
import type { FlowRecord } from '../types'
import { FeatureTable } from './FeatureTable'

interface FlowDetailsModalProps {
  flow: FlowRecord | null
  onClose: () => void
}

export const FlowDetailsModal: React.FC<FlowDetailsModalProps> = ({ flow, onClose }) => {
  if (!flow) return null

  const getPredictionBadge = (pred: string) => {
    switch (pred) {
      case 'Human':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" /> Human
          </span>
        )
      case 'Bot':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-orange-500/10 text-orange-400 border border-orange-500/20">
            <AlertTriangle className="w-3.5 h-3.5" /> Bot
          </span>
        )
      case 'Suspicious':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <ShieldAlert className="w-3.5 h-3.5" /> Suspicious
          </span>
        )
      default:
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-gray-700/30 text-gray-300 border border-gray-600/30">
            {pred}
          </span>
        )
    }
  }

  const probs = flow.probability_estimates || { Human: 0, Bot: 0, Suspicious: 0 }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs">
      <div className="bg-[#12141d] border border-[#232734] w-full max-w-3xl rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#232734] flex items-center justify-between bg-[#151824]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-100 font-mono">{flow.flow_id}</h3>
              <p className="text-[11px] text-gray-400">
                Source: {flow.source_file} ({flow.source_type}) • {flow.timestamp}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-100 hover:bg-[#202432] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6 overflow-y-auto">
          {/* Classification Banner */}
          <div className="p-4 rounded-lg bg-[#161924] border border-[#252a38] flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="text-[11px] text-gray-400 uppercase tracking-wider mb-1">
                Classification Result
              </div>
              <div className="flex items-center gap-3">
                {getPredictionBadge(flow.predicted_label)}
                <span className="text-xs text-gray-400">
                  Expected: <strong className="text-gray-200">{flow.expected_label}</strong>
                </span>
                <span
                  className={`text-[11px] px-2 py-0.5 rounded font-mono ${
                    flow.is_match
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                  }`}
                >
                  {flow.is_match ? 'MATCH' : 'MISMATCH / UNCERTAINTY'}
                </span>
              </div>
            </div>

            <div className="text-right">
              <div className="text-[11px] text-gray-400">Classifier</div>
              <div className="text-xs font-mono font-medium text-gray-200">{flow.model_type}</div>
            </div>
          </div>

          {/* Probability Breakdown */}
          <div>
            <h4 className="text-xs font-medium uppercase tracking-wider text-gray-400 mb-3">
              Class Probability Estimates
            </h4>
            <div className="grid grid-cols-3 gap-3">
              {(['Human', 'Bot', 'Suspicious'] as const).map((cls) => {
                const val = (probs[cls] || 0) * 100
                const color =
                  cls === 'Human'
                    ? 'text-emerald-400 bg-emerald-500'
                    : cls === 'Bot'
                    ? 'text-orange-400 bg-orange-500'
                    : 'text-rose-400 bg-rose-500'

                return (
                  <div key={cls} className="p-3 rounded-lg bg-[#161924] border border-[#232734]">
                    <div className="flex justify-between items-center text-xs mb-1.5">
                      <span className="text-gray-400">{cls}</span>
                      <span className={`font-mono font-semibold ${color.split(' ')[0]}`}>
                        {val.toFixed(2)}%
                      </span>
                    </div>
                    <div className="w-full bg-[#202432] h-1.5 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${color.split(' ')[1]}`}
                        style={{ width: `${Math.min(100, Math.max(0, val))}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Flow Metrics Summary */}
          <div className="grid grid-cols-4 gap-3">
            <div className="p-3 rounded-lg bg-[#161924] border border-[#232734]">
              <div className="text-[10px] uppercase text-gray-400">Packets</div>
              <div className="text-sm font-semibold font-mono text-gray-200 mt-0.5">
                {flow.packet_count}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-[#161924] border border-[#232734]">
              <div className="text-[10px] uppercase text-gray-400">Duration</div>
              <div className="text-sm font-semibold font-mono text-gray-200 mt-0.5">
                {flow.session_duration.toFixed(4)}s
              </div>
            </div>
            <div className="p-3 rounded-lg bg-[#161924] border border-[#232734]">
              <div className="text-[10px] uppercase text-gray-400">Bytes</div>
              <div className="text-sm font-semibold font-mono text-gray-200 mt-0.5">
                {flow.bytes_transferred.toLocaleString()} B
              </div>
            </div>
            <div className="p-3 rounded-lg bg-[#161924] border border-[#232734]">
              <div className="text-[10px] uppercase text-gray-400">Protocol</div>
              <div className="text-sm font-semibold font-mono text-blue-400 mt-0.5">
                {flow.protocol}
              </div>
            </div>
          </div>

          {/* 9 Contract Features */}
          <div>
            <h4 className="text-xs font-medium uppercase tracking-wider text-gray-400 mb-2">
              Extracted Model Features (9 Contract Inputs)
            </h4>
            <div className="rounded-lg border border-[#232734] overflow-hidden bg-[#141620]">
              <FeatureTable features={flow.features} />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-[#232734] bg-[#151824] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-md text-xs font-medium bg-[#232734] text-gray-200 hover:bg-[#2b3040] transition-colors"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  )
}

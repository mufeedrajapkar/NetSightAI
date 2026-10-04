import React, { useEffect, useState } from 'react'
import {
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
} from 'lucide-react'
import type { BotTiersResponse } from '../types'
import { fetchBotTiers } from '../services/api'

export const BotAnalysisPage: React.FC = () => {
  const [data, setData] = useState<BotTiersResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    fetchBotTiers()
      .then((res) => {
        setData(res)
        setLoading(false)
      })
      .catch(() => {
        setLoading(false)
      })
  }, [])

  if (loading) {
    return <div className="p-8 text-xs text-gray-400">Loading bot tier evaluations...</div>
  }

  const tiers = data?.tiers || []

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div>
        <h2 className="text-xl font-semibold text-gray-100 tracking-tight">
          Bot Behavioral Sophistication Tiers & Evasion Analysis
        </h2>
        <p className="text-xs text-gray-400 mt-1">
          Comparative evaluation of three distinct bot generation tiers against the baseline classification model.
        </p>
      </div>

      {/* Model Limitation / Domain Shift Callout */}
      <div className="p-4 rounded-lg bg-amber-950/20 border border-amber-800/30 flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="text-xs text-gray-300 space-y-1">
          <div className="font-semibold text-amber-300">
            Model Domain Shift & Behavioral Evasion Limitation:
          </div>
          <div className="text-gray-400 leading-relaxed">
            The model was trained on synthetic data (<code>sentinelnet_sample_500.csv</code>). The generated PCAP
            traffic has a different feature distribution (such as <code>num_connections = 1</code> and physical loopback
            packet sizes of ~95–101 bytes), which causes distribution shift. Tier 3 further demonstrates the fundamental
            boundary of statistical macro-interval analysis against human-mimicking bots.
          </div>
        </div>
      </div>

      {/* Evaluated Comparison Table */}
      <div className="p-6 rounded-xl bg-[#12141d] border border-[#202432]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-200">
              Bot Tier Evaluation Matrix (Generated PCAP Replay)
            </h3>
            <p className="text-[11px] text-gray-400">
              Preserved evaluation outcomes reflecting genuine mathematical logit calculations.
            </p>
          </div>
          <div className="text-[11px] font-mono text-gray-400">
            Evaluated: 3 Tiers • 1 Match • 2 Mismatches
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#232734] text-gray-400 text-[10px] uppercase tracking-wider">
                <th className="py-3 px-4">Bot Tier</th>
                <th className="py-3 px-4">Sophistication</th>
                <th className="py-3 px-4">Expected Label</th>
                <th className="py-3 px-4">Predicted Label</th>
                <th className="py-3 px-4">Result Status</th>
                <th className="py-3 px-4">Bot Probability</th>
                <th className="py-3 px-4">Human Probability</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1c202b]">
              {tiers.map((t) => {
                const isMatch = t.baseline_result.toLowerCase().includes('match') && !t.baseline_result.toLowerCase().includes('mismatch')
                return (
                  <tr key={t.id} className="hover:bg-[#161924] transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-gray-200">
                      {t.name}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#1c202d] text-gray-300">
                        {t.sophistication}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono font-medium text-gray-300">
                      {t.expected_label}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-semibold">
                      <span
                        className={
                          t.baseline_result.includes('Bot') ? 'text-orange-400' : 'text-emerald-400'
                        }
                      >
                        {t.baseline_result.includes('Bot') ? 'Bot' : 'Human'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-medium border ${
                          isMatch
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                        }`}
                      >
                        {isMatch ? <CheckCircle2 className="w-3 h-3" /> : <HelpCircle className="w-3 h-3" />}
                        {isMatch ? 'MATCH' : 'MISMATCH / UNCERTAINTY'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-orange-400 font-medium">
                      {(t.bot_probability * 100).toFixed(4)}%
                    </td>
                    <td className="py-3.5 px-4 font-mono text-emerald-400 font-medium">
                      {(t.human_probability * 100).toFixed(4)}%
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Deep-Dive Tier Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {tiers.map((t) => (
          <div key={t.id} className="p-5 rounded-xl bg-[#12141d] border border-[#202432] space-y-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-semibold text-gray-100">{t.name}</h4>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  {t.sophistication} Sophistication
                </span>
              </div>
              <p className="text-xs text-gray-400 mb-3 leading-relaxed">
                {t.description}
              </p>
            </div>

            <div className="space-y-3 pt-3 border-t border-[#1e2230]">
              <div className="p-3 rounded-lg bg-[#161924] border border-[#232734] space-y-1.5 text-xs">
                <div className="text-[10px] uppercase text-gray-400 font-semibold">
                  Behavioral Root-Cause Analysis
                </div>
                <p className="text-[11px] text-gray-300 leading-relaxed">
                  {t.behavior_notes}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2 rounded bg-[#161924] border border-[#232734]">
                  <span className="text-[10px] text-gray-400 block">Bot Conf</span>
                  <span className="text-orange-400 font-semibold">{(t.bot_probability * 100).toFixed(2)}%</span>
                </div>
                <div className="p-2 rounded bg-[#161924] border border-[#232734]">
                  <span className="text-[10px] text-gray-400 block">Human Conf</span>
                  <span className="text-emerald-400 font-semibold">{(t.human_probability * 100).toFixed(2)}%</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

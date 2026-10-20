import React, { useEffect, useState } from 'react'
import {
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  TrendingDown,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
} from 'lucide-react'
import type { BotTiersResponse, AdversarialResponse } from '../types'
import { fetchBotTiers, fetchAdversarial } from '../services/api'

export const BotAnalysisPage: React.FC = () => {
  const [data, setData] = useState<BotTiersResponse | null>(null)
  const [adversarial, setAdversarial] = useState<AdversarialResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = () => {
    setLoading(true)
    setError(null)
    Promise.allSettled([fetchBotTiers(), fetchAdversarial()]).then(([tiersRes, advRes]) => {
      if (tiersRes.status === 'fulfilled') {
        setData(tiersRes.value)
      } else {
        setError(tiersRes.reason?.message || 'Failed to load bot tier evaluations')
      }
      if (advRes.status === 'fulfilled') {
        setAdversarial(advRes.value)
      }
      setLoading(false)
    })
  }

  useEffect(() => {
    loadData()
  }, [])

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center text-xs text-gray-400">
        <RefreshCw className="w-4 h-4 animate-spin mr-2 text-blue-400" />
        Loading bot tier difficulty evaluations...
      </div>
    )
  }

  if (error || !data || data.tiers.length === 0) {
    return (
      <div className="p-8 max-w-4xl mx-auto space-y-4">
        <div className="p-6 rounded-xl bg-amber-950/20 border border-amber-800/40 text-amber-300 space-y-3">
          <div className="flex items-center gap-2 font-semibold text-sm">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            Bot Tier Analysis Experiment Not Yet Executed
          </div>
          <p className="text-xs text-gray-300 leading-relaxed">
            No empirical bot tier results were found in <code>ai/models/bot_tier_results.json</code>.
            Execute the analysis script to compute real F1, recall, and feature separation metrics:
          </p>
          <pre className="p-3 rounded bg-black/40 border border-amber-800/30 text-xs font-mono text-gray-200">
            python ai/bot_tier_analysis.py
          </pre>
          <button
            onClick={loadData}
            className="px-4 py-1.5 rounded-lg text-xs font-medium bg-amber-600 hover:bg-amber-500 text-white transition-colors"
          >
            Retry Loading
          </button>
        </div>
      </div>
    )
  }

  const tiers = data.tiers || []

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold text-gray-100 tracking-tight">
              Bot Behavioral Sophistication Tiers & Evasion Analysis
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
              Dataset: {data.dataset_type === 'real' ? 'Real Captures' : 'Synthetic Prototype'}
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Empirical evaluation of detection performance across three ascending sophistication tiers.
          </p>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium bg-[#1a1d28] hover:bg-[#222634] text-gray-300 border border-[#262b3a] transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Results
        </button>
      </div>

      {/* Model Limitation / Sophistication Notice */}
      <div className="p-4 rounded-lg bg-blue-950/20 border border-blue-800/30 flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
        <div className="text-xs text-gray-300 space-y-1">
          <div className="font-semibold text-blue-300">
            Empirical Difficulty Gradient & Evasion Analysis:
          </div>
          <div className="text-gray-400 leading-relaxed">
            As bot behavior evolves from naive deterministic loops (Tier 1) to Poisson jitter (Tier 2) and
            empirical human pause distributions (Tier 3), detection accuracy decreases. Higher tiers mimic human
            session duration and request interval variance, narrowing the feature distance separating them from genuine users.
          </div>
        </div>
      </div>

      {/* Evaluated Comparison Table */}
      <div className="p-6 rounded-xl bg-[#12141d] border border-[#202432]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-200">
              Bot Tier Evaluation Matrix (Real Empirical Results)
            </h3>
            <p className="text-[11px] text-gray-400">
              Computed metrics from <code>ai/bot_tier_analysis.py</code> without hardcoded constants.
            </p>
          </div>
          <div className="text-[11px] font-mono text-gray-400">
            Evaluated: {data.evaluation_summary.total_tiers} Tiers • {data.evaluation_summary.matches} Matches • {data.evaluation_summary.mismatches} Mismatches
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#232734] text-gray-400 text-[10px] uppercase tracking-wider">
                <th className="py-3 px-4">Bot Tier</th>
                <th className="py-3 px-4">Sophistication</th>
                <th className="py-3 px-4">Samples</th>
                <th className="py-3 px-4">Detection Rate</th>
                <th className="py-3 px-4">Precision</th>
                <th className="py-3 px-4">Recall</th>
                <th className="py-3 px-4">F1 Score</th>
                <th className="py-3 px-4">Result Status</th>
                <th className="py-3 px-4">Bot Probability</th>
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
                    <td className="py-3.5 px-4 font-mono text-gray-300">
                      {t.sample_count ?? 'N/A'}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-semibold text-emerald-400">
                      {t.detection_rate !== undefined ? `${(t.detection_rate * 100).toFixed(1)}%` : 'N/A'}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-gray-300">
                      {t.precision !== undefined ? `${(t.precision * 100).toFixed(1)}%` : 'N/A'}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-gray-300">
                      {t.recall !== undefined ? `${(t.recall * 100).toFixed(1)}%` : 'N/A'}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-semibold text-blue-400">
                      {t.f1 !== undefined ? t.f1.toFixed(3) : 'N/A'}
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
                        {t.baseline_result}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-orange-400 font-medium">
                      {(t.bot_probability * 100).toFixed(2)}%
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Difficulty Curve Plot Section */}
      <div className="p-6 rounded-xl bg-[#12141d] border border-[#202432]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-blue-400" />
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-200">
                Detection F1 vs Bot Sophistication Curve
              </h3>
            </div>
            <p className="text-[11px] text-gray-400 mt-0.5">
              Visual proof of difficulty curve generated by <code>ai/bot_tier_analysis.py</code>.
            </p>
          </div>
          <span className="text-[10px] font-mono text-gray-400 bg-[#161924] px-2.5 py-1 rounded border border-[#232734]">
            Plot: ai/models/bot_tier_curve.png
          </span>
        </div>

        <div className="p-4 rounded-lg bg-[#0e1017] border border-[#1e2230] flex items-center justify-center">
          <img
            src="/api/bot-tiers/curve"
            alt="Bot Tier Difficulty Curve"
            className="max-h-96 object-contain rounded-md"
            onError={(e) => {
              // Hide image if not found
              (e.target as HTMLElement).style.display = 'none'
            }}
          />
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
                  {t.sophistication}
                </span>
              </div>
              <p className="text-xs text-gray-400 mb-3 leading-relaxed">
                {t.description}
              </p>
            </div>

            <div className="space-y-3 pt-3 border-t border-[#1e2230]">
              {/* Feature Separation Callout */}
              {t.least_separated_features && t.least_separated_features.length > 0 && (
                <div className="p-3 rounded-lg bg-[#161924] border border-[#232734] space-y-1.5 text-xs">
                  <div className="text-[10px] uppercase text-gray-400 font-semibold">
                    Least Separated Features (Closest to Human):
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {t.least_separated_features.map((f: any) => (
                      <span key={f.feature} className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#1c202d] text-amber-300 border border-amber-500/20">
                        {f.feature} (d={f.cohens_d})
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="p-3 rounded-lg bg-[#161924] border border-[#232734] space-y-1.5 text-xs">
                <div className="text-[10px] uppercase text-gray-400 font-semibold">
                  Behavioral Analysis
                </div>
                <p className="text-[11px] text-gray-300 leading-relaxed">
                  {t.behavior_notes}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2 rounded bg-[#161924] border border-[#232734]">
                  <span className="text-[10px] text-gray-400 block">Detection F1</span>
                  <span className="text-blue-400 font-semibold">{t.f1 !== undefined ? t.f1.toFixed(3) : 'N/A'}</span>
                </div>
                <div className="p-2 rounded bg-[#161924] border border-[#232734]">
                  <span className="text-[10px] text-gray-400 block">Bot Conf</span>
                  <span className="text-orange-400 font-semibold">{(t.bot_probability * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Adversarial Evasion Benchmark (Tier 4) */}
      {adversarial && adversarial.scenarios && (
        <div className="p-6 rounded-xl bg-[#12141d] border border-rose-950/40 space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <ShieldAlert className="w-5 h-5 text-rose-400" />
              <div>
                <h3 className="text-sm font-semibold text-gray-100">
                  Tier 4 Adversarial Evasion Robustness Benchmark
                </h3>
                <p className="text-[11px] text-gray-400 mt-0.5">
                  Evaluates classifier, Isolation Forest, and hybrid defense resilience against delay & feature-shaping bots.
                </p>
              </div>
            </div>
            <span className="text-[10px] font-mono px-2.5 py-1 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
              Provenance: {adversarial.benchmark_provenance}
            </span>
          </div>

          {/* Scenario Comparison Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(adversarial.scenarios).map(([key, sc]: [string, any]) => (
              <div key={key} className="p-4 rounded-lg bg-[#0e1017] border border-[#1e2230] space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-gray-200 capitalize">
                    {key.replace(/_/g, ' ')}
                  </h4>
                  <span className="text-[10px] font-mono text-gray-400">
                    N = {sc.total_sessions} sessions
                  </span>
                </div>
                <p className="text-[11px] text-gray-400">
                  {sc.description}
                </p>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-2 border-t border-[#1a1d28]">
                  <div className="p-2 rounded bg-[#161924] border border-[#232734]">
                    <span className="text-[10px] text-gray-400 block">Classifier Evasion</span>
                    <span className="text-rose-400 font-semibold">
                      {(sc.classifier_evasion_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="p-2 rounded bg-[#161924] border border-[#232734]">
                    <span className="text-[10px] text-gray-400 block">Suspicious Rescue</span>
                    <span className="text-amber-400 font-semibold">
                      {(sc.suspicious_rescue_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="p-2 rounded bg-[#161924] border border-[#232734]">
                    <span className="text-[10px] text-gray-400 block">Outright Bot Verdict</span>
                    <span className="text-emerald-400 font-semibold">
                      {(sc.bot_detection_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="p-2 rounded bg-[#161924] border border-[#232734]">
                    <span className="text-[10px] text-gray-400 block">Net Evasion Rate</span>
                    <span className="text-purple-400 font-semibold">
                      {(sc.hybrid_sentinelnet_evasion_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Vulnerability & Recommended Countermeasures */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-2">
            <div className="p-4 rounded-lg bg-[#0e1017] border border-amber-900/30 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-amber-300">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                Vulnerability Analysis
              </div>
              <p className="text-xs text-gray-300 leading-relaxed">
                {adversarial.vulnerability_analysis}
              </p>
            </div>

            <div className="p-4 rounded-lg bg-[#0e1017] border border-blue-900/30 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-blue-300">
                <ShieldCheck className="w-4 h-4 text-blue-400" />
                Recommended Evasion Countermeasures
              </div>
              <div className="space-y-1.5">
                {adversarial.recommended_countermeasures.map((c, i) => (
                  <div key={i} className="text-[11px] text-gray-300 flex items-start gap-1.5">
                    <span className="text-blue-400 font-semibold shrink-0">[{c.dimension}]</span>
                    <span><strong>{c.feature}:</strong> {c.rationale}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


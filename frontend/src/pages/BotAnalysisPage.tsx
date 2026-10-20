
import React, { useCallback, useEffect, useState } from 'react'
import {
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  TrendingDown,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Bot,
  Activity,
  BarChart3,
  Target,
  Layers3,
  ChevronRight,
  BrainCircuit,
} from 'lucide-react'
import type { BotTiersResponse, AdversarialResponse } from '../types'
import { fetchBotTiers, fetchAdversarial } from '../services/api'

export const BotAnalysisPage: React.FC = () => {
  const [data, setData] = useState<BotTiersResponse | null>(null)
  const [adversarial, setAdversarial] = useState<AdversarialResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)

    const [tiersRes, advRes] = await Promise.allSettled([
      fetchBotTiers(),
      fetchAdversarial(),
    ])

    if (tiersRes.status === 'fulfilled') {
      setData(tiersRes.value)
    } else {
      setError(
        tiersRes.reason?.message || 'Failed to load bot tier evaluations'
      )
      setData(null)
    }

    if (advRes.status === 'fulfilled') {
      setAdversarial(advRes.value)
    } else {
      setAdversarial(null)
    }

    setLoading(false)
  }, [])

  useEffect(() => {
    void loadData()
  }, [loadData])

  if (loading) {
    return (
      <div className="mx-auto flex min-h-[360px] max-w-7xl items-center justify-center p-8">
        <div className="flex flex-col items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-blue-500/20 bg-blue-500/10">
            <RefreshCw className="h-5 w-5 animate-spin text-blue-400" />
          </div>
          <p className="text-sm font-medium text-gray-300">
            Loading bot tier evaluations
          </p>
          <p className="text-xs text-gray-500">
            Retrieving empirical detection results...
          </p>
        </div>
      </div>
    )
  }

  if (error || !data || data.tiers.length === 0) {
    return (
      <div className="mx-auto max-w-4xl p-4 sm:p-8">
        <div className="overflow-hidden rounded-xl border border-amber-500/25 bg-[#101722]">
          <div className="flex items-start gap-4 border-b border-amber-500/15 bg-amber-500/[0.06] p-5 sm:p-6">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-amber-500/20 bg-amber-500/10">
              <AlertTriangle className="h-5 w-5 text-amber-400" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-gray-100">
                Bot Tier Analysis Unavailable
              </h2>
              <p className="mt-1 text-xs leading-5 text-gray-400">
                {error ||
                  'No empirical bot tier results are currently available.'}
              </p>
            </div>
          </div>

          <div className="space-y-4 p-5 sm:p-6">
            <p className="text-xs leading-5 text-gray-400">
              No usable tier evaluation results were returned. If the
              experiment has not been executed, run the analysis script to
              calculate detection metrics from its evaluation data.
            </p>

            <div className="rounded-lg border border-[#29364a] bg-[#0b121c] p-4">
              <div className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
                Analysis command
              </div>
              <code className="break-all font-mono text-xs text-blue-300">
                python ai/bot_tier_analysis.py
              </code>
            </div>

            <button
              type="button"
              onClick={() => void loadData()}
              className="inline-flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-2.5 text-xs font-semibold text-amber-300 transition-colors hover:bg-amber-500/15 focus:outline-none focus:ring-2 focus:ring-amber-500/40"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Retry Loading
            </button>
          </div>
        </div>
      </div>
    )
  }

  const tiers = data.tiers || []

  const formatPercent = (value: number | undefined, digits = 1) =>
    value !== undefined && Number.isFinite(value)
      ? `${(value * 100).toFixed(digits)}%`
      : 'N/A'

  const formatScore = (value: number | undefined) =>
    value !== undefined && Number.isFinite(value) ? value.toFixed(3) : 'N/A'

  const getF1Style = (value: number | undefined) => {
    if (value === undefined || !Number.isFinite(value)) {
      return 'text-gray-400'
    }
    if (value >= 0.8) return 'text-emerald-400'
    if (value >= 0.6) return 'text-blue-400'
    return 'text-amber-400'
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div className="min-w-0">
          <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-blue-400">
            <BrainCircuit className="h-3.5 w-3.5" />
            Behavioral Intelligence
          </div>
          <h2 className="text-xl font-semibold tracking-tight text-gray-100 sm:text-2xl">
            Bot Sophistication Analysis
          </h2>
          <p className="mt-1.5 max-w-2xl text-xs leading-5 text-gray-400 sm:text-sm">
            Evaluate detection performance across increasing levels of bot
            behavioral sophistication and adversarial evasion.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-lg border border-[#2b3b52] bg-[#141e2c] px-3 py-2 text-[11px] text-gray-300">
            Dataset:{' '}
            <span className="font-medium text-blue-300">
              {data.dataset_type === 'real'
                ? 'Real Captures'
                : 'Synthetic Prototype'}
            </span>
          </span>
          <button
            type="button"
            onClick={() => void loadData()}
            className="inline-flex items-center gap-2 rounded-lg border border-[#2b3b52] bg-[#172235] px-3 py-2 text-xs font-medium text-gray-300 transition-colors hover:border-blue-500/40 hover:bg-[#1b2a40] hover:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh Results
          </button>
        </div>
      </header>

      {/* Difficulty interpretation */}
      <section className="flex items-start gap-3 rounded-xl border border-blue-500/20 bg-blue-500/[0.045] p-4 sm:p-5">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-blue-500/20 bg-blue-500/10">
          <TrendingDown className="h-4 w-4 text-blue-400" />
        </div>
        <div>
          <h3 className="text-xs font-semibold text-blue-200">
            Empirical Difficulty Gradient &amp; Evasion Analysis
          </h3>
          <p className="mt-1.5 text-xs leading-5 text-gray-400">
            As bot behaviour evolves from naive deterministic loops (Tier 1)
            to Poisson jitter (Tier 2) and empirical human pause distributions
            (Tier 3), detection accuracy can decrease. Higher tiers mimic human
            session duration and request interval variance, narrowing the
            feature distance separating them from genuine users.
          </p>
        </div>
      </section>

      {/* Summary metrics */}
      <section className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-[#253044] bg-[#101722] p-4">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-500">
              Evaluated tiers
            </span>
            <Layers3 className="h-4 w-4 text-blue-400" />
          </div>
          <div className="mt-3 font-mono text-2xl font-semibold text-gray-100">
            {data.evaluation_summary.total_tiers}
          </div>
          <p className="mt-1 text-[10px] text-gray-500">
            Behavioral difficulty levels
          </p>
        </div>

        <div className="rounded-xl border border-emerald-500/15 bg-[#101722] p-4">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-500">
              Baseline matches
            </span>
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="mt-3 font-mono text-2xl font-semibold text-emerald-400">
            {data.evaluation_summary.matches}
          </div>
          <p className="mt-1 text-[10px] text-gray-500">
            Matches in the evaluation summary
          </p>
        </div>

        <div className="rounded-xl border border-amber-500/15 bg-[#101722] p-4">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-500">
              Baseline mismatches
            </span>
            <AlertTriangle className="h-4 w-4 text-amber-400" />
          </div>
          <div className="mt-3 font-mono text-2xl font-semibold text-amber-400">
            {data.evaluation_summary.mismatches}
          </div>
          <p className="mt-1 text-[10px] text-gray-500">
            Mismatches in the evaluation summary
          </p>
        </div>
      </section>

      {/* Evaluation matrix */}
      <section className="overflow-hidden rounded-xl border border-[#253044] bg-[#101722]">
        <div className="flex flex-col justify-between gap-3 border-b border-[#253044] p-4 sm:flex-row sm:items-center sm:p-5">
          <div>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-blue-400" />
              <h3 className="text-sm font-semibold text-gray-100">
                Bot Tier Evaluation Matrix
              </h3>
            </div>
            <p className="mt-1 text-[11px] leading-5 text-gray-500">
              Empirical metrics computed by{' '}
              <code className="text-blue-300">ai/bot_tier_analysis.py</code>.
            </p>
          </div>
          <span className="w-fit rounded-md border border-[#29364a] bg-[#141e2c] px-2.5 py-1 text-[10px] font-mono text-gray-400">
            {tiers.length} records
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[920px] text-left text-xs">
            <thead>
              <tr className="border-b border-[#253044] bg-[#0d141e] text-[10px] uppercase tracking-wider text-gray-500">
                <th className="px-4 py-3.5 font-semibold">Bot tier</th>
                <th className="px-4 py-3.5 font-semibold">Sophistication</th>
                <th className="px-4 py-3.5 font-semibold">Samples</th>
                <th className="px-4 py-3.5 font-semibold">Detection</th>
                <th className="px-4 py-3.5 font-semibold">Precision</th>
                <th className="px-4 py-3.5 font-semibold">Recall</th>
                <th className="px-4 py-3.5 font-semibold">F1 score</th>
                <th className="px-4 py-3.5 font-semibold">Baseline result</th>
                <th className="px-4 py-3.5 font-semibold">Bot probability</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#202a39]">
              {tiers.map((tier) => {
                const result = tier.baseline_result.toLowerCase()
                const isMatch =
                  result.includes('match') && !result.includes('mismatch')

                return (
                  <tr
                    key={tier.id}
                    className="transition-colors hover:bg-[#172131]"
                  >
                    <td className="px-4 py-4 font-semibold text-gray-200">
                      {tier.name}
                    </td>
                    <td className="px-4 py-4">
                      <span className="inline-flex rounded-md border border-[#2b3b52] bg-[#172235] px-2 py-1 font-mono text-[10px] text-blue-300">
                        {tier.sophistication}
                      </span>
                    </td>
                    <td className="px-4 py-4 font-mono text-gray-300">
                      {tier.sample_count ?? 'N/A'}
                    </td>
                    <td className="px-4 py-4 font-mono font-semibold text-gray-200">
                      {formatPercent(tier.detection_rate)}
                    </td>
                    <td className="px-4 py-4 font-mono text-gray-300">
                      {formatPercent(tier.precision)}
                    </td>
                    <td className="px-4 py-4 font-mono text-gray-300">
                      {formatPercent(tier.recall)}
                    </td>
                    <td className={`px-4 py-4 font-mono font-semibold ${getF1Style(tier.f1)}`}>
                      {formatScore(tier.f1)}
                    </td>
                    <td className="px-4 py-4">
                      <span
                        className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-1 text-[10px] font-medium ${
                          isMatch
                            ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-400'
                            : 'border-amber-500/20 bg-amber-500/10 text-amber-400'
                        }`}
                      >
                        {isMatch ? (
                          <CheckCircle2 className="h-3 w-3" />
                        ) : (
                          <HelpCircle className="h-3 w-3" />
                        )}
                        {tier.baseline_result}
                      </span>
                    </td>
                    <td className="px-4 py-4 font-mono font-semibold text-orange-400">
                      {formatPercent(tier.bot_probability, 2)}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        <div className="border-t border-[#253044] px-4 py-3 text-[10px] text-gray-500">
          Scroll horizontally to inspect all evaluation metrics.
        </div>
      </section>

      {/* Difficulty curve */}
      <section className="overflow-hidden rounded-xl border border-[#253044] bg-[#101722]">
        <div className="flex flex-col justify-between gap-3 border-b border-[#253044] p-4 sm:flex-row sm:items-center sm:p-5">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-blue-500/20 bg-blue-500/10">
              <TrendingDown className="h-4 w-4 text-blue-400" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-100">
                Detection F1 vs. Bot Sophistication
              </h3>
              <p className="mt-1 text-[11px] leading-5 text-gray-500">
                Difficulty curve generated by the bot tier analysis experiment.
              </p>
            </div>
          </div>
          <span className="w-fit rounded-md border border-[#29364a] bg-[#141e2c] px-2.5 py-1 font-mono text-[10px] text-gray-400">
            bot_tier_curve.png
          </span>
        </div>

        <div className="p-3 sm:p-5">
          <div className="flex min-h-[220px] items-center justify-center overflow-hidden rounded-lg border border-[#253044] bg-[#0b121c] p-3 sm:min-h-[300px] sm:p-5">
            <img
              src="/api/bot-tiers/curve"
              alt="Bot tier difficulty curve showing detection F1 across sophistication levels"
              className="max-h-[420px] w-full rounded-md object-contain"
              onError={(event) => {
                event.currentTarget.style.display = 'none'
              }}
            />
          </div>
          <p className="mt-3 text-[10px] text-gray-500">
            Source: <code className="text-gray-400">ai/models/bot_tier_curve.png</code>
          </p>
        </div>
      </section>

      {/* Tier detail cards */}
      <section>
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-violet-500/20 bg-violet-500/10">
            <Bot className="h-4 w-4 text-violet-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-100">
              Behavioral Tier Breakdown
            </h3>
            <p className="mt-1 text-[11px] text-gray-500">
              Feature separation and behavioral observations for each tier.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {tiers.map((tier, index) => (
            <article
              key={tier.id}
              className="flex min-w-0 flex-col overflow-hidden rounded-xl border border-[#253044] bg-[#101722] transition-colors hover:border-[#34465f]"
            >
              <div className="border-b border-[#253044] p-4">
                <div className="mb-3 flex items-center justify-between gap-2">
                  <span className="font-mono text-[10px] uppercase tracking-wider text-gray-500">
                    Tier 0{index + 1}
                  </span>
                  <span className="rounded-md border border-blue-500/20 bg-blue-500/10 px-2 py-1 font-mono text-[10px] text-blue-300">
                    {tier.sophistication}
                  </span>
                </div>
                <h4 className="text-sm font-semibold text-gray-100">
                  {tier.name}
                </h4>
                <p className="mt-2 text-xs leading-5 text-gray-400">
                  {tier.description}
                </p>
              </div>

              <div className="flex flex-1 flex-col gap-4 p-4">
                {tier.least_separated_features &&
                  tier.least_separated_features.length > 0 && (
                    <div className="rounded-lg border border-amber-500/15 bg-amber-500/[0.035] p-3">
                      <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wider text-amber-300">
                        <Target className="h-3.5 w-3.5" />
                        Closest features to human
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {tier.least_separated_features.map((feature) => (
                          <span
                            key={feature.feature}
                            className="rounded-md border border-[#354052] bg-[#141e2c] px-2 py-1 font-mono text-[10px] text-gray-300"
                            title={`Cohen's d: ${feature.cohens_d}`}
                          >
                            {feature.feature}
                            <span className="ml-1 text-amber-300">
                              d={feature.cohens_d}
                            </span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                <div className="rounded-lg border border-[#253044] bg-[#0d141e] p-3">
                  <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                    <Activity className="h-3.5 w-3.5 text-blue-400" />
                    Behavioral analysis
                  </div>
                  <p className="text-xs leading-5 text-gray-300">
                    {tier.behavior_notes}
                  </p>
                </div>

                <div className="mt-auto grid grid-cols-2 gap-2">
                  <div className="rounded-lg border border-[#253044] bg-[#0d141e] p-3">
                    <div className="text-[10px] text-gray-500">
                      Detection F1
                    </div>
                    <div className={`mt-1 font-mono text-lg font-semibold ${getF1Style(tier.f1)}`}>
                      {formatScore(tier.f1)}
                    </div>
                  </div>
                  <div className="rounded-lg border border-[#253044] bg-[#0d141e] p-3">
                    <div className="text-[10px] text-gray-500">
                      Bot probability
                    </div>
                    <div className="mt-1 font-mono text-lg font-semibold text-orange-400">
                      {formatPercent(tier.bot_probability)}
                    </div>
                  </div>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* Tier 4 adversarial benchmark */}
      {adversarial && adversarial.scenarios && (
        <section className="overflow-hidden rounded-xl border border-rose-500/20 bg-[#101722]">
          <div className="border-b border-rose-500/15 bg-rose-500/[0.035] p-4 sm:p-5">
            <div className="flex flex-col justify-between gap-3 xl:flex-row xl:items-center">
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-rose-500/20 bg-rose-500/10">
                  <ShieldAlert className="h-5 w-5 text-rose-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-100">
                    Tier 4 Adversarial Evasion Benchmark
                  </h3>
                  <p className="mt-1 max-w-2xl text-xs leading-5 text-gray-400">
                    Evaluates classifier, Isolation Forest, and hybrid defense
                    resilience against delay and feature-shaping bots.
                  </p>
                </div>
              </div>
              <span className="w-fit max-w-full break-words rounded-md border border-rose-500/20 bg-rose-500/10 px-2.5 py-1.5 font-mono text-[10px] text-rose-300">
                Provenance: {adversarial.benchmark_provenance}
              </span>
            </div>
          </div>

          <div className="space-y-6 p-4 sm:p-5">
            <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
              {Object.entries(adversarial.scenarios).map(([key, scenario]: [string, any]) => (
                <article
                  key={key}
                  className="rounded-xl border border-[#253044] bg-[#0d141e] p-4"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-rose-500/15 bg-rose-500/[0.07]">
                        <ShieldAlert className="h-4 w-4 text-rose-400" />
                      </div>
                      <h4 className="text-xs font-semibold capitalize text-gray-200">
                        {key.replace(/_/g, ' ')}
                      </h4>
                    </div>
                    <span className="rounded-md border border-[#29364a] bg-[#141e2c] px-2 py-1 font-mono text-[10px] text-gray-400">
                      N = {scenario.total_sessions}
                    </span>
                  </div>

                  <p className="mt-3 text-xs leading-5 text-gray-400">
                    {scenario.description}
                  </p>

                  <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
                    <div className="rounded-lg border border-[#29364a] bg-[#111a27] p-3">
                      <div className="text-[10px] text-gray-500">
                        Classifier evasion
                      </div>
                      <div className="mt-1 font-mono text-lg font-semibold text-rose-400">
                        {formatPercent(scenario.classifier_evasion_rate)}
                      </div>
                    </div>
                    <div className="rounded-lg border border-[#29364a] bg-[#111a27] p-3">
                      <div className="text-[10px] text-gray-500">
                        Suspicious rescue
                      </div>
                      <div className="mt-1 font-mono text-lg font-semibold text-amber-400">
                        {formatPercent(scenario.suspicious_rescue_rate)}
                      </div>
                    </div>
                    <div className="rounded-lg border border-[#29364a] bg-[#111a27] p-3">
                      <div className="text-[10px] text-gray-500">
                        Outright bot verdict
                      </div>
                      <div className="mt-1 font-mono text-lg font-semibold text-emerald-400">
                        {formatPercent(scenario.bot_detection_rate)}
                      </div>
                    </div>
                    <div className="rounded-lg border border-[#29364a] bg-[#111a27] p-3">
                      <div className="text-[10px] text-gray-500">
                        Net SentinelNet evasion
                      </div>
                      <div className="mt-1 font-mono text-lg font-semibold text-violet-400">
                        {formatPercent(scenario.hybrid_sentinelnet_evasion_rate)}
                      </div>
                    </div>
                  </div>
                </article>
              ))}
            </div>

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
              <article className="rounded-xl border border-amber-500/15 bg-amber-500/[0.025] p-4">
                <div className="mb-3 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-400" />
                  <h4 className="text-xs font-semibold text-amber-200">
                    Vulnerability Analysis
                  </h4>
                </div>
                <p className="text-xs leading-5 text-gray-300">
                  {adversarial.vulnerability_analysis}
                </p>
              </article>

              <article className="rounded-xl border border-blue-500/15 bg-blue-500/[0.025] p-4">
                <div className="mb-3 flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-blue-400" />
                  <h4 className="text-xs font-semibold text-blue-200">
                    Recommended Countermeasures
                  </h4>
                </div>
                <div className="space-y-3">
                  {adversarial.recommended_countermeasures.map((item, index) => (
                    <div key={`${item.dimension}-${item.feature}-${index}`} className="flex items-start gap-2">
                      <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-blue-400" />
                      <div className="min-w-0 text-xs leading-5 text-gray-300">
                        <span className="mr-1 font-semibold text-blue-300">
                          [{item.dimension}]
                        </span>
                        <strong>{item.feature}:</strong> {item.rationale}
                      </div>
                    </div>
                  ))}
                </div>
              </article>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}


import React from 'react'
import {
  Network,
  Cpu,
  Activity,
  ArrowDown,
  ArrowRight,
  CheckCircle2,
  CircleDot,
  GitBranch,
  Layers3,
  Workflow,
  ShieldCheck,
  Database,
  BrainCircuit,
} from 'lucide-react'

export const ArchitecturePage: React.FC = () => {
  const stages = [
    {
      title: 'Traffic Source',
      number: '01',
      desc: 'Local test server (Flask), automated bot scripts (Tiers 1–3), or physical TCP streams.',
      domain: 'Source',
      status: 'Implemented',
    },
    {
      title: 'Packet Ingestion',
      number: '02',
      desc: 'Scapy sniffing with targeted BPF filter or zero-dependency binary PCAP replay (rdpcap).',
      domain: 'CN',
      status: 'PCAP Verified / Live Unverified',
    },
    {
      title: 'Packet Parser',
      number: '03',
      desc: 'packet_parser.py decodes 12-tuple metadata (IPs, ports, TCP flags, sequence numbers).',
      domain: 'CN',
      status: 'Unit Verified',
    },
    {
      title: 'Flow Tracking',
      number: '04',
      desc: 'FlowTracker + SessionTracker maintain bidirectional 5-tuple state and TCP lifecycles.',
      domain: 'CN',
      status: 'Integration Verified',
    },
    {
      title: 'Feature Extraction',
      number: '05',
      desc: 'extract_features() computes the 9 AI contract metrics (rates, intervals, sizes, variance).',
      domain: 'CN',
      status: 'Contract Verified',
    },
    {
      title: 'AI Bridge',
      number: '06',
      desc: 'ai_bridge.py validates contract schemas, guards against NaN/Inf, and applies StandardScaler.',
      domain: 'AI',
      status: '29 Tests Verified',
    },
    {
      title: 'ML Classifier',
      number: '07',
      desc: 'Multinomial Logistic Regression calculates class decision logits and softmax probabilities.',
      domain: 'AI',
      status: 'Trained Baseline',
    },
    {
      title: 'Dashboard Presentation',
      number: '08',
      desc: 'Web intelligence dashboard visualizes telemetry, distributions, and root causes.',
      domain: 'Web',
      status: 'Active',
    },
  ]

  const domainStyle: Record<string, string> = {
    Source: 'border-slate-500/25 bg-slate-500/10 text-slate-300',
    CN: 'border-blue-500/25 bg-blue-500/10 text-blue-300',
    AI: 'border-violet-500/25 bg-violet-500/10 text-violet-300',
    Web: 'border-emerald-500/25 bg-emerald-500/10 text-emerald-300',
  }

  const cnCapabilities = [
    'Scapy packet sniffing and binary PCAP decoding',
    'TCP handshake (SYN/ACK) and teardown (FIN/RST) state machine',
    'Bidirectional 5-tuple flow key generation',
    'Inter-arrival time variance and rate computation',
  ]

  const aiCapabilities = [
    '9-feature contract schema validation and NaN/Inf protection',
    'StandardScaler and OneHotEncoder preprocessing',
    'Multinomial Logistic Regression classification',
    'Human, Bot, and Suspicious class probability estimates',
  ]

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8">
      {/* Page header */}
      <header>
        <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-blue-400">
          <Workflow className="h-3.5 w-3.5" />
          Technical Overview
        </div>
        <h2 className="text-xl font-semibold tracking-tight text-gray-100 sm:text-2xl">
          System Architecture
        </h2>
        <p className="mt-1.5 max-w-3xl text-xs leading-5 text-gray-400 sm:text-sm">
          End-to-end architecture of SentinelNet, from packet capture and
          connection tracking to behavioral feature extraction and AI inference.
        </p>
      </header>

      {/* Architecture summary */}
      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          {
            label: 'Pipeline stages',
            value: '08',
            icon: Workflow,
            color: 'text-blue-400',
          },
          {
            label: 'Core domains',
            value: '04',
            icon: Layers3,
            color: 'text-violet-400',
          },
          {
            label: 'AI contract features',
            value: '09',
            icon: BrainCircuit,
            color: 'text-cyan-400',
          },
          {
            label: 'Primary input',
            value: 'TCP',
            icon: Network,
            color: 'text-emerald-400',
          },
        ].map((metric) => {
          const Icon = metric.icon

          return (
            <div
              key={metric.label}
              className="rounded-xl border border-[#253044] bg-[#101722] p-4"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-[10px] font-medium uppercase tracking-wider text-gray-500">
                  {metric.label}
                </span>
                <Icon className={`h-4 w-4 shrink-0 ${metric.color}`} />
              </div>
              <div className={`mt-3 font-mono text-2xl font-semibold ${metric.color}`}>
                {metric.value}
              </div>
            </div>
          )
        })}
      </section>

      {/* Domain breakdown */}
      <section>
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-gray-100">
            System Domains
          </h3>
          <p className="mt-1 text-[11px] text-gray-500">
            Responsibilities and principal capabilities of the core technical layers.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {/* Computer Networks */}
          <article className="overflow-hidden rounded-xl border border-blue-500/20 bg-[#101722]">
            <div className="flex items-center gap-3 border-b border-blue-500/15 bg-blue-500/[0.035] p-4 sm:p-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-blue-500/20 bg-blue-500/10">
                <Network className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-gray-100">
                  Computer Networks
                </h4>
                <p className="mt-1 text-[10px] uppercase tracking-wider text-blue-300">
                  Packet processing · Flow tracking
                </p>
              </div>
            </div>

            <div className="p-4 sm:p-5">
              <p className="text-xs leading-6 text-gray-400">
                Responsible for transport-layer network interaction, packet
                decoding, stateful connection tracking, and converting raw
                packet timestamps and byte counters into nine statistical
                behavioral features.
              </p>

              <div className="mt-4 space-y-3">
                {cnCapabilities.map((capability, index) => (
                  <div key={capability} className="flex items-start gap-3">
                    <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md border border-blue-500/15 bg-blue-500/[0.07] font-mono text-[10px] text-blue-300">
                      {String(index + 1).padStart(2, '0')}
                    </div>
                    <p className="pt-1 text-xs leading-5 text-gray-300">
                      {capability}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </article>

          {/* Artificial Intelligence */}
          <article className="overflow-hidden rounded-xl border border-violet-500/20 bg-[#101722]">
            <div className="flex items-center gap-3 border-b border-violet-500/15 bg-violet-500/[0.035] p-4 sm:p-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-violet-500/20 bg-violet-500/10">
                <Cpu className="h-5 w-5 text-violet-400" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-gray-100">
                  Artificial Intelligence
                </h4>
                <p className="mt-1 text-[10px] uppercase tracking-wider text-violet-300">
                  Feature validation · Classification
                </p>
              </div>
            </div>

            <div className="p-4 sm:p-5">
              <p className="text-xs leading-6 text-gray-400">
                Receives validated contract features, standardizes numerical
                ranges, computes logistic decision boundaries, and estimates
                class probability distributions.
              </p>

              <div className="mt-4 space-y-3">
                {aiCapabilities.map((capability, index) => (
                  <div key={capability} className="flex items-start gap-3">
                    <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md border border-violet-500/15 bg-violet-500/[0.07] font-mono text-[10px] text-violet-300">
                      {String(index + 1).padStart(2, '0')}
                    </div>
                    <p className="pt-1 text-xs leading-5 text-gray-300">
                      {capability}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </article>
        </div>
      </section>

      {/* End-to-end pipeline */}
      <section className="overflow-hidden rounded-xl border border-[#253044] bg-[#101722]">
        <div className="flex flex-col justify-between gap-3 border-b border-[#253044] p-4 sm:flex-row sm:items-center sm:p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-blue-500/20 bg-blue-500/10">
              <GitBranch className="h-4 w-4 text-blue-400" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-100">
                End-to-End Data Pipeline
              </h3>
              <p className="mt-1 text-[11px] text-gray-500">
                Eight stages from network input to dashboard presentation.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-[10px] text-gray-400">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-blue-400" />
              Computer Networks
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-violet-400" />
              AI
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              Web
            </span>
          </div>
        </div>

        <div className="p-4 sm:p-5">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {stages.map((stage, index) => (
              <React.Fragment key={stage.number}>
                <article className="group relative flex min-w-0 flex-col rounded-xl border border-[#29364a] bg-[#0d141e] p-4 transition-colors hover:border-[#3b506c] hover:bg-[#111b29]">
                  <div className="mb-4 flex items-center justify-between gap-2">
                    <span className="font-mono text-[10px] tracking-widest text-gray-500">
                      STAGE {stage.number}
                    </span>
                    <span
                      className={`rounded-md border px-2 py-1 text-[10px] font-medium ${domainStyle[stage.domain]}`}
                    >
                      {stage.domain}
                    </span>
                  </div>

                  <h4 className="text-sm font-semibold leading-5 text-gray-100">
                    {stage.title.replace(/^\d+\.\s*/, '')}
                  </h4>

                  <p className="mt-2 flex-1 text-xs leading-5 text-gray-400">
                    {stage.desc}
                  </p>

                  <div className="mt-4 border-t border-[#253044] pt-3">
                    <div className="mb-1.5 flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-gray-500">
                      <CircleDot className="h-3 w-3" />
                      Verification status
                    </div>
                    <div className="flex items-start gap-2 text-[11px] leading-5 text-gray-300">
                      <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-400" />
                      <span>{stage.status}</span>
                    </div>
                  </div>
                </article>

                {index < stages.length - 1 && (
                  <div
                    aria-hidden="true"
                    className="flex items-center justify-center text-gray-600 sm:hidden"
                  >
                    <ArrowDown className="h-4 w-4" />
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>

          <div className="mt-5 flex items-center justify-center gap-2 rounded-lg border border-[#253044] bg-[#0d141e] px-4 py-3 text-center">
            <Database className="h-4 w-4 shrink-0 text-blue-400" />
            <span className="text-[11px] text-gray-400">
              Packet data
            </span>
            <ArrowRight className="h-3.5 w-3.5 shrink-0 text-gray-600" />
            <Activity className="h-4 w-4 shrink-0 text-violet-400" />
            <span className="text-[11px] text-gray-400">
              Behavioral inference
            </span>
            <ArrowRight className="h-3.5 w-3.5 shrink-0 text-gray-600" />
            <ShieldCheck className="h-4 w-4 shrink-0 text-emerald-400" />
            <span className="text-[11px] text-gray-400">
              Dashboard
            </span>
          </div>
        </div>
      </section>
    </div>
  )
}

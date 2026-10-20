
import React from 'react'
import {
  ShieldCheck,
  AlertTriangle,
  Network,
  Cpu,
  Code2,
  FlaskConical,
  Database,
  Activity,
  LockKeyhole,
  ArrowUpRight,
  Layers3,
  Terminal,
} from 'lucide-react'

export const AboutPage: React.FC = () => {
  const actualTechStack = [
    {
      category: 'Network Packet Processing',
      icon: Network,
      color: 'text-blue-400',
      items: ['Scapy 2.8.0', 'BPF Filtering', 'TCP State Machine', 'PCAP I/O'],
    },
    {
      category: 'Machine Learning & Preprocessing',
      icon: Cpu,
      color: 'text-violet-400',
      items: [
        'scikit-learn 1.9.0',
        'joblib 1.6.0',
        'StandardScaler',
        'OneHotEncoder',
        'LogisticRegression',
      ],
    },
    {
      category: 'Data & Mathematical Modeling',
      icon: Database,
      color: 'text-cyan-400',
      items: [
        'pandas 3.0.5',
        'numpy 2.5.2',
        'Statistical Moments & Variance',
      ],
    },
    {
      category: 'Backend API Service',
      icon: Terminal,
      color: 'text-emerald-400',
      items: ['Python 3.13', 'Flask 3.1.3 (Zero-dependency CORS)'],
    },
    {
      category: 'Frontend Intelligence Dashboard',
      icon: Code2,
      color: 'text-blue-400',
      items: [
        'React 18',
        'TypeScript',
        'Vite',
        'Tailwind CSS',
        'Recharts',
        'Lucide Icons',
      ],
    },
    {
      category: 'Verification & Testing',
      icon: FlaskConical,
      color: 'text-amber-400',
      items: ['pytest 9.1.1 (62 Unit & Integration Tests)'],
    },
  ]

  const limitations = [
    {
      title: 'Synthetic Training Baseline',
      description:
        'The AI classifier was trained on 500 synthetic prototype sessions (sentinelnet_sample_500.csv). Real-world detection accuracy on wild internet traffic is not established.',
    },
    {
      title: 'Domain Shift Mismatches',
      description:
        'In physical PCAP replay, single-flow connection counts (num_connections = 1) and small loopback packet sizes (~95–101 B) differ from training distributions, leading to Tier 2 and Tier 3 mismatches.',
    },
    {
      title: 'Behavioral Mimicry Limits',
      description:
        'Tier 3 bot traffic draws from empirical human delay intervals, intentionally evading linear statistical macro-interval models.',
    },
    {
      title: 'Platform Dependency for Live Sniffing',
      description:
        'Windows live packet capture requires the Npcap kernel driver and Administrator privileges. SentinelNet defaults to fully reproducible offline PCAP replay.',
    },
  ]

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8">
      {/* Page heading */}
      <header>
        <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-blue-400">
          <ShieldCheck className="h-3.5 w-3.5" />
          Project Information
        </div>
        <h2 className="text-xl font-semibold tracking-tight text-gray-100 sm:text-2xl">
          About SentinelNet
        </h2>
        <p className="mt-1.5 text-xs leading-5 text-gray-400 sm:text-sm">
          Project objectives, technical implementation, and evaluation limitations.
        </p>
      </header>

      {/* Project banner */}
      <section className="relative overflow-hidden rounded-2xl border border-blue-500/20 bg-[#101722]">
        <div className="pointer-events-none absolute -right-12 -top-16 h-64 w-64 rounded-full bg-blue-500/[0.07] blur-3xl" />
        <div className="pointer-events-none absolute -bottom-24 right-1/3 h-48 w-48 rounded-full bg-cyan-500/[0.04] blur-3xl" />

        <div className="relative space-y-6 p-5 sm:p-8">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-blue-500/25 bg-blue-500/10">
              <ShieldCheck className="h-7 w-7 text-blue-400" />
            </div>

            <div className="min-w-0">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <span className="rounded-md border border-emerald-500/20 bg-emerald-500/[0.07] px-2 py-1 text-[9px] font-semibold uppercase tracking-wider text-emerald-300">
                  Academic Project
                </span>
              </div>

              <h3 className="text-xl font-bold leading-tight tracking-tight text-gray-100 sm:text-2xl">
                SentinelNet
              </h3>
              <p className="mt-2 text-sm leading-6 text-blue-300">
                AI-Assisted Network Traffic Intelligence
              </p>
              <p className="mt-2 text-xs leading-5 text-gray-400">
                Academic Computer Networks &amp; Machine Learning Integration Project
              </p>
            </div>
          </div>

          <blockquote className="rounded-xl border border-[#29364a] border-l-2 border-l-blue-400 bg-[#0b121c]/80 p-4 sm:p-5">
            <p className="text-sm leading-6 text-gray-200 sm:text-base">
              “Wireshark tells you what is happening; SentinelNet tells you what it probably means.”
            </p>
          </blockquote>

          <p className="max-w-4xl text-xs leading-6 text-gray-400 sm:text-sm">
            SentinelNet analyzes network-flow behavioral telemetry at the
            transport and session layer, extracting statistical rate and timing
            features to predict whether traffic originates from a{' '}
            <strong className="font-medium text-emerald-400">Human</strong>, a{' '}
            <strong className="font-medium text-orange-400">Bot</strong>, or a{' '}
            <strong className="font-medium text-rose-400">Suspicious</strong>{' '}
            actor without inspecting or decrypting application payloads.
          </p>

          <div className="grid grid-cols-1 gap-3 border-t border-[#253044] pt-5 sm:grid-cols-3">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-blue-500/15 bg-blue-500/[0.07]">
                <Network className="h-4 w-4 text-blue-400" />
              </div>
              <div>
                <div className="text-xs font-semibold text-gray-200">
                  Network telemetry
                </div>
                <div className="mt-1 text-[10px] text-gray-500">
                  Packet and flow analysis
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-violet-500/15 bg-violet-500/[0.07]">
                <Cpu className="h-4 w-4 text-violet-400" />
              </div>
              <div>
                <div className="text-xs font-semibold text-gray-200">
                  ML inference
                </div>
                <div className="mt-1 text-[10px] text-gray-500">
                  Statistical classification
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-emerald-500/15 bg-emerald-500/[0.07]">
                <Activity className="h-4 w-4 text-emerald-400" />
              </div>
              <div>
                <div className="text-xs font-semibold text-gray-200">
                  Intelligence dashboard
                </div>
                <div className="mt-1 text-[10px] text-gray-500">
                  Behavioral insights
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Project objective */}
      <section className="rounded-xl border border-[#253044] bg-[#101722] p-5 sm:p-6">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-blue-500/20 bg-blue-500/10">
            <TargetIcon />
          </div>
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-gray-100">
              Project Objective
            </h3>
            <p className="mt-2 text-xs leading-6 text-gray-400 sm:text-sm">
              The goal of SentinelNet is to establish a rigorous, validated
              integration bridge between low-level packet capture and flow
              processing (Computer Networks) and statistical machine learning
              (Artificial Intelligence). The system demonstrates how
              transport-layer timing variance, packet sizes, and connection
              states can be quantified into a standard nine-feature contract
              for ML inference.
            </p>
          </div>
        </div>
      </section>

      {/* Technology stack */}
      <section>
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-cyan-500/20 bg-cyan-500/10">
            <Layers3 className="h-4 w-4 text-cyan-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-100">
              Technology Stack
            </h3>
            <p className="mt-1 text-[11px] text-gray-500">
              Technologies and libraries documented in the repository.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
          {actualTechStack.map((tech) => {
            const Icon = tech.icon

            return (
              <article
                key={tech.category}
                className="group rounded-xl border border-[#253044] bg-[#101722] p-4 transition-colors hover:border-[#354761]"
              >
                <div className="flex items-start gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-[#29364a] bg-[#141e2c]">
                    <Icon className={`h-4 w-4 ${tech.color}`} />
                  </div>
                  <div className="min-w-0 pt-0.5">
                    <h4 className="text-xs font-semibold leading-5 text-gray-200">
                      {tech.category}
                    </h4>
                    <span className="mt-1 block text-[9px] uppercase tracking-wider text-gray-600">
                      {tech.items.length} components
                    </span>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-1.5">
                  {tech.items.map((item) => (
                    <span
                      key={item}
                      className="rounded-md border border-[#29364a] bg-[#0d141e] px-2 py-1.5 font-mono text-[10px] leading-4 text-gray-300"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </article>
            )
          })}
        </div>
      </section>

      {/* Limitations */}
      <section className="overflow-hidden rounded-xl border border-amber-500/20 bg-[#101722]">
        <div className="flex items-start gap-3 border-b border-amber-500/15 bg-amber-500/[0.035] p-4 sm:p-5">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-amber-500/20 bg-amber-500/10">
            <AlertTriangle className="h-5 w-5 text-amber-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-100">
              Known Limitations &amp; Evaluation Findings
            </h3>
            <p className="mt-1 text-xs leading-5 text-gray-500">
              Current constraints and evaluation findings documented for the project.
            </p>
          </div>
        </div>

        <div className="space-y-3 p-4 sm:p-5">
          {limitations.map((limitation, index) => (
            <article
              key={limitation.title}
              className="flex items-start gap-3 rounded-lg border border-[#293242] bg-[#0d141e] p-4"
            >
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-amber-500/15 bg-amber-500/[0.07] font-mono text-xs font-semibold text-amber-400">
                0{index + 1}
              </div>

              <div className="min-w-0 flex-1">
                <h4 className="text-xs font-semibold text-gray-200">
                  {limitation.title}
                </h4>
                <p className="mt-1.5 text-xs leading-5 text-gray-400">
                  {limitation.description}
                </p>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* Project note */}
      <footer className="flex items-start gap-3 rounded-xl border border-[#253044] bg-[#101722] p-4">
        <LockKeyhole className="mt-0.5 h-4 w-4 shrink-0 text-gray-500" />
        <p className="text-[11px] leading-5 text-gray-500">
          SentinelNet uses network-flow statistics for behavioral inference.
          Its predictions should be interpreted in the context of the documented
          training data, validation results, and known limitations.
        </p>
        <ArrowUpRight className="ml-auto h-4 w-4 shrink-0 text-gray-600" />
      </footer>
    </div>
  )
}

const TargetIcon: React.FC = () => (
  <Activity className="h-4 w-4 text-blue-400" />
)

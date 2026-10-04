import React from 'react'
import {
  ShieldCheck,
  AlertTriangle,
} from 'lucide-react'

export const AboutPage: React.FC = () => {
  const actualTechStack = [
    { category: 'Network Packet Processing', items: ['Scapy 2.8.0', 'BPF Filtering', 'TCP State Machine', 'PCAP I/O'] },
    { category: 'Machine Learning & Preprocessing', items: ['scikit-learn 1.9.0', 'joblib 1.6.0', 'StandardScaler', 'OneHotEncoder', 'LogisticRegression'] },
    { category: 'Data & Mathematical Modeling', items: ['pandas 3.0.5', 'numpy 2.5.2', 'Statistical Moments & Variance'] },
    { category: 'Backend API Service', items: ['Python 3.13', 'Flask 3.1.3 (Zero-dependency CORS)'] },
    { category: 'Frontend Intelligence Dashboard', items: ['React 18', 'TypeScript', 'Vite', 'Tailwind CSS', 'Recharts', 'Lucide Icons'] },
    { category: 'Verification & Testing', items: ['pytest 9.1.1 (62 Unit & Integration Tests)'] },
  ]

  const limitations = [
    'Synthetic Training Baseline: The AI classifier was trained on 500 synthetic prototype sessions (sentinelnet_sample_500.csv). Real-world detection accuracy on wild internet traffic is not established.',
    'Domain Shift Mismatches: In physical PCAP replay, single-flow connection counts (num_connections = 1) and small loopback packet sizes (~95-101 B) differ from training distributions, leading to Tier 2 and Tier 3 mismatches.',
    'Behavioral Mimicry Limits: Tier 3 bot traffic draws from empirical human delay intervals, intentionally evading linear statistical macro-interval models.',
    'Platform Dependency for Live Sniffing: Windows live packet capture requires the Npcap kernel driver and Administrator privileges. SentinelNet defaults to fully reproducible offline PCAP replay.',
  ]

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Project Banner & One-Liner */}
      <div className="p-8 rounded-xl bg-linear-to-r from-[#141724] to-[#12141e] border border-[#232734] space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-100 tracking-tight">
              SentinelNet — AI-Assisted Network Traffic Intelligence
            </h2>
            <p className="text-xs text-blue-400 font-mono mt-0.5">
              Academic Computer Networks & Machine Learning Integration Project
            </p>
          </div>
        </div>

        <blockquote className="p-4 rounded-lg bg-[#0e1017] border-l-2 border-blue-500 text-sm text-gray-300 italic font-serif">
          "Wireshark tells you what is happening; SentinelNet tells you what it probably means."
        </blockquote>

        <p className="text-xs text-gray-400 leading-relaxed max-w-4xl">
          SentinelNet analyzes network-flow behavioral telemetry at the transport and session layer,
          extracting statistical rate and timing features to predict whether traffic originates from a{' '}
          <strong className="text-emerald-400 font-medium">Human</strong>, a{' '}
          <strong className="text-orange-400 font-medium">Bot</strong>, or a{' '}
          <strong className="text-rose-400 font-medium">Suspicious</strong> actor without inspecting
          or decrypting application payloads.
        </p>
      </div>

      {/* Project Objective */}
      <div className="p-6 rounded-xl bg-[#12141d] border border-[#202432] space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-200">
          Project Objective
        </h3>
        <p className="text-xs text-gray-300 leading-relaxed">
          The goal of SentinelNet is to establish a rigorous, validated integration bridge between low-level
          packet capture / flow processing (Computer Networks) and statistical machine learning (Artificial Intelligence).
          The system demonstrates how transport-layer timing variance, packet sizes, and connection states can be
          quantified into a standard 9-feature contract for ML inference.
        </p>
      </div>

      {/* Actual Technology Stack */}
      <div className="p-6 rounded-xl bg-[#12141d] border border-[#202432] space-y-4">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-200">
          Actual Technology Stack in Repository
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {actualTechStack.map((tech, idx) => (
            <div key={idx} className="p-4 rounded-lg bg-[#151822] border border-[#232734] space-y-2">
              <span className="text-[11px] font-semibold text-blue-400 block">{tech.category}</span>
              <ul className="space-y-1">
                {tech.items.map((item, itemIdx) => (
                  <li key={itemIdx} className="text-xs text-gray-300 font-mono flex items-center gap-1.5">
                    <span className="w-1 h-1 rounded-full bg-gray-500" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Known Limitations Callout */}
      <div className="p-6 rounded-xl bg-[#12141d] border border-[#202432] space-y-4">
        <div className="flex items-center gap-2 text-amber-400">
          <AlertTriangle className="w-4 h-4" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-200">
            Known Limitations & Evaluation Findings
          </h3>
        </div>
        <div className="space-y-2.5">
          {limitations.map((lim, idx) => (
            <div key={idx} className="p-3.5 rounded-lg bg-[#151722] border border-[#232734] text-xs text-gray-300 leading-relaxed flex items-start gap-2.5">
              <span className="font-mono text-amber-400 font-semibold shrink-0">{idx + 1}.</span>
              <span>{lim}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

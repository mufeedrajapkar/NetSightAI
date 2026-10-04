import React from 'react'
import {
  Network,
  Cpu,
} from 'lucide-react'

export const ArchitecturePage: React.FC = () => {
  const stages = [
    {
      title: '1. Traffic Source',
      desc: 'Local test server (Flask), automated bot scripts (Tiers 1–3), or physical TCP streams.',
      domain: 'Source',
      status: 'Implemented',
    },
    {
      title: '2. Packet Ingestion',
      desc: 'Scapy sniffing with targeted BPF filter or zero-dependency binary PCAP replay (rdpcap).',
      domain: 'CN',
      status: 'PCAP Verified / Live Unverified',
    },
    {
      title: '3. Packet Parser',
      desc: 'packet_parser.py decodes 12-tuple metadata (IPs, ports, TCP flags, sequence numbers).',
      domain: 'CN',
      status: 'Unit Verified',
    },
    {
      title: '4. Flow Tracking',
      desc: 'FlowTracker + SessionTracker maintain bidirectional 5-tuple state and TCP lifecycles.',
      domain: 'CN',
      status: 'Integration Verified',
    },
    {
      title: '5. Feature Extraction',
      desc: 'extract_features() computes the 9 AI contract metrics (rates, intervals, sizes, variance).',
      domain: 'CN',
      status: 'Contract Verified',
    },
    {
      title: '6. AI Bridge',
      desc: 'ai_bridge.py validates contract schemas, guards against NaN/Inf, and applies StandardScaler.',
      domain: 'AI',
      status: '29 Tests Verified',
    },
    {
      title: '7. ML Classifier',
      desc: 'Multinomial Logistic Regression calculates class decision logits and softmax probabilities.',
      domain: 'AI',
      status: 'Trained Baseline',
    },
    {
      title: '8. Dashboard Presentation',
      desc: 'Minimalist web intelligence dashboard visualizing telemetry, distributions, and root-causes.',
      domain: 'Web',
      status: 'Active',
    },
  ]

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div>
        <h2 className="text-xl font-semibold text-gray-100 tracking-tight">
          System Architecture & Pipeline Topology
        </h2>
        <p className="text-xs text-gray-400 mt-1">
          Visual specification of data transformations from raw packet capture to machine learning inference.
        </p>
      </div>

      {/* Domain Breakdown Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Computer Networks Card */}
        <div className="p-5 rounded-xl bg-[#12141d] border border-[#202432] space-y-3">
          <div className="flex items-center gap-2 text-blue-400">
            <Network className="w-5 h-5" />
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-200">
              Computer Networks Domain
            </h3>
          </div>
          <p className="text-xs text-gray-400 leading-relaxed">
            Responsible for transport-layer network interaction, packet decoding, stateful connection tracking,
            and converting raw packet timestamps and byte counters into 9 statistical behavioral features.
          </p>
          <ul className="space-y-1.5 pt-2 text-xs text-gray-300 font-mono">
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
              Scapy packet sniffing & binary PCAP decoding
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
              TCP handshake (SYN/ACK) & teardown (FIN/RST) state machine
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
              Bidirectional 5-tuple flow key generation
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
              Inter-arrival time variance and rate computation
            </li>
          </ul>
        </div>

        {/* Artificial Intelligence Card */}
        <div className="p-5 rounded-xl bg-[#12141d] border border-[#202432] space-y-3">
          <div className="flex items-center gap-2 text-purple-400">
            <Cpu className="w-5 h-5" />
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-200">
              Artificial Intelligence Domain
            </h3>
          </div>
          <p className="text-xs text-gray-400 leading-relaxed">
            Responsible for receiving contract features through a strictly validated bridge, standardizing numerical
            ranges, computing logistic decision boundaries, and estimating class probability distributions.
          </p>
          <ul className="space-y-1.5 pt-2 text-xs text-gray-300 font-mono">
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
              9-feature contract schema validation (defense against NaN/Inf)
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
              StandardScaler + OneHotEncoder preprocessing
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
              Multinomial Logistic Regression classification
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
              Probability estimates for Human, Bot, and Suspicious classes
            </li>
          </ul>
        </div>
      </div>

      {/* End-to-End Pipeline Stage Diagram */}
      <div className="p-6 rounded-xl bg-[#12141d] border border-[#202432] space-y-4">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-200 mb-2">
          End-to-End Data Pipeline Flow
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {stages.map((st, idx) => (
            <div
              key={idx}
              className="p-4 rounded-lg bg-[#151822] border border-[#232734] flex flex-col justify-between space-y-3 relative"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-100">{st.title}</span>
                  <span
                    className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                      st.domain === 'CN'
                        ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                        : st.domain === 'AI'
                        ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                        : 'bg-gray-700/20 text-gray-300'
                    }`}
                  >
                    {st.domain}
                  </span>
                </div>
                <p className="text-[11px] text-gray-400 leading-relaxed">{st.desc}</p>
              </div>

              <div className="pt-2 border-t border-[#1e2230] flex items-center justify-between text-[10px] font-mono">
                <span className="text-gray-400">Status:</span>
                <span className="text-emerald-400 font-semibold">{st.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

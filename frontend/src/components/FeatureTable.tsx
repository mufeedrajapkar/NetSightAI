import React from 'react'
import type { FeatureValues } from '../types'

interface FeatureTableProps {
  features: FeatureValues
}

interface FeatureMeta {
  key: keyof FeatureValues
  name: string
  description: string
  unit: string
  format: (val: any) => string
}

const FEATURE_DEFINITIONS: FeatureMeta[] = [
  {
    key: 'requests_per_sec',
    name: 'requests_per_sec',
    description: 'Packet arrival rate (packet_count / session_duration)',
    unit: 'pkts/s',
    format: (v) => (typeof v === 'number' ? v.toFixed(4) : String(v)),
  },
  {
    key: 'session_duration',
    name: 'session_duration',
    description: 'Duration between first and last observed packets in session',
    unit: 'sec',
    format: (v) => (typeof v === 'number' ? `${v.toFixed(4)}s` : String(v)),
  },
  {
    key: 'packet_size_mean',
    name: 'packet_size_mean',
    description: 'Sample mean of packet byte sizes',
    unit: 'bytes',
    format: (v) => (typeof v === 'number' ? `${v.toFixed(2)} B` : String(v)),
  },
  {
    key: 'packet_size_var',
    name: 'packet_size_var',
    description: 'Variance of packet sizes within session',
    unit: 'B²',
    format: (v) => (typeof v === 'number' ? v.toFixed(2) : String(v)),
  },
  {
    key: 'request_interval_mean',
    name: 'request_interval_mean',
    description: 'Mean inter-packet arrival time (delta t)',
    unit: 'sec',
    format: (v) => (typeof v === 'number' ? `${v.toFixed(4)}s` : String(v)),
  },
  {
    key: 'request_interval_var',
    name: 'request_interval_var',
    description: 'Variance of inter-packet arrival intervals',
    unit: 's²',
    format: (v) => (typeof v === 'number' ? v.toFixed(6) : String(v)),
  },
  {
    key: 'bytes_transferred',
    name: 'bytes_transferred',
    description: 'Total volume of bytes transferred across session',
    unit: 'bytes',
    format: (v) => (typeof v === 'number' ? `${v.toLocaleString()} B` : String(v)),
  },
  {
    key: 'num_connections',
    name: 'num_connections',
    description: 'Total distinct TCP connections in this session',
    unit: 'count',
    format: (v) => String(v),
  },
  {
    key: 'protocol',
    name: 'protocol',
    description: 'Transport layer protocol (TCP/UDP)',
    unit: 'protocol',
    format: (v) => String(v),
  },
]

export const FeatureTable: React.FC<FeatureTableProps> = ({ features }) => {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs">
        <thead>
          <tr className="border-b border-[#232734] text-gray-400 uppercase text-[10px] tracking-wider">
            <th className="py-2.5 px-3">Contract Feature</th>
            <th className="py-2.5 px-3">Physical CN Meaning</th>
            <th className="py-2.5 px-3 text-right">Extracted Value</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#1c202b]">
          {FEATURE_DEFINITIONS.map((def) => {
            const rawVal = features[def.key]
            const formatted = def.format(rawVal)
            return (
              <tr key={def.key} className="hover:bg-[#161922] transition-colors">
                <td className="py-2.5 px-3 font-mono font-medium text-blue-400">
                  {def.name}
                </td>
                <td className="py-2.5 px-3 text-gray-400">
                  {def.description}
                </td>
                <td className="py-2.5 px-3 text-right font-mono font-semibold text-gray-100">
                  {formatted}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

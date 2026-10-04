import type {
  SystemStatus,
  OverviewData,
  FlowRecord,
  BotTiersResponse,
  ArchitectureResponse,
} from '../types'

const API_BASE = '/api'

export async function fetchStatus(): Promise<SystemStatus> {
  const res = await fetch(`${API_BASE}/status`)
  if (!res.ok) {
    throw new Error(`Failed to fetch status: ${res.statusText}`)
  }
  return res.json()
}

export async function fetchOverview(): Promise<OverviewData> {
  const res = await fetch(`${API_BASE}/overview`)
  if (!res.ok) {
    throw new Error(`Failed to fetch overview: ${res.statusText}`)
  }
  return res.json()
}

export async function fetchFlows(): Promise<{ count: number; flows: FlowRecord[] }> {
  const res = await fetch(`${API_BASE}/flows`)
  if (!res.ok) {
    throw new Error(`Failed to fetch flows: ${res.statusText}`)
  }
  return res.json()
}

export async function fetchFlowDetail(flowId: string): Promise<FlowRecord> {
  const res = await fetch(`${API_BASE}/flows/${encodeURIComponent(flowId)}`)
  if (!res.ok) {
    throw new Error(`Failed to fetch flow detail: ${res.statusText}`)
  }
  return res.json()
}

export async function triggerReplay(tier: string): Promise<{ message: string; flow: FlowRecord }> {
  const res = await fetch(`${API_BASE}/replay/${encodeURIComponent(tier)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || 'PCAP replay failed')
  }
  return res.json()
}

export async function fetchBotTiers(): Promise<BotTiersResponse> {
  const res = await fetch(`${API_BASE}/bot-tiers`)
  if (!res.ok) {
    throw new Error(`Failed to fetch bot tiers: ${res.statusText}`)
  }
  return res.json()
}

export async function fetchArchitecture(): Promise<ArchitectureResponse> {
  const res = await fetch(`${API_BASE}/architecture`)
  if (!res.ok) {
    throw new Error(`Failed to fetch architecture: ${res.statusText}`)
  }
  return res.json()
}

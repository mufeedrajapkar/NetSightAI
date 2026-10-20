import type {
  SystemStatus,
  OverviewData,
  FlowRecord,
  BotTiersResponse,
  ArchitectureResponse,
  AdversarialResponse,
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

export async function startCapture(options?: {
  filter?: string
  port?: number
  all_ip?: boolean
  interface?: string
}): Promise<{ message: string; status: string; interface: string; filter: string }> {
  const res = await fetch(`${API_BASE}/capture/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(options || {}),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || err.details || 'Failed to start live capture')
  }
  return res.json()
}

export async function stopCapture(): Promise<{
  message: string
  status: string
  packets_captured: number
  packets_parsed: number
}> {
  const res = await fetch(`${API_BASE}/capture/stop`, {
    method: 'POST',
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || 'Failed to stop live capture')
  }
  return res.json()
}

export async function fetchCaptureStatus(): Promise<any> {
  const res = await fetch(`${API_BASE}/capture/status`)
  if (!res.ok) {
    throw new Error(`Failed to fetch capture status: ${res.statusText}`)
  }
  return res.json()
}

export async function fetchAdversarial(): Promise<AdversarialResponse> {
  const res = await fetch(`${API_BASE}/adversarial`)
  if (!res.ok) {
    throw new Error(`Failed to fetch adversarial benchmark: ${res.statusText}`)
  }
  return res.json()
}


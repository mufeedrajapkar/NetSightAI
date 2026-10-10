export interface FeatureValues {
  requests_per_sec: number
  session_duration: number
  packet_size_mean: number
  packet_size_var: number
  request_interval_mean: number
  request_interval_var: number
  bytes_transferred: number
  num_connections: number
  protocol: string
}

export interface ProbabilityEstimates {
  Human: number
  Bot: number
  Suspicious: number
  [key: string]: number
}

export interface FlowRecord {
  flow_id: string
  session_id?: string
  device_id?: string
  tier?: string
  source_type: string
  source_file: string
  timestamp: string
  epoch_time: number
  expected_label: string
  predicted_label: 'Human' | 'Bot' | 'Suspicious' | string
  is_match: boolean | null
  model_type: string

  probability_estimates: ProbabilityEstimates
  features: FeatureValues
  metadata: Record<string, any>
  packet_count: number
  raw_packet_count: number
  session_duration: number
  bytes_transferred: number
  protocol: string
}

export interface SystemStatus {
  status: string
  service: string
  timestamp: number
  environment: {
    pcap_available: boolean
    is_admin: boolean
    loopback_iface: string | null
    can_capture_live: boolean
    message: string
    setup_guide: string
  }
  model: {
    is_loaded: boolean
    model_type: string
    dataset_type?: string
    dataset_note?: string
    classes: string[]
    contract_features: string[]
    numerical_features: string[]
    supported_protocols: string[]
  }
  operating_mode: string
  active_capture: {
    is_capturing: boolean
    start_time: number | null
    interface?: string | null
    filter?: string | null
    packets_seen?: number
  }
}

export interface CaptureStatusResponse {
  is_capturing: boolean
  status: 'running' | 'stopped'
  interface: string | null
  filter: string | null
  packets_seen: number
  packets_parsed: number
  start_time: number | null
  duration: number
}

export interface OverviewData {
  total_flows: number
  dataset_type?: string
  counts: {
    human: number
    bot: number
    suspicious: number
  }
  distribution: {
    name: string
    value: number
    color: string
  }[]
  capture_mode: string
  model_type: string
  recent_flows: FlowRecord[]
}

export interface BotTier {
  id: string
  name: string
  sophistication: string
  description: string
  expected_label: string
  baseline_result: string
  bot_probability: number
  human_probability: number
  latest_run?: FlowRecord | null
  behavior_notes: string
}

export interface BotTiersResponse {
  tiers: BotTier[]
  evaluation_summary: {
    total_tiers: number
    matches: number
    mismatches: number
    source: string
    limitation_note: string
  }
}

export interface ArchitectureStage {
  stage_number: number
  name: string
  domain: string
  description: string
  components: string[]
  status: string
}

export interface ArchitectureResponse {
  stages: ArchitectureStage[]
  domains: {
    computer_networks: string[]
    artificial_intelligence: string[]
  }
}

import React, { useEffect, useState } from 'react'
import { Sidebar } from './components/Sidebar'
import type { NavTab } from './components/Sidebar'
import { TopBar } from './components/TopBar'
import { OverviewPage } from './pages/OverviewPage'
import { LiveTrafficPage } from './pages/LiveTrafficPage'
import { AIAnalysisPage } from './pages/AIAnalysisPage'
import { BotAnalysisPage } from './pages/BotAnalysisPage'
import { ArchitecturePage } from './pages/ArchitecturePage'
import { AboutPage } from './pages/AboutPage'
import { FlowDetailsModal } from './components/FlowDetailsModal'
import type { SystemStatus, OverviewData, FlowRecord } from './types'
import { fetchStatus, fetchOverview, fetchFlows } from './services/api'

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('overview')
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [overview, setOverview] = useState<OverviewData | null>(null)
  const [flows, setFlows] = useState<FlowRecord[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [selectedFlow, setSelectedFlow] = useState<FlowRecord | null>(null)

  const loadAllData = async () => {
    try {
      setLoading(true)
      const [statusRes, overviewRes, flowsRes] = await Promise.all([
        fetchStatus().catch(() => null),
        fetchOverview().catch(() => null),
        fetchFlows().catch(() => ({ count: 0, flows: [] })),
      ])

      setStatus(statusRes)
      setOverview(overviewRes)
      setFlows(flowsRes.flows || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAllData()
  }, [])

  return (
    <div className="flex h-screen bg-[#0c0d12] text-gray-100 overflow-hidden font-sans">
      {/* Sidebar Navigation */}
      <Sidebar currentTab={currentTab} onSelectTab={setCurrentTab} />

      {/* Main Content Viewport */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <TopBar status={status} loading={loading} />

        <main className="flex-1 overflow-y-auto">
          {currentTab === 'overview' && (
            <OverviewPage
              data={overview}
              loading={loading}
              onRefresh={loadAllData}
              onSelectFlow={setSelectedFlow}
              onNavigateTab={setCurrentTab}
            />
          )}

          {currentTab === 'traffic' && (
            <LiveTrafficPage
              flows={flows}
              status={status}
              loading={loading}
              onSelectFlow={setSelectedFlow}
              onRefresh={loadAllData}
            />
          )}

          {currentTab === 'ai' && <AIAnalysisPage flows={flows} />}

          {currentTab === 'bots' && <BotAnalysisPage />}

          {currentTab === 'architecture' && <ArchitecturePage />}

          {currentTab === 'about' && <AboutPage />}
        </main>
      </div>

      {/* Flow Details Modal */}
      <FlowDetailsModal flow={selectedFlow} onClose={() => setSelectedFlow(null)} />
    </div>
  )
}

export default App


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
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true)
  const [selectedFlow, setSelectedFlow] = useState<FlowRecord | null>(null)

  const loadAllData = async (silent: boolean = false) => {
    try {
      if (!silent) setLoading(true)

      const [statusRes, overviewRes, flowsRes] = await Promise.all([
        fetchStatus().catch(() => null),
        fetchOverview().catch(() => null),
        fetchFlows().catch(() => ({ count: 0, flows: [] })),
      ])

      if (statusRes) setStatus(statusRes)
      if (overviewRes) setOverview(overviewRes)
      if (flowsRes?.flows) setFlows(flowsRes.flows)
    } finally {
      if (!silent) setLoading(false)
    }
  }

  useEffect(() => {
    void loadAllData(false)
  }, [])

  useEffect(() => {
    if (!autoRefresh) return

    const intervalId = window.setInterval(() => {
      void loadAllData(true)
    }, 3500)

    return () => window.clearInterval(intervalId)
  }, [autoRefresh])

  return (
    <div className="app-shell">
      <Sidebar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
      />

      <div className="app-main">
        <TopBar
          status={status}
          loading={loading}
          autoRefresh={autoRefresh}
          onToggleAutoRefresh={() => setAutoRefresh((prev) => !prev)}
        />

        <main className="app-viewport" key={currentTab}>
          <div className="app-page-transition">
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
          </div>
        </main>
      </div>

      <FlowDetailsModal
        flow={selectedFlow}
        onClose={() => setSelectedFlow(null)}
      />
    </div>
  )
}

export default App

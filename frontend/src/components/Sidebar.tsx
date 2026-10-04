import React from 'react'
import {
  LayoutDashboard,
  Activity,
  Cpu,
  Bot,
  Layers,
  Info,
  ShieldCheck,
} from 'lucide-react'

export type NavTab = 'overview' | 'traffic' | 'ai' | 'bots' | 'architecture' | 'about'

interface SidebarProps {
  currentTab: NavTab
  onSelectTab: (tab: NavTab) => void
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  const navItems: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    { id: 'overview', label: 'Overview', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'traffic', label: 'Live Traffic', icon: <Activity className="w-4 h-4" /> },
    { id: 'ai', label: 'AI Analysis', icon: <Cpu className="w-4 h-4" /> },
    { id: 'bots', label: 'Bot Analysis', icon: <Bot className="w-4 h-4" /> },
    { id: 'architecture', label: 'Architecture', icon: <Layers className="w-4 h-4" /> },
    { id: 'about', label: 'About Project', icon: <Info className="w-4 h-4" /> },
  ]

  return (
    <aside className="w-64 bg-[#11131a] border-r border-[#1f2430] flex flex-col justify-between shrink-0 select-none">
      <div>
        {/* Brand Header */}
        <div className="h-16 px-6 flex items-center gap-3 border-b border-[#1f2430]">
          <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-semibold text-sm tracking-wide text-gray-100">SentinelNet</h1>
            <p className="text-[11px] text-gray-400 font-mono">Network Intelligence</p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const isActive = currentTab === item.id
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-md text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-[#181b24]'
                }`}
              >
                <span className={isActive ? 'text-blue-400' : 'text-gray-400'}>
                  {item.icon}
                </span>
                {item.label}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-[#1f2430]">
        <div className="p-3 rounded-md bg-[#161822] border border-[#232734]">
          <div className="flex items-center justify-between text-[11px] text-gray-400 mb-1">
            <span>Pipeline</span>
            <span className="text-emerald-400 font-mono">CN + AI</span>
          </div>
          <div className="text-[10px] text-gray-400 leading-tight">
            Academic prototype for network flow behavioral classification.
          </div>
        </div>
      </div>
    </aside>
  )
}

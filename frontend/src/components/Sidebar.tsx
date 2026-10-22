
import React from 'react'
import {
  LayoutDashboard,
  Activity,
  Cpu,
  Bot,
  Layers,
  Info,
  ChevronRight,
} from 'lucide-react'

export type NavTab =
  | 'overview'
  | 'traffic'
  | 'ai'
  | 'bots'
  | 'architecture'
  | 'about'

interface SidebarProps {
  currentTab: NavTab
  onSelectTab: (tab: NavTab) => void
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
}) => {
  const navItems: {
    id: NavTab
    label: string
    description: string
    icon: React.ReactNode
  }[] = [
    {
      id: 'overview',
      label: 'Overview',
      description: 'Network summary',
      icon: <LayoutDashboard className="h-[17px] w-[17px]" />,
    },
    {
      id: 'traffic',
      label: 'Live Traffic',
      description: 'Packet monitoring',
      icon: <Activity className="h-[17px] w-[17px]" />,
    },
    {
      id: 'ai',
      label: 'AI Analysis',
      description: 'Model inference',
      icon: <Cpu className="h-[17px] w-[17px]" />,
    },
    {
      id: 'bots',
      label: 'Bot Analysis',
      description: 'Behavioral detection',
      icon: <Bot className="h-[17px] w-[17px]" />,
    },
    {
      id: 'architecture',
      label: 'Architecture',
      description: 'System pipeline',
      icon: <Layers className="h-[17px] w-[17px]" />,
    },
    {
      id: 'about',
      label: 'About Project',
      description: 'Project information',
      icon: <Info className="h-[17px] w-[17px]" />,
    },
  ]

  return (
    <aside className="flex h-full w-64 shrink-0 select-none flex-col border-r border-[#253044] bg-[#0c131e]">
      {/* Brand */}
      <div className="flex h-[100px] shrink-0 items-center gap-3 border-b border-[#253044] px-3">
        <div className="flex h-[68px] w-[68px] shrink-0 items-center justify-center">
          <img
            src="https://res.cloudinary.com/dtz0urit6/image/upload/q_auto:best,f_jpg/cloudinary-tools-uploads/e3ch7xxxvmk4juf1w46i"
            alt="NetSight AI logo"
            className="h-full w-full object-contain"
            loading="eager"
            decoding="async"
          />
        </div>

        <div className="min-w-0 flex-1">
          <h1 className="whitespace-nowrap text-sm font-bold tracking-wide text-gray-100">
            NetSight AI
          </h1>
          <p className="mt-1 whitespace-nowrap text-[10px] tracking-wide text-gray-500">
            Network Intelligence
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav
        aria-label="Main navigation"
        className="flex-1 overflow-y-auto px-3 py-5"
      >
        <div className="mb-3 px-3 text-[9px] font-semibold uppercase tracking-[0.2em] text-gray-600">
          Workspace
        </div>

        <div className="space-y-1">
          {navItems.map((item) => {
            const isActive = currentTab === item.id

            return (
              <button
                key={item.id}
                type="button"
                aria-current={isActive ? 'page' : undefined}
                onClick={() => onSelectTab(item.id)}
                className={`group relative flex w-full items-center gap-3 rounded-lg border px-3 py-3 text-left transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60 ${
                  isActive
                    ? 'border-blue-500/20 bg-blue-500/[0.09] text-blue-300'
                    : 'border-transparent text-gray-400 hover:border-[#29364a] hover:bg-[#141e2c] hover:text-gray-200'
                }`}
              >
                {isActive && (
                  <span
                    aria-hidden="true"
                    className="absolute bottom-2 left-0 top-2 w-[3px] rounded-r-full bg-blue-400"
                  />
                )}

                <span
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-500/10 text-blue-300'
                      : 'text-gray-500 group-hover:text-gray-300'
                  }`}
                >
                  {item.icon}
                </span>

                <span className="min-w-0 flex-1">
                  <span
                    className={`block text-xs font-medium ${
                      isActive ? 'text-blue-200' : ''
                    }`}
                  >
                    {item.label}
                  </span>

                  <span
                    className={`mt-1 block text-[10px] ${
                      isActive ? 'text-blue-300/60' : 'text-gray-600'
                    }`}
                  >
                    {item.description}
                  </span>
                </span>

                <ChevronRight
                  className={`h-3.5 w-3.5 shrink-0 transition-all ${
                    isActive
                      ? 'translate-x-0 text-blue-400 opacity-100'
                      : '-translate-x-1 text-gray-600 opacity-0 group-hover:translate-x-0 group-hover:opacity-100'
                  }`}
                />
              </button>
            )
          })}
        </div>
      </nav>
    </aside>
  )
}

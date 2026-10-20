import React from 'react'

interface StatCardProps {
  title: string
  value: string | number
  subtext?: string
  icon?: React.ReactNode
  accentColor?: 'blue' | 'green' | 'orange' | 'red' | 'default'
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtext,
  icon,
  accentColor = 'default',
}) => {
  const getBorderColor = () => {
    switch (accentColor) {
      case 'green':
        return 'border-emerald-500/30'
      case 'orange':
        return 'border-orange-500/30'
      case 'red':
        return 'border-rose-500/30'
      case 'blue':
        return 'border-blue-500/30'
      default:
        return 'border-[#222634]'
    }
  }

  const getTextColor = () => {
    switch (accentColor) {
      case 'green':
        return 'text-emerald-400'
      case 'orange':
        return 'text-orange-400'
      case 'red':
        return 'text-rose-400'
      case 'blue':
        return 'text-blue-400'
      default:
        return 'text-gray-100'
    }
  }

  return (
    <div className={`p-4 rounded-lg bg-[#141620] border ${getBorderColor()} transition-colors`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-gray-400 tracking-wide uppercase">{title}</span>
        {icon && <span className="text-gray-400">{icon}</span>}
      </div>
      <div className={`text-2xl font-semibold tracking-tight ${getTextColor()}`}>
        {value}
      </div>
      {subtext && (
        <div className="text-[11px] text-gray-400 mt-1 font-mono">
          {subtext}
        </div>
      )}
    </div>
  )
}

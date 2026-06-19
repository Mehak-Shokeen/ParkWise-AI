import { NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard,
  Map,
  BarChart3,
  Brain,
  Car,
  Settings,
  Shield,
  Activity,
} from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/map', icon: Map, label: 'Hotspot Map' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/model', icon: Brain, label: 'Model Insights' },
  { to: '/vehicles', icon: Car, label: 'Vehicle Search' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="w-64 flex-shrink-0 flex flex-col h-full"
      style={{
        background: 'rgba(15, 23, 42, 0.95)',
        borderRight: '1px solid rgba(255,255,255,0.05)',
      }}
    >
      {/* Brand */}
      <div className="px-5 py-6 border-b border-white/5">
        <div className="flex items-center gap-3 mb-1">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ background: 'linear-gradient(135deg, #3B82F6, #1D4ED8)' }}
          >
            <Shield size={16} className="text-white" />
          </div>
          <span className="font-bold text-white text-base tracking-tight">ParkWise AI</span>
        </div>
        <p className="text-slate-500 text-xs ml-11 leading-tight">
          Bengaluru Traffic Command Center
        </p>
      </div>

      {/* Live status */}
      <div className="px-5 py-3 border-b border-white/5">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-low opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-low" />
          </span>
          <span className="text-low text-xs font-medium">System Operational</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <p className="text-slate-600 text-xs font-semibold uppercase tracking-wider px-3 mb-3">
          Navigation
        </p>
        {navItems.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'active' : ''}`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={16} className={isActive ? 'text-accent' : 'text-slate-500'} />
                <span>{label}</span>
                {isActive && (
                  <motion.div
                    layoutId="nav-indicator"
                    className="ml-auto w-1.5 h-1.5 rounded-full bg-accent"
                  />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-white/5">
        <div className="flex items-center gap-2">
          <Activity size={12} className="text-slate-600" />
          <span className="text-slate-600 text-xs font-mono">v0.1.0 · Phase 3</span>
        </div>
        <p className="text-slate-700 text-xs mt-1">© 2024 Bengaluru Traffic Police</p>
      </div>
    </motion.aside>
  )
}

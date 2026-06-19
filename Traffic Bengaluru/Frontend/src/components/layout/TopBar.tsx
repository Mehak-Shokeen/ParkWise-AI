import { useState, useEffect } from 'react'
import { Bell, Search, User } from 'lucide-react'
import { motion } from 'framer-motion'

export default function TopBar() {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const formatted = time.toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    timeZone: 'Asia/Kolkata',
  })

  const dateFormatted = time.toLocaleDateString('en-IN', {
    weekday: 'short',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    timeZone: 'Asia/Kolkata',
  })

  return (
    <header
      className="flex items-center justify-between px-6 py-3 flex-shrink-0"
      style={{
        background: 'rgba(15, 23, 42, 0.8)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
      }}
    >
      {/* Left: live clock */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex items-center gap-3"
      >
        <div>
          <p className="font-mono text-white text-lg font-semibold leading-none">{formatted}</p>
          <p className="text-slate-500 text-xs mt-0.5">IST · {dateFormatted}</p>
        </div>
      </motion.div>

      {/* Center: search */}
      <div className="flex-1 max-w-md mx-8">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search stations, junctions, vehicles..."
            className="w-full bg-white/5 border border-white/10 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-300 placeholder-slate-600 focus:outline-none focus:border-accent/50 focus:bg-white/8 transition-all"
          />
        </div>
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-3">
        <button className="relative p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors border border-white/10">
          <Bell size={15} className="text-slate-400" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-critical rounded-full" />
        </button>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 cursor-pointer hover:bg-white/10 transition-colors">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-accent to-blue-700 flex items-center justify-center">
            <User size={12} className="text-white" />
          </div>
          <div>
            <p className="text-white text-xs font-medium">Cmd. Officer</p>
            <p className="text-slate-500 text-xs">Admin</p>
          </div>
        </div>
      </div>
    </header>
  )
}

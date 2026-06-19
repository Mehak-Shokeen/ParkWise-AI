import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
} from 'recharts'

// ─── Shared tooltip style ──────────────────────────────────────────────────────

export const DARK_TOOLTIP = {
  contentStyle: {
    background: '#1E293B',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: '8px',
    color: '#E2E8F0',
    fontSize: '12px',
    boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
  },
  labelStyle: { color: '#94A3B8', marginBottom: 4 },
  itemStyle: { color: '#CBD5E1' },
}

// ─── ViolationsLineChart ───────────────────────────────────────────────────────

interface ViolationsLineChartProps {
  data: Array<{ label: string; count: number }>
  color?: string
  height?: number
}

export function ViolationsLineChart({
  data,
  color = '#3B82F6',
  height = 220,
}: ViolationsLineChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: -10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis
          dataKey="label"
          tick={{ fill: '#64748B', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          interval={2}
        />
        <YAxis
          tick={{ fill: '#64748B', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`}
        />
        <Tooltip
          {...DARK_TOOLTIP}
          formatter={(v: number) => [v.toLocaleString('en-IN'), 'Violations']}
        />
        <Line
          type="monotone"
          dataKey="count"
          stroke={color}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: color }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

// ─── StationBarChart ───────────────────────────────────────────────────────────

interface StationBarChartProps {
  data: Array<{ station: string; count: number }>
  height?: number
}

const BAR_COLORS = [
  '#3B82F6', '#22C55E', '#F97316', '#EF4444',
  '#FACC15', '#A78BFA', '#38BDF8', '#FB7185',
  '#34D399', '#FBBF24',
]

export function StationBarChart({ data, height = 280 }: StationBarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 5, right: 60, bottom: 5, left: 10 }}
      >
        <XAxis
          type="number"
          tick={{ fill: '#64748B', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`}
        />
        <YAxis
          type="category"
          dataKey="station"
          tick={{ fill: '#94A3B8', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={115}
        />
        <Tooltip
          {...DARK_TOOLTIP}
          formatter={(v: number) => [v.toLocaleString('en-IN'), 'Violations']}
        />
        <Bar dataKey="count" radius={[0, 4, 4, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ─── DayBarChart ───────────────────────────────────────────────────────────────

interface DayBarChartProps {
  data: Array<{ day: string; count: number }>
  height?: number
}

export function DayBarChart({ data, height = 200 }: DayBarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: -10 }}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="rgba(255,255,255,0.05)"
          vertical={false}
        />
        <XAxis
          dataKey="day"
          tick={{ fill: '#64748B', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: '#64748B', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`}
        />
        <Tooltip
          {...DARK_TOOLTIP}
          formatter={(v: number) => [v.toLocaleString('en-IN'), 'Violations']}
        />
        <Bar dataKey="count" fill="#3B82F6" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

// ─── SeverityPieChart ─────────────────────────────────────────────────────────

interface SeverityPieChartProps {
  data: Array<{ name: string; value: number; color: string }>
  height?: number
}

export function SeverityPieChart({ data, height = 180 }: SeverityPieChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={50}
          outerRadius={75}
          dataKey="value"
          strokeWidth={0}
          paddingAngle={2}
        >
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip
          {...DARK_TOOLTIP}
          formatter={(v: number) => [v.toLocaleString('en-IN'), 'Violations']}
        />
        <Legend
          formatter={(value) => (
            <span style={{ color: '#94A3B8', fontSize: 11 }}>{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}

// ─── ModelRadarChart ──────────────────────────────────────────────────────────

interface ModelRadarChartProps {
  data: Array<{ metric: string; value: number }>
  height?: number
}

export function ModelRadarChart({ data, height = 240 }: ModelRadarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart data={data}>
        <PolarGrid stroke="rgba(255,255,255,0.08)" />
        <PolarAngleAxis
          dataKey="metric"
          tick={{ fill: '#94A3B8', fontSize: 11 }}
        />
        <Radar
          name="Score"
          dataKey="value"
          stroke="#3B82F6"
          fill="#3B82F6"
          fillOpacity={0.18}
          strokeWidth={2}
        />
        <Tooltip
          {...DARK_TOOLTIP}
          formatter={(v: number) => [`${v.toFixed(2)}%`, 'Score']}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}

// ─── FeatureImportanceBar ─────────────────────────────────────────────────────

interface FeatureImportanceBarProps {
  data: Array<{ feature: string; importance: number }>
  maxItems?: number
}

export function FeatureImportanceBar({
  data,
  maxItems = 10,
}: FeatureImportanceBarProps) {
  const items = data.slice(0, maxItems)
  const max = items[0]?.importance ?? 1

  return (
    <div className="space-y-2.5">
      {items.map((f, i) => (
        <div key={f.feature} className="flex items-center gap-3">
          <span className="text-slate-600 font-mono text-xs w-5 text-right flex-shrink-0">
            {i + 1}
          </span>
          <span
            className="text-slate-300 text-xs truncate flex-shrink-0"
            style={{ width: '148px' }}
          >
            {f.feature}
          </span>
          <div className="flex-1 bg-white/5 rounded-full h-1.5 overflow-hidden">
            <div
              className="h-full bg-accent rounded-full transition-all duration-700"
              style={{ width: `${(f.importance / max) * 100}%` }}
            />
          </div>
          <span className="text-accent font-mono text-xs w-14 text-right flex-shrink-0">
            {(f.importance * 100).toFixed(2)}%
          </span>
        </div>
      ))}
    </div>
  )
}

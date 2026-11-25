import { Bar, BarChart, CartesianGrid, Legend, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { METHODS, type RunsByMethod } from '../stats'
import { COLORS, LABELS } from '../theme'

interface Props {
  grouped: Map<string, RunsByMethod>
  onSelect: (instance: string) => void
}

export default function PercentChart({ grouped, onSelect }: Props) {
  // A missing value leaves the bar out, and the tooltip says "sem solução"
  const data = [...grouped].map(([instance, runs]) => ({
    instance,
    label: instance.replace('instance_', ''),
    genetic: runs.genetic?.percent_of_best ?? null,
    exact: runs.exact?.percent_of_best ?? null,
  }))

  return (
    <ResponsiveContainer width="100%" height={340}>
      <BarChart data={data} onClick={(state) => {
        const index = Number(state?.activeTooltipIndex)
        if (Number.isInteger(index) && data[index]) onSelect(data[index].instance)
      }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="label" angle={-45} textAnchor="end" height={60} interval={0} fontSize={12} />
        <YAxis domain={[0, 110]} ticks={[0, 25, 50, 75, 100]} unit="%" />
        <Tooltip formatter={(value) => (value == null ? 'sem solução' : `${Number(value).toFixed(2)}%`)} />
        <Legend verticalAlign="top" />
        <ReferenceLine y={100} stroke="currentColor" strokeDasharray="4 4" />
        {METHODS.map((method) => (
          <Bar key={method} dataKey={method} name={LABELS[method]} fill={COLORS[method]} cursor="pointer" isAnimationActive={false} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}

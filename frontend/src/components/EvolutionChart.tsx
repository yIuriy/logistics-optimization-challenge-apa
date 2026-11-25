import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { Run } from '../types'
import { COLORS } from '../theme'

interface Props {
  runs: { label: string; run: Run }[]
  bestOfficial: number | null
}

// Shades of the genetic algorithm's color, so every curve still reads as that method
const SHADES = [COLORS.genetic, '#7fb3d5', '#1b4f72', '#5dade2', '#154360']

// Extending the last value to the end of the run, to show where the search stopped improving
function points(run: Run) {
  const history = run.history ?? []
  const last = history.at(-1)
  const extended = last ? [...history, [run.elapsed_seconds, last[1]]] : history
  return extended.map(([seconds, objective]) => ({ seconds, objective }))
}

export default function EvolutionChart({ runs, bestOfficial }: Props) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="seconds" type="number" scale="log" domain={['auto', 'auto']} allowDataOverflow
          tickFormatter={(value) => `${Number(value).toPrecision(2)}`} label={{ value: 'segundos (escala log)', position: 'insideBottom', offset: -2 }} height={40} />
        <YAxis dataKey="objective" type="number" domain={['auto', 'auto']} width={70} />
        <Tooltip labelFormatter={(value) => `${Number(value).toFixed(2)} s`} formatter={(value) => Number(value).toFixed(2)} />
        <Legend verticalAlign="top" />
        {bestOfficial !== null && (
          <ReferenceLine y={bestOfficial} stroke={COLORS.official} strokeDasharray="5 5" label={{ value: 'melhor oficial', fill: COLORS.official, position: 'insideBottomRight' }} />
        )}
        {runs.map(({ label, run }, index) => (
          <Line key={label} data={points(run)} dataKey="objective" name={label} type="stepAfter"
            stroke={SHADES[index % SHADES.length]} dot={false} isAnimationActive={false} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}

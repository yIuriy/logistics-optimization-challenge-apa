import type { Run } from '../types'
import { formatNumber, formatPercent, runLabel } from '../theme'

interface Props {
  runs: Run[]
}

export default function RunComparison({ runs }: Props) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>execução</th>
            <th className="number">objetivo</th>
            <th className="number">% do melhor oficial</th>
            <th className="number">gerações</th>
            <th className="number">segundos</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={runLabel(run)}>
              <td>{runLabel(run)}</td>
              <td className="number">{formatNumber(run.objective)}</td>
              <td className="number">{formatPercent(run.percent_of_best)}</td>
              <td className="number">{run.generations ?? '—'}</td>
              <td className="number">{run.elapsed_seconds.toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

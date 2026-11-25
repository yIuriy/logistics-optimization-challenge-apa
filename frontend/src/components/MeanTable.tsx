import { DATASETS, METHODS, OVERALL, filterByDataset, meanPercent, type RunsByMethod } from '../stats'
import { LABELS, formatPercent } from '../theme'

interface Props {
  grouped: Map<string, RunsByMethod>
}

// Same table as "Médias da porcentagem do melhor valor oficial" in results/summary.md
export default function MeanTable({ grouped }: Props) {
  const groups = [
    ...DATASETS.map((dataset) => ({ label: `Conjunto ${dataset}`, runs: filterByDataset(grouped, dataset) })),
    { label: OVERALL, runs: filterByDataset(grouped, null) },
  ].filter((group) => group.runs.size > 0)

  return (
    <table className="compact">
      <thead>
        <tr>
          <th>conjunto</th>
          {METHODS.map((method) => (
            <th key={method} className="number">{LABELS[method]}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {groups.map(({ label, runs }) => (
          <tr key={label}>
            <td>{label} ({runs.size} instâncias)</td>
            {METHODS.map((method) => (
              <td key={method} className="number">{formatPercent(meanPercent(runs, method))}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

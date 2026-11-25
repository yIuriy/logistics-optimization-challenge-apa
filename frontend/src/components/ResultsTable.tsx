import { useState } from 'react'
import type { RunsByMethod } from '../stats'
import { formatNumber, formatPercent } from '../theme'

interface Props {
  grouped: Map<string, RunsByMethod>
  selected: string | null
  onSelect: (instance: string) => void
}

interface Row {
  instance: string
  best: number | null
  exact: number | null
  upper: number | null
  genetic: number | null
  percent: number | null
}

type Column = keyof Row

// Same columns as the comparison table of results/summary.md
const COLUMNS: [Column, string][] = [
  ['instance', 'instância'],
  ['best', 'melhor oficial'],
  ['exact', 'algoritmo exato'],
  ['upper', 'limite superior do algoritmo exato'],
  ['genetic', 'algoritmo genético'],
  ['percent', '% do melhor (algoritmo genético)'],
]

function toRow(instance: string, runs: RunsByMethod): Row {
  const anyRun = runs.genetic ?? runs.exact
  return {
    instance,
    best: anyRun?.best_official ?? null,
    exact: runs.exact?.objective ?? null,
    upper: runs.exact?.upper_bound ?? null,
    genetic: runs.genetic?.objective ?? null,
    percent: runs.genetic?.percent_of_best ?? null,
  }
}

// Putting missing values last, whatever the direction
function compare(a: Row, b: Row, column: Column) {
  const [left, right] = [a[column], b[column]]
  if (left === right) return 0
  if (left === null) return 1
  if (right === null) return -1
  return left < right ? -1 : 1
}

export default function ResultsTable({ grouped, selected, onSelect }: Props) {
  const [sort, setSort] = useState<{ column: Column; ascending: boolean }>({ column: 'instance', ascending: true })
  const rows = [...grouped].map(([instance, runs]) => toRow(instance, runs))
  rows.sort((a, b) => (sort.ascending ? 1 : -1) * compare(a, b, sort.column))

  const toggle = (column: Column) =>
    setSort((current) => ({ column, ascending: current.column === column ? !current.ascending : true }))

  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {COLUMNS.map(([column, label]) => (
              <th key={column} className={column === 'instance' ? '' : 'number'}>
                <button type="button" className="sort" onClick={() => toggle(column)}>
                  {label} {sort.column === column ? (sort.ascending ? '▲' : '▼') : ''}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.instance} className={row.instance === selected ? 'selected' : ''} onClick={() => onSelect(row.instance)}>
              <td>{row.instance}</td>
              <td className="number">{formatNumber(row.best)}</td>
              <td className="number">{formatNumber(row.exact)}</td>
              <td className="number">{formatNumber(row.upper)}</td>
              <td className="number">{formatNumber(row.genetic)}</td>
              <td className="number">{formatPercent(row.percent)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// Same rules as src/order_selection/results.py, so the page and the charts agree
import type { Method, Run } from './types'

export type Dataset = 'B' | 'X'
export const DATASETS: Dataset[] = ['B', 'X']
export const METHODS: Method[] = ['genetic', 'exact']
export const OVERALL = 'Geral'

export type RunsByMethod = Partial<Record<Method, Run>>

export function datasetOf(instance: string): Dataset | null {
  if (instance.startsWith('b_')) return 'B'
  if (instance.startsWith('x_')) return 'X'
  return null
}

// Keeping the first run of each method per instance, like runs_by_instance
export function runsByInstance(runs: Run[]): Map<string, RunsByMethod> {
  const grouped = new Map<string, RunsByMethod>()
  for (const run of runs) {
    const methods = grouped.get(run.instance) ?? {}
    methods[run.method] ??= run
    grouped.set(run.instance, methods)
  }
  return new Map([...grouped].sort(([a], [b]) => a.localeCompare(b)))
}

// A run without a solution counts as 0%, as an infeasible solution scores zero
export const percentOrZero = (run: Run | undefined) => run?.percent_of_best ?? 0

export function meanPercent(grouped: Map<string, RunsByMethod>, method: Method) {
  const values = [...grouped.values()].map((runs) => percentOrZero(runs[method]))
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null
}

export function filterByDataset(grouped: Map<string, RunsByMethod>, dataset: Dataset | null) {
  return new Map(
    [...grouped].filter(([name]) =>
      dataset === null ? datasetOf(name) !== null : datasetOf(name) === dataset,
    ),
  )
}

import type { Method, Run } from './types'

// Same colors and labels as src/order_selection/charts.py and the slides
export const COLORS = { genetic: '#2a7ab0', exact: '#e07b39', official: '#2e8b57' }

export const LABELS: Record<Method, string> = {
  genetic: 'algoritmo genético',
  exact: 'algoritmo exato',
}

export const formatNumber = (value: number | null | undefined, digits = 2) =>
  value == null ? 'sem solução' : value.toFixed(digits)

export const formatPercent = (value: number | null | undefined) =>
  value == null ? 'sem solução' : `${value.toFixed(2)}%`

// Describing a run by where it came from and the parameters in its file name
export const runLabel = (run: Run) =>
  `${run.source === 'batch' ? 'lote final' : 'tela'}: pop ${run.parameters.population_size}, torneio ${run.parameters.tournament_size}, mutação ${run.parameters.mutation_rate}, semente ${run.parameters.seed}, ${run.parameters.time_limit_seconds} s`

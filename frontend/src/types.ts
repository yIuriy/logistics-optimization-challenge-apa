// Shapes of the JSON that server.py returns (formats of issues #13, #14 and #18)

export type Method = 'genetic' | 'exact'

export interface Run {
  instance: string
  method: Method
  n_orders: number
  parameters: Record<string, number>
  objective: number | null
  best_official: number | null
  percent_of_best: number | null
  elapsed_seconds: number
  source: 'batch' | 'web'
  // Genetic algorithm only
  generations?: number
  history?: [number, number][]
  // Exact algorithm only
  lower_bound?: number | null
  upper_bound?: number | null
  status?: string
}

export interface InstanceInfo {
  instance: string
  dataset: 'B' | 'X' | null
  n_orders: number
  best_official: number | null
}

export interface GeneticParameters {
  population_size: number
  tournament_size: number
  mutation_rate: number
  max_generations: number
  seed: number
  time_limit_seconds: number
}

export interface Defaults {
  parameters: GeneticParameters
  max_time_limit_seconds: number
}

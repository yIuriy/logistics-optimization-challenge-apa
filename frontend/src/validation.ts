// Same rules as src/order_selection/run_request.py, checked before sending
import type { GeneticParameters } from './types'

const INTEGER_MINIMUMS: [keyof GeneticParameters, number][] = [
  ['population_size', 1],
  ['tournament_size', 1],
  ['max_generations', 1],
  ['seed', 0],
]

export function validateParameters(parameters: GeneticParameters, maxTimeLimit: number): string | null {
  for (const [name, minimum] of INTEGER_MINIMUMS) {
    const value = parameters[name]
    if (!Number.isInteger(value) || value < minimum) return `${name} deve ser um inteiro maior ou igual a ${minimum}`
  }
  if (parameters.tournament_size > parameters.population_size) {
    return 'tournament_size deve ser menor ou igual a population_size'
  }
  const rate = parameters.mutation_rate
  if (!Number.isFinite(rate) || rate < 0 || rate > 1) return 'mutation_rate deve estar entre 0 e 1'
  const limit = parameters.time_limit_seconds
  if (!Number.isFinite(limit) || limit <= 0 || limit > maxTimeLimit) {
    return `time_limit_seconds deve estar entre 0 e ${maxTimeLimit}`
  }
  return null
}

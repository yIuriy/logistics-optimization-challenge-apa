import type { RunsByMethod } from '../stats'
import { LABELS, formatNumber, formatPercent } from '../theme'
import EvolutionChart from './EvolutionChart'

// Status names of exact_algorithm.solve, written for the audience
const STATUS: Record<string, string> = {
  optimal: 'ótimo provado',
  time_limit: 'parou no tempo limite',
  no_solution: 'sem solução',
}

interface Props {
  instance: string
  runs: RunsByMethod
}

export default function InstanceDetail({ instance, runs }: Props) {
  const { genetic, exact } = runs
  const bestOfficial = (genetic ?? exact)?.best_official ?? null

  return (
    <section className="card">
      <h3>{instance}</h3>
      <dl className="facts">
        <dt>melhor oficial</dt><dd>{formatNumber(bestOfficial)}</dd>
        <dt>{LABELS.genetic}</dt><dd>{formatNumber(genetic?.objective)} ({formatPercent(genetic?.percent_of_best)})</dd>
        <dt>gerações</dt><dd>{genetic?.generations ?? '—'}</dd>
        <dt>limite inferior do algoritmo exato</dt><dd>{formatNumber(exact?.lower_bound)}</dd>
        <dt>limite superior do algoritmo exato</dt><dd>{formatNumber(exact?.upper_bound)}</dd>
        <dt>situação do algoritmo exato</dt><dd>{exact?.status ? (STATUS[exact.status] ?? exact.status) : 'sem solução'}</dd>
      </dl>
      {genetic?.history?.length ? (
        <>
          <h4>Evolução do algoritmo genético</h4>
          <EvolutionChart runs={[{ label: LABELS.genetic, run: genetic }]} bestOfficial={bestOfficial} />
        </>
      ) : null}
    </section>
  )
}

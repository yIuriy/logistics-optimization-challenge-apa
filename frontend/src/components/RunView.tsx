import { useEffect, useState } from 'react'
import { postRun } from '../api'
import type { Defaults, GeneticParameters, InstanceInfo, Run } from '../types'
import { formatNumber, formatPercent, runLabel } from '../theme'
import EvolutionChart from './EvolutionChart'
import RunComparison from './RunComparison'
import RunForm from './RunForm'

interface Props {
  instances: InstanceInfo[]
  defaults: Defaults
  runs: Run[]
  onRunFinished: (run: Run) => void
}

// Ticking the elapsed time while a run is going, so the audience sees it is alive
function useElapsedSeconds(startedAt: number | null) {
  const [now, setNow] = useState(() => performance.now())
  useEffect(() => {
    if (startedAt === null) return
    const timer = setInterval(() => setNow(performance.now()), 200)
    return () => clearInterval(timer)
  }, [startedAt])
  return startedAt === null ? 0 : Math.max(0, now - startedAt) / 1000
}

export default function RunView({ instances, defaults, runs, onRunFinished }: Props) {
  const [instance, setInstance] = useState(instances[0]?.instance ?? '')
  const [startedAt, setStartedAt] = useState<number | null>(null)
  const running = startedAt !== null
  const [error, setError] = useState<string | null>(null)
  const [lastRun, setLastRun] = useState<Run | null>(null)
  const elapsed = useElapsedSeconds(startedAt)

  const submit = async (parameters: GeneticParameters) => {
    setStartedAt(performance.now())
    setError(null)
    try {
      const run = await postRun(instance, parameters)
      setLastRun(run)
      onRunFinished(run)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught))
    } finally {
      setStartedAt(null)
    }
  }

  const previous = runs.filter((run) => run.instance === instance && run.method === 'genetic')
  const shown = lastRun?.instance === instance ? lastRun : null
  const bestOfficial = instances.find((info) => info.instance === instance)?.best_official ?? null

  return (
    <div className="run-layout">
      <RunForm instances={instances} defaults={defaults} instance={instance} running={running}
        onInstanceChange={setInstance} onSubmit={submit} />
      <div>
        {running && <p className="card status">Executando… {elapsed.toFixed(1)} s</p>}
        {error && <p className="card error">{error}</p>}
        {shown && (
          <section className="card">
            <h2>Última execução</h2>
            <dl className="facts">
              <dt>objetivo</dt><dd>{formatNumber(shown.objective)}</dd>
              <dt>% do melhor oficial</dt><dd>{formatPercent(shown.percent_of_best)}</dd>
              <dt>gerações</dt><dd>{shown.generations}</dd>
            </dl>
          </section>
        )}
        {previous.length > 0 && (
          <section className="card">
            <h2>Evolução do algoritmo genético em {instance}</h2>
            <EvolutionChart runs={previous.map((run) => ({ label: runLabel(run), run }))} bestOfficial={bestOfficial} />
            <RunComparison runs={previous} />
          </section>
        )}
      </div>
    </div>
  )
}

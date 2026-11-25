import { useEffect, useState } from 'react'
import { fetchDefaults, fetchInstances, fetchResults } from './api'
import ResultsView from './components/ResultsView'
import RunView from './components/RunView'
import type { Defaults, InstanceInfo, Run } from './types'

type Tab = 'results' | 'run'

interface Data {
  runs: Run[]
  instances: InstanceInfo[]
  defaults: Defaults
}

export default function App() {
  const [tab, setTab] = useState<Tab>('results')
  const [data, setData] = useState<Data | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([fetchResults(), fetchInstances(), fetchDefaults()])
      .then(([runs, instances, defaults]) => setData({ runs, instances, defaults }))
      .catch((caught: Error) => setError(caught.message))
  }, [])

  // Replacing an older run with the same file name, as the server overwrote it
  const addRun = (run: Run) =>
    setData((current) => current && {
      ...current,
      runs: [...current.runs.filter((old) => !(old.source === 'web' && sameRun(old, run))), run],
    })

  return (
    <>
      <header>
        <h1>Seleção de pedidos em ondas</h1>
        <nav className="segmented">
          <button type="button" className={tab === 'results' ? 'active' : ''} onClick={() => setTab('results')}>Resultados</button>
          <button type="button" className={tab === 'run' ? 'active' : ''} onClick={() => setTab('run')}>Execução</button>
        </nav>
      </header>
      <main>
        {error && <p className="card error">Não foi possível falar com o servidor: {error}</p>}
        {!data && !error && <p>Carregando…</p>}
        {data && tab === 'results' && <ResultsView runs={data.runs} />}
        {data && tab === 'run' && (
          <RunView instances={data.instances} defaults={data.defaults} runs={data.runs} onRunFinished={addRun} />
        )}
      </main>
    </>
  )
}

// Two runs share a file when the instance and the tagged parameters match (batch_runner.parameter_tag)
function sameRun(a: Run, b: Run) {
  const tagged = ['population_size', 'tournament_size', 'mutation_rate', 'seed']
  return a.instance === b.instance && tagged.every((name) => a.parameters[name] === b.parameters[name])
}

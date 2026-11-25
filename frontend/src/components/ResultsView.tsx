import { useState } from 'react'
import { filterByDataset, runsByInstance, type Dataset } from '../stats'
import type { Run } from '../types'
import DatasetFilter from './DatasetFilter'
import InstanceDetail from './InstanceDetail'
import MeanTable from './MeanTable'
import PercentChart from './PercentChart'
import ResultsTable from './ResultsTable'

interface Props {
  runs: Run[]
}

export default function ResultsView({ runs }: Props) {
  const [dataset, setDataset] = useState<Dataset | null>(null)
  const [selected, setSelected] = useState<string | null>(null)

  // Comparing only the final batch, the same runs as summary.md and the charts
  const grouped = runsByInstance(runs.filter((run) => run.source === 'batch'))
  const visible = filterByDataset(grouped, dataset)

  if (grouped.size === 0) return <p>Nenhum resultado em results/. Rode um lote antes.</p>

  return (
    <>
      <section className="card">
        <h2>Média da porcentagem do melhor valor oficial</h2>
        <MeanTable grouped={grouped} />
      </section>
      <section className="card">
        <div className="card-header">
          <h2>Porcentagem do melhor valor oficial por instância</h2>
          <DatasetFilter value={dataset} onChange={setDataset} />
        </div>
        <PercentChart grouped={visible} onSelect={setSelected} />
      </section>
      {selected && grouped.has(selected) && <InstanceDetail instance={selected} runs={grouped.get(selected)!} />}
      <section className="card">
        <h2>Tabela comparativa</h2>
        <p className="hint">Clique numa coluna para ordenar e numa linha para ver os detalhes da instância.</p>
        <ResultsTable grouped={visible} selected={selected} onSelect={setSelected} />
      </section>
    </>
  )
}

import { useState, type FormEvent } from 'react'
import type { Defaults, GeneticParameters, InstanceInfo } from '../types'
import { validateParameters } from '../validation'

interface Props {
  instances: InstanceInfo[]
  defaults: Defaults
  instance: string
  running: boolean
  onInstanceChange: (instance: string) => void
  onSubmit: (parameters: GeneticParameters) => void
}

// Field names are the parameter names of issues #13 and #14
const FIELDS: [keyof GeneticParameters, string, number][] = [
  ['population_size', 'tamanho da população', 1],
  ['tournament_size', 'tamanho do torneio', 1],
  ['mutation_rate', 'taxa de mutação', 0.001],
  ['max_generations', 'número máximo de gerações', 1],
  ['seed', 'semente', 1],
  ['time_limit_seconds', 'tempo limite (segundos)', 1],
]

export default function RunForm({ instances, defaults, instance, running, onInstanceChange, onSubmit }: Props) {
  const [parameters, setParameters] = useState<GeneticParameters>(defaults.parameters)
  const error = validateParameters(parameters, defaults.max_time_limit_seconds)

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!error && !running) onSubmit(parameters)
  }

  return (
    <form className="card run-form" onSubmit={submit}>
      <label>
        instância
        <select value={instance} onChange={(event) => onInstanceChange(event.target.value)} disabled={running}>
          {instances.map((info) => (
            <option key={info.instance} value={info.instance}>
              {info.instance} ({info.n_orders} pedidos)
            </option>
          ))}
        </select>
      </label>
      {FIELDS.map(([name, label, step]) => (
        <label key={name}>
          {label} <code>{name}</code>
          <input
            type="number"
            step={step}
            value={Number.isNaN(parameters[name]) ? '' : parameters[name]}
            disabled={running}
            onChange={(event) => setParameters({ ...parameters, [name]: event.target.valueAsNumber })}
          />
        </label>
      ))}
      {error && <p className="error">{error}</p>}
      <button type="submit" className="primary" disabled={running || error !== null}>
        {running ? 'Executando…' : 'Executar algoritmo genético'}
      </button>
    </form>
  )
}

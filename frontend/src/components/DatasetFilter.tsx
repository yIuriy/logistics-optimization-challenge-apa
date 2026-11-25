import { DATASETS, type Dataset } from '../stats'

interface Props {
  value: Dataset | null
  onChange: (dataset: Dataset | null) => void
}

export default function DatasetFilter({ value, onChange }: Props) {
  const options: [Dataset | null, string][] = [
    [null, 'Todos'],
    ...DATASETS.map((dataset): [Dataset, string] => [dataset, `Conjunto ${dataset}`]),
  ]
  return (
    <div className="segmented" role="group" aria-label="Filtro por conjunto">
      {options.map(([dataset, label]) => (
        <button
          key={label}
          type="button"
          className={dataset === value ? 'active' : ''}
          onClick={() => onChange(dataset)}
        >
          {label}
        </button>
      ))}
    </div>
  )
}

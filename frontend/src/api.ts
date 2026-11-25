import type { Defaults, InstanceInfo, Run } from './types'

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init)
  const content = await response.json()
  // Showing the server's own message, which already explains what was wrong
  if (!response.ok) throw new Error(content.error ?? `erro ${response.status}`)
  return content as T
}

export const fetchResults = () => getJson<Run[]>('/api/results')
export const fetchInstances = () => getJson<InstanceInfo[]>('/api/instances')
export const fetchDefaults = () => getJson<Defaults>('/api/defaults')

export const postRun = (instance: string, parameters: object) =>
  getJson<Run>('/api/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ instance, method: 'genetic', parameters }),
  })

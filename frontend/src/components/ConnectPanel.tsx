/**
 * Header bar + dialog for connecting the app to the user's own database.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Database, Loader2, Plug, X } from 'lucide-react'

import { connectAPI } from '@/services/api'
import { useSessionStore } from '@/stores/sessionStore'
import { useGraphStore } from '@/stores/graphStore'
import { useChatStore } from '@/stores/chatStore'

const TEMPLATES: Record<string, string> = {
  PostgreSQL: 'postgresql://user:password@host:5432/dbname',
  'MySQL / MariaDB': 'mysql://user:password@host:3306/dbname',
  'SQL Server': 'mssql://user:password@host:1433/dbname',
  Oracle: 'oracle://user:password@host:1521/?service_name=SERVICE',
}

function errorMessage(err: any): string {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (err?.code === 'ECONNABORTED') return 'The connection timed out. Is the database reachable from the internet?'
  return 'Something went wrong. Please try again.'
}

function resetWorkspace() {
  useGraphStore.getState().clearGraph()
  useGraphStore.getState().clearFlowHighlight()
  useChatStore.getState().clearMessages()
}

export default function ConnectPanel() {
  const { session, setSession } = useSessionStore()
  const [open, setOpen] = useState(false)
  const [dbType, setDbType] = useState('PostgreSQL')
  const [url, setUrl] = useState('')
  const [accessCode, setAccessCode] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { data: config } = useQuery({ queryKey: ['connect-config'], queryFn: connectAPI.getConfig })

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const r = await connectAPI.connect(url.trim(), accessCode || undefined)
      resetWorkspace()
      setSession({
        sessionId: r.session_id,
        dialect: r.dialect,
        database: r.database,
        tables: r.tables,
        nodes: r.nodes,
        edges: r.edges,
      })
      setUrl('') // don't keep credentials in component state
      setOpen(false)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const disconnect = async () => {
    try {
      await connectAPI.disconnect()
    } catch {
      /* session may already be gone */
    }
    resetWorkspace()
    setSession(null)
  }

  return (
    <>
      <header className="flex items-center justify-between px-4 py-2 border-b border-border bg-white">
        <div className="flex items-center gap-2 text-sm">
          <Database className="w-4 h-4 text-blue-600" />
          {session ? (
            <span>
              Connected to <strong>{session.database}</strong>{' '}
              <span className="text-gray-500">
                ({session.dialect} · {session.tables} tables · {session.nodes} nodes · {session.edges} edges)
              </span>
            </span>
          ) : (
            <span className="text-gray-600">
              {config?.sample_data_available
                ? 'Showing built-in sample data. Connect your database to replace it.'
                : 'No database connected'}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {session && (
            <button onClick={disconnect} className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded">
              Disconnect
            </button>
          )}
          <button
            onClick={() => setOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <Plug className="w-4 h-4" />
            {session ? 'Switch database' : 'Connect your database'}
          </button>
        </div>
      </header>

      {open && (
        <div className="fixed inset-0 z-[100] bg-black/40 flex items-center justify-center p-4" role="dialog" aria-modal="true">
          <form onSubmit={submit} className="bg-white rounded-lg shadow-xl w-full max-w-lg p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Connect your database</h2>
              <button type="button" onClick={() => setOpen(false)} aria-label="Close">
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="text-xs bg-amber-50 border border-amber-200 text-amber-900 rounded p-3 space-y-1">
              <p><strong>Use a read-only database user.</strong> Queries are checked and run read-only, but a read-only account is the strongest protection.</p>
              <p>The database must be reachable from the internet. Your URL is held in server memory for {config?.session_ttl_minutes ?? 30} minutes and is never stored.</p>
            </div>

            <label className="block text-sm">
              <span className="text-gray-700">Database type</span>
              <select
                value={dbType}
                onChange={(e) => setDbType(e.target.value)}
                className="mt-1 w-full border border-gray-300 rounded px-3 py-2"
              >
                {Object.keys(TEMPLATES).map((t) => (
                  <option key={t}>{t}</option>
                ))}
              </select>
            </label>

            <label className="block text-sm">
              <span className="text-gray-700">Connection URL</span>
              <input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder={TEMPLATES[dbType]}
                autoComplete="off"
                spellCheck={false}
                required
                className="mt-1 w-full border border-gray-300 rounded px-3 py-2 font-mono text-sm"
              />
            </label>

            {config?.access_code_required && (
              <label className="block text-sm">
                <span className="text-gray-700">Access code</span>
                <input
                  type="password"
                  value={accessCode}
                  onChange={(e) => setAccessCode(e.target.value)}
                  autoComplete="off"
                  required
                  className="mt-1 w-full border border-gray-300 rounded px-3 py-2"
                />
              </label>
            )}

            {error && <p className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2">{error}</p>}

            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setOpen(false)} className="px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded">
                Cancel
              </button>
              <button
                type="submit"
                disabled={busy}
                className="flex items-center gap-2 px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-60"
              >
                {busy && <Loader2 className="w-4 h-4 animate-spin" />}
                {busy ? 'Connecting…' : 'Connect'}
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  )
}

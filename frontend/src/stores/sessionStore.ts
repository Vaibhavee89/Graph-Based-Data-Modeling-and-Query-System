/**
 * Connection session state. The token lives in sessionStorage only (cleared when the tab closes);
 * database credentials are never stored in the browser.
 */
import { create } from 'zustand'

export interface SessionInfo {
  sessionId: string
  dialect: string
  database: string
  tables: number
  nodes: number
  edges: number
}

const KEY = 'graph-session'

function load(): SessionInfo | null {
  try {
    const raw = sessionStorage.getItem(KEY)
    return raw ? (JSON.parse(raw) as SessionInfo) : null
  } catch {
    return null
  }
}

interface SessionStore {
  session: SessionInfo | null
  setSession: (s: SessionInfo | null) => void
}

export const useSessionStore = create<SessionStore>((set) => ({
  session: load(),
  setSession: (session) => {
    try {
      if (session) sessionStorage.setItem(KEY, JSON.stringify(session))
      else sessionStorage.removeItem(KEY)
    } catch {
      /* storage unavailable: keep in memory only */
    }
    set({ session })
  },
}))

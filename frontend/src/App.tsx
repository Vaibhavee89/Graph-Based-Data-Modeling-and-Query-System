import { useEffect } from 'react'
import { healthCheck } from './services/api'
import GraphCanvas from './components/GraphCanvas/GraphCanvas'
import ChatInterface from './components/ChatInterface/ChatInterface'
import ConnectPanel from './components/ConnectPanel'
import { useSessionStore } from './stores/sessionStore'

function App() {
  const sessionId = useSessionStore((st) => st.session?.sessionId ?? 'demo')

  useEffect(() => {
    // Check backend health on mount
    healthCheck()
      .then((data) => {
        console.log('Backend health check:', data)
      })
      .catch((error) => {
        console.error('Backend connection failed:', error)
      })
  }, [])

  return (
    <div className="w-full h-full flex flex-col">
      <ConnectPanel />
      {/* Remount the workspace whenever the data source changes */}
      <div key={sessionId} className="flex-1 min-h-0 flex">
        {/* Graph Canvas - Left 60% */}
        <div className="w-[60%] h-full border-r border-border bg-slate-50">
          <GraphCanvas />
        </div>

        {/* Chat Interface - Right 40% */}
        <div className="w-[40%] h-full bg-background">
          <ChatInterface />
        </div>
      </div>
    </div>
  )
}

export default App

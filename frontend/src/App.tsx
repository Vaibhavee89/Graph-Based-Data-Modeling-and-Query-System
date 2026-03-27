import { useEffect } from 'react'
import { healthCheck } from './services/api'
import GraphCanvas from './components/GraphCanvas/GraphCanvas'
import ChatInterface from './components/ChatInterface/ChatInterface'

function App() {
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
    <div className="w-full h-full flex">
      {/* Graph Canvas - Left 60% */}
      <div className="w-[60%] h-full border-r border-border bg-slate-50">
        <GraphCanvas />
      </div>

      {/* Chat Interface - Right 40% */}
      <div className="w-[40%] h-full bg-background">
        <ChatInterface />
      </div>
    </div>
  )
}

export default App

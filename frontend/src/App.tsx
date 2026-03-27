import { useEffect } from 'react'
import { healthCheck } from './services/api'

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
        <div className="w-full h-full flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-700 mb-2">
              Graph Canvas
            </h2>
            <p className="text-gray-500">
              Graph visualization will be rendered here
            </p>
          </div>
        </div>
      </div>

      {/* Chat Interface - Right 40% */}
      <div className="w-[40%] h-full bg-background">
        <div className="w-full h-full flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-700 mb-2">
              Chat Interface
            </h2>
            <p className="text-gray-500">
              Natural language query interface will be here
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App

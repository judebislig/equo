import { useState, useEffect } from 'react'
import Dashboard from './pages/Dashboard'
import LogMeal from './pages/LogMeal'
import LogWorkout from './pages/LogWorkout'

export default function App() {
  const [page, setPage] = useState(window.location.pathname)

  if (page === "/log-meal") return <LogMeal />
  if (page === "/log-workout") return <LogWorkout />
  return <Dashboard />
}
